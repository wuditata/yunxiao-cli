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
  "project": "<project_id>",
  "assignee": "<assignee>"
}
```

| 字段 | 说明 |
|------|------|
| `token` | 云效登录 token，用于 `yunxiao_cli login token <token>` |
| `profile` | CLI profile 名，作为所有命令的 `--profile` 参数 |
| `project` | 当前代码仓对应的云效项目 ID |
| `assignee` | 当前用户身份标识，用于过滤"我的工作项"、"指派负责人"等场景 |

## 初始化流程

首次配置后执行：

```bash
yunxiao_cli login token <token> --account <assignee>
yunxiao_cli profile add <profile> --account <assignee> --org <org_id> --project <project_id>
yunxiao_cli profile use <profile>
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
yunxiao_cli workitem get 1001 --profile <profile>
yunxiao_cli workitem mine --category all --profile <profile>
yunxiao_cli workitem search --category Task --status "处理中" --profile <profile>
yunxiao_cli workitem update 1001 --desc-file ./req.md --profile <profile>
yunxiao_cli workitem transition 1001 --to "已完成" --profile <profile>
# 目标状态有必填字段时，transition 支持直接传字段
yunxiao_cli workitem transition 1001 --to "处理中" --profile <profile> \
  --field-json '{"79":"2026-03-17","80":"2026-03-20","101586":3.5}' 
```

## 状态流转必填字段

当状态流转校验必填字段时，`workitem update` 与 `workitem transition` 都支持：

- `--field "字段名或字段ID=值"`（可重复）
- `--field-json '{"字段名或字段ID": 值}'`（推荐，一次传完整字段集）

示例：

```bash
yunxiao_cli workitem transition 1001 --to "处理中" --profile <profile> \
  --field-json '{"计划开始时间":"2026-03-17","计划完成时间":"2026-03-20","预计工时":3.5}'
```

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
- 不自动合并 MR
