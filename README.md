# Yunxiao CLI

面向云效工作项协作的统一命令行。

## 安装

```bash
./install.sh
```

Windows:

```bat
install.bat
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
yunxiao_cli workitem get 1001 --profile pm-dev --with-parent
yunxiao_cli workitem mine --profile pm-dev --category all
yunxiao_cli workitem search --profile pm-dev --category Task --status "处理中"
yunxiao_cli workitem update 1001 --profile pm-dev --assigned-to "张三"
yunxiao_cli workitem transition 1001 --profile pm-dev --to "已完成"
```

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
