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

## 前置要求

```bash
cd /opt/foxhis/projects/lab/yunxiao-cli
./install.sh
```

## 典型流程

登录并建立 profile：

```bash
yunxiao_cli login token <token> --account pm-a
yunxiao_cli profile add pm-dev --account pm-a --org <org_id> --project <project_id>
yunxiao_cli profile use pm-dev
```

查看项目元数据：

```bash
yunxiao_cli meta reload --profile pm-dev
yunxiao_cli meta types --profile pm-dev
yunxiao_cli meta statuses --profile pm-dev --category Task
yunxiao_cli meta fields --profile pm-dev --category Task
```

查看项目信息：

```bash
yunxiao_cli project list --profile pm-dev
yunxiao_cli project get --profile pm-dev
```

工作项协作：

```bash
yunxiao_cli workitem create --profile pm-dev --category Req --subject "新需求"
yunxiao_cli workitem get 1001 --profile pm-dev --with-parent
yunxiao_cli workitem mine --profile pm-dev --category all
yunxiao_cli workitem update 1001 --profile pm-dev --desc-file ./req.md
yunxiao_cli workitem transition 1001 --profile pm-dev --to "已完成"
yunxiao_cli workitem search --profile pm-dev --category Task --status "处理中"
```

评论与父子关系：

```bash
yunxiao_cli comment add --profile pm-dev --workitem 1001 --content "@agent 请评审"
yunxiao_cli comment list --profile pm-dev --workitem 1001
yunxiao_cli relation add --profile pm-dev --parent 1001 --child 2001
yunxiao_cli relation children --profile pm-dev --parent 1001
```

## 约束

- Agent 场景优先显式传 `--profile`
- 状态、类型、字段、成员解析统一走项目缓存
- 不自动合并 MR
- 旧脚本只用于排查或迁移参考

## 参考

- [README.md](/opt/foxhis/projects/lab/yunxiao-cli/README.md)
- [SKILLS.md](/opt/foxhis/projects/lab/yunxiao-cli/skills/SKILLS.md)
