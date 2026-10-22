#!/usr/bin/env python3
"""collab.py — 让多个 AI 对话（或人）互相留消息、被唤醒的最小工具集。

不依赖任何第三方库，只用标准库；Windows / macOS / Linux 均可。

核心思路
--------
1. 写消息 → 立刻把收件人的 flag 置为「有新内容」
2. 收件方在自己的会话里挂一个「等待任务」（本地阻塞，不惊动模型）
3. flag 变化 → 等待任务退出 → 会话被唤醒 → 读消息 → flag 归零 → 重新挂起

空闲时零成本（等待任务只是本地轮询一个几字节的 JSON 文件）。

命令
----
    python collab.py init --people A,B,C            # 初始化（生成 collab.json）
    python collab.py post B "内容" --from A          # 给 B 留言（自动置 B 的 flag）
    python collab.py poll --as B                     # 读留言并把 flag 归零
    python collab.py wait --as B --timeout 14400     # 后台等待（醒来即退出）
    python collab.py flag --as B                     # 只看未读数
    python collab.py status                          # 所有人状态
    python collab.py daemon --as B --interval 60     # 常驻：日志/状态监控（可选）
    python collab.py selftest                        # 通道自检
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

VERSION = "1.0.0"
CONFIG_NAME = "collab.json"

# ---------------------------------------------------------------- 基础

ROOT = Path(os.environ.get("COLLAB_ROOT") or Path(__file__).resolve().parent).resolve()


def cfg_path() -> Path:
    return ROOT / CONFIG_NAME


def cfg() -> dict:
    try:
        j = json.loads(cfg_path().read_text(encoding="utf-8"))
        if isinstance(j.get("people"), list) and j["people"]:
            j.setdefault("board", "board/messages.jsonl")
            j.setdefault("inbox", "inbox")
            j.setdefault("logs", "logs")
            return j
    except Exception:
        pass
    return {"people": [], "board": "board/messages.jsonl",
            "inbox": "inbox", "logs": "logs"}


def path_of(key: str) -> Path:
    return ROOT / cfg()[key]


def board_path() -> Path:
    return path_of("board")


def inbox_dir(who: str) -> Path:
    p = path_of("inbox") / who.upper()
    p.mkdir(parents=True, exist_ok=True)
    return p


def people() -> list[str]:
    return [str(x).strip() for x in cfg().get("people") or []]


def valid_who(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_-]{1,16}", str(name).strip()))


def now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------- 文件锁

def _lock(fh) -> None:
    try:
        import msvcrt
        msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
    except Exception:
        try:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        except Exception:
            pass


def _unlock(fh) -> None:
    try:
        import msvcrt
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    except Exception:
        try:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass


def load_json(p: Path, default: dict) -> dict:
    try:
        return {**default, **json.loads(p.read_text(encoding="utf-8"))}
    except Exception:
        return dict(default)


def save_json(p: Path, data: dict) -> None:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(p)
    except Exception:
        pass


# ---------------------------------------------------------------- flag

def flag_of(who: str) -> dict:
    return load_json(inbox_dir(who) / "flag.json",
                     {"unread": 0, "last_kind": "", "last_ts": "", "seq": 0})


def bump_flag(who: str, kind: str = "新消息") -> None:
    if not valid_who(who):
        return
    f = inbox_dir(who) / "flag.json"
    for _ in range(5):
        cur = flag_of(who)
        cur["unread"] = int(cur.get("unread") or 0) + 1
        cur["last_kind"] = kind
        cur["last_ts"] = now()
        cur["seq"] = int(cur.get("seq") or 0) + 1
        save_json(f, cur)
        return


# ---------------------------------------------------------------- 写消息

def cmd_init(a) -> int:
    ids = [x.strip() for x in a.people.replace("，", ",").split(",") if x.strip()]
    bad = [x for x in ids if not valid_who(x)]
    if bad:
        print(f"身份名不合法（只允许字母数字下划线连字符，1~16 位）: {bad}")
        return 1
    ROOT.mkdir(parents=True, exist_ok=True)
    save_json(cfg_path(), {"people": ids, "board": "board/messages.jsonl",
                           "inbox": "inbox", "logs": "logs",
                           "created": now(), "version": VERSION})
    board_path().parent.mkdir(parents=True, exist_ok=True)
    board_path().touch(exist_ok=True)
    for p in ids:
        inbox_dir(p)
    print(f"已初始化：{ROOT}")
    print(f"  身份：{', '.join(ids)}")
    print(f"  消息板：{board_path()}")
    print(f"  收件箱：{path_of('inbox')}")
    print("\n下一步（每个身份在自己的会话里）：")
    print(f"  python collab.py wait --as {ids[0]} --timeout 14400")
    return 0


def cmd_post(a) -> int:
    body = a.body if isinstance(a.body, str) else " ".join(a.body)
    to = a.to.upper()
    frm = (a.sender or "unknown").upper()
    if not valid_who(to):
        print(f"收件人名字不合法：{to}")
        return 1
    if to not in people():
        print(f"提示：{to} 不在 collab.json 的 people 里（仍会写入）")
    bp = board_path()
    bp.parent.mkdir(parents=True, exist_ok=True)
    lock = bp.parent / ".write.lock"
    with open(lock, "a+b") as lk:
        _lock(lk)
        try:
            with open(bp, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": now(), "from": frm, "to": to,
                                    "body": body}, ensure_ascii=False) + "\n")
                f.flush()
        finally:
            _unlock(lk)
    bump_flag(to)
    print(f"已留言给 {to}")
    return 0


# ---------------------------------------------------------------- 读消息

def cmd_poll(a) -> int:
    who = a.who.upper()
    if not valid_who(who):
        print(f"身份不合法：{who}")
        return 1
    d = inbox_dir(who)
    # 消息游标
    bc = d / "board_cursor.json"
    cur = load_json(bc, {"offset": 0})
    off = int(cur.get("offset") or 0)
    msgs = []
    bp = board_path()
    if bp.exists():
        size = bp.stat().st_size
        if off > size:
            off = 0
        if off < size:
            with bp.open("r", encoding="utf-8", errors="replace") as f:
                f.seek(off)
                chunk = f.read()
                new_off = f.tell()
            for line in chunk.splitlines():
                if not line.strip():
                    continue
                try:
                    m = json.loads(line)
                except Exception:
                    continue
                if str(m.get("to", "")).upper() in (who, "ALL", ""):
                    msgs.append(m)
            save_json(bc, {"offset": new_off})
    # 日志错误（可选目录）
    errs = []
    logs = path_of("logs")
    if logs.exists():
        lc = d / "log_cursor.json"
        lcur = load_json(lc, {"pos": {}})
        pos = {k: int(v) for k, v in (lcur.get("pos") or {}).items()}
        pat = re.compile(r"(Traceback|ERROR|Exception|\[中止\]|中止：|\b429\b|\b403\b|ERR )")
        for f in sorted(logs.glob("*.log")):
            if (f.name.endswith(".test.log") or f.name.startswith("_selftest")
                    or f.name.startswith("_diag")):
                continue
            try:
                size = f.stat().st_size
                start = pos.get(f.name, 0)
                if start > size:
                    start = 0
                if start == size:
                    continue
                with f.open("r", encoding="utf-8", errors="replace") as fh:
                    fh.seek(start)
                    chunk = fh.read()
                    pos[f.name] = fh.tell()
            except Exception:
                continue
            for ln in chunk.splitlines():
                if pat.search(ln):
                    errs.append(f"{f.stem}: {ln.strip()[:140]}")
        save_json(lc, {"pos": pos})
    # 归零
    fl = flag_of(who)
    fl["unread"] = 0
    fl["consumed_at"] = now()
    save_json(d / "flag.json", fl)

    if a.json:
        print(json.dumps({"who": who, "msgs": len(msgs), "logs": len(errs),
                          "messages": [{"from": m.get("from"),
                                        "body": (m.get("body") or "")[:500]}
                                       for m in msgs], "errors": errs[:10]},
                         ensure_ascii=False))
        return 0
    print(f"[{who}] 新消息 {len(msgs)} 条 · 日志错误 {len(errs)} 条")
    for m in msgs:
        print(f"  · {m.get('from')}→{m.get('to')}  {m.get('body')}")
    for e in errs[:8]:
        print(f"  ! {e}")
    print(f"[{who}] flag 已归零")
    return 0


# ---------------------------------------------------------------- 等待

def cmd_flag(a) -> int:
    who = a.who.upper()
    n = int(flag_of(who).get("unread") or 0)
    print(n)
    return 0 if n == 0 else 0


def cmd_wait(a) -> int:
    who = a.who.upper()
    d = inbox_dir(who)
    fp = d / "flag.json"
    hb = d / "waiter.json"
    t0 = time.time()
    try:
        hb.write_text(json.dumps({"pid": os.getpid(), "started": now(),
                                  "ts": time.time()}, ensure_ascii=False),
                      encoding="utf-8")
    except Exception:
        pass
    try:
        while time.time() - t0 < a.timeout:
            try:
                n = int(json.loads(fp.read_text(encoding="utf-8")).get("unread") or 0)
            except Exception:
                n = 0
            if n > 0:
                print(f"FLAG=1 unread={n}（等了 {int(time.time() - t0)} 秒）", flush=True)
                return 0
            if int(time.time() - t0) % 10 == 0:
                try:
                    hb.write_text(json.dumps({"pid": os.getpid(), "started": now(),
                                              "ts": time.time()}, ensure_ascii=False),
                                  encoding="utf-8")
                except Exception:
                    pass
            time.sleep(1)
        print(f"TIMEOUT {a.timeout}s，flag 仍为 0", flush=True)
        return 1
    finally:
        try:
            hb.unlink(missing_ok=True)
        except Exception:
            pass


# ---------------------------------------------------------------- 状态

def _alive(pid: int) -> bool:
    """判断进程是否存活（跨平台）。"""
    if pid <= 0:
        return False
    try:
        if os.name == "nt":
            r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                               capture_output=True, text=True, timeout=8)
            return str(pid) in (r.stdout or "")
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _read_pid(p: Path) -> int:
    try:
        return int((p.read_text(encoding="utf-8").strip() or "0"))
    except Exception:
        return 0


def cmd_status(a) -> int:
    ids = people() or ["A", "B", "C"]
    print(f"{'身份':<6}{'守护':<14}{'等待任务':<14}{'未读':<6}心跳")
    print("-" * 56)
    miss = []
    for who in ids:
        d = path_of("inbox") / who
        dpid = _read_pid(d / "daemon.pid")
        wpid = _read_pid(d / "waiter.json")
        dm = f"pid {dpid}" if _alive(dpid) else "未运行"
        wt = f"pid {wpid}" if _alive(wpid) else "未挂"
        try:
            hb = json.loads((d / "state.json").read_text(encoding="utf-8")).get("updated", "-")
        except Exception:
            hb = "-"
        n = int(flag_of(who).get("unread") or 0)
        print(f"{who:<6}{dm:<14}{wt:<14}{n:<6}{hb}")
        if not _alive(wpid):
            miss.append(who)
    print()
    if miss:
        print(f"需要挂等待：{', '.join(miss)}")
        for w in miss:
            print(f"  python collab.py wait --as {w} --timeout 14400")
    else:
        print("所有等待任务在线。")
    return 0


# ---------------------------------------------------------------- 守护（可选）

def cmd_daemon(a) -> int:
    who = a.who.upper()
    d = inbox_dir(who)
    pidf = d / "daemon.pid"
    stopf = d / "stop"
    pidf.write_text(str(os.getpid()), encoding="utf-8")
    stopf.unlink(missing_ok=True)
    msg_pos = 0
    bp = board_path()
    if bp.exists():
        msg_pos = bp.stat().st_size
    log_pos: dict[str, int] = {}
    logs = path_of("logs")
    if logs.exists():
        for f in logs.glob("*.log"):
            try:
                log_pos[f.name] = f.stat().st_size
            except Exception:
                pass

    def emit(kind: str, text: str, bump: bool = True) -> None:
        print(f"[{now()[11:]}] {kind}: {text}", flush=True)
        if bump:
            bump_flag(who, kind)

    last_slow = 0.0
    print(f"守护启动 · {who} · 每 {a.interval}s 扫日志 · 每 2s 扫消息", flush=True)
    try:
        while True:
            if stopf.exists():
                stopf.unlink(missing_ok=True)
                break
            if bp.exists():
                size = bp.stat().st_size
                if size < msg_pos:
                    msg_pos = 0
                if size > msg_pos:
                    with bp.open("r", encoding="utf-8", errors="replace") as f:
                        f.seek(msg_pos)
                        chunk = f.read()
                        msg_pos = f.tell()
                    for line in chunk.splitlines():
                        if not line.strip():
                            continue
                        try:
                            m = json.loads(line)
                        except Exception:
                            continue
                        if str(m.get("to", "")).upper() != who:
                            continue
                        emit("新消息", f"{m.get('from')}→{m.get('to')}  "
                                       f"{(m.get('body') or '')[:120]}", bump=False)
            if time.time() - last_slow >= a.interval:
                last_slow = time.time()
                if logs.exists():
                    pat = re.compile(r"(Traceback|ERROR|Exception|\[中止\]|中止：|\b429\b|\b403\b|ERR )")
                    for f in sorted(logs.glob("*.log")):
                        if (f.name.endswith(".test.log") or f.name.startswith("_selftest")
                    or f.name.startswith("_diag")):
                            continue
                        try:
                            size = f.stat().st_size
                            start = log_pos.get(f.name, 0)
                            if start > size:
                                start = 0
                            if start == size:
                                continue
                            with f.open("r", encoding="utf-8", errors="replace") as fh:
                                fh.seek(start)
                                chunk = fh.read()
                                log_pos[f.name] = fh.tell()
                        except Exception:
                            continue
                        for ln in chunk.splitlines():
                            if pat.search(ln):
                                emit("日志异常", f"{f.stem}: {ln.strip()[:140]}")
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        pidf.unlink(missing_ok=True)
        print("守护退出", flush=True)
    return 0


# ---------------------------------------------------------------- 自检

def cmd_selftest(a) -> int:
    who = a.who.upper()
    res = []

    def check(name, ok, detail=""):
        res.append(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    # 清空
    cmd_poll(argparse.Namespace(who=who, json=True))

    t0 = time.time()
    cmd_post(argparse.Namespace(to=who, body=["selftest-1"], sender=who))
    lat = None
    for _ in range(30):
        if int(flag_of(who).get("unread") or 0) > 0:
            lat = time.time() - t0
            break
        time.sleep(0.2)
    check("消息→flag 置位", lat is not None and lat < 3,
          f"{lat:.2f}s" if lat else "超时")
    cmd_poll(argparse.Namespace(who=who, json=True))
    check("消费后归零", int(flag_of(who).get("unread") or 0) == 0)

    # 批量
    for i in range(5):
        cmd_post(argparse.Namespace(to=who, body=[f"batch-{i}"], sender=who))
    out = subprocess.run([sys.executable, str(Path(__file__)),
                          "poll", "--as", who],
                         capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout or ""
    check("批量 5 条一次读完", sum(1 for i in range(5) if f"batch-{i}" in out) == 5)

    # 并发写
    bp = board_path()
    before = len(bp.read_text(encoding="utf-8").strip().splitlines()) if bp.exists() else 0
    procs = []
    for k in range(3):
        code = (f"import sys;sys.path.insert(0,{str(ROOT)!r});import collab;"
                f"[collab.cmd_post(type('X',(),{{'to':'{who}','body':[f'cc{k}-{{i}}'],"
                f"'sender':'{who}'}})()) for i in range(5)]")
        procs.append(subprocess.Popen([sys.executable, "-c", code],
                                      stdout=subprocess.DEVNULL))
    for p in procs:
        p.wait(timeout=60)
    after = len(bp.read_text(encoding="utf-8").strip().splitlines())
    bad = 0
    for line in bp.read_text(encoding="utf-8").strip().splitlines()[before:]:
        try:
            json.loads(line)
        except Exception:
            bad += 1
    check("并发写 3×5 行不丢", after - before == 15 and bad == 0,
          f"新增 {after - before}/15")
    cmd_poll(argparse.Namespace(who=who, json=True))

    # 等待超时
    r = subprocess.run([sys.executable, str(Path(__file__)), "wait",
                        "--as", who, "--timeout", "3"],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=30)
    hb = path_of("inbox") / who / "waiter.json"
    check("等待任务超时行为", "TIMEOUT" in (r.stdout or "") and r.returncode == 1
          and not hb.exists(), f"exit={r.returncode}")

    ok = sum(1 for x in res if x)
    print(f"\n通过 {ok}/{len(res)}")
    return 0 if ok == len(res) else 1


# ---------------------------------------------------------------- 入口

def main() -> int:
    ap = argparse.ArgumentParser(
        prog="collab.py",
        description="多对话协作：留言 / 唤醒 / 状态（无第三方依赖）")
    ap.add_argument("--version", action="version", version=f"collab {VERSION}")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("init", help="初始化协作目录")
    p.add_argument("--people", default="A,B,C", help="逗号分隔的身份列表")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("post", help="给某人留言")
    p.add_argument("to")
    p.add_argument("body", nargs="+")
    p.add_argument("--from", dest="sender", default="")
    p.set_defaults(func=cmd_post)

    p = sub.add_parser("poll", help="读留言并把 flag 归零")
    p.add_argument("--as", dest="who", default="B")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_poll)

    p = sub.add_parser("wait", help="阻塞等待 flag（醒来即退出）")
    p.add_argument("--as", dest="who", default="B")
    p.add_argument("--timeout", type=int, default=14400)
    p.set_defaults(func=cmd_wait)

    p = sub.add_parser("flag", help="打印未读数")
    p.add_argument("--as", dest="who", default="B")
    p.set_defaults(func=cmd_flag)

    p = sub.add_parser("status", help="所有人状态")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("daemon", help="常驻监控（可选）")
    p.add_argument("--as", dest="who", default="B")
    p.add_argument("--interval", type=float, default=60)
    p.set_defaults(func=cmd_daemon)

    p = sub.add_parser("selftest", help="通道自检")
    p.add_argument("--as", dest="who", default="B")
    p.set_defaults(func=cmd_selftest)

    a = ap.parse_args()
    if not getattr(a, "func", None):
        ap.print_help()
        return 0
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
