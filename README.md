# Yunxiao CLI

面向云效工作项协作的统一命令行。

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
yunxiao_cli workitem get 1001 --profile pm-dev --with-parent
yunxiao_cli workitem mine --profile pm-dev --category all
yunxiao_cli workitem search --profile pm-dev --category Task --status "处理中"
yunxiao_cli workitem update 1001 --profile pm-dev --assigned-to "张三"
yunxiao_cli workitem transition 1001 --profile pm-dev --to "已完成"
# 状态流转有必填字段时，可在 transition 一次传入
yunxiao_cli workitem transition 1001 --profile pm-dev --to "处理中" --field-json '{"79":"2026-03-17","80":"2026-03-20","101586":3.5}'
```

已执行 `yunxiao_cli profile use <name>` 后，命令可省略 `--profile`。

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

## 开发验证

```bash
python -m unittest discover tests -v
python -m py_compile $(find src -name '*.py' -type f)
PYTHONPATH=src python -m yunxiao_cli.main --help
```
