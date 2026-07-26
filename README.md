# 栈桥 OJ：本地 408 数据结构刷题平台

一个面向个人学习的本地 Online Judge。支持题目与测试点管理、C/C++ 在线编辑、提交历史，以及使用 Docker 一次性沙箱完成编译和逐测试点判题。

## 启动

前置条件：Windows 10/11、Docker Desktop（Linux containers / WSL 2 后端）。

```powershell
docker compose up --build -d
```

浏览器打开 [http://localhost:3000](http://localhost:3000)。首次构建需要下载 Node、Python、PostgreSQL、Nginx 和 Debian 基础镜像。也可以在 PowerShell 中运行：

```powershell
.\start.ps1
```

查看状态和判题日志：

```powershell
docker compose ps
docker compose logs -f worker
```

停止服务（数据保留）：

```powershell
docker compose down
```

PostgreSQL 数据保存在 Docker 卷 `local-408-oj-data`。只有执行 `docker compose down -v` 才会同时删除全部题目、测试点和提交记录。

## 主要能力

- 题目：创建、编辑、删除、搜索、标签分类，配置题面、样例、时间与内存限制。
- 题面：使用单一 Markdown 文档，支持 GFM 表格、任务列表、代码块和 KaTeX 数学公式，并提供实时预览。
- 测试点：在线输入或成对上传 UTF-8 input/output 文件，一题支持任意多个测试点。
- 编辑器：C 17 / C++ 17 语法高亮、行号、自动缩进、括号匹配和本地草稿。
- 判题：Accepted、Wrong Answer、Compile Error、Runtime Error、Time Limit Exceeded、Memory Limit Exceeded。
- 记录：保存每次源码、编译信息、最长用时和逐测试点结果。

空数据库会自动加入 3 道可直接练习的示例题。可在 `.env` 中设置 `SEED_DEMO_DATA=false` 关闭。

## 408 真题题库

API 启动时会幂等导入 2009-2025 年原卷中明确要求使用 C/C++/Java 实现算法或函数的 17 道数据结构代码题，恰好每年一道，共 188 个测试点。手工计算、证明、算法执行模拟和只要求简述思路的综合应用题不会改编进 OJ。每道题均包含：

- 完整的洛谷式 Markdown 题面和统一的 `【真题（年份）】` 标记；
- 原卷题号、OJ 改编说明、输入输出、数据范围与样例；
- 固定随机种子生成的边界及随机测试点；
- 由可信参考算法计算的标准输出。

导入器通过题面中的稳定来源标识更新官方题库，不会按标题匹配，也不会删除或覆盖自行创建的题目。重复运行只检查版本和内容：

```powershell
docker compose exec api python -m app.import_questions
```

题库范围收窄或某道受管题退出目录后，可显式清理旧受管题；该命令只删除带内部来源标记且不在当前目录中的题目：

```powershell
docker compose exec api python -m app.import_questions --prune-stale
```

可通过 `.env` 中的 `IMPORT_408_QUESTIONS=false` 关闭启动时导入。

题目范围采用严格的“原卷要求程序实现”口径，而不是“理论上可以改成程序”的口径。核验使用 [2009-2025 重制试卷](https://github.com/neville-studio/408-exam-paper) 为主来源，并与 [CodeBrick 逐年数据结构题库](https://www.codebrick.tech/exam-408/ds/) 和公开历年大题整理交叉检查。2022 年第 42 题虽要求设计算法，但原卷明确注明“不需要程序实现”，因此也不导入。

2026 年考试目前没有可用于逐题核验的公开原卷，公开回忆版之间仍有题面和分值冲突，因此没有以 `【真题（2026）】` 导入。这样可以避免把未经核实的回忆内容标成准确真题。

## 服务结构

```text
Browser :3000
    |
  Nginx / React
    |
 FastAPI API ----- PostgreSQL volume
    |
 database queue
    |
 Judge worker ----- Docker Desktop socket
                         |
                   ephemeral sandbox
```

`api` 容器不挂载 Docker socket。只有可信的 `worker` 能创建沙箱；用户代码所在沙箱不会挂载宿主机目录，也不会获得 Docker socket。

## 沙箱约束

每次提交先在独立编译容器中生成二进制，然后每个测试点使用一个全新的运行容器。运行容器采用：

- `--network none` 禁止网络访问；
- 只读根文件系统，仅提供有大小上限的临时目录；
- 非 root 用户、`cap-drop ALL`、`no-new-privileges`；
- Docker cgroup 内存/CPU 限制、进程数限制和文件描述符限制；
- CPU/墙钟超时和 2 MB 输出限制；
- 判题结束后强制删除一次性容器。

这是适合个人本地学习的隔离方案。Docker socket 本身拥有较高权限，因此不要向不受信任的网络暴露 API 或 worker；默认部署只面向本机端口。

## API

FastAPI 文档位于 [http://localhost:8000/docs](http://localhost:8000/docs)，健康检查为 `GET /api/health`。前端通过 Nginx 的 `/api` 反向代理访问后端。
