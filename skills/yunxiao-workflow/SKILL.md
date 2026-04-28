---
name: yunxiao-workflow
description: >
  Use when an agent needs to operate Alibaba Yunxiao workitems, code repositories, or project management.
  Auto-trigger when user mentions workitem serial numbers like #ABC-1234, #PROJ-56, or any #<prefix>-<number> pattern.
triggers:
  - pattern: "#[A-Za-z]+-\\d+"
    description: "Yunxiao workitem serial number, e.g. #REQ-42, #BUG-1234, #TASK-7"
  - keywords: ["云效", "yunxiao", "工作项", "workitem", "迭代", "sprint", "codeup", "合并请求", "MR"]
---

# Yunxiao Workflow

## 概述

云效工作项协作统一走 `yunxiao_cli`。

- 主入口是 `yunxiao_cli`
- 输出统一为 JSON：`success`、`profile`、`data`、`warnings`
- `workitem search` / `workitem mine` 默认返回摘要列表；需要详情时调用 `workitem get`

## 识别规则

当用户消息中出现以下模式时，应使用本 skill 处理：

| 模式 | 示例 | 含义 |
|------|------|------|
| `#前缀-数字` | `#REQ-42`、`#BUG-1234`、`#TASK-7` | 云效工作项流水号 |
| `看一下 #XXX-数字` | "看一下 #FE-128 的进展" | 查询工作项详情 |
| `处理 #XXX-数字` | "处理一下 #BUG-99" | 流转工作项状态 |
| 提到"云效/yunxiao/工作项/迭代/sprint/codeup/MR" | "当前迭代有什么任务" | 云效相关操作 |

**流水号解析规则：**

- 格式：`#前缀-数字`，如 `#REQ-42` → serialNumber 为 `REQ-42`
- 用 `workitem get` 时直接传流水号：`yunxiao_cli workitem get REQ-42`
- 用 `knowledge context` 聚合上下文：`yunxiao_cli knowledge context REQ-42`
- 多个流水号出现时（如"看一下 #FE-1 和 #FE-2"），逐个处理

## 项目级配置

优先使用项目根目录 `.yunxiao.json` 作为 repo 级默认上下文。

如果配置不存在：

1. 先从当前对话收集 `profile`、`assignee`、`project`
2. 信息足够时直接执行 `yunxiao_cli context init --profile <profile> --assignee <assignee> --project <project>`
3. 只缺字段时一次性追问补齐，不要拆成多轮

## 字段说明

```json
{
  "profile": "<profile>",
  "assignee": "<assignee>",
  "project": "<project_id>"
}
```

扩展写法：

```json
{
  "profile": "<profile>",
  "assignee": "<assignee>",
  "project": "<project_id>",
  "token": "<token>"
}
```

| 字段 | 说明 |
|------|------|
| `profile` | CLI profile 名，作为所有命令的 `--profile` 参数 |
| `assignee` | 当前项目默认负责人；创建/更新/`mine` 等场景优先使用 |
| `project` | 当前 repo 绑定的默认项目 ID |
| `token` | 可选；存在时，命令执行前先用它刷新本地登录态 |

## 初始化流程

首次配置后执行：

```bash
yunxiao_cli login token <token> --account <assignee>
yunxiao_cli profile add <profile> --account <assignee> --org <org_id> --project <project_id>
yunxiao_cli profile use <profile>
```

多项目可直接使用：

```bash
yunxiao_cli profile add <profile> --account <assignee> --org <org_id> --project <project_id_1>,<project_id_2>
```

然后为当前 repo 写入项目配置：

```bash
yunxiao_cli context init --profile <profile> --assignee <assignee> --project <project_id>
```

## 使用流程

| 场景 | 说明 | 文档 |
|------|------|------|
| 标准研发流 | PM → 评审 → 设计 → 开发 → 测试的完整多 agent 协作流 | [flows/standard-flow.md](./flows/standard-flow.md) |

## 基础命令参考

登录与 profile：

```bash
yunxiao_cli login token <token> --account <assignee>
yunxiao_cli profile add <profile> --account <assignee> --org <org_id> --project <project_id>
yunxiao_cli profile use <profile>
```

元数据与项目：

```bash
yunxiao_cli meta reload --profile <profile>
yunxiao_cli meta types --profile <profile>
yunxiao_cli project list --profile <profile>
```

工作项：

```bash
yunxiao_cli workitem create --category Req --subject "新需求" --profile <profile>
yunxiao_cli workitem create --category Bug --subject "登录失败" --profile <profile> \
  --field "严重程度=3-一般"
yunxiao_cli workitem create --category Req --subject "附带材料" --profile <profile> \
  --attachment ./spec.md --attachment ./demo.png
yunxiao_cli workitem get 1001 --profile <profile>
yunxiao_cli workitem mine --category all --profile <profile>
yunxiao_cli workitem mine --category all --project <project_id_1>,<project_id_2> --sort time --profile <profile>
yunxiao_cli workitem search --category Task --status "处理中" --profile <profile>
yunxiao_cli workitem search --category Task --status "处理中" --project <project_id_1>,<project_id_2> --sort time --profile <profile>
yunxiao_cli workitem search --category Task --status "处理中" --profile <profile> --raw
yunxiao_cli workitem search --keyword "支付超时" --profile <profile>
yunxiao_cli workitem search --tag "性能" --priority "P1" --assigned-to "张三" --profile <profile>
yunxiao_cli workitem update 1001 --desc-file ./req.md --profile <profile>
yunxiao_cli workitem transition 1001 --to "已完成" --profile <profile>
# 目标状态有必填字段时，transition 支持直接传字段
yunxiao_cli workitem transition 1001 --to "处理中" --profile <profile> \
  --field-json '{"79":"2026-03-17","80":"2026-03-20","101586":3.5}' 
```

## 创建/更新/状态流转必填字段

当创建、更新或状态流转校验必填字段时，`workitem create`、`workitem update`、`workitem transition` 都支持：

- `--field "字段名或字段ID=值"`（可重复）
- `--field-json '{"字段名或字段ID": 值}'`（推荐，一次传完整字段集）

示例：

```bash
yunxiao_cli workitem create --category Bug --subject "登录失败" --profile <profile> \
  --field-json '{"严重程度":"3-一般"}'

yunxiao_cli workitem transition 1001 --to "处理中" --profile <profile> \
  --field-json '{"计划开始时间":"2026-03-17","计划完成时间":"2026-03-20","预计工时":3.5}'
```

多行 Markdown 描述（尤其包含代码块）统一使用 `--desc-file`，避免 shell 解析破坏正文内容。

附件：

```bash
yunxiao_cli workitem attachment upload 1001 --profile <profile> --path ./spec.md
yunxiao_cli workitem attachment list 1001 --profile <profile>
yunxiao_cli workitem attachment get 1001 --profile <profile> --file file-1
```

附件相关参数说明：

- `workitem create --attachment <file>`：可重复传入多个文件；工单创建成功后按顺序上传
- `workitem attachment upload <id> --path <file>`：给已有工单补传单个附件
- `workitem attachment get <id> --file <file_id>`：查看附件文件信息和下载地址

失败语义：

- `workitem create --attachment` 先创建工单，再逐个上传附件
- 附件上传 `fail-fast`
- 任一附件失败，命令直接返回失败
- 错误返回里会带上 `workitem`、`uploaded_attachments`、`failed_attachment`

评论与关联：

```bash
yunxiao_cli comment add --workitem <id> --content "@agent 请评审" --profile <profile>
yunxiao_cli comment list --workitem <id> --profile <profile>
yunxiao_cli relation add --parent <id> --child <id> --profile <profile>
yunxiao_cli relation children --parent <id> --profile <profile>
```

查询约定：

- `workitem search` / `workitem mine` 默认返回摘要字段：`id`、`serial`、`subject`、`category`、`type`、`projectId`、`project`、`statusId`、`status`、`statusPhase`、`assigneeId`、`assignee`、`parentId`、`updatedAt`
- 默认不要假设搜索结果里有完整详情字段；需要正文、评论、附件、父项等详情时，拿摘要里的 `id` 再调用 `workitem get`
- 只有排障或兼容旧脚本时才使用 `--raw`

## 约束

- Agent 先读项目根目录 `.yunxiao.json`
- 有 `token`：先执行登录刷新，再继续后续命令
- 无 `token`：直接复用本机已保存的 profile 与 account
- 默认把 `.yunxiao.json.project` 作为当前 repo 的项目上下文
- 默认把 `.yunxiao.json.assignee` 作为当前 repo 的负责人上下文
- 状态、类型、字段、成员解析统一走项目缓存
- `workitem mine` 与 `workitem search` 在多项目 profile 下会对每个项目拉取全部分页数据后再统一按 `--sort` 排序；但 repo 已绑定 `project` 时默认只查该项目

## 搜索增强参数

`workitem search` 除了 `--category` 和 `--status`，还支持以下过滤条件：

| 参数 | 说明 |
|------|------|
| `--keyword` | 全文搜索标题+描述 |
| `--tag` | 标签过滤，多个用逗号分隔 |
| `--priority` | 优先级，如 P1、P2 |
| `--assigned-to` | 负责人 userId 或名称 |
| `--sprint` | 迭代 ID |
| `--created-after` / `--created-before` | 创建时间范围，格式 `YYYY-MM-DD` |
| `--updated-after` / `--updated-before` | 更新时间范围，格式 `YYYY-MM-DD` |

```bash
yunxiao_cli workitem search --keyword "支付超时"
yunxiao_cli workitem search --tag "性能,P1" --assigned-to "张三"
yunxiao_cli workitem search --created-after "2026-01-01" --created-before "2026-03-31"
yunxiao_cli workitem search --category Task --keyword "登录" --priority "P1"
```

## 迭代与版本

```bash
# 迭代
yunxiao_cli sprint list                                  # 列出迭代
yunxiao_cli sprint list --status DOING                   # 只看进行中的
yunxiao_cli sprint get <sprint_id> --project <project_id> # 迭代详情

# 版本
yunxiao_cli version list                                 # 列出版本
yunxiao_cli version list --status TODO                   # 只看待开始的
yunxiao_cli version list --name "v2.0"                   # 按名称搜索
```

| 场景 | 操作 |
|------|------|
| "当前迭代有哪些任务" | 先 `sprint list --status DOING` 拿 sprint ID，再 `workitem search --sprint <id>` |
| "v2.0 包含哪些需求" | `version list --name v2.0` |

## 知识聚合

### `knowledge context` — 单个工作项的完整上下文

```bash
yunxiao_cli knowledge context <workitem_id>
yunxiao_cli knowledge context <workitem_id> --depth 3
```

返回结构：

| 字段 | 含义 |
|------|------|
| `workitem` | 工作项完整详情（标题、描述、状态、负责人等） |
| `comments` | 所有评论和讨论 |
| `attachments` | 附件列表 |
| `parentChain` | 从直接父项到根的链，理解需求层级 |
| `childrenTree` | 递归子项树，按 `--depth` 控制深度 |

### `knowledge project-summary` — 项目全局概览

```bash
yunxiao_cli knowledge project-summary
yunxiao_cli knowledge project-summary --project <project_id>
```

返回结构：`activeSprints`（活跃迭代列表）+ `categoryStats`（各分类工作项数量统计）。

| 场景 | 操作 |
|------|------|
| "总结需求 #1234 的讨论" | `knowledge context 1234` → 读 `comments` |
| "这个需求拆了哪些任务" | `knowledge context 1234 --depth 2` → 分析 `childrenTree` |
| "这个 Bug 属于哪个大需求" | `knowledge context <bug_id>` → 读 `parentChain` |
| "项目目前什么状态" | `knowledge project-summary` |

注意：`--depth` 越大请求越多，建议不超过 3。

## 代码管理（Codeup）

```bash
# 仓库
yunxiao_cli codeup repo list [--search "frontend"]
yunxiao_cli codeup repo get <repo_id>

# 分支
yunxiao_cli codeup branch list <repo_id> [--search "feature"]

# 文件
yunxiao_cli codeup file list <repo_id> [--path "src/main"] [--ref develop] [--recursive]
yunxiao_cli codeup file get <repo_id> "README.md" [--ref develop]

# 提交
yunxiao_cli codeup commit list <repo_id> [--ref develop] [--path "src/"] [--search "fix"]
yunxiao_cli codeup commit list <repo_id> --since "2026-04-01T00:00:00Z"
yunxiao_cli codeup commit get <repo_id> <sha>

# 代码比较
yunxiao_cli codeup compare <repo_id> --from master --to develop

# 合并请求（MR）
yunxiao_cli codeup mr list [--repo <repo_id>] [--state opened] [--search "新功能"]
yunxiao_cli codeup mr get <repo_id> <local_id>
yunxiao_cli codeup mr comments <repo_id> <local_id>
```

| 场景 | 操作 |
|------|------|
| "README 写了什么" | `codeup file get <repo_id> README.md` |
| "src 目录有哪些文件" | `codeup file list <repo_id> --path src` |
| "最近有什么代码变更" | `codeup commit list <repo_id> --since 2026-04-20T00:00:00Z` |
| "master 和 develop 差了什么" | `codeup compare <repo_id> --from master --to develop` |
| "有哪些待审查的 MR" | `codeup mr list --state opened` |
| "审查者对 MR #5 说了什么" | `codeup mr comments <repo_id> 5` |

注意：`repo_id` 可以是数字 ID 也可以是 `orgId/repoName` 格式；`codeup file get` 返回 base64 编码内容。

## 工作项内容模板与规范

创建工作项或发表评论时，**必须**按以下流程使用对应模板。

### 模板通用规则

- 模板文件中 `{{占位符}}` 标记的位置**必须填充**实际内容
- 模板文件中 `<!-- -->` HTML 注释是给 AI 的提示，生成最终内容时**必须删除**
- 标题规范写在模板顶部注释块中，生成后传入 `--subject` 参数
- 可选章节（标题含"可选"）不适用时**整节删除**，不要留空

### 创建工作项（Req / Task / Bug）

操作流程：

1. 根据 `--category` 选择对应模板文件
2. 读取模板，按上下文填充所有 `{{}}` 占位符
3. 删除所有 `<!-- -->` 注释
4. 将最终内容写入临时 `.md` 文件，通过 `--desc-file` 传入
5. 按模板顶部注释的「标题规范」生成标题，通过 `--subject` 传入

| category | 标题格式 | 描述模板 |
|----------|----------|----------|
| Req | `[模块/归属] 需求简述` | [requirement-template.md](./templates/requirement-template.md) |
| Task | `[父需求摘要] 具体任务` | [task-template.md](./templates/task-template.md) |
| Bug | `[环境/模块] 现象表现` | [bug-template.md](./templates/bug-template.md) |

### 发表评论

根据评论目的选择对应模板，填充后作为 `comment add --content` 的内容：

| 评论目的 | 模板 |
|----------|------|
| 进度同步 / 代码提交 | [reply-progress-template.md](./templates/reply-progress-template.md) |
| 疑点确认 / 阻塞报告 | [reply-blocker-template.md](./templates/reply-blocker-template.md) |
| 评审申请 | [reply-review-template.md](./templates/reply-review-template.md) |

### Git 提交规范

| 模板 | 说明 |
|------|------|
| [git-commit-template.md](./templates/git-commit-template.md) | Angular 规范 + 云效工作项自动关联 |
