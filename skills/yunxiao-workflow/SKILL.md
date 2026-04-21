---
name: yunxiao-workflow
description: Use when an agent needs to operate Alibaba Yunxiao workitems through the standalone yunxiao_cli project.
---

# Yunxiao Workflow

## 概述

云效工作项协作统一走 `yunxiao_cli`。

- 主入口是 `yunxiao_cli`
- 输出统一为 JSON：`success`、`profile`、`data`、`warnings`
- `workitem search` / `workitem mine` 默认返回摘要列表；需要详情时调用 `workitem get`

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

## 工作项内容模板与规范

在创建不同类型的工作项或发表评论交流时，为了保证信息的高效可读性，各 Agent 和协作者应参考以下规范使用对应的模板格式记录信息：

| 模板类型 | 适用场景 | 模板文档 |
|----------|----------|----------|
| 需求规范 | 描述业务线新功能、期望与验收标准 | [requirement-template.md](./templates/requirement-template.md) |
| 任务规范 | 拆解自需求的具体开发或实施步骤指引 | [task-template.md](./templates/task-template.md) |
| Bug规范 | 记录系统异常、缺陷复现与排查建议 | [bug-template.md](./templates/bug-template.md) |
| 回复规范 | 进度同步、代码提交、答疑确认或评审 | [reply-template.md](./templates/reply-template.md) |
| Git规范 | 指导标准代码提交与自动关联工作项 | [git-commit-template.md](./templates/git-commit-template.md) |
