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

项目根目录下的 `.yunxiao.json` 主要给 `skills/yunxiao-workflow` 读取项目默认配置。

首次接入时，可直接基于模板创建：

```bash
cp .yunxiao.json.temple .yunxiao.json
```

Windows PowerShell：

```powershell
Copy-Item .yunxiao.json.temple .yunxiao.json
```

模板字段说明：

- `token`：云效登录 token
- `profile`：CLI profile 名称
- `project`：支持三种写法：单项目 ID、逗号分隔字符串、项目 ID 数组
- `assignee`：当前用户在云效中的标识

创建后按实际值替换占位符，再执行：

```bash
yunxiao_cli login token <token> --account <assignee>
yunxiao_cli profile add <profile> --account <assignee> --org <org_id> --project <project_id>
yunxiao_cli profile use <profile>
```

多项目场景可直接传逗号分隔：

```bash
yunxiao_cli profile add <profile> --account <assignee> --org <org_id> --project <project_id_1>,<project_id_2>
```

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
yunxiao_cli workitem update 1001 --profile pm-dev --assigned-to "张三"
yunxiao_cli workitem transition 1001 --profile pm-dev --to "已完成"
# 状态流转有必填字段时，可在 transition 一次传入
yunxiao_cli workitem transition 1001 --profile pm-dev --to "处理中" --field-json '{"79":"2026-03-17","80":"2026-03-20","101586":3.5}'
```

创建工作项常用参数：

- `--category`：工作项分类，如 `Req`、`Task`、`Bug`
- `--project`：项目 ID 过滤，多个用逗号分隔；不传时使用当前 profile 的全部项目
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

已执行 `yunxiao_cli profile use <name>` 后，命令可省略 `--profile`。

`workitem mine` 与 `workitem search` 在多项目 profile 下会对每个项目拉取全部分页数据后再统一排序。

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

## 开发验证

```bash
python -m unittest discover tests -v
python -m py_compile $(find src -name '*.py' -type f)
PYTHONPATH=src python -m yunxiao_cli.main --help
```
