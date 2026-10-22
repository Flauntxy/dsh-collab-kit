# collab.py · 让多个 AI 对话互相留言并自动被唤醒

> 单个文件、零依赖、纯本地。适合「一个任务由多个对话/多个 agent 分工」的场景：
> 比如 A 负责选题、B 负责代码、C 负责执行——他们需要互相通知，但**不希望靠轮询烧 token**。

**English summary**：A tiny, dependency-free, file-based message bus for **multi-agent / multi-conversation** workflows. Agents post messages, a per-agent flag flips instantly, and a local waiter process wakes the target conversation within ~0.3–2s — **zero token cost while idle**. No server, no network, no API keys. Tested on two independent Windows machines (including reboot recovery).

> 关键词：多智能体协作 / 跨会话通信 / 跨对话留言 / agent 编排 / 免轮询唤醒 /
> multi-agent collaboration, cross-session messaging, agent coordination, zero-polling wake-up.

---

## 问题

多个对话协作时，常见做法是「每 N 分钟检查一次有没有新消息」。
问题是：**每次检查都是一次完整的模型回合**。30 秒一次就是每天 2880 次，
即使什么都没有，也在持续消耗。

## 做法

```
写消息 → 立刻把收件人的 flag 置为 1
         ↓
收件人会话里挂着一个「等待任务」（本地进程，只读一个几字节的文件）
         ↓
flag 变化 → 等待任务退出 → 会话被唤醒 → 读消息 → flag 归零 → 重新挂起
```

**空闲时零成本**，有消息时约 0.1 秒置位、**0.3~2 秒**唤醒。

> 已在两台独立 Windows 机器（含虚拟机）验证：唤醒 0.32 秒、并发写零丢失、**重启后未读状态与消息完整保留**。

---

## 三分钟上手

```bash
# 1. 初始化（在任何空目录）
python collab.py init --people A,B,C

# 2. 每个身份在自己的会话里挂一个等待任务（后台执行）
python collab.py wait --as A --timeout 14400

# 3. 给某人留言（会自动置对方 flag）
python collab.py post B "采集脚本改完了，可以跑" --from A

# 4. B 被唤醒后读消息（并把 flag 归零）
python collab.py poll --as B
```

看所有人状态：

```bash
python collab.py status
```

---

## 命令一览

| 命令 | 作用 |
|---|---|
| `init --people A,B,C` | 初始化，生成 `collab.json` |
| `post <收件人> <内容> --from <发件人>` | 留言（自动置对方 flag） |
| `poll --as <身份>` | 读消息 + 日志错误，flag 归零 |
| `wait --as <身份> --timeout 14400` | 阻塞等待，醒来即退出（**零 token**） |
| `flag --as <身份>` | 只看未读数 |
| `status` | 所有人：守护 / 等待任务 / 未读 / 心跳 |
| `daemon --as <身份> --interval 60` | 可选常驻：把日志错误也变成唤醒源 |
| `selftest --as <身份>` | 自检（含并发写、超时、批量） |

---

## 目录结构

```
collab.py            本工具（单文件）
collab.json          配置：身份列表、路径
board/messages.jsonl 消息板（一行一条 JSON）
board/.write.lock    写入锁（防并发丢行）
inbox/<身份>/
    flag.json            未读数（0/1/2…）
    board_cursor.json    读到哪条消息
    log_cursor.json      读到哪段日志
    waiter.json          等待任务心跳
logs/                可选：被监控的日志目录
```

---

## 文档

| 文件 | 内容 |
|---|---|
| [QUICKSTART.md](QUICKSTART.md) | 从零到跑通（含 Windows） |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 原理、数据结构、延迟、边界 |
| [docs/RULES.md](docs/RULES.md) | 协作规则**建议**（可直接改） |
| [docs/ADAPTATION.md](docs/ADAPTATION.md) | 2 人 / 4 人 / 不同分工怎么套 |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | 常见故障与判断方法 |
| [docs/VERIFY.md](docs/VERIFY.md) | 换台机器验证（10 分钟清单） |
| [docs/CASE-ranking-pipeline.md](docs/CASE-ranking-pipeline.md) | 真实案例：三分支跑内容流水线 |
| [docs/DISCOVERY.md](docs/DISCOVERY.md) | 发布与推广清单（仓库元信息、话题、文案） |

---

## 适用与不适用

**适合**

- 多个对话/多个人分工同一个项目，需要互相通知
- 你希望「有事才唤醒」，不想付轮询成本
- 单机、本地文件、不需要公网

**不适合**

- 跨机器 / 跨网络（本工具只读写本地文件）
- 要求消息投递保证（这是文件轮询，不是消息队列）
- 完全无人值守（见下方「唯一的缺口」）

## 唯一的缺口

等待任务活在**会话进程内**。DSH 关闭或机器重启后它会消失，
而守护进程只能记录事件、**无法唤醒会话**。

所以：**重启后每个对话需要被「说一句话」唤醒一次**，之后按协议自行维持。
这一点无法绕过——它由「只有会话自己的进程能通知会话」决定。

---

## 许可

MIT。详见 [LICENSE](LICENSE)。
