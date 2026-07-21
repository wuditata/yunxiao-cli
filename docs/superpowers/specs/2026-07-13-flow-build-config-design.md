# Flow 打包配置设计

## 目标

让 Agent 从项目级或全局项目配置中解析测试、生产环境的多个 Flow 打包项，并复用现有 `yunxiao flow run create` 命令启动流水线。

不新增面向用户的打包命令，不引入模板、继承或流水线名称查询。

## 配置模型

项目级配置位于仓库的 `.yunxiao.json`。全局配置位于：

```text
~/.yunxiao/projects/<project-name>-<project-id>.json
```

两处使用完全相同的结构：

```json
{
  "profile": "default",
  "assignee": "user",
  "project": "456",
  "flow": {
    "test": {
      "backend": {
        "pipelineId": "1001",
        "params": {
          "envs": {
            "ENV": "test"
          }
        }
      }
    },
    "prod": {
      "backend": {
        "pipelineId": "2001",
        "params": {
          "envs": {
            "ENV": "prod"
          }
        }
      },
      "frontend": {
        "pipelineId": "2002",
        "params": {}
      }
    }
  }
}
```

- `flow` 的第一层键是环境名，首期约定 `test`、`prod`。
- 第二层键是供自然语言选择的打包项目名，例如 `backend`、`frontend`、`miniapp`。
- `pipelineId` 是流水线的唯一执行标识。
- `params` 是云效 Flow 官方运行参数对象，原样序列化后传入现有命令。

`ProjectContextConfig` 保留 `flow` 原始对象，确保读取或重新生成项目上下文时不会丢失配置。

## 配置解析

1. 按现有规则向上查找当前仓库的 `.yunxiao.json`。
2. 当前配置包含 `flow` 时直接使用。
3. 当前配置不包含 `flow` 时，根据已解析的项目 ID 查找 `~/.yunxiao/projects/*-<project-id>.json`。
4. 全局配置必须唯一匹配；不存在或匹配多个文件均明确报错。
5. 项目级与全局配置不做合并，避免配置来源不透明。

文件名中的项目名只提供可读性，末尾项目 ID 是匹配依据。

以上查找和选择逻辑由 `yunxiao-workflow` Skill 指导 Agent 执行，不增加 CLI 配置解析命令。

## Agent 执行规则

- “打包生产环境”选择 `prod` 下全部打包项目。
- “打包生产环境后端”只选择 `prod.backend`。
- “打包测试环境”按相同规则选择 `test`。
- 环境或项目不存在时停止执行并报告合法选项，不做模糊猜测。

启动前一次性校验全部选中项：`pipelineId` 必须非空，`params` 必须是 JSON 对象。任一配置无效时不启动任何流水线。

每个选中项目直接调用：

```powershell
yunxiao flow run create <pipelineId> --params <params-json>
```

多个项目逐个提交。单项失败不阻断其余项目，最终汇总每个项目的 `pipelineRunId` 或错误信息。打包层不自动重试，避免重复创建流水线运行。

## 改动范围

- 扩展项目上下文数据模型，使其读取并保留 `flow`。
- 更新 `.yunxiao.json.temple` 和 README 配置说明。
- 更新 `yunxiao-workflow` Skill，增加自然语言选择、配置查找和现有 Flow 命令调用规则。
- 不修改 Flow OpenAPI 和 `flow run create` 的参数协议。

## 验证

- 项目上下文读取和写回时保留 `flow`。
- 通过 Skill 工作流验证项目级配置优先于全局配置。
- 通过 Skill 工作流验证全环境打包、单项目打包和参数透传。
- 缺少环境、缺少项目、无效参数和全局配置冲突时不启动流水线。
- 单项目 API 执行失败时继续其余有效项目并返回汇总结果。
