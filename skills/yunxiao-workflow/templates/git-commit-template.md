# Git 代码提交与关联规范 (Git Commit Template)

在研发协作中，标准的 Git Commit Message 不仅能清晰反馈代码变更，还可以通过特征标识**自动关联并流转云效工作项（Workitem）**，实现研发数据的无缝串联。

## 1. Commit Message 格式规范

每次提交代码时，请严格遵守 Angular 规范格式：
```text
<type>(<scope>): <subject>

<body>

<footer>
```

### 必填字段说明
- **type (提交类型)**：
  - `feat`: 新增功能 (Feature)
  - `fix`: 修复 Bug
  - `docs`: 文档更改
  - `style`: 格式调整 (空格、格式化等，不影响代码逻辑)
  - `refactor`: 代码重构 (既不是新增功能也不是修复 bug)
  - `perf`: 性能优化
  - `test`: 测试用例增删改查
  - `chore`: 构建过程或辅助工具库更改
- **scope (影响范围)**：可选。用于说明本次提交的影响模块（如 api、router、components 等）。
- **subject (简短描述)**：不超过 50 个字符。动词开头，简要说明意图。

## 2. 自动关联工作项机制 (Smart Commit)

云效支持在提交时自动将 Commit 记录体现在所对应的工作项详情中。为实现该能力，请在 Commit Message 的 `subject` 或 `body` 任意一处附带上 **工作项ID标识**。

### 关联语法
> 格式：`#[工作项ID]` 或者带关键字语法（如 `fix #[工作项ID]`、`refs #[工作项ID]`）
- **仅关联记录**：在 Message 中带上 `#<ID>`。例如：`feat(user): 新增白名单接口 #1001`。推送到远端后，编号为 1001 的工作项下的“代码关联”里会自动展示此条 Commit。
- **关联并修改状态**：对于 Bug 修复，某些配置下可用关键字如 `fix #1002`，能使关联的这只缺陷在合入后自动流转状态。

### 实战示例
**单行简单提交 (推荐)**：
```bash
git commit -m "feat(api): 增加获取用户详细信息的统一接口 #28394"
```

**多行附带正文提交**：
```bash
git commit -m "fix(payment): 解决退款时偶发的空指针异常

这是因为退款金额字段上游未做保底校验导致的系统崩溃。

fixes #83910"
```
