# 命令速查

主 SKILL.md 覆盖四条日常路线；本文件是其余命令与参数的完整参考。所有命令支持 `--profile <name>`，repo 有 `.yunxiao.json` 时可省略。flag 细节以 `yunxiao <命令> --help` 为准。

## 搜索参数

`workitem search` 全部过滤条件（可组合）：

| 参数 | 说明 |
|------|------|
| `--category` | 分类：Req / Task / Bug，或 all |
| `--status` | 状态名称或状态 ID |
| `--keyword` | 全文搜索标题+描述 |
| `--tag` | 标签过滤，多个逗号分隔 |
| `--priority` | 优先级，如 P1、P2 |
| `--assigned-to` | 负责人 userId 或名称 |
| `--sprint` | 迭代 ID |
| `--created-after` / `--created-before` | 创建时间范围 `YYYY-MM-DD` |
| `--updated-after` / `--updated-before` | 更新时间范围 `YYYY-MM-DD` |
| `--project` | 项目 ID 过滤，多个逗号分隔 |
| `--sort` | 聚合排序，当前支持 `time` |
| `--raw` | 返回原始接口字段（仅排障用） |

## 元数据

```bash
yunxiao meta reload                      # 刷新类型/状态/字段/成员缓存
yunxiao meta types [--category Task]     # 工作项类型
yunxiao meta statuses --category Task    # 合法状态名（transition --to 用）
yunxiao meta fields --category Bug       # 字段 ID、名称、类型、可选值
yunxiao project list                     # 组织下可见项目
yunxiao project get                      # 当前 profile 绑定的项目
```

## 迭代与版本

```bash
yunxiao sprint list [--status DOING]                   # TODO / DOING / DONE
yunxiao sprint get <sprint_id> --project <project_id>
yunxiao version list [--status TODO] [--name "v2.0"]
```

| 场景 | 操作 |
|------|------|
| "当前迭代有哪些任务" | `sprint list --status DOING` → `workitem search --sprint <id>` |
| "v2.0 包含哪些需求" | `version list --name v2.0` |

## 知识聚合

```bash
yunxiao knowledge context <id或流水号> [--depth 3]
```

返回：`workitem`（详情）、`comments`、`attachments`、`parentChain`（到根的父链）、`childrenTree`（递归子树）。`--depth` 越大请求越多，≤3。

```bash
yunxiao knowledge project-summary [--project <project_id>]
```

返回：`activeSprints` + `categoryStats`（单页统计，`capped=true` 表示该分类至少 100 条）。

| 场景 | 操作 |
|------|------|
| "总结 #1234 的讨论" | `knowledge context 1234` → 读 `comments` |
| "这个需求拆了哪些任务" | `knowledge context 1234 --depth 2` → `childrenTree` |
| "这个 Bug 属于哪个大需求" | `knowledge context <id>` → `parentChain` |
| "项目目前什么状态" | `knowledge project-summary` |

## Thoughts 知识库导出

知识库文档不在 OpenAPI 覆盖范围，走浏览器 Cookie 导出为本地 Markdown 后直接读文件：

```bash
yunxiao thoughts download --url https://thoughts.aliyun.com/workspaces/<workspace_id>/overview --browser edge
```

`--cookie` / `--cookie-file` / `--browser`（chrome/edge/brave/firefox）三选一；可加 `--output <dir>`、`--thread <n>`。首次使用需 `playwright install chromium`。

## Flow 流水线

```bash
yunxiao flow pipeline list --search sfe          # 发现流水线 → id
yunxiao flow pipeline get <pipeline_id>          # 读代码源、配置详情
yunxiao flow run create <pipeline_id> --branch main
yunxiao flow run create <pipeline_id> --tag v1.0.0
yunxiao flow run create <pipeline_id> --env ENV=prod --param debug=true
yunxiao flow run create <pipeline_id> \
  --params '{"runningBranchs":{"https://codeup.aliyun.com/org/repo.git":"main"}}'
yunxiao flow job start <pipeline_id> <pipeline_run_id> <job_id>
```

- 只传 `--branch` / `--tag` 时 CLI 自动读取代码源生成 `runningBranchs` / `runningTags`
- 多仓库分支用 `--repo-branch <repo_url>=<branch>`
- `flow job start` 不接受请求体；需要运行参数时启动新 run

## Codeup 读操作

```bash
yunxiao codeup repo list [--search "frontend"]
yunxiao codeup repo get <repo_id>
yunxiao codeup branch list <repo_id> [--search "feature"]
yunxiao codeup file list <repo_id> [--path "src"] [--ref develop] [--recursive]
yunxiao codeup file get <repo_id> "README.md" [--ref develop]     # 内容为 base64
yunxiao codeup commit list <repo_id> [--ref develop] [--path "src/"] [--search "fix"] [--since "2026-04-01T00:00:00Z"]
yunxiao codeup commit get <repo_id> <sha>
yunxiao codeup compare <repo_id> --from master --to develop
yunxiao codeup mr get <repo_id> <local_id>
yunxiao codeup mr comments <repo_id> <local_id>
```

MR 创建/评论/合并/审核见 SKILL.md 路线 D。跨库合并才需要 `--source-project-id` / `--target-project-id`。

## 附件

```bash
yunxiao workitem create ... --attachment ./spec.md --attachment ./demo.png   # 可重复
yunxiao workitem attachment upload <id> --path ./hotfix.patch
yunxiao workitem attachment list <id>
yunxiao workitem attachment get <id> --file <file_id>       # 文件信息 + 下载地址
```
