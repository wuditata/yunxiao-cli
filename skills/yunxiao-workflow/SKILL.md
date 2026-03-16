---
name: yunxiao-workflow
description: Use when an agent needs to operate Alibaba Yunxiao workitems through the standalone yunxiao_cli project.
---

# Yunxiao Workflow

## 概述

云效工作项协作统一走 `yunxiao_cli`。

- 主入口是 `yunxiao_cli`
- 输出统一为 JSON：`success`、`profile`、`data`、`warnings`
- 旧 `workflow_*.py` 脚本仅保留为实现参考，不再作为主调用方式

## 项目级配置

每个使用本 skill 的项目，在根目录放 `.yunxiao.json`，详见 [config.md](./config.md)。

## 使用流程

| 场景 | 说明 | 文档 |
|------|------|------|
| 标准研发流 | PM → 评审 → 设计 → 开发 → 测试的完整多 agent 协作流 | [flows/standard-flow.md](./flows/standard-flow.md) |

## 基础命令参考

登录与 profile：

```bash
yunxiao_cli login token <token> --account pm-a
yunxiao_cli profile add pm-dev --account pm-a --org <org_id> --project <project_id>
yunxiao_cli profile use pm-dev
```

元数据与项目：

```bash
yunxiao_cli meta reload --profile pm-dev
yunxiao_cli meta types --profile pm-dev
yunxiao_cli project list --profile pm-dev
```

工作项：

```bash
yunxiao_cli workitem create --profile pm-dev --category Req --subject "新需求"
yunxiao_cli workitem get 1001 --profile pm-dev
yunxiao_cli workitem mine --profile pm-dev --category all
yunxiao_cli workitem search --profile pm-dev --category Task --status "处理中"
yunxiao_cli workitem update 1001 --profile pm-dev --desc-file ./req.md
yunxiao_cli workitem transition 1001 --profile pm-dev --to "已完成"
```

评论与关联：

```bash
yunxiao_cli comment add --profile pm-dev --workitem 1001 --content "@agent 请评审"
yunxiao_cli comment list --profile pm-dev --workitem 1001
yunxiao_cli relation add --profile pm-dev --parent 1001 --child 2001
yunxiao_cli relation children --profile pm-dev --parent 1001
```

## 约束

- Agent 读取项目根目录 `.yunxiao.json` 获取 `profile`，显式传 `--profile`
- 状态、类型、字段、成员解析统一走项目缓存
- 不自动合并 MR
- 旧脚本只用于排查或迁移参考

