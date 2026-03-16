# Standard Flow：标准研发流

多 agent 协作的产品类需求（默认需求）完整研发流程。创建需求时打标签 `standard-flow`，各 agent 按状态 + 标签过滤自己的任务。

## 状态机

```
待处理 → 待评审 → 设计中 → 设计完成 → 开发中 → 开发完成 → 测试中 → 已完成
                                                                    ↘ 已取消（异常终止）
```

## 各阶段职责

### 阶段 1：PM Agent — 需求创建（待处理）

**触发**：用户主动唤起 PM agent，口述需求。

**步骤**：

1. 与用户对话，整理需求，生成需求文档
2. 用户确认文档后，创建工作项：

```bash
yunxiao_cli workitem create --profile <profile> \
  --category Req \
  --subject "<需求标题>" \
  --desc-file ./req.md \
  --tag standard-flow
# 默认状态为：待处理
```

3. 在评论中指定评审 agent，并推进状态：

```bash
yunxiao_cli comment add --profile <profile> --workitem <id> \
  --content "@review-agent 请评审此需求"

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
2. 为每个设计产物创建子任务（UI 流程图、交互说明、接口草稿等）：

```bash
yunxiao_cli workitem create --profile <profile> \
  --category Task --subject "UI 流程设计 - <需求名>"
yunxiao_cli relation add --profile <profile> --parent <req_id> --child <task_id>
```

3. 设计完成后更新子任务状态，在父需求评论中汇总，推进需求状态：

```bash
yunxiao_cli comment add --profile <profile> --workitem <req_id> \
  --content "设计已完成，产物：<子任务列表>"
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
yunxiao_cli workitem transition <req_id> --profile <profile> --to "开发中"
```

2. 拆解开发子任务并关联：

```bash
yunxiao_cli workitem create --profile <profile> \
  --category Task --subject "<功能模块名>"
yunxiao_cli relation add --profile <profile> --parent <req_id> --child <task_id>
```

3. 所有开发子任务完成后，推进状态：

```bash
yunxiao_cli comment add --profile <profile> --workitem <req_id> \
  --content "开发已完成，PR：<链接>"
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
