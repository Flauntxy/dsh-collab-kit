# 发布到 GitHub

本目录已经是一个可直接发布的仓库内容（13 个文件，约 20 KB）。

## 一、先在 GitHub 建仓库

网页操作：

1. 打开 https://github.com/new
2. Repository name：`dsh-collab-kit`（或你喜欢的名字）
3. 选 Public / Private
4. **不要**勾选 Add a README / .gitignore / license（这里已经有了）
5. 点 Create repository

## 二、本机安装 git

当前这台机器**没有安装 git**（`git --version` 找不到）。

任选其一：

| 方式 | 命令 |
|---|---|
| 官网安装包 | https://git-scm.com/download/win 下载后一路下一步 |
| Scoop | `scoop install git` |
| 便携版 | 下载 PortableGit，解压后把 `cmd` 目录加入 PATH |

装完后新开一个终端验证：

```bash
git --version
```

## 三、推送（在 dsh-collab-kit 目录里）

```bash
cd <你的工具包目录>

git init
git add -A
git -c user.name="your-name" -c user.email="you@example.com" commit -m "feat: 多对话协作通道（留言 + 唤醒 + 自检）"
git branch -M main
git remote add origin https://github.com/<你的用户名>/dsh-collab-kit.git
git push -u origin main
```

> 第一次 push 会要求登录。GitHub 已不支持密码，请用
> **Personal Access Token**（Settings → Developer settings → Tokens）当密码，
> 或用 GitHub Desktop / VS Code 的图形界面推送。

## 四、不想装 git 的替代方案

GitHub 网页支持直接上传文件：

1. 打开新建的仓库
2. 点 **Add file → Upload files**
3. 把 `dsh-collab-kit` 里的文件拖进去（含 `docs` 子目录）
4. 填一句提交说明，点 Commit

> 网页上传不保留可执行位，但本仓库都是 .py/.md/.bat，不受影响。

## 五、发布前检查清单

- [ ] `collab.json` 没有提交（含身份列表，属于个人配置，已在 .gitignore）
- [ ] `board/`、`inbox/`、`logs/` 没有提交（运行时数据，已忽略）
- [ ] `__pycache__` 没有提交（已忽略）
- [ ] 没有把真实 cookie / token 写进任何文档
- [ ] README 里的链接能点开

可以用一条命令确认将提交什么：

```bash
git status --short
```

## 六、发布后建议补的

| 项 | 说明 |
|---|---|
| Topics | 在仓库 Settings 里加 `ai-agents`、`multi-agent`、`collaboration`、`deepseek` |
| About | 一句话：让多个 AI 对话互相留言并被自动唤醒（零轮询成本） |
| Releases | 打一个 `v1.0.0` tag，附上 zip |
| Issue 模板 | 至少给「bug」和「用法提问」两个模板 |
