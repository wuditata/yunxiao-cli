---
name: yunxiao-workflow
description: Use when an agent needs to operate Alibaba Yunxiao workitems through the standalone yunxiao_cli project.
---

# Yunxiao Workflow

## 概述

云效工作项协作统一走 `yunxiao_cli`。

- 主入口是 `yunxiao_cli`
- 输出统一为 JSON：`success`、`profile`、`data`、`warnings`

## 项目级配置

每个使用本 skill 的项目，在根目录必须存在配置文件 `.yunxiao.json`

## 字段说明

```json
{
  "token": "<token>",
  "profile": "<profile>",
  "project": ["<project_id>"],
  "assignee": "<assignee>"
}
```

| 字段 | 说明 |
|------|------|
| `token` | 云效登录 token，用于 `yunxiao_cli login token <token>` |
| `profile` | CLI profile 名，作为所有命令的 `--profile` 参数 |
| `project` | 支持单项目 ID、逗号分隔的多个项目 ID，或项目 ID 数组 |
| `assignee` | 当前用户身份标识，用于过滤"我的工作项"、"指派负责人"等场景 |

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

## 约束

- Agent 读取项目根目录 `.yunxiao.json` 获取 `profile`，显式传 `--profile`
- 状态、类型、字段、成员解析统一走项目缓存
- `workitem mine` 与 `workitem search` 在多项目 profile 下会对每个项目拉取全部分页数据后再统一按 `--sort` 排序

## 工作项内容模板与规范

在创建不同类型的工作项或发表评论交流时，为了保证信息的高效可读性，各 Agent 和协作者应参考以下规范使用对应的模板格式记录信息：

| 模板类型 | 适用场景 | 模板文档 |
|----------|----------|----------|
| 需求规范 | 描述业务线新功能、期望与验收标准 | [requirement-template.md](./templates/requirement-template.md) |
| 任务规范 | 拆解自需求的具体开发或实施步骤指引 | [task-template.md](./templates/task-template.md) |
| Bug规范 | 记录系统异常、缺陷复现与排查建议 | [bug-template.md](./templates/bug-template.md) |
| 回复规范 | 进度同步、代码提交、答疑确认或评审 | [reply-template.md](./templates/reply-template.md) |
| Git规范 | 指导标准代码提交与自动关联工作项 | [git-commit-template.md](./templates/git-commit-template.md) |
