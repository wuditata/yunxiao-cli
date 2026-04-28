# Yunxiao CLI

面向云效工作项协作的统一命令行，适合开发者、自动化脚本和 Agent Workflow。

它解决的不是“能不能调接口”，而是“能不能稳定地在多项目、多账号、多命令场景下把工作项协作跑顺”。

## 亮点

- 支持多 profile：同一台机器可同时管理多个账号、组织、项目上下文
- 覆盖工作项主流程：创建、查询、搜索、更新、状态流转、评论、父子关联
- 支持附件处理：可先对已有工单上传附件，也可在 `create` 时一并处理
- 字段输入友好：支持字段名或字段 ID，适合人手执行和自动化脚本
- 输出统一为 JSON：天然适合 shell、CI、Agent、编辑器插件集成
- 自带 Skill 集成：可和仓库内 `skills/yunxiao-workflow` 配套使用
- `workitem search` / `workitem mine` 默认返回摘要，`workitem get` 返回详情

## 30 秒了解它能做什么

```bash
# 多 profile 切换
yunxiao_cli profile add pm-dev --account pm-a --org <org_id> --project <project_id>
yunxiao_cli profile use pm-dev

# 创建工作项并附带多个附件
yunxiao_cli workitem create --category Req --subject "支持 CLI" \
  --attachment ./spec.md --attachment ./demo.png

# 给已有工单补传附件
yunxiao_cli workitem attachment upload 1001 --path ./hotfix.patch

# 状态流转时一次补齐必填字段
yunxiao_cli workitem transition 1001 --to "处理中" \
  --field-json '{"计划开始时间":"2026-03-17","计划完成时间":"2026-03-20","预计工时":3.5}'
```

## 安装

安装 CLI：

```bash
./install.sh
```

安装 Skill（分发到 ~/.agents/skills 及各编辑器）：

```bash
./install_skill.sh install
```

Windows:

```bat
install.bat
install_skill.bat
```

只安装 Python 包也可以：

```bash
pip install -e .
```

安装后可直接使用：

```bash
yunxiao_cli --help
```

## 首次使用

项目根目录下的 `.yunxiao.json` 用于保存 repo 级默认上下文，CLI 和 `skills/yunxiao-workflow` 都会读取它。

首次接入时，推荐直接生成最小配置：

```bash
yunxiao_cli context init --profile <profile> --assignee <assignee> --project <project_id>
```

也可以基于模板创建：

```bash
cp .yunxiao.json.temple .yunxiao.json
```

Windows PowerShell：

```powershell
Copy-Item .yunxiao.json.temple .yunxiao.json
```

模板字段说明：

- `profile`：CLI profile 名称
- `assignee`：当前项目默认负责人
- `project`：当前 repo 绑定的默认项目 ID
- `token`：可选；存在时 CLI 执行命令前会先刷新本地登录态

初始化 profile：

```bash
yunxiao_cli login token <token> --account <assignee>
yunxiao_cli profile add <profile> --account <assignee> --org <org_id> --project <project_id>
yunxiao_cli profile use <profile>
```

多项目场景可直接传逗号分隔：

```bash
yunxiao_cli profile add <profile> --account <assignee> --org <org_id> --project <project_id_1>,<project_id_2>
```

如果项目里已经有 `.yunxiao.json`，后续常用命令可直接省略 `--profile`；创建和更新工单时也会优先使用其中的 `assignee`。

## 项目结构

```text
yunxiao-cli/
├── skills/
│   ├── SKILLS.md
│   └── yunxiao-workflow/SKILL.md
├── src/yunxiao_cli/
├── tests/
├── install.sh
├── install.bat
├── .yunxiao.json.temple
└── pyproject.toml
```

## 基本用法

登录并保存账号：

```bash
yunxiao_cli login token <token> --account pm-a
```

登录结果会返回当前可见的组织和项目，之后添加 profile 并切换默认：

```bash
yunxiao_cli profile add pm-dev --account pm-a --org <org_id> --project <project_id>
yunxiao_cli profile use pm-dev
```

多项目 profile：

```bash
yunxiao_cli profile add pm-dev --account pm-a --org <org_id> --project <project_id_1>,<project_id_2>
```

为当前 repo 绑定默认上下文：

```bash
yunxiao_cli context init --profile pm-dev --assignee pm-a --project <project_id>
```

查看元数据：

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

工作项操作：

```bash
yunxiao_cli workitem create --profile pm-dev --category Req --subject "支持 CLI"
yunxiao_cli workitem create --profile pm-dev --category Bug --subject "登录失败" --field "严重程度=3-一般"
yunxiao_cli workitem create --profile pm-dev --category Req --subject "附带材料" --attachment ./spec.md --attachment ./demo.png
yunxiao_cli workitem get 1001 --profile pm-dev --with-parent
yunxiao_cli workitem mine --profile pm-dev --category all
yunxiao_cli workitem mine --profile pm-dev --project 456,457 --sort time
yunxiao_cli workitem search --profile pm-dev --category Task --status "处理中"
yunxiao_cli workitem search --profile pm-dev --project 456,457 --category Task --status "处理中" --sort time
yunxiao_cli workitem search --profile pm-dev --category Task --status "处理中" --raw
yunxiao_cli workitem update 1001 --profile pm-dev --assigned-to "张三"
yunxiao_cli workitem transition 1001 --profile pm-dev --to "已完成"
# 状态流转有必填字段时，可在 transition 一次传入
yunxiao_cli workitem transition 1001 --profile pm-dev --to "处理中" --field-json '{"79":"2026-03-17","80":"2026-03-20","101586":3.5}'
```

创建工作项常用参数：

- `--category`：工作项分类，如 `Req`、`Task`、`Bug`
- `--project`：项目 ID 过滤，多个用逗号分隔；不传时优先使用 `.yunxiao.json.project`，否则使用当前 profile 的全部项目
- `--sort`：聚合排序方式，当前支持 `time`
- `--type`：工作项类型 ID 或名称；不传时按分类取默认类型
- `--subject`：工作项标题
- `--desc`：直接传入描述内容，适合短文本
- `--desc-file`：从文件读取描述，推荐多行 Markdown 使用
- `--parent`：父工作项 ID 或流水号
- `--assigned-to`：负责人，可传 userId、成员名或昵称
- `--attachment`：附件文件路径，可重复传多个；工单创建成功后按顺序上传，失败即停止
- `--field`：字段赋值，可重复传，如 `--field "严重程度=3-一般"`
- `--field-json`：一次传完整字段集，推荐，如 `--field-json '{"严重程度":"3-一般"}'`

已执行 `yunxiao_cli profile use <name>` 或当前目录存在 `.yunxiao.json` 后，命令可省略 `--profile`。

`workitem mine` 与 `workitem search` 在多项目 profile 下会对每个项目拉取全部分页数据后再统一排序；如果当前 repo 存在 `.yunxiao.json.project`，默认只查询该项目。

查询返回约定：

- `workitem search` / `workitem mine` 默认返回摘要列表和聚合统计，适合人和 Agent 先做筛选
- 摘要字段固定为：`id`、`serial`、`subject`、`category`、`type`、`projectId`、`project`、`statusId`、`status`、`statusPhase`、`assigneeId`、`assignee`、`parentId`、`updatedAt`
- 如需原始接口字段，显式传 `--raw`
- 如需正文、评论、附件、父项等明细，调用 `workitem get <id>`

## 创建/更新/流转必填字段

当创建、更新或流转校验必填字段（如：严重程度、计划开始时间、计划完成时间、预计工时）时，可通过 `--field` 或 `--field-json` 一次传入。

```bash
# 创建 Bug 时传严重程度
yunxiao_cli workitem create --category Bug --subject "登录失败" \
  --field-json '{"严重程度":"3-一般"}'

# 用字段 ID（推荐）
yunxiao_cli workitem transition 1001 --to "处理中" \
  --field-json '{"79":"2026-03-17","80":"2026-03-20","101586":3.5}'

# 或用字段名（会自动映射到字段 ID）
yunxiao_cli workitem transition 1001 --to "处理中" \
  --field-json '{"计划开始时间":"2026-03-17","计划完成时间":"2026-03-20","预计工时":3.5}'
```

多行 Markdown 描述（尤其包含代码块）建议使用 `--desc-file`，避免 shell 展开导致内容被污染。

评论与父子关系：

```bash
yunxiao_cli comment add --profile pm-dev --workitem 1001 --content "@agent 请评审"
yunxiao_cli comment list --profile pm-dev --workitem 1001
yunxiao_cli relation add --profile pm-dev --parent 1001 --child 2001
yunxiao_cli relation children --profile pm-dev --parent 1001
```

工作项附件：

```bash
yunxiao_cli workitem attachment upload 1001 --profile pm-dev --path ./spec.md
yunxiao_cli workitem attachment list 1001 --profile pm-dev
yunxiao_cli workitem attachment get 1001 --profile pm-dev --file file-1
```

附件命令参数：

- `workitem attachment upload <workitem_id> --path <file>`：上传单个附件到指定工作项
- `workitem attachment list <workitem_id>`：列出工作项附件
- `workitem attachment get <workitem_id> --file <file_id>`：查看附件文件信息和下载地址

`workitem create --attachment` 的执行顺序：

1. 先创建工单
2. 再按传入顺序逐个上传附件
3. 任一附件上传失败，立即停止并返回失败

失败时会在错误返回里附带：

- 已创建的 `workitem`
- 已成功上传的 `uploaded_attachments`
- 当前失败的 `failed_attachment`

## 知识库下载

知识库下载走云效 Thoughts 的浏览器态能力，不依赖 OpenAPI token，而是依赖浏览器 Cookie。

首次使用前请先安装 Playwright 浏览器：

```bash
playwright install chromium
```

支持两种认证方式：

- 直接传 `--cookie`
- 传 `--cookie-file` 读取浏览器导出的 Cookie JSON
- 从本机浏览器导入 `--browser`，当前支持 `chrome`、`edge`、`brave`、`firefox`
- 支持 `--thread` 控制并发导出数，默认 `3`

示例：

```bash
# 直接传 Cookie
yunxiao_cli knowledge download \
  --url https://thoughts.aliyun.com/workspaces/<workspace_id>/overview \
  --cookie "<your_cookie>"

# 传浏览器导出的 Cookie JSON 文件
yunxiao_cli knowledge download \
  --url https://thoughts.aliyun.com/workspaces/<workspace_id>/overview \
  --cookie-file ./edge-cookies.json

# 从 Edge 导入 Cookie
yunxiao_cli knowledge download \
  --url https://thoughts.aliyun.com/workspaces/<workspace_id>/overview \
  --browser edge \
  --thread 3 \
  --output ./thoughts-export
```

下载结果会保持知识库目录结构，并导出为 Markdown。

## 开发验证

```bash
python -m unittest discover tests -v
python -m py_compile $(find src -name '*.py' -type f)
PYTHONPATH=src python -m yunxiao_cli.main --help
```
