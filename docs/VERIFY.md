# 换台机器验证（10 分钟）

> 目的：确认这个工具在**别人的机器上**也能按文档跑通，而不是只在你自己的环境里好使。
> 建议在一台干净的 Windows（或虚拟机）上做一次。

## 前置

只要求一件事：**Python 3.9+**。

```bash
python --version
```

没有的话装一个（Windows 商店版或官网安装包都可以，勾选 Add to PATH）。

## 步骤

### 1. 复制文件

把 `dsh-collab-kit` 整个目录（或解压后的 zip）复制到目标机器，**不要**带这些运行时目录：

```
__pycache__/  collab.json  board/  inbox/  logs/
```

### 2. 初始化

```bash
cd dsh-collab-kit
python collab.py init --people A,B
```

期望输出包含：`已初始化`、身份列表、消息板路径、收件箱路径。

### 3. 发一条消息

```bash
python collab.py post B "hello" --from A
python collab.py flag --as B
```

期望：`已留言给 B`，然后 `flag` 输出 `1`。

### 4. 读消息

```bash
python collab.py poll --as B
```

期望：

```
[B] 新消息 1 条 · 日志错误 0 条
  · A→B  hello
[B] flag 已归零
```

再执行一次 `flag --as B`，应为 `0`。

### 5. 等待任务

```bash
# 终端 1
python collab.py wait --as B --timeout 120

# 终端 2
python collab.py post B "wake" --from A
```

期望：终端 1 立刻输出 `FLAG=1 unread=1` 并退出（返回码 0）。

### 6. 看状态

```bash
python collab.py status
```

期望：列出 A/B，未读数正确。

### 7. 自检

```bash
python collab.py selftest --as B
```

期望 5 项全 PASS。

### 8. 边界测试（建议）

| 场景 | 做法 | 期望 |
|---|---|---|
| 路径含中文/空格 | 放到 `C:\测试 目录\collab\` 再跑一遍 | 正常（不依赖 ASCII 路径） |
| 路径含非 ASCII 用户名 | 放在 `C:\Users\张三\Desktop\` | 正常 |
| 没有 logs 目录 | 直接跑 `poll` | 正常，日志错误 0 条 |
| 重复 init | 再跑一次 `init --people A,B` | 覆盖配置，不报错 |
| 消息含换行/emoji | `post B "第一行`n第二行 😀"` | 原样存储与显示 |

## 通过标准

第 2–7 步全部按期望输出，第 8 步没有异常。

## 已知限制（不是 bug）

- **等待任务不会唤醒任何 AI 对话**：它只在本地退出。唤醒是由宿主（DSH 等）检测后台任务结束实现的
- 没有 `logs/` 目录时守护什么也不做，属正常
- 跨机器不互通：本工具只读写本地文件

## 反馈什么

如果哪一步和文档不一致，记下：

```
步骤：
命令：
实际输出：
期望：
系统：Windows 10 / 11，Python 版本
路径：是否含中文/空格
```
