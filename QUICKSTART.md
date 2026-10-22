# 快速上手

## 0. 环境

只需要 Python 3.9+，**不需要安装任何包**。
Windows / macOS / Linux 都可以。

```bash
python --version
```

## 1. 初始化

在一个空目录里放 `collab.py`，然后：

```bash
python collab.py init --people A,B,C
```

输出会告诉你身份列表和目录位置。如果不写 `--people`，默认 `A,B,C`。

> 身份名只能包含字母、数字、`_`、`-`，长度 1~16。
> 用真名也可以，例如 `--people alice,bob`。

## 2. 每个身份挂一个等待任务

**关键**：必须在**各自的会话里**以后台任务的方式运行，而不是用
`start` / `nohup` / 独立进程——只有会话内的后台任务，退出时才会通知会话。

DSH（DeepSeek Harness）里的写法：

```
pwsh 工具，run_in_background = true
命令：python collab.py wait --as A --timeout 14400
```

其它环境：

```bash
# tmux / screen 里跑，或用 supervisor —— 但记住：只有「会话内的后台任务」能唤醒会话
python collab.py wait --as A --timeout 14400
```

`--timeout` 是保险丝：4 小时后自动退出，避免挂死。醒来后重新挂即可。

## 3. 发消息

```bash
python collab.py post B "数据库迁移完成，可以跑同步了" --from A
```

写完后 **B 的 flag 立刻变成 1**，B 的等待任务在 2 秒内退出并通知 B 的会话。

## 4. 收到唤醒后读消息

```bash
python collab.py poll --as B
```

输出：

```
[B] 新消息 1 条 · 日志错误 0 条
  · A→B  数据库迁移完成，可以跑同步了
[B] flag 已归零
```

读完之后：**处理内容 → 再挂一次等待任务**。

## 5. 看状态

```bash
python collab.py status
```

```
身份    守护            等待任务          未读    心跳
--------------------------------------------------------
A      pid 19168       pid 17568       0     -
B      未运行           未挂             1     -
```

## 6. 自检

```bash
python collab.py selftest --as B
```

会测：置位延迟、消费归零、批量读取、并发写入、等待超时。

## Windows 小工具

`install.bat`：把 `collab.py` 复制到目标目录并初始化。
`waiter.bat`：双击即可给某个身份挂等待任务（会开一个窗口）。

```bat
waiter.bat A
```

> 注意：用 `waiter.bat` 起的进程脱离会话，**能收消息但不会唤醒对话**。
> 它适合「人肉值守」场景；AI 对话请用会话内后台任务。

## 下一步

- 想定规则 → [docs/RULES.md](docs/RULES.md)
- 想改人数/分工 → [docs/ADAPTATION.md](docs/ADAPTATION.md)
- 出问题 → [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
