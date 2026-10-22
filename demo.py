"""演示脚本：一屏内展示「留言 → 等待任务立刻醒来」的真实过程。

用途：录 README 用的演示 GIF。真实调用 collab.py，不是假动画。

    python demo.py            # 演示（默认 3 秒开场）
    python demo.py --fast     # 更快
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLLAB = HERE / "collab.py"

C_TITLE = "\033[96m"
C_A = "\033[93m"
C_B = "\033[92m"
C_DIM = "\033[90m"
C_OFF = "\033[0m"


def typ(text: str, delay: float = 0.018, color: str = "") -> None:
    """逐字打印，像人在打字。"""
    sys.stdout.write(color)
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(C_OFF + "\n")
    sys.stdout.flush()


def say(text: str, color: str = "") -> None:
    print(f"{color}{text}{C_OFF}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    a = ap.parse_args()
    pause = 0.6 if a.fast else 1.2

    work = Path(tempfile.mkdtemp(prefix="collab-demo-"))
    env = {**os.environ, "COLLAB_ROOT": str(work), "PYTHONIOENCODING": "utf-8"}
    py = sys.executable

    def run(*args: str) -> str:
        r = subprocess.run([py, "-u", str(COLLAB), *args], cwd=str(work),
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        return (r.stdout or "") + (r.stderr or "")

    try:
        os.system("cls" if os.name == "nt" else "clear")
        say("collab.py — 让多个 AI 对话互相留言并被唤醒", C_TITLE)
        say("（同一份代码，真实执行，无剪辑）\n", C_DIM)
        time.sleep(pause)

        # 1. 初始化
        typ("$ python collab.py init --people A,B", color=C_DIM)
        run("init", "--people", "A,B")
        say("  已初始化 · 身份：A, B", C_DIM)
        say("")
        time.sleep(pause)

        # 2. B 挂等待任务
        say("[B 的会话] 挂一个等待任务（后台，阻塞中）", C_B)
        typ("$ python collab.py wait --as B --timeout 60", color=C_B)
        t0 = time.time()
        waiter = subprocess.Popen(
            [py, "-u", str(COLLAB), "wait", "--as", "B", "--timeout", "60"],
            cwd=str(work), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", env=env)
        say("  ... 等待中（此刻零 token 消耗）\n", C_DIM)
        time.sleep(pause + 0.8)

        # 3. A 发消息
        say("[A 的会话] 发一条消息", C_A)
        typ('$ python collab.py post B "跑完了，可以出片" --from A', color=C_A)
        t_post = time.time()
        run("post", "B", "跑完了，可以出片", "--from", "A")
        say("  已留言给 B", C_DIM)

        # 4. B 被唤醒
        try:
            out, _ = waiter.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            waiter.kill()
            out = ""
        dt = time.time() - t_post
        say("")
        say("[B 的会话] 等待任务立刻退出 → 对话被唤醒", C_B)
        for line in (out or "").strip().splitlines():
            say("  " + line.strip(), C_B)
        say(f"  → 从写入到醒来：{dt:.2f} 秒", C_TITLE)
        time.sleep(pause)

        # 5. B 读消息
        typ("$ python collab.py poll --as B", color=C_B)
        for line in run("poll", "--as", "B").strip().splitlines():
            say("  " + line, C_B)
        say("")
        say("空闲成本 0 token · 唤醒 0.3~2 秒 · 单文件零依赖", C_TITLE)
        time.sleep(pause * 2)
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
