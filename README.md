# dsh-collab-kit

多个 AI 对话（或人）在同一台机器上互相留言。有人留言时，对方会话里挂着的本地等待进程会退出，从而把对话叫醒——空闲时不必反复问模型「有没有新消息」。

核心就一个文件：`collab.py`。只用 Python 标准库，不联网、不装第三方包。

（English: a tiny local mailbox so sessions on the same machine can notify each other without polling the model.）

## 怎么用

```bash
python collab.py init --people A,B,C

# 在各自会话里以后台任务挂着（进程退出时才会通知会话）
python collab.py wait --as A --timeout 14400

python collab.py post B "采集脚本改完了，可以跑" --from A
python collab.py poll --as B
python collab.py status
```

Windows 上也可以用 `install.bat` 初始化、`waiter.bat A` 开一个独立等待窗口（注意：独立窗口收得到文件变化，但叫不醒对话；对话要用会话内后台任务）。

更细的步骤见 [QUICKSTART.md](QUICKSTART.md)。

## 命令

| 命令 | 作用 |
|---|---|
| `init --people A,B,C` | 生成 `collab.json` |
| `post <to> <内容> --from <from>` | 留言，并置对方 flag |
| `poll --as <身份>` | 读新留言（和可选日志错误），flag 归零 |
| `wait --as <身份> --timeout 14400` | 等 flag；有变化就退出 |
| `flag --as <身份>` | 只看未读数 |
| `status` | 所有人状态 |
| `daemon --as <身份> --interval 60` | 可选：扫日志错误再 bump flag |
| `selftest` | 自检 |

## 它实际在干什么

留言写进 `board/messages.jsonl`，同时把 `inbox/<身份>/flag.json` 标成有未读。`wait` 只轮询这个几字节的 JSON，不碰模型。flag 一变就退出，会话接着 `poll`。

```
post → 写消息 + 置 flag
wait → 本地阻塞，flag 变了就退出
poll → 读新内容，flag 归零，然后可以再挂 wait
```

## 边界

- 只读写本机文件，不做跨机器、不做消息队列那套投递保证。
- `wait` 必须挂在**会话自己的后台任务**里，否则文件能变、对话醒不了。
- 会话关掉或机器重启后，`wait` 没了；需要再说一句让对话重新挂上。守护进程可以记事件，但唤醒不了会话。

## 文档

| 文件 | 内容 |
|---|---|
| [QUICKSTART.md](QUICKSTART.md) | 从零跑通 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 数据结构与边界 |
| [docs/RULES.md](docs/RULES.md) | 协作约定（建议，可改） |
| [docs/ADAPTATION.md](docs/ADAPTATION.md) | 2 / 3 / N 人怎么套 |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | 常见问题 |
| [docs/VERIFY.md](docs/VERIFY.md) | 换机自测清单 |
| [docs/CASE-ranking-pipeline.md](docs/CASE-ranking-pipeline.md) | 一个实际用法 |

## 许可

MIT，见 [LICENSE](LICENSE)。
