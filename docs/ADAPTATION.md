# 不同人数 / 不同分工怎么套

本工具不假设人数，也不假设角色名。身份就是 `collab.json` 里的一个字符串列表。

---

## 情况一：2 个对话（最常见）

```bash
python collab.py init --people 开发,审核
```

```
开发  → 提交改动 → post 审核 "PR 好了"
审核  → 被唤醒 → 看代码 → post 开发 "第 3 点要改"
```

规则可以只留三条：写消息用工具 / 每次回答完自检 / 一个身份一个等待任务。

## 情况二：3 个对话（分工型）

本项目就是这种：选题、代码、执行三条线。

```bash
python collab.py init --people A,B,C
```

适合：一个人不可能同时做研究、实现、上线，需要并行。

## 情况三：4 个以上

```bash
python collab.py init --people A,B,C,D,E
```

注意事项：

| 项 | 建议 |
|---|---|
| 广播 | 工具只支持点对点。要广播就挨个 post，或约定一个 `ALL` 身份并由它转发 |
| 消息量 | 超过 5 人时建议加一列「主题」在正文开头，例如 `[构建] ...` |
| 状态查看 | `status` 会列出所有人，超过 8 人会开始刷屏，可以加 `--as` 只看自己 |

## 情况四：角色不对等（有协调者）

```bash
python collab.py init --people lead,dev,ops
```

约定：`lead` 不参与具体执行，只处理「别人无法决策」的事。
其余人之间直接沟通，不经过 lead。

## 情况五：人机混合

一个人 + 两个 agent：

```bash
python collab.py init --people me,agent1,agent2
```

`me` 不挂等待任务（人本来就会被消息提醒），
但 agent 之间和 agent→me 用同一套通道。

## 情况六：只有一个人（自用）

用它给自己做「待办提醒 + 日志告警」也可以：

```bash
python collab.py init --people me
python collab.py daemon --as me --interval 60   # 日志报错就 bump flag
```

---

## 迁移 / 改名

改 `collab.json` 的 `people` 即可，不用改代码。

新增身份后，让它在自己会话里挂一次等待任务：

```bash
python collab.py wait --as <新身份> --timeout 14400
```

旧身份的 inbox 目录保留，历史消息不影响。
