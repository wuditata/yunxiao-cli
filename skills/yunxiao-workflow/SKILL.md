---
name: yunxiao-workflow
description: >
  Operate Alibaba Cloud Yunxiao (阿里云云效) via the `yunxiao` CLI: workitems, sprints, versions,
  Codeup repos/MRs, Flow pipelines, knowledge aggregation and Thoughts docs.
  Use whenever the user mentions 云效/yunxiao, workitem serial numbers like #REQ-42, #BUG-1234
  or any #<prefix>-<number> pattern, 工作项/需求/任务/缺陷, 迭代/sprint, 版本, codeup,
  合并请求/MR, 流水线/flow/pipeline, 打包测试或生产环境 — or asks to init project config, fetch/update tasks,
  review code, create/review/merge MRs, even without naming the tool.
triggers:
  - pattern: "#[A-Za-z]+-\\d+"
    description: "Yunxiao workitem serial number, e.g. #REQ-42, #BUG-1234, #TASK-7"
  - keywords: ["云效", "yunxiao", "工作项", "workitem", "迭代", "sprint", "codeup", "合并请求", "MR", "flow", "流水线", "打包"]
---

# Yunxiao Workflow

云效协作统一走 `yunxiao` CLI。所有命令输出 JSON 信封：`success` / `profile` / `data` / `warnings`；失败时 `success=false` 且 `error.message` 带原因。命令失败先读 `error.message`，按下方各路线的「失败分支」处理，同一命令最多重试 1 次。

## 何时用哪条路线

| 用户意图（示例） | 路线 |
|------|------|
| "初始化云效配置"、"这个 repo 绑哪个项目"、首次在新 repo 执行任何云效操作 | [路线 A：项目上下文](#路线-a项目上下文获取或生成) |
| "我有哪些任务"、"当前迭代要做什么"、"看一下 #REQ-42" | [路线 B：领取任务](#路线-b领取任务) |
| "处理 #BUG-99"、"更新任务描述"、"把它流转到已完成"、"汇报进度" | [路线 C：推进任务](#路线-c推进任务) |
| "提个 MR"、"审一下 MR #5"、"合并 MR"、"评审意见发到 MR 上" | [路线 D：代码评审与 MR](#路线-d代码评审与-mr) |
| "打包测试环境"、"打包生产环境"、"打包生产环境后端" | [路线 E：配置化 Flow 打包](#路线-e配置化-flow-打包) |
| 流水线 / 迭代版本 / 知识聚合 / Thoughts 导出 / Codeup 读文件 | [references/commands.md](./references/commands.md) |
| 多 agent 标准研发流（PM→评审→设计→开发→测试） | [flows/standard-flow.md](./flows/standard-flow.md) |

**流水号识别**：`#前缀-数字`（如 `#REQ-42`）是工作项流水号，去掉 `#` 后可直接传给 `workitem get / update / transition` 和 `knowledge context`，无需先换算成 ID。多个流水号逐个处理。

---

## 路线 A：项目上下文（获取或生成）

任何工作项/MR 操作前都先走这一步。目标：确定 `profile` / `assignee` / `project` 三元组。

**A1. 读取现有配置**（优先）

读项目根目录 `.yunxiao.json`：

```json
{"profile": "<profile>", "assignee": "<assignee>", "project": "<project_id>", "token": "<可选>"}
```

- 文件存在 → 直接使用，后续命令可省略 `--profile`；有 `token` 字段时 CLI 会自动刷新登录态，无需手动处理
- `assignee` 只影响 `create` 和 `mine` 的默认负责人；`update` 永远不会隐式改负责人（改负责人必须显式传 `--assigned-to`）

**A2. 配置不存在 → 生成**

1. 从对话上下文收集三元组；能收集齐就直接执行，缺什么一次性追问补齐（不要拆成多轮）：

```bash
yunxiao context init --profile <profile> --assignee <assignee> --project <project_id>
```

2. 不知道有哪些 project 可选时，先列出让用户挑：

```bash
yunxiao project list --profile <profile>        # → data.projects[].id / .name
```

**A3. 本机连 profile 都没有 → 完整初始化**（只在全新机器上需要）

```bash
yunxiao login token <token> --account <account>    # → 返回可见组织和项目
yunxiao profile add <profile> --account <account> --org <org_id> --project <project_id>[,<project_id_2>]
yunxiao profile use <profile>
yunxiao context init --profile <profile> --assignee <account> --project <project_id>
```

token 由用户提供（云效个人设置 → 个人访问令牌），不要编造。

**失败分支**：命令报 profile/账号不存在 → 走 A3；报项目无权限 → `project list` 核对可见项目后让用户确认。

---

## 路线 B：领取任务

**B1. 我的任务**

```bash
yunxiao workitem mine --category all            # → data.items[] 摘要列表
```

摘要字段固定为：`id`、`serial`、`subject`、`category`、`type`、`projectId`、`project`、`statusId`、`status`、`statusPhase`、`assignee`、`parentId`、`updatedAt`。按 `status` / `statusPhase` 在结果里过滤"待处理/处理中"，不要假设摘要里有正文。

**B2. 当前迭代的任务**

```bash
yunxiao sprint list --status DOING              # → 取 data.sprints[].id
yunxiao workitem search --sprint <sprint_id>    # → 该迭代全部工作项
```

**B3. 条件搜索**（找特定任务）

```bash
yunxiao workitem search --category Task --status "处理中"
yunxiao workitem search --keyword "支付超时"                 # 标题+描述全文
yunxiao workitem search --assigned-to "张三" --priority P1
```

其余过滤参数（tag/时间范围等）见 [references/commands.md](./references/commands.md#搜索参数)。

**B4. 读取选中任务的完整上下文**

从摘要选中目标后，用一条命令拿全部详情（替代 get+comment list+relation 多次调用）：

```bash
yunxiao knowledge context <id或流水号>            # → workitem + comments + attachments + parentChain + childrenTree
yunxiao knowledge context REQ-42 --depth 2       # 需要看子任务拆解时加 depth（≤3）
```

只要正文不要评论时用 `workitem get <id>` 即可。

---

## 路线 C：推进任务

**前置**：先 B4 读一遍上下文再动手，尤其要看清当前 `status` 和评论里的最新讨论。

**C1. 更新描述/标题**

```bash
yunxiao workitem update <id或流水号> --desc-file ./desc.md      # 多行 Markdown 一律走文件，防 shell 破坏内容
yunxiao workitem update <id或流水号> --subject "新标题"
```

**C2. 汇报进度 / 提问（评论）**

按目的选模板填充（`{{}}` 占位符必填、`<!-- -->` 注释删除）后发评论：

| 目的 | 模板 |
|------|------|
| 进度同步 / 代码提交 | [reply-progress-template.md](./templates/reply-progress-template.md) |
| 疑点确认 / 阻塞报告 | [reply-blocker-template.md](./templates/reply-blocker-template.md) |
| 评审申请 | [reply-review-template.md](./templates/reply-review-template.md) |

```bash
yunxiao comment add --workitem <id> --content "<填充后的模板内容>"
```

**C3. 状态流转**

```bash
yunxiao workitem transition <id或流水号> --to "<目标状态名>"
```

**失败分支（重要）**：

- 报必填字段缺失 → 先查字段定义，再带字段重试**一次**：

```bash
yunxiao meta fields --category <category>       # → 字段 ID、名称、类型、可选值；不要猜字段名和取值
yunxiao workitem transition <id> --to "处理中" \
  --field-json '{"计划开始时间":"2026-03-17","计划完成时间":"2026-03-20","预计工时":3.5}'
```

- 报状态不存在 → `yunxiao meta statuses --category <category>` 查合法状态名后重试
- 仍失败 → 停止，把 `error.message` 原样报给用户

**C4. 新建任务/缺陷**（拆子任务、报 Bug）

1. 按 category 选模板生成描述文件：Req → [requirement-template.md](./templates/requirement-template.md)、Task → [task-template.md](./templates/task-template.md)、Bug → [bug-template.md](./templates/bug-template.md)；标题格式按模板顶部注释（Req `[模块] 简述` / Task `[父需求摘要] 任务` / Bug `[环境/模块] 现象`）
2. 创建并关联：

```bash
yunxiao workitem create --category Task --subject "[支付] 超时重试逻辑" --desc-file ./task.md \
  [--parent <父项id或流水号>] [--attachment ./spec.md]
yunxiao relation add --parent <req_id> --child <task_id>     # create 没传 --parent 时补关联
```

创建 Bug 常见必填「严重程度」：`--field-json '{"严重程度":"3-一般"}'`；报必填字段错误时同 C3 失败分支。

**C5. 登记实际工时**

```bash
yunxiao workitem effort add <id或流水号> --hours 4 --date 2026-07-21 --description "完成 Gateway SLS 日志接入"
yunxiao workitem effort list <id或流水号>
```

- `--work-type` 可选，仅在项目已配置对应类型时传入。
- 不要通过 `workitem update --field-json` 修改「实际工时」，该字段是工时记录的只读汇总。
- 登记后使用 `workitem effort list` 或 `workitem get` 核对记录及汇总。

---

## 路线 D：代码评审与 MR

MR 在云效 OpenAPI 里叫 ChangeRequest。`repo_id` 优先用数字 ID。

**D0. 定位仓库**（不知道 repo_id 时）

```bash
yunxiao codeup repo list --search "<仓库名关键词>"     # → data.repositories[].id
```

仓库名通常取 git remote URL 的最后一段（`git remote get-url origin`）。

**D1. 提交 MR**（代码写完 → MR → 回填工作项）

1. 提交代码：commit message 按 [git-commit-template.md](./templates/git-commit-template.md)（Angular 规范 + 关联工作项）
2. MR 描述写入 `mr.md`（多行 Markdown 一律走 `--desc-file`），创建 MR：

```bash
yunxiao codeup mr create <repo_id> \
  --title "feat: 支付超时重试" \
  --source <当前分支> --target main \
  --desc-file ./mr.md \
  --workitem <工作项id> \
  [--reviewer <user_id_1>,<user_id_2>] [--ai-review]
# → data.changeRequest.localId / .detailUrl
```

3. 回填工作项：按 reply-progress 模板评论 MR 链接（C2），需要时流转状态（C3）。

**D2. 评审 MR**（别人代码 → 意见 → 通过则合并）

1. 找目标 MR：

```bash
yunxiao codeup mr list --state opened [--repo <repo_id>] [--search "<标题关键词>"]   # → localId
```

2. 一条命令拿全部评审上下文：

```bash
yunxiao codeup mr review <repo_id> <local_id>
# → data.changeRequest（详情）/ patchSets（版本）/ comments（已有评论）/ compare.diffs（代码差异）
```

3. 基于 `compare.diffs` 逐文件审查，产出意见。
4. 发表评审意见——具体问题发行内评论（钉在文件+行号上），总体结论发全局评论；版本 ID 自动解析，无需手动传：

```bash
yunxiao codeup mr comment <repo_id> <local_id> --file src/main.py --line 42 --content "这里会空指针"
yunxiao codeup mr comment <repo_id> <local_id> --content-file ./review-summary.md
yunxiao codeup mr comment <repo_id> <local_id> --reply <comment_biz_id> --content "已修复" --resolved
```

5. 结论处理：
   - 通过 → 合并（默认 no-fast-forward、保留源分支；确需删分支才加 `--remove-source-branch`）：

```bash
yunxiao codeup mr merge <repo_id> <local_id> [--message "..."]
```

   - 需修改 → 行内评论列清问题，**不要合并**，告知作者。

**危险操作确认**：`mr merge`、`--remove-source-branch`、`workitem transition --to 已取消` 属于不可逆/高影响操作，执行前先向用户展示目标和影响，获得明确同意再执行。

---

## 路线 E：配置化 Flow 打包

**E1. 读取配置**

1. 优先读取当前项目 `.yunxiao.json`；其中包含非空 `flow` 对象时直接使用。
2. 项目配置不存在或没有 `flow` 时，先取项目配置中的 `project`；没有项目配置则执行 `yunxiao profile show`，取 `data.profile.project`。
3. 根据项目 ID 唯一匹配 `~/.yunxiao/projects/*-<project-id>.json`。全局文件名固定为 `~/.yunxiao/projects/<project-name>-<project-id>.json`，文件内容与项目级配置完全一致。

项目级与全局配置不合并。全局配置不存在或同一项目 ID 匹配多个文件时停止执行并报告原因。

**E2. 选择并校验**

- “打包生产环境”选择 `prod` 下全部目标；“打包生产环境后端”只选择 `prod.backend`；测试环境使用 `test`。
- 启动前一次性校验全部选中项：`pipelineId` 必须非空，`params` 必须是 JSON 对象。
- 环境、目标或配置无效时不启动任何流水线，并返回合法选项。

**E3. 启动流水线**

将每项 `params` 压缩为 JSON，逐个调用现有命令：

```bash
yunxiao flow run create <pipeline_id> --params '<params-json>' --profile <profile>
```

PowerShell 7 中使用变量传递 JSON，避免转义破坏参数：

```powershell
$params = $target.params | ConvertTo-Json -Depth 100 -Compress
yunxiao flow run create $target.pipelineId --params $params --profile $config.profile
```

单项 API 失败时继续其余目标，最终按目标汇总 `pipelineRunId` 或错误。打包层不自动重试，避免重复创建流水线运行。

---

## 通用约束

- 摘要 vs 详情：`search`/`mine` 只给摘要（够选目标即可），正文/评论/附件一律再调 `get` 或 `knowledge context`；`--raw` 只在排障时用
- 不要编造 ID、流水号、状态名、字段名；不确定就先查（`meta fields` / `meta statuses` / `project list`），或问用户
- 多项目 profile 下 `mine`/`search` 会聚合全部项目再排序；repo 已绑定 `.yunxiao.json.project` 时默认只查该项目
- `workitem get` 返回 `resources[]`，聚合了附件与正文内嵌资源的真实下载地址
- 附件上传 fail-fast：`create --attachment` 先建单后传附件，任一失败即返回错误（错误里带 `workitem`、`uploaded_attachments`、`failed_attachment`）

## 详细参考

- [references/commands.md](./references/commands.md) — 全量命令速查：搜索参数、迭代/版本、知识聚合、Thoughts 导出、Flow 流水线、Codeup 读操作、附件
- [flows/standard-flow.md](./flows/standard-flow.md) — 多 agent 标准研发流
- [templates/](./templates/) — 工作项/评论/commit 模板（`{{}}` 必填、`<!-- -->` 删除、可选章节不适用整节删）
