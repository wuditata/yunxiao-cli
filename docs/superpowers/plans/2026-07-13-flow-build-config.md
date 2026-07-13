# Flow 打包配置实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Agent 从统一的项目配置中选择测试或生产环境的多个 Flow 打包项，并直接调用现有 `flow run create`。

**Architecture:** CLI 的 `ProjectContextConfig` 只负责读取和保留 `flow` 原始对象，现有 Flow API 与命令保持不变。仓库内 `yunxiao-workflow` Skill 负责项目级/全局配置查找、环境与目标选择、校验和多次命令调用。

**Tech Stack:** Python 3.11、`dataclasses`、`unittest`、Markdown

---

### Task 1: 项目上下文保留 Flow 配置

**Files:**
- Modify: `tests/test_context_command.py`
- Modify: `src/yunxiao_cli/domain/models.py`
- Modify: `src/yunxiao_cli/app/context_service.py`

- [ ] **Step 1: 写入失败测试**

在 `ProfileCommandTest` 中增加重新初始化项目上下文后仍保留 `flow` 的测试：

```python
def test_context_init_preserves_flow_config(self):
    flow = {
        "prod": {
            "backend": {
                "pipelineId": "2001",
                "params": {"envs": {"ENV": "prod"}},
            }
        }
    }
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir) / "apollo-repo"
        project_root.mkdir(parents=True, exist_ok=True)
        config_path = project_root / ".yunxiao.json"
        config_path.write_text(
            json.dumps(
                {
                    "profile": "old",
                    "assignee": "old-user",
                    "project": "123456",
                    "flow": flow,
                }
            ),
            encoding="utf-8",
        )
        current_dir = Path.cwd()
        try:
            os.chdir(project_root)
            result = run_cli_json(
                [
                    "context",
                    "init",
                    "--profile",
                    "apollo",
                    "--assignee",
                    "wyx",
                    "--project",
                    "123456",
                ]
            )
        finally:
            os.chdir(current_dir)
        config = json.loads(config_path.read_text(encoding="utf-8"))

    self.assertTrue(result["success"])
    self.assertEqual(flow, config["flow"])
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m unittest tests.test_context_command.ProfileCommandTest.test_context_init_preserves_flow_config`

Expected: FAIL，`config["flow"]` 不存在。

- [ ] **Step 3: 实现最小数据模型和写回保护**

在 `ProjectContextConfig` 中保存原始 Flow 对象：

```python
@dataclass(slots=True)
class ProjectContextConfig:
    profile: str
    assignee: str
    project: str
    token: str = ""
    flow: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = {
            "profile": self.profile,
            "assignee": self.assignee,
            "project": self.project,
        }
        if self.token:
            data["token"] = self.token
        if self.flow:
            data["flow"] = self.flow
        return data
```

`from_dict` 校验 `flow` 必须是对象，并传给构造函数：

```python
flow = data.get("flow") or {}
if not isinstance(flow, dict):
    raise ValueError("flow must be an object")

return cls(
    profile=profile,
    assignee=assignee,
    project=project,
    token=str(data.get("token") or "").strip(),
    flow=flow,
)
```

`ContextService.init_project_context` 只在目标文件已存在时读取旧配置并复用 `flow`：

```python
path = (cwd or Path.cwd()) / self.FILE_NAME
existing, _ = self.load_project_context(cwd=path.parent) if path.exists() else (None, None)
config = ProjectContextConfig(
    profile=profile.strip(),
    assignee=assignee.strip(),
    project=project.strip(),
    token=(token or "").strip(),
    flow=existing.flow if existing else {},
)
```

- [ ] **Step 4: 运行上下文测试**

Run: `python -m unittest tests.test_context_command`

Expected: PASS。

- [ ] **Step 5: 提交数据模型改动**

```powershell
git add -- tests/test_context_command.py src/yunxiao_cli/domain/models.py src/yunxiao_cli/app/context_service.py
git commit -m "feat: 保留 Flow 打包配置"
```

### Task 2: 发布统一配置语法和 Agent 执行规则

**Files:**
- Modify: `tests/test_install_docs.py`
- Modify: `.yunxiao.json.temple`
- Modify: `README.md`
- Modify: `skills/yunxiao-workflow/SKILL.md`

- [ ] **Step 1: 写入失败测试**

扩展安装文档测试，锁定模板和 Skill 的关键契约：

```python
def test_skill_doc_describes_configured_flow_builds(self):
    content = (ROOT / "skills" / "yunxiao-workflow" / "SKILL.md").read_text(encoding="utf-8")
    self.assertIn("~/.yunxiao/projects/<project-name>-<project-id>.json", content)
    self.assertIn("pipelineId", content)
    self.assertIn("打包生产环境", content)
    self.assertIn("yunxiao flow run create <pipeline_id> --params", content)

def test_template_contains_flow_build_config(self):
    content = (ROOT / ".yunxiao.json.temple").read_text(encoding="utf-8")
    self.assertIn('"flow"', content)
    self.assertIn('"test"', content)
    self.assertIn('"prod"', content)
    self.assertIn('"pipelineId"', content)
    self.assertIn('"params"', content)
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m unittest tests.test_install_docs.InstallDocsTest.test_skill_doc_describes_configured_flow_builds tests.test_install_docs.InstallDocsTest.test_template_contains_flow_build_config`

Expected: FAIL，模板和 Skill 尚未包含新配置契约。

- [ ] **Step 3: 更新配置模板**

将 `.yunxiao.json.temple` 扩展为同一份项目配置：

```json
{
  "profile": "<your_profile_name>",
  "assignee": "<your_assignee>",
  "project": "<your_project_id>",
  "flow": {
    "test": {
      "<target_name>": {
        "pipelineId": "<pipeline_id>",
        "params": {}
      }
    },
    "prod": {
      "<target_name>": {
        "pipelineId": "<pipeline_id>",
        "params": {}
      }
    }
  }
}
```

- [ ] **Step 4: 更新 README 和 Skill**

README 增加项目级/全局同构配置、文件名规则和现有命令调用说明。

在 Flow 章节加入以下内容，并引用模板中的完整 JSON：

````markdown
### 配置化打包

项目级配置使用 `.yunxiao.json.flow`。需要跨仓库复用时，将相同结构保存到
`~/.yunxiao/projects/<project-name>-<project-id>.json`；项目级 `flow` 优先，
不存在时才读取全局配置，两者不合并。

当 Agent 收到“打包生产环境”等指令时，会选择对应环境的打包项，并将每项的
`pipelineId`、`params` 直接传给现有命令：

```powershell
yunxiao flow run create <pipeline_id> --params '<params-json>' --profile <profile>
```
````

Skill 增加以下执行规则：

```text
1. 优先读取当前项目 `.yunxiao.json.flow`。
2. 缺少 `flow` 时，按项目 ID 唯一匹配 `~/.yunxiao/projects/*-<project-id>.json`。
3. “打包生产环境”选择 `prod` 全部目标；带目标名称时只选择对应项。
4. 启动前校验全部 `pipelineId` 非空、`params` 为对象。
5. 对每个目标调用 `yunxiao flow run create <pipeline_id> --params '<params-json>' --profile <profile>`。
6. 不自动重试；单项 API 失败时继续其余目标并汇总结果。
```

- [ ] **Step 5: 运行文档契约测试**

Run: `python -m unittest tests.test_install_docs`

Expected: PASS。

- [ ] **Step 6: 提交配置和 Skill 改动**

```powershell
git add -- tests/test_install_docs.py .yunxiao.json.temple README.md skills/yunxiao-workflow/SKILL.md
git commit -m "docs: 增加 Flow 自动打包配置"
```

### Task 3: 全量验证

**Files:**
- Verify only

- [ ] **Step 1: 运行完整测试集**

Run: `python -m unittest discover -s tests`

Expected: 全部 PASS。

- [ ] **Step 2: 检查工作区和提交**

Run: `git status --short`

Expected: 无未提交文件。

Run: `git log -4 --oneline`

Expected: 包含设计、计划、数据模型和配置 Skill 四个提交。
