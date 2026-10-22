# 发布收尾与推广清单

> 仓库：https://github.com/Flauntxy/dsh-collab-kit
> 目标：让「有多对话协作需求」的人能搜到它。

---

## 一、仓库元信息（GitHub 设置页，5 分钟）

### 1. 可见性

`Settings` → 拉到底 `Danger Zone` → **Change repository visibility** → Make public。

改成公开前建议再扫一次敏感词（仓库里已无凭据，但改动过后应复查）。

### 2. About（右上角齿轮）

**Description**（一句英文 + 一句中文，合计不超过 350 字符）：

```
Zero-polling message bus for multi-agent workflows: post a message, a local waiter wakes the target AI conversation in ~0.3s. Single file, no deps, no network.
多对话协作的零轮询消息通道：留言即唤醒目标会话（约 0.3 秒），单文件零依赖、纯本地。
```

**Website**：留空，或填你自己的说明页。

### 3. Topics（最多 20 个，直接影响被检索到的概率）

复制下面这组（GitHub 按空格/回车切分）：

```
multi-agent
ai-agents
agent-framework
agent-collaboration
multi-agent-systems
llm
llmops
ai-workflow
collaboration
messaging
message-bus
inter-process-communication
file-watcher
no-dependencies
python
developer-tools
productivity
automation
deepseek
dsh
```

### 4. Releases

`Releases` → `Draft a new release` → tag `v1.0.0` → 标题 `v1.0.0 — 首个可用版本`
→ 描述里贴下面的要点：

```
- post / poll / wait / flag / status / daemon / selftest
- 留言即时置位 0.1s，唤醒 0.3~2s，空闲零 token
- 并发写不丢（跨进程文件锁），位点持久化（重启可续读）
- 已在两台独立 Windows 验证：唤醒 0.32s、重启后未读逐字节保留
```

---

## 二、README 已做的优化（不用你再动）

| 项 | 处理 |
|---|---|
| 首段加入 English summary | 英文搜索也能命中；外国人点开能立刻判断是否相关 |
| 关键词行 | multi-agent / cross-session / agent coordination / zero-polling |
| 快速上手前移 | 三分钟内能看到可跑的命令 |
| 明确「不适用」 | 减少误用与无效 issue |

---

## 三、推广渠道（按性价比排序）

### 高性价比（直接对口，纯文本即可）

| 渠道 | 怎么发 | 注意 |
|---|---|---|
| **GitHub 自己的话题页** | 靠 Topics 自动进入 `github.com/topics/multi-agent` 等 | 前提是 topics 填了 |
| **r/LocalLLaMA**（Reddit） | 标题写实测数据，正文讲「为什么不用轮询」 | 不要硬广，先讲问题 |
| **Hacker News · Show HN** | `Show HN: Zero-polling message bus for multi-agent workflows` | 早上 8-10 点美东发 |
| **V2EX · 程序员 / 分享创造** | 中文，讲清场景与实测 | 附仓库链接 |
| **掘金 / 知乎** | 写一篇「多对话协作如何不烧 token」 | 正文链接仓库 |

### 中性价比

| 渠道 | 说明 |
|---|---|
| **awesome-multi-agent** 类清单 | 找到对应 repo，提 PR 加一行 |
| **awesome-llm-agents** | 同上 |
| **X / Twitter** | 一条推文 + GIF 演示（flag 变 1 → 会话醒来） |
| **即刻 / 少数派** | 偏产品向，适合写「我怎么让自己三个 AI 助手互相通知」 |

### 不建议一开始做的

- Product Hunt（受众不匹配）
- 付费推广
- 群发私信

---

## 四、可复用的发帖文案

### 英文（Reddit / HN）

```
Show HN: Zero-polling message bus for multi-agent workflows

Problem: when several AI conversations split one project, they need to notify
each other. The usual answer is "poll every N minutes" — but each poll is a full
model turn. At 30s interval that's 2,880 turns/day doing nothing.

What I built: a single-file, dependency-free Python tool.

  post  → flips the recipient's flag to 1 (≈0.1s)
  wait  → a local process blocks on that tiny JSON file (no model involved)
  flag  → waiter exits → the conversation is woken → poll reads + resets

Idle cost: zero tokens. Wake latency: 0.32s measured on two independent Windows
machines (one VM). Reboot recovery verified: unread state survives byte-for-byte.

Not a message queue — it's a local file-based bus for single-machine setups.
Docs cover architecture, rules (as suggestions), adaptation for 2/3/N agents,
troubleshooting, and a real case study.

https://github.com/Flauntxy/dsh-collab-kit
```

### 中文（V2EX / 掘金）

```
标题：多对话协作怎么不烧 token？我做了一个「留言即唤醒」的小工具

背景：一个项目拆给三个 AI 对话做（选题/写代码/跑任务），他们得互相通知。
最初用「每 30 秒查一次留言」，一天 2880 次模型回合，全是空转。

做法：写留言 → 把收件人的 flag 置 1 → 对方会话里挂的本地等待进程退出 →
会话被唤醒 → 读消息 → flag 归零 → 重新挂起。

空闲时不消耗任何 token，实测唤醒 0.32 秒（两台独立 Windows，含虚拟机）。
重启后未读消息与位点逐字节保留。

单文件、零依赖、纯本地，MIT。文档里有原理、规则建议、不同人数怎么套、
故障排查和一个真实案例。

https://github.com/Flauntxy/dsh-collab-kit
```

---

## 五、发布后自查

打开仓库（未登录窗口），确认：

- [ ] 页面能打开（公开）
- [ ] About 显示描述
- [ ] Topics 在右侧显示
- [ ] README 首屏能看到 English summary 与「三分钟上手」
- [ ] `docs/` 六个文件都能点开
- [ ] `git clone` 到临时目录后 `python collab.py init` 能跑
- [ ] Release v1.0.0 存在

---

## 六、如果要做演示 GIF（提升转化最明显）

一段 15 秒的录屏即可：

```
左窗格：终端执行 post B "..."（瞬间 flag=1）
右窗格：另一个终端里 wait 立刻退出，打印 FLAG=1 unread=1（等了 1 秒）
```

放在 README 顶部（`![demo](docs/demo.gif)`），比任何文字都有说服力。
