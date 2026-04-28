# Standard Flow：标准研发流

多 agent 协作的产品类需求（默认需求）完整研发流程。创建需求时打标签 `standard-flow`，各 agent 按状态 + 标签过滤自己的任务。

查询约定：

- `workitem search` 只用于拿摘要列表和候选 `id`
- 选中目标工作项后，必须再调用 `workitem get <id>` 读取正文、评论、附件、父项等详情
- 不要假设 `search` 结果里自带完整详情字段

## 状态机

```
待处理 → 待评审 → 设计中 → 设计完成 → 开发中 → 开发完成 → 测试中 → 已完成
                                                                    ↘ 已取消（异常终止）
```

## 创建/流转必填字段说明

若创建或目标状态配置了必填字段（例如：严重程度、计划开始时间、计划完成时间、预计工时），需在命令中同时传字段值：

```bash
# 创建 Bug 时传严重程度
yunxiao_cli workitem create --profile <profile> \
  --category Bug \
  --subject "登录失败" \
  --field-json '{"严重程度":"3-一般"}'

# 流转状态时传字段
yunxiao_cli workitem transition <id> --profile <profile> --to "处理中" \
  --field-json '{"79":"2026-03-17","80":"2026-03-20","101586":3.5}'
```

多行 Markdown 描述统一使用 `--desc-file`，避免 shell 展开影响正文内容。

## 各阶段职责

### 阶段 1：PM Agent — 需求创建（待处理）

**触发**：用户主动唤起 PM agent，口述需求。

**步骤**：

1. 与用户对话，整理需求
2. 读取模板 [requirement-template.md](../templates/requirement-template.md)，填充所有 `{{}}` 占位符，删除 `<!-- -->` 注释，生成 `req.md`
3. 用户确认文档后，创建工作项：

```bash
yunxiao_cli workitem create --profile <profile> \
  --category Req \
  --subject "[用户运营] 新增用户画像标签" \
  --desc-file ./req.md \
  --tag standard-flow
# 默认状态为：待处理
```

4. 读取模板 [reply-review-template.md](../templates/reply-review-template.md)，填充后在评论中指定评审 agent，并推进状态：

```bash
yunxiao_cli comment add --profile <profile> --workitem <id> \
  --content "<按 reply-review-template 填充的评审申请内容>"

yunxiao_cli workitem transition <id> --profile <profile> --to "待评审"
```

---

### 阶段 2：Review Agent — 需求评审（待评审）

**触发**：agent 被唤起后，查询待评审任务：

```bash
yunxiao_cli workitem search --profile <profile> \
  --category Req --status "待评审" --tag standard-flow
```

**步骤**：

1. 读取需求文档，分析合理性和可行性

```bash
yunxiao_cli workitem get <id> --profile <profile> --with-parent
```

2. 在评论中写明评审意见：

```bash
yunxiao_cli comment add --profile <profile> --workitem <id> \
  --content "评审意见：<内容>"
```

3. PM agent 根据意见修改需求文档后，推进状态：

```bash
yunxiao_cli workitem update <id> --profile <profile> --desc-file ./req.md
yunxiao_cli workitem transition <id> --profile <profile> --to "设计中"
```

---

### 阶段 3：Design Agent — UI/交互设计（设计中）

**触发**：agent 被唤起后，查询设计中任务：

```bash
yunxiao_cli workitem search --profile <profile> \
  --category Req --status "设计中" --tag standard-flow
```

**步骤**：

1. 读取需求文档，制定设计方案

```bash
yunxiao_cli workitem get <id> --profile <profile> --with-parent
```

2. 为每个设计产物创建子任务：读取 [task-template.md](../templates/task-template.md) 填充后生成描述文件

```bash
yunxiao_cli workitem create --profile <profile> \
  --category Task \
  --subject "[用户画像标签] UI 流程设计" \
  --desc-file ./task-ui.md
yunxiao_cli relation add --profile <profile> --parent <req_id> --child <task_id>
```

3. 设计完成后，读取 [reply-progress-template.md](../templates/reply-progress-template.md) 填充后汇总评论，推进需求状态：

```bash
yunxiao_cli comment add --profile <profile> --workitem <req_id> \
  --content "<按 reply-progress-template 填充的进度同步内容>"
yunxiao_cli workitem transition <req_id> --profile <profile> --to "设计完成"
```

---

### 阶段 4：Dev Agent — 功能开发（设计完成 → 开发中）

**触发**：agent 被唤起后，查询设计完成的需求：

```bash
yunxiao_cli workitem search --profile <profile> \
  --category Req --status "设计完成" --tag standard-flow
```

**步骤**：

1. 读取需求文档和设计子任务，推进需求至开发中：

```bash
yunxiao_cli workitem get <req_id> --profile <profile> --with-parent
```

```bash
yunxiao_cli workitem transition <req_id> --profile <profile> --to "开发中"
```

2. 拆解开发子任务：读取 [task-template.md](../templates/task-template.md) 填充后生成描述文件并关联：

```bash
yunxiao_cli workitem create --profile <profile> \
  --category Task \
  --subject "[用户画像标签] 后端 getUserTag 接口" \
  --desc-file ./task-dev.md
yunxiao_cli relation add --profile <profile> --parent <req_id> --child <task_id>
```

3. 所有开发子任务完成后，读取 [reply-progress-template.md](../templates/reply-progress-template.md) 填充后推进状态：

```bash
yunxiao_cli comment add --profile <profile> --workitem <req_id> \
  --content "<按 reply-progress-template 填充的进度同步内容>"
yunxiao_cli workitem transition <req_id> --profile <profile> --to "开发完成"
```

---

### 阶段 5：QA Agent — 测试（开发完成 → 测试中）

**触发**：agent 被唤起后，查询开发完成的需求：

```bash
yunxiao_cli workitem search --profile <profile> \
  --category Req --status "开发完成" --tag standard-flow
```

**步骤**：

1. 推进至测试中，创建测试子任务：

```bash
yunxiao_cli workitem transition <req_id> --profile <profile> --to "测试中"
yunxiao_cli workitem create --profile <profile> \
  --category Task --subject "测试 - <需求名>"
yunxiao_cli relation add --profile <profile> --parent <req_id> --child <task_id>
```

2. 测试通过后：

```bash
yunxiao_cli comment add --profile <profile> --workitem <req_id> \
  --content "测试通过，用例：<数量>"
yunxiao_cli workitem transition <req_id> --profile <profile> --to "已完成"
```

3. 测试发现阻塞问题，回退至开发中：

```bash
yunxiao_cli comment add --profile <profile> --workitem <req_id> \
  --content "测试未通过，问题：<描述>"
yunxiao_cli workitem transition <req_id> --profile <profile> --to "开发中"
```

---

### 异常终止

任意阶段发现需求无法继续（需求撤销、技术不可行等）：

```bash
yunxiao_cli comment add --profile <profile> --workitem <req_id> \
  --content "终止原因：<说明>"
yunxiao_cli workitem transition <req_id> --profile <profile> --to "已取消"
```

## 约束

- 每个 agent 只处理与自己角色对应的入态
- 状态流转前必须在评论中记录操作摘要
- 不跳过状态，严格按状态机顺序推进
- 子任务通过 `relation add` 与父需求关联
