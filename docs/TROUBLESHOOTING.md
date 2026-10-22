# 故障排查

## 先看一件事：`status`

```bash
python collab.py status
```

| 现象 | 含义 | 处置 |
|---|---|---|
| 等待任务 `未挂`，且 `inbox/<身份>/waiter.json` 不存在 | **从没挂上** | 用会话内后台任务重挂 |
| 等待任务 `未挂`，但 `waiter.json` 存在过 | **挂上后立即死** | 看后台任务输出里的报错 |
| 等待任务 `pid xxx` | 正常 | — |
| 未读数一直 > 0 | 有人发消息但没人读 | `poll --as <身份>` |

---

## 常见问题

### Q1：我发了消息，对方没反应

1. 对方挂了等待任务吗？→ `status`
2. 对方是用**会话内后台任务**挂的吗？→ 用 `start`/`nohup` 起的能收消息但不会唤醒会话
3. 消息是工具发的吗？→ 手改 `messages.jsonl` 不会置 flag

### Q2：`wait` 一启动就退出

说明 flag 已经 > 0（有未读）。先 `poll` 读掉，再挂。

### Q3：重启电脑后全都没反应

预期行为：等待任务随会话消失。

处置：在每个对话里说一句话触发补挂，或手动：

```bash
python collab.py wait --as A --timeout 14400
```

### Q4：同一个文件被重复报「日志错误」

日志文件被**截断或重建**时会从头再读（这是有意的）。
如果不想重复报，把测试日志命名为 `*.test.log`，本工具会跳过。

### Q5：并发写会不会丢消息

工具内已加跨进程文件锁，实测 4 进程各写 10 条 → 40/40。
**但不要手写文件**——只有 `post` 走锁。

### Q6：`status` 显示守护 `未运行`

守护是可选的。它只影响「日志错误能不能主动叫醒你」。
要开：

```bash
python collab.py daemon --as A --interval 60
```

长时间运行建议用系统计划任务（Windows 任务计划 / systemd / launchd）。

### Q7：消息板越来越大

一条消息约 200 字节，1 万条约 2 MB。可以定期归档：

```bash
# 把已读部分移到归档文件（自行决定策略）
```

工具不做自动清理，避免误删未读。

---

## 自检命令

```bash
python collab.py selftest --as B
```

覆盖：置位延迟 / 消费归零 / 批量读取 / 并发写入 / 等待超时。
改过代码或换机器后跑一遍，5 项全过即可放心用。

---

## Windows 特有的两个坑（真实遇到）

### 1. python 是微软商店占位符

现象：输入 python collab.py init ... 后**没有任何输出**，直接回到提示符。

原因：没装 Python 时，python 命中 Windows 的「应用执行别名」，
它可能静默退出，也可能弹出商店。

确认：

`powershell
python --version
where.exe python
`

处置：装 Python 3.9+（官网安装包务必勾 Add python.exe to PATH），
装完**关掉终端重新开**。或用 py --version 看是否已有 py launcher。

### 2. PowerShell 里调用带引号的路径需要 &

现象：C:\path\python.exe collab.py 报「不是可识别的命令」。

原因：PowerShell 把带引号的字符串当普通文本，不会当命令执行。

正确写法：

`powershell
& C:\path\python.exe collab.py init --people A,B
`

（CMD 不需要这个 &，这是 PowerShell 的语法差异。）
