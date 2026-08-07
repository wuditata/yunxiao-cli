import argparse
import textwrap


HELP_DETAILS = {
    "yunxiao": (
        "云效协作 CLI，统一输出 JSON。",
        """
        示例:
          yunxiao login token <token> --account <account>
          yunxiao profile add <name> --account <account> --org <org_id> --project <project_id>
          yunxiao context init --profile <name> --assignee <user> --project <project_id>
          yunxiao workitem mine --category all
          yunxiao codeup mr list --repo <repo_id>
          yunxiao flow run create <pipeline_id> --branch main
        """,
    ),
    "yunxiao login": (
        "登录并保存云效账号。登录信息会写入本地 CLI 数据目录，供 profile 复用。",
        """
        子命令:
          token    使用云效 token 登录

        示例:
          yunxiao login token <token> --account pm-a
        """,
    ),
    "yunxiao login token": (
        "使用云效 token 登录，并把账号、组织和项目可见性保存到本地。",
        """
        示例:
          yunxiao login token <token> --account pm-a

        输出:
          JSON，包含账号、组织、项目和告警信息。
        """,
    ),
    "yunxiao profile": (
        "管理本地 profile。profile 绑定账号、组织和一个或多个项目，是大多数业务命令的默认上下文。",
        """
        子命令:
          add     新增 profile 并刷新元数据缓存
          use     切换默认 profile
          list    列出已保存的 profile
          show    查看指定或默认 profile

        示例:
          yunxiao profile add pm-dev --account pm-a --org <org_id> --project <project_id>
          yunxiao profile use pm-dev
        """,
    ),
    "yunxiao profile add": (
        "新增 profile，并刷新当前项目类型、状态、字段、成员等元数据缓存。",
        """
        示例:
          yunxiao profile add pm-dev --account pm-a --org <org_id> --project <project_id>
          yunxiao profile add pm-dev --account pm-a --org <org_id> --project <project_id_1>,<project_id_2>
        """,
    ),
    "yunxiao profile use": (
        "设置默认 profile。后续命令未显式传 --profile 时会优先使用默认 profile。",
        """
        示例:
          yunxiao profile use pm-dev
        """,
    ),
    "yunxiao profile list": (
        "列出本机保存的所有 profile。",
        """
        示例:
          yunxiao profile list
        """,
    ),
    "yunxiao profile show": (
        "查看指定 profile；未传 --profile 时查看默认 profile。",
        """
        示例:
          yunxiao profile show
          yunxiao profile show --profile pm-dev
        """,
    ),
    "yunxiao context": (
        "管理当前项目目录下的 .yunxiao.json。该文件用于绑定 repo 级默认 profile、负责人和项目。",
        """
        子命令:
          init    初始化项目配置

        示例:
          yunxiao context init --profile pm-dev --assignee pm-a --project <project_id>
        """,
    ),
    "yunxiao context init": (
        "在当前目录写入 .yunxiao.json，供 CLI 和 yunxiao workflow skill 读取。",
        """
        示例:
          yunxiao context init --profile pm-dev --assignee pm-a --project <project_id>
          yunxiao context init --profile pm-dev --assignee pm-a --project <project_id> --token <token>
        """,
    ),
    "yunxiao meta": (
        "查看或刷新项目元数据，包括工作项类型、状态、字段和成员映射。",
        """
        子命令:
          reload      刷新元数据缓存
          types       查看工作项类型
          statuses    查看状态列表
          fields      查看字段列表

        示例:
          yunxiao meta reload --profile pm-dev
          yunxiao meta fields --category Task
        """,
    ),
    "yunxiao meta reload": (
        "刷新当前 profile 绑定项目的元数据缓存。",
        """
        示例:
          yunxiao meta reload
          yunxiao meta reload --profile pm-dev
        """,
    ),
    "yunxiao meta types": (
        "列出项目下可用的工作项类型，可按分类过滤。",
        """
        示例:
          yunxiao meta types
          yunxiao meta types --category Task
        """,
    ),
    "yunxiao meta statuses": (
        "列出某个工作项分类可用的状态。",
        """
        示例:
          yunxiao meta statuses --category Task
          yunxiao meta statuses --profile pm-dev --category Bug
        """,
    ),
    "yunxiao meta fields": (
        "列出某个工作项分类的字段定义，用于确认字段 ID、字段名和必填项。",
        """
        示例:
          yunxiao meta fields --category Req
          yunxiao meta fields --profile pm-dev --category Task
        """,
    ),
    "yunxiao project": (
        "查看云效项目信息。可列出组织下可见项目，或查看当前 profile 绑定的项目。",
        """
        子命令:
          list    列出项目
          get     查看当前项目

        示例:
          yunxiao project list --account pm-a --org <org_id>
          yunxiao project get --profile pm-dev
        """,
    ),
    "yunxiao project list": (
        "列出组织下当前账号可见的项目。",
        """
        示例:
          yunxiao project list --profile pm-dev
          yunxiao project list --account pm-a --org <org_id>
        """,
    ),
    "yunxiao project get": (
        "查看当前 profile 绑定的项目信息。",
        """
        示例:
          yunxiao project get
          yunxiao project get --profile pm-dev
        """,
    ),
    "yunxiao workitem": (
        "工作项主流程命令。覆盖创建、查看、搜索、更新、状态流转和附件管理。",
        """
        子命令:
          create        创建工作项
          get           查看工作项详情
          mine          查看当前负责人工作项
          search        多条件搜索工作项
          update        更新工作项
          transition    流转工作项状态
          attachment    管理工作项附件

        示例:
          yunxiao workitem create --category Req --subject "支持 CLI"
          yunxiao workitem mine --category all --sort time
          yunxiao workitem get <workitem_id> --with-parent
        """,
    ),
    "yunxiao workitem create": (
        "创建工作项。支持描述、父项、负责人、字段赋值和附件上传。",
        """
        示例:
          yunxiao workitem create --category Req --subject "支持 CLI"
          yunxiao workitem create --category Bug --subject "登录失败" --field "严重程度=3-一般"
          yunxiao workitem create --category Req --subject "附带材料" --attachment ./spec.md --attachment ./demo.png

        说明:
          --field 可重复传入 key=value；--field-json 适合一次传多个字段。
          --attachment 会在工作项创建成功后按顺序上传，任一失败即停止。
        """,
    ),
    "yunxiao workitem get": (
        "查看单个工作项详情。默认返回评论、附件和正文资源信息。",
        """
        示例:
          yunxiao workitem get <workitem_id>
          yunxiao workitem get <workitem_id> --with-parent
          yunxiao workitem get <workitem_id> --no-comments --no-attachments
        """,
    ),
    "yunxiao workitem mine": (
        "查看当前用户负责的工作项。默认返回摘要，适合人工筛选和 Agent 读取。",
        """
        示例:
          yunxiao workitem mine
          yunxiao workitem mine --category all
          yunxiao workitem mine --project <project_id_1>,<project_id_2> --sort time

        说明:
          多项目 profile 会跨项目聚合；传 --raw 可返回原始接口列表。
        """,
    ),
    "yunxiao workitem search": (
        "按分类、状态、关键字、标签、优先级、负责人、迭代和时间范围搜索工作项。",
        """
        示例:
          yunxiao workitem search --category Task --status "处理中"
          yunxiao workitem search --keyword "登录" --assigned-to "张三"
          yunxiao workitem search --project <project_id_1>,<project_id_2> --sort time

        说明:
          默认返回摘要和统计；需要接口原始字段时传 --raw。
        """,
    ),
    "yunxiao workitem update": (
        "更新工作项标题、描述、负责人、状态或字段。",
        """
        示例:
          yunxiao workitem update <workitem_id> --subject "新标题"
          yunxiao workitem update <workitem_id> --assigned-to "张三"
          yunxiao workitem update <workitem_id> --field-json '{"预计工时":1.5}'
        """,
    ),
    "yunxiao workitem transition": (
        "流转工作项到目标状态，并可一次传入流转所需字段。",
        """
        示例:
          yunxiao workitem transition <workitem_id> --to "处理中"
          yunxiao workitem transition <workitem_id> --to "处理中" --field-json '{"计划开始时间":"2026-03-17","预计工时":3.5}'
        """,
    ),
    "yunxiao workitem attachment": (
        "管理工作项附件。支持上传、列出和查看附件文件信息。",
        """
        子命令:
          upload    上传附件
          list      列出附件
          get       查看附件文件信息

        示例:
          yunxiao workitem attachment upload <workitem_id> --path ./spec.md
          yunxiao workitem attachment list <workitem_id>
          yunxiao workitem attachment get <workitem_id> --file <file_id>
        """,
    ),
    "yunxiao workitem attachment upload": (
        "上传单个本地文件到指定工作项。",
        """
        示例:
          yunxiao workitem attachment upload <workitem_id> --path ./spec.md
          yunxiao workitem attachment upload <workitem_id> --path ./spec.md --operator-id <user_id>
        """,
    ),
    "yunxiao workitem attachment list": (
        "列出指定工作项的附件列表。",
        """
        示例:
          yunxiao workitem attachment list <workitem_id>
          yunxiao workitem attachment list <workitem_id> --profile pm-dev
        """,
    ),
    "yunxiao workitem attachment get": (
        "查看指定附件的文件信息和下载地址。",
        """
        示例:
          yunxiao workitem attachment get <workitem_id> --file <file_id>
        """,
    ),
    "yunxiao comment": (
        "管理工作项评论。",
        """
        子命令:
          add     新增评论
          list    列出评论

        示例:
          yunxiao comment add --workitem <workitem_id> --content "@agent 请评审"
          yunxiao comment list --workitem <workitem_id>
        """,
    ),
    "yunxiao comment add": (
        "给指定工作项新增评论。",
        """
        示例:
          yunxiao comment add --workitem <workitem_id> --content "@agent 请评审"
        """,
    ),
    "yunxiao comment list": (
        "查看指定工作项的评论列表。",
        """
        示例:
          yunxiao comment list --workitem <workitem_id>
        """,
    ),
    "yunxiao relation": (
        "管理工作项父子关系。",
        """
        子命令:
          add         建立父子关系
          children    查看子项

        示例:
          yunxiao relation add --parent <parent_id> --child <child_id>
          yunxiao relation children --parent <parent_id>
        """,
    ),
    "yunxiao relation add": (
        "设置 parent -> child 父子关系。",
        """
        示例:
          yunxiao relation add --parent <parent_id> --child <child_id>
        """,
    ),
    "yunxiao relation children": (
        "查看指定父工作项的子项列表。",
        """
        示例:
          yunxiao relation children --parent <parent_id>
        """,
    ),
    "yunxiao sprint": (
        "查看迭代信息。",
        """
        子命令:
          list    列出迭代
          get     查看迭代详情

        示例:
          yunxiao sprint list --project <project_id>
          yunxiao sprint get <sprint_id> --project <project_id>
        """,
    ),
    "yunxiao sprint list": (
        "列出项目下的迭代列表，可按状态过滤。",
        """
        示例:
          yunxiao sprint list
          yunxiao sprint list --project <project_id> --status DOING
        """,
    ),
    "yunxiao sprint get": (
        "查看指定迭代详情。",
        """
        示例:
          yunxiao sprint get <sprint_id> --project <project_id>
        """,
    ),
    "yunxiao version": (
        "查看项目版本信息。",
        """
        子命令:
          list    列出版本

        示例:
          yunxiao version list --project <project_id>
        """,
    ),
    "yunxiao version list": (
        "列出项目下的版本列表，可按状态或名称过滤。",
        """
        示例:
          yunxiao version list
          yunxiao version list --project <project_id> --status TODO
          yunxiao version list --name "1.0"
        """,
    ),
    "yunxiao knowledge": (
        "聚合多个数据源，生成面向 AI 的知识上下文。",
        """
        子命令:
          context          聚合单个工作项的完整上下文
          project-summary  项目全局概览

        示例:
          yunxiao knowledge context 1001
          yunxiao knowledge context REQ-42 --depth 2
          yunxiao knowledge project-summary --project <project_id>
        """,
    ),
    "yunxiao knowledge context": (
        "聚合单个工作项的完整上下文：详情、评论、附件、父项链和递归子项树。支持工作项 ID 或流水号。",
        """
        示例:
          yunxiao knowledge context 1001
          yunxiao knowledge context REQ-42 --depth 3
        """,
    ),
    "yunxiao knowledge project-summary": (
        "生成项目全局概览：活跃迭代列表和各分类工作项统计。",
        """
        示例:
          yunxiao knowledge project-summary
          yunxiao knowledge project-summary --project <project_id>
        """,
    ),
    "yunxiao thoughts": (
        "云效 Thoughts 知识库文档操作。当前支持导出知识库为本地 Markdown。",
        """
        子命令:
          download    下载知识库为 Markdown

        示例:
          yunxiao thoughts download --url https://thoughts.aliyun.com/workspaces/<workspace_id>/overview --browser edge
        """,
    ),
    "yunxiao thoughts download": (
        "根据工作区概览 URL 下载整个 Thoughts 知识库，保持目录结构并导出为 Markdown。",
        """
        示例:
          yunxiao thoughts download --url https://thoughts.aliyun.com/workspaces/<workspace_id>/overview --cookie "<cookie>"
          yunxiao thoughts download --url https://thoughts.aliyun.com/workspaces/<workspace_id>/overview --browser edge --thread 3 --output ./thoughts-export

        说明:
          --cookie、--cookie-file、--browser 三选一。
        """,
    ),
    "yunxiao flow": (
        "Flow 流水线操作。覆盖流水线查询、运行启动和既有任务手动启动。",
        """
        子命令:
          pipeline    流水线查询
          run    流水线运行操作
          job    流水线任务操作

        示例:
          yunxiao flow pipeline list --search sfe
          yunxiao flow pipeline get <pipeline_id>
          yunxiao flow run create <pipeline_id> --branch main
          yunxiao flow job start <pipeline_id> <pipeline_run_id> <job_id>
        """,
    ),
    "yunxiao flow pipeline": (
        "Flow 流水线查询。用于发现可部署应用和读取流水线详情。",
        """
        子命令:
          list    列出流水线
          get     查看流水线详情

        示例:
          yunxiao flow pipeline list --search sfe --profile xinmai
          yunxiao flow pipeline get 4921657 --profile xinmai
        """,
    ),
    "yunxiao flow pipeline list": (
        "列出组织下可见 Flow 流水线，可按流水线名称关键字搜索。",
        """
        示例:
          yunxiao flow pipeline list --search sfe --profile xinmai
          yunxiao flow pipeline list --status SUCCESS,RUNNING --page 1 --per-page 20
        """,
    ),
    "yunxiao flow pipeline get": (
        "查看指定 Flow 流水线详情，包括代码源、配置和标签等接口返回内容。",
        """
        示例:
          yunxiao flow pipeline get 4921657 --profile xinmai
        """,
    ),
    "yunxiao flow run": (
        "流水线运行操作。当前支持创建一次新的流水线运行。",
        """
        子命令:
          create    创建流水线运行

        示例:
          yunxiao flow run create <pipeline_id> --branch main
          yunxiao flow run create <pipeline_id> --params '{"branchModeBranchs":["main"]}'
        """,
    ),
    "yunxiao flow run create": (
        "创建流水线运行。支持原始 params，也支持分支、标签、环境变量和制品等简化参数。",
        """
        示例:
          yunxiao flow run create <pipeline_id> --branch main
          yunxiao flow run create <pipeline_id> --env ENV=prod --param debug=true
          yunxiao flow run create <pipeline_id> --repo-branch https://codeup.aliyun.com/org/repo.git=release/1.0
          yunxiao flow run create <pipeline_id> --params '{"runningBranchs":{"https://codeup.aliyun.com/org/repo.git":"main"}}'

        说明:
          --params / --params-file 传原始 JSON 对象，并优先于所有简化参数。
          只传 --branch 或 --tag 时，会读取流水线代码源并生成 runningBranchs / runningTags。
        """,
    ),
    "yunxiao flow job": (
        "流水线任务操作。用于操作已存在运行实例里的任务。",
        """
        子命令:
          start    手动启动任务

        示例:
          yunxiao flow job start <pipeline_id> <pipeline_run_id> <job_id>
        """,
    ),
    "yunxiao flow job start": (
        "手动启动指定流水线运行实例中的任务。",
        """
        示例:
          yunxiao flow job start <pipeline_id> <pipeline_run_id> <job_id>

        说明:
          官方 job start 接口不接受请求体；需要运行参数时使用 flow run create 的 --params 或简化参数。
        """,
    ),
    "yunxiao codeup": (
        "Codeup 代码管理操作。覆盖仓库、分支、文件、提交、比较和合并请求。",
        """
        子命令:
          repo       仓库操作
          branch     分支操作
          file       文件操作
          commit     提交操作
          compare    代码比较
          mr         合并请求操作

        示例:
          yunxiao codeup repo list --search api
          yunxiao codeup file get <repo_id> README.md --ref master
          yunxiao codeup mr create <repo_id> --title "fix" --source feature/a --target master
        """,
    ),
    "yunxiao codeup repo": (
        "Codeup 仓库操作。",
        """
        子命令:
          list    列出仓库
          get     查看仓库详情

        示例:
          yunxiao codeup repo list --search api
          yunxiao codeup repo get <repo_id>
        """,
    ),
    "yunxiao codeup repo list": (
        "列出组织下的代码仓库，可按仓库名搜索。",
        """
        示例:
          yunxiao codeup repo list
          yunxiao codeup repo list --search api
        """,
    ),
    "yunxiao codeup repo get": (
        "查看指定 Codeup 仓库详情。",
        """
        示例:
          yunxiao codeup repo get <repo_id>
          yunxiao codeup repo get <org_id>/<repo_name>
        """,
    ),
    "yunxiao codeup branch": (
        "Codeup 分支操作。",
        """
        子命令:
          list    列出分支

        示例:
          yunxiao codeup branch list <repo_id> --search feature
        """,
    ),
    "yunxiao codeup branch list": (
        "列出仓库下的分支，可按分支名搜索。",
        """
        示例:
          yunxiao codeup branch list <repo_id>
          yunxiao codeup branch list <repo_id> --search feature
        """,
    ),
    "yunxiao codeup file": (
        "Codeup 文件操作。支持浏览文件树和读取文件内容。",
        """
        子命令:
          list    浏览文件树
          get     读取文件内容

        示例:
          yunxiao codeup file list <repo_id> --path src --ref master
          yunxiao codeup file get <repo_id> README.md --ref master
        """,
    ),
    "yunxiao codeup file list": (
        "列出仓库中的文件和目录。",
        """
        示例:
          yunxiao codeup file list <repo_id>
          yunxiao codeup file list <repo_id> --path src/main --ref master
          yunxiao codeup file list <repo_id> --recursive
        """,
    ),
    "yunxiao codeup file get": (
        "读取仓库中指定文件的内容。",
        """
        示例:
          yunxiao codeup file get <repo_id> README.md
          yunxiao codeup file get <repo_id> src/main/App.java --ref feature/a
        """,
    ),
    "yunxiao codeup commit": (
        "Codeup 提交操作。支持列出提交历史和查看提交详情。",
        """
        子命令:
          list    列出提交历史
          get     查看提交详情

        示例:
          yunxiao codeup commit list <repo_id> --ref master
          yunxiao codeup commit get <repo_id> <sha>
        """,
    ),
    "yunxiao codeup commit list": (
        "列出仓库提交历史，可按分支、路径、关键字和时间范围过滤。",
        """
        示例:
          yunxiao codeup commit list <repo_id>
          yunxiao codeup commit list <repo_id> --ref master --path src
          yunxiao codeup commit list <repo_id> --since 2026-03-01T00:00:00Z --until 2026-03-31T23:59:59Z
        """,
    ),
    "yunxiao codeup commit get": (
        "查看指定提交的详细信息。",
        """
        示例:
          yunxiao codeup commit get <repo_id> <sha>
        """,
    ),
    "yunxiao codeup compare": (
        "比较两个分支、标签或提交之间的差异。",
        """
        示例:
          yunxiao codeup compare <repo_id> --from master --to feature/a
          yunxiao codeup compare <repo_id> --from <base_sha> --to <head_sha>
        """,
    ),
    "yunxiao codeup mr": (
        "Codeup 合并请求操作。支持查询、创建、评论、合并和生成本地审核上下文。",
        """
        子命令:
          list        列出合并请求
          get         查看合并请求详情
          create      创建合并请求
          comments    查看 MR 评论
          comment     发表 MR 评论（全局/行内/回复）
          merge       合并 MR
          review      获取本地 agent 审核上下文

        示例:
          yunxiao codeup mr list --repo <repo_id> --state opened
          yunxiao codeup mr get <repo_id> <local_id>
          yunxiao codeup mr review <repo_id> <local_id>
          yunxiao codeup mr comment <repo_id> <local_id> --content "LGTM"
        """,
    ),
    "yunxiao codeup mr list": (
        "列出 Codeup 合并请求，支持按仓库、状态和标题关键字过滤。",
        """
        示例:
          yunxiao codeup mr list
          yunxiao codeup mr list --repo <repo_id> --state opened
          yunxiao codeup mr list --search "登录"
        """,
    ),
    "yunxiao codeup mr get": (
        "查看指定合并请求的详细信息。",
        """
        示例:
          yunxiao codeup mr get <repo_id> <local_id>
        """,
    ),
    "yunxiao codeup mr create": (
        "创建 Codeup 合并请求，并可关联评审人、工作项和 AI 评审。",
        """
        示例:
          yunxiao codeup mr create <repo_id> --title "修复登录" --source feature/login --target master
          yunxiao codeup mr create <repo_id> --title "修复登录" --source feature/login --target master --reviewer <user_id> --workitem <workitem_id>

        说明:
          --reviewer 和 --workitem 可重复，也可传逗号分隔值。
        """,
    ),
    "yunxiao codeup mr comments": (
        "查看合并请求评论和代码审查意见。",
        """
        示例:
          yunxiao codeup mr comments <repo_id> <local_id>
        """,
    ),
    "yunxiao codeup mr comment": (
        "给合并请求发表评论。默认全局评论；传 --file/--line 发行内评论；传 --reply 回复已有评论。版本 ID 自动解析。",
        """
        示例:
          yunxiao codeup mr comment <repo_id> <local_id> --content "整体 LGTM，两处小问题见行内评论"
          yunxiao codeup mr comment <repo_id> <local_id> --content-file ./review.md
          yunxiao codeup mr comment <repo_id> <local_id> --file src/main.py --line 42 --content "这里会空指针"
          yunxiao codeup mr comment <repo_id> <local_id> --reply <comment_biz_id> --content "已修复" --resolved
        """,
    ),
    "yunxiao codeup mr merge": (
        "通过 Codeup OpenAPI 合并合并请求。",
        """
        示例:
          yunxiao codeup mr merge <repo_id> <local_id>
          yunxiao codeup mr merge <repo_id> <local_id> --message "merge feature/login" --remove-source-branch
        """,
    ),
    "yunxiao codeup mr review": (
        "获取合并请求详情、版本、评论和代码差异，用于本地 Agent 审核。",
        """
        示例:
          yunxiao codeup mr review <repo_id> <local_id>
        """,
    ),
}


class YunxiaoHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=32, width=100)

    def _format_action(self, action):
        if isinstance(action, argparse._SubParsersAction):
            return "".join(self._format_action(subaction) for subaction in action._get_subactions())
        if type(action).__name__ == "_ChoicesPseudoAction":
            invocation = self._format_action_invocation(action)
            help_text = self._expand_help(action) if action.help else ""
            return f"{' ' * self._current_indent}{invocation:<16} {help_text}\n"
        return super()._format_action(action)


class YunxiaoArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter_class", YunxiaoHelpFormatter)
        super().__init__(*args, **kwargs)
        self._positionals.title = "参数"
        self._optionals.title = "选项"
        self.set_defaults(_help_parser=self)
        for action in self._actions:
            if isinstance(action, argparse._HelpAction):
                action.help = "显示帮助并退出"


def _configure_parser_tree(parser: argparse.ArgumentParser) -> None:
    child_parsers = []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            child_parsers.extend(action.choices.values())

    parser.formatter_class = YunxiaoHelpFormatter
    details = HELP_DETAILS.get(parser.prog)
    if details:
        parser.description = details[0]
        parser.epilog = _format_epilog(details[1], has_subcommands=bool(child_parsers))

    if child_parsers:
        parser.usage = f"{parser.prog} [options] <command> [args]"
    parser.set_defaults(_help_parser=parser, _runs_command=not child_parsers)
    for child in child_parsers:
        _configure_parser_tree(child)


def _format_epilog(epilog: str, *, has_subcommands: bool) -> str:
    text = textwrap.dedent(epilog).strip()
    if not has_subcommands or "子命令:" not in text:
        return text
    before_examples, separator, examples = text.partition("示例:")
    if not separator:
        return text
    prefix = before_examples.split("子命令:", 1)[0].strip()
    example_text = f"示例:{examples}".strip()
    return "\n\n".join(part for part in (prefix, example_text) if part)


def _add_subparsers(parser: argparse.ArgumentParser, *, dest: str):
    return parser.add_subparsers(dest=dest, title="命令", metavar="<command>")


def _add_thoughts_download_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--url", required=True, help="知识库工作区概览 URL")
    parser.add_argument("--output", help="本地输出目录；不传时默认使用知识库名称")
    parser.add_argument("--cookie", help="浏览器会话 Cookie 字符串，或导出的 Cookie JSON")
    parser.add_argument("--cookie-file", help="Cookie 文件路径，支持浏览器导出的 JSON")
    parser.add_argument(
        "--thread",
        dest="concurrency",
        metavar="THREAD",
        type=int,
        default=3,
        help="并发导出数，默认 3",
    )
    parser.add_argument(
        "--browser",
        choices=["chrome", "edge", "brave", "firefox"],
        help="从本机浏览器导入 aliyun.com Cookie",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = YunxiaoArgumentParser(
        prog="yunxiao",
        description=HELP_DETAILS["yunxiao"][0],
    )
    subparsers = _add_subparsers(parser, dest="command")

    login_parser = subparsers.add_parser("login", help="登录并保存账号")
    login_subparsers = _add_subparsers(login_parser, dest="login_command")
    login_token_parser = login_subparsers.add_parser(
        "token",
        help="使用云效 token 登录",
        description="使用云效 token 登录并保存账号。",
    )
    login_token_parser.add_argument("token", help="云效个人 token")
    login_token_parser.add_argument("--account", required=True, help="本地保存的账号名")

    profile_parser = subparsers.add_parser("profile", help="管理 profile")
    profile_subparsers = _add_subparsers(profile_parser, dest="profile_command")
    profile_add_parser = profile_subparsers.add_parser("add", help="新增 profile", description="新增 profile 并刷新元数据缓存。")
    profile_add_parser.add_argument("name", help="profile 名称")
    profile_add_parser.add_argument("--account", required=True, help="账号名")
    profile_add_parser.add_argument("--org", required=True, help="组织 ID")
    profile_add_parser.add_argument("--project", required=True, help="项目 ID，多个用逗号分隔")
    profile_use_parser = profile_subparsers.add_parser("use", help="切换默认 profile", description="设置默认 profile。")
    profile_use_parser.add_argument("name", help="profile 名称")
    profile_subparsers.add_parser("list", help="列出 profile", description="列出已保存的 profile。")
    profile_show_parser = profile_subparsers.add_parser("show", help="查看 profile", description="查看指定或默认 profile。")
    profile_show_parser.add_argument("--profile", help="profile 名称，缺省时使用默认 profile")

    context_parser = subparsers.add_parser("context", help="管理项目级云效上下文")
    context_subparsers = _add_subparsers(context_parser, dest="context_command")
    context_init_parser = context_subparsers.add_parser(
        "init",
        help="初始化项目配置",
        description="在当前目录写入 .yunxiao.json。",
    )
    context_init_parser.add_argument("--profile", required=True, help="profile 名称")
    context_init_parser.add_argument("--assignee", required=True, help="项目默认负责人")
    context_init_parser.add_argument("--project", required=True, help="项目 ID")
    context_init_parser.add_argument("--token", help="可选 token；存在时执行命令前会刷新登录态")

    meta_parser = subparsers.add_parser("meta", help="查看项目元数据")
    meta_subparsers = _add_subparsers(meta_parser, dest="meta_command")
    meta_reload_parser = meta_subparsers.add_parser("reload", help="刷新元数据缓存", description="刷新类型、状态、字段、成员等缓存。")
    meta_reload_parser.add_argument("--profile", help="profile 名称")
    meta_types_parser = meta_subparsers.add_parser("types", help="查看工作项类型", description="查看项目下可用的工作项类型。")
    meta_types_parser.add_argument("--profile", help="profile 名称")
    meta_types_parser.add_argument("--category", help="按分类过滤，如 Req、Task、Bug")
    meta_statuses_parser = meta_subparsers.add_parser(
        "statuses",
        help="查看状态列表",
        description="查看某个工作项分类的可用状态。",
    )
    meta_statuses_parser.add_argument("--profile", help="profile 名称")
    meta_statuses_parser.add_argument("--category", required=True, help="工作项分类，如 Req、Task、Bug")
    meta_fields_parser = meta_subparsers.add_parser(
        "fields",
        help="查看字段列表",
        description="查看某个工作项分类的字段定义。",
    )
    meta_fields_parser.add_argument("--profile", help="profile 名称")
    meta_fields_parser.add_argument("--category", required=True, help="工作项分类，如 Req、Task、Bug")

    project_parser = subparsers.add_parser("project", help="查看项目信息")
    project_subparsers = _add_subparsers(project_parser, dest="project_command")
    project_list_parser = project_subparsers.add_parser("list", help="列出项目", description="列出组织下可见项目。")
    project_list_parser.add_argument("--profile", help="profile 名称")
    project_list_parser.add_argument("--account", help="账号名")
    project_list_parser.add_argument("--org", help="组织 ID")
    project_get_parser = project_subparsers.add_parser("get", help="查看当前项目", description="查看当前 profile 绑定的项目信息。")
    project_get_parser.add_argument("--profile", help="profile 名称")

    workitem_parser = subparsers.add_parser("workitem", help="工作项相关操作")
    workitem_subparsers = _add_subparsers(workitem_parser, dest="workitem_command")
    workitem_create_parser = workitem_subparsers.add_parser(
        "create",
        help="创建工作项",
        description="创建工作项；如果传入 --attachment，会在工单创建成功后顺序上传附件，失败即停止。",
    )
    workitem_create_parser.add_argument("--profile", help="profile 名称")
    workitem_create_parser.add_argument("--category", required=True, help="工作项分类，如 Req、Task、Bug")
    workitem_create_parser.add_argument("--type", help="工作项类型 ID 或名称；缺省时按分类取默认类型")
    workitem_create_parser.add_argument("--subject", required=True, help="工作项标题")
    workitem_create_parser.add_argument("--desc", help="工作项描述，支持 Markdown")
    workitem_create_parser.add_argument("--desc-file", help="从文件读取工作项描述，推荐多行 Markdown 使用")
    workitem_create_parser.add_argument("--parent", help="父工作项 ID 或流水号")
    workitem_create_parser.add_argument("--assigned-to", help="负责人 userId、成员名或昵称")
    workitem_create_parser.add_argument(
        "--attachment",
        action="append",
        help="附件文件路径，可重复传入多个；创建成功后按顺序上传，失败即停止",
    )
    workitem_create_parser.add_argument("--field", action="append", help='字段赋值，可重复，如 "严重程度=3-一般"')
    workitem_create_parser.add_argument(
        "--field-json",
        action="append",
        help='字段 JSON，可重复，如 \'{"严重程度":"3-一般"}\'',
    )

    workitem_get_parser = workitem_subparsers.add_parser("get", help="查看工作项", description="查看工作项详情。")
    workitem_get_parser.add_argument("workitem_id", help="工作项 ID")
    workitem_get_parser.add_argument("--profile", help="profile 名称")
    workitem_get_parser.add_argument("--no-comments", action="store_true", help="不返回评论")
    workitem_get_parser.add_argument("--with-parent", action="store_true", help="同时返回父工作项")
    workitem_get_parser.add_argument("--no-attachments", action="store_true", help="不返回附件和正文图片")

    workitem_mine_parser = workitem_subparsers.add_parser("mine", help="查看我的工作项", description="查看当前用户负责的工作项。")
    workitem_mine_parser.add_argument("--profile", help="profile 名称")
    workitem_mine_parser.add_argument("--category", help='工作项分类；传 "all" 时搜索全部分类')
    workitem_mine_parser.add_argument("--project", help="项目 ID 过滤，多个用逗号分隔；不传时使用 profile 内全部项目")
    workitem_mine_parser.add_argument("--sort", help="聚合排序方式，当前支持 time")
    workitem_mine_parser.add_argument("--raw", action="store_true", help="返回原始工作项列表；默认返回摘要")

    workitem_search_parser = workitem_subparsers.add_parser("search", help="搜索工作项", description="按多种条件搜索工作项。")
    workitem_search_parser.add_argument("--profile", help="profile 名称")
    workitem_search_parser.add_argument("--category", help="工作项分类")
    workitem_search_parser.add_argument("--status", help="状态名称或状态 ID")
    workitem_search_parser.add_argument("--keyword", help="全文搜索关键字，搜索标题和描述")
    workitem_search_parser.add_argument("--tag", help="标签过滤，多个用逗号分隔")
    workitem_search_parser.add_argument("--priority", help="优先级过滤，如 P1,P2")
    workitem_search_parser.add_argument("--assigned-to", help="负责人 userId、成员名或昵称")
    workitem_search_parser.add_argument("--sprint", help="迭代 ID 过滤")
    workitem_search_parser.add_argument("--created-after", help="创建时间起始，格式 YYYY-MM-DD")
    workitem_search_parser.add_argument("--created-before", help="创建时间截止，格式 YYYY-MM-DD")
    workitem_search_parser.add_argument("--updated-after", help="更新时间起始，格式 YYYY-MM-DD")
    workitem_search_parser.add_argument("--updated-before", help="更新时间截止，格式 YYYY-MM-DD")
    workitem_search_parser.add_argument("--project", help="项目 ID 过滤，多个用逗号分隔；不传时使用 profile 内全部项目")
    workitem_search_parser.add_argument("--sort", help="聚合排序方式，当前支持 time")
    workitem_search_parser.add_argument("--raw", action="store_true", help="返回原始工作项列表；默认返回摘要")

    workitem_update_parser = workitem_subparsers.add_parser("update", help="更新工作项", description="更新标题、描述、负责人、状态或字段。")
    workitem_update_parser.add_argument("workitem_id", help="工作项 ID")
    workitem_update_parser.add_argument("--profile", help="profile 名称")
    workitem_update_parser.add_argument("--subject", help="新标题")
    workitem_update_parser.add_argument("--desc", help="新描述，支持 Markdown")
    workitem_update_parser.add_argument("--desc-file", help="从文件读取新描述")
    workitem_update_parser.add_argument("--assigned-to", help="负责人 userId、成员名或昵称")
    workitem_update_parser.add_argument("--status", help="目标状态名称或状态 ID")
    workitem_update_parser.add_argument("--field", action="append", help='字段赋值，可重复，如 "计划完成时间=2026-03-31"')
    workitem_update_parser.add_argument(
        "--field-json",
        action="append",
        help='字段 JSON，可重复，如 \'{"预计工时":1.5}\'',
    )

    workitem_transition_parser = workitem_subparsers.add_parser(
        "transition",
        help="流转工作项状态",
        description="流转工作项到目标状态，并支持一次传入必填字段。",
    )
    workitem_transition_parser.add_argument("workitem_id", help="工作项 ID")
    workitem_transition_parser.add_argument("--profile", help="profile 名称")
    workitem_transition_parser.add_argument("--to", required=True, help="目标状态名称或状态 ID")
    workitem_transition_parser.add_argument("--field", action="append", help='字段赋值，可重复，如 "计划开始时间=2026-03-17"')
    workitem_transition_parser.add_argument(
        "--field-json",
        action="append",
        help='字段 JSON，可重复，如 \'{"计划完成时间":"2026-03-20"}\'',
    )

    workitem_attachment_parser = workitem_subparsers.add_parser(
        "attachment",
        help="管理工作项附件",
        description="上传、列出或查看工作项附件。",
    )
    workitem_attachment_subparsers = _add_subparsers(workitem_attachment_parser, dest="workitem_attachment_command")
    workitem_attachment_upload_parser = workitem_attachment_subparsers.add_parser(
        "upload",
        help="上传附件",
        description="上传单个文件到指定工作项。",
    )
    workitem_attachment_upload_parser.add_argument("workitem_id", help="工作项 ID")
    workitem_attachment_upload_parser.add_argument("--profile", help="profile 名称")
    workitem_attachment_upload_parser.add_argument("--path", required=True, help="本地文件路径")
    workitem_attachment_upload_parser.add_argument("--operator-id", help="操作者 userId，个人 token 时通常可省略")
    workitem_attachment_list_parser = workitem_attachment_subparsers.add_parser(
        "list",
        help="列出附件",
        description="列出工作项附件列表。",
    )
    workitem_attachment_list_parser.add_argument("workitem_id", help="工作项 ID")
    workitem_attachment_list_parser.add_argument("--profile", help="profile 名称")
    workitem_attachment_get_parser = workitem_attachment_subparsers.add_parser(
        "get",
        help="查看附件文件信息",
        description="查看工作项附件文件信息和下载地址。",
    )
    workitem_attachment_get_parser.add_argument("workitem_id", help="工作项 ID")
    workitem_attachment_get_parser.add_argument("--profile", help="profile 名称")
    workitem_attachment_get_parser.add_argument("--file", required=True, help="文件 ID")

    comment_parser = subparsers.add_parser("comment", help="管理评论")
    comment_subparsers = _add_subparsers(comment_parser, dest="comment_command")
    comment_add_parser = comment_subparsers.add_parser("add", help="新增评论", description="给工作项新增评论。")
    comment_add_parser.add_argument("--profile", help="profile 名称")
    comment_add_parser.add_argument("--workitem", required=True, help="工作项 ID")
    comment_add_parser.add_argument("--content", required=True, help="评论内容")
    comment_list_parser = comment_subparsers.add_parser("list", help="列出评论", description="查看工作项评论列表。")
    comment_list_parser.add_argument("--profile", help="profile 名称")
    comment_list_parser.add_argument("--workitem", required=True, help="工作项 ID")

    relation_parser = subparsers.add_parser("relation", help="管理父子关系")
    relation_subparsers = _add_subparsers(relation_parser, dest="relation_command")
    relation_add_parser = relation_subparsers.add_parser("add", help="建立父子关系", description="设置 parent -> child 关系。")
    relation_add_parser.add_argument("--profile", help="profile 名称")
    relation_add_parser.add_argument("--parent", required=True, help="父工作项 ID")
    relation_add_parser.add_argument("--child", required=True, help="子工作项 ID")
    relation_children_parser = relation_subparsers.add_parser(
        "children",
        help="查看子项",
        description="查看指定父工作项的子项列表。",
    )
    relation_children_parser.add_argument("--profile", help="profile 名称")
    relation_children_parser.add_argument("--parent", required=True, help="父工作项 ID")

    sprint_parser = subparsers.add_parser("sprint", help="查看迭代信息")
    sprint_subparsers = _add_subparsers(sprint_parser, dest="sprint_command")
    sprint_list_parser = sprint_subparsers.add_parser("list", help="列出迭代", description="列出项目下的迭代列表。")
    sprint_list_parser.add_argument("--profile", help="profile 名称")
    sprint_list_parser.add_argument("--project", help="项目 ID；不传时使用 profile 内全部项目")
    sprint_list_parser.add_argument("--status", help="迭代状态过滤，如 TODO、DOING、DONE")
    sprint_get_parser = sprint_subparsers.add_parser("get", help="查看迭代详情", description="查看指定迭代的详细信息。")
    sprint_get_parser.add_argument("sprint_id", help="迭代 ID")
    sprint_get_parser.add_argument("--profile", help="profile 名称")
    sprint_get_parser.add_argument("--project", required=True, help="项目 ID")

    version_parser = subparsers.add_parser("version", help="查看版本信息")
    version_subparsers = _add_subparsers(version_parser, dest="version_command")
    version_list_parser = version_subparsers.add_parser("list", help="列出版本", description="列出项目下的版本列表。")
    version_list_parser.add_argument("--profile", help="profile 名称")
    version_list_parser.add_argument("--project", help="项目 ID；不传时使用 profile 内全部项目")
    version_list_parser.add_argument("--status", help="版本状态过滤，如 TODO、DOING、ARCHIVED")
    version_list_parser.add_argument("--name", help="按名称搜索版本")

    knowledge_parser = subparsers.add_parser("knowledge", help="聚合工作项知识上下文")
    knowledge_subparsers = _add_subparsers(knowledge_parser, dest="knowledge_command")
    knowledge_context_parser = knowledge_subparsers.add_parser(
        "context",
        help="聚合单个工作项的完整上下文",
        description="聚合工作项详情、评论、附件、父项链和递归子项树。",
    )
    knowledge_context_parser.add_argument("workitem_id", help="工作项 ID 或流水号（如 REQ-42）")
    knowledge_context_parser.add_argument("--profile", help="profile 名称")
    knowledge_context_parser.add_argument("--depth", type=int, default=1, help="子项树递归深度，默认 1")
    knowledge_summary_parser = knowledge_subparsers.add_parser(
        "project-summary",
        help="项目全局概览",
        description="生成项目知识概览，包含活跃迭代和各分类工作项统计。",
    )
    knowledge_summary_parser.add_argument("--profile", help="profile 名称")
    knowledge_summary_parser.add_argument("--project", help="项目 ID；不传时使用 profile 内全部项目")

    thoughts_parser = subparsers.add_parser("thoughts", help="云效 Thoughts 知识库文档操作")
    thoughts_subparsers = _add_subparsers(thoughts_parser, dest="thoughts_command")
    thoughts_download_parser = thoughts_subparsers.add_parser(
        "download",
        help="下载知识库为 Markdown",
        description="根据工作区概览 URL 下载整个 Thoughts 知识库，保持目录结构并导出为 Markdown。",
    )
    _add_thoughts_download_arguments(thoughts_download_parser)

    flow_parser = subparsers.add_parser("flow", help="Flow 流水线操作")
    flow_subparsers = _add_subparsers(flow_parser, dest="flow_command")

    flow_pipeline_parser = flow_subparsers.add_parser("pipeline", help="流水线查询")
    flow_pipeline_subparsers = _add_subparsers(flow_pipeline_parser, dest="flow_pipeline_command")
    flow_pipeline_list = flow_pipeline_subparsers.add_parser(
        "list",
        help="列出流水线",
        description="列出组织下可见 Flow 流水线。",
    )
    flow_pipeline_list.add_argument("--profile", help="profile 名称")
    flow_pipeline_list.add_argument("--search", help="按流水线名称关键字搜索")
    flow_pipeline_list.add_argument("--status", help="状态列表，多个用逗号分隔")
    flow_pipeline_list.add_argument("--page", type=int, default=1, help="页码，默认 1")
    flow_pipeline_list.add_argument("--per-page", type=int, default=20, help="每页数量，默认 20")
    flow_pipeline_get = flow_pipeline_subparsers.add_parser(
        "get",
        help="查看流水线详情",
        description="查看指定 Flow 流水线详情。",
    )
    flow_pipeline_get.add_argument("pipeline_id", help="流水线 ID")
    flow_pipeline_get.add_argument("--profile", help="profile 名称")

    flow_run_parser = flow_subparsers.add_parser("run", help="流水线运行操作")
    flow_run_subparsers = _add_subparsers(flow_run_parser, dest="flow_run_command")
    flow_run_create = flow_run_subparsers.add_parser(
        "create",
        help="创建流水线运行",
        description="创建流水线运行，支持运行参数。",
    )
    flow_run_create.add_argument("pipeline_id", help="流水线 ID")
    flow_run_create.add_argument("--profile", help="profile 名称")
    flow_run_create.add_argument("--params", help="原始运行参数 JSON 对象字符串，优先于所有简化参数")
    flow_run_create.add_argument("--params-file", help="从文件读取原始运行参数 JSON 对象")
    flow_run_create.add_argument(
        "--param",
        action="append",
        help="运行参数 key=value，可重复；value 会按 JSON 解析，解析失败按字符串处理",
    )
    flow_run_create.add_argument("--branch", help="使用指定分支运行流水线")
    flow_run_create.add_argument("--tag", help="使用指定标签运行流水线")
    flow_run_create.add_argument("--branches", action="append", help="分支模式分支，可重复或用逗号分隔")
    flow_run_create.add_argument("--branch-mode", action="store_true", help="启用分支模式；未传 --branches 时会使用 --branch")
    flow_run_create.add_argument("--repo", dest="repositories", action="append", help="仓库 URL，可重复或用逗号分隔")
    flow_run_create.add_argument("--repo-branch", action="append", help="指定仓库分支，格式 <repo_url>=<branch>")
    flow_run_create.add_argument("--repo-tag", action="append", help="指定仓库标签，格式 <repo_url>=<tag>")
    flow_run_create.add_argument("--env", action="append", help="环境变量，格式 KEY=VALUE，可重复")
    flow_run_create.add_argument("--pipeline-artifact", action="append", help="流水线制品，格式 KEY=VALUE，可重复")
    flow_run_create.add_argument("--acr-artifact", action="append", help="ACR 制品，格式 KEY=VALUE，可重复")
    flow_run_create.add_argument("--package-artifact", action="append", help="Packages 制品，格式 KEY=VALUE，可重复")
    flow_run_create.add_argument("--release-branch", help="Release 分支名")
    flow_run_create.add_argument("--create-release-branch", action="store_true", help="运行时创建 Release 分支")
    flow_run_create.add_argument("--comment", help="本次运行备注")

    flow_job_parser = flow_subparsers.add_parser("job", help="流水线任务操作")
    flow_job_subparsers = _add_subparsers(flow_job_parser, dest="flow_job_command")
    flow_job_start = flow_job_subparsers.add_parser(
        "start",
        help="手动启动任务",
        description="手动启动指定流水线运行实例中的任务。",
    )
    flow_job_start.add_argument("pipeline_id", help="流水线 ID")
    flow_job_start.add_argument("pipeline_run_id", help="流水线运行实例 ID")
    flow_job_start.add_argument("job_id", help="流水线运行任务 ID")
    flow_job_start.add_argument("--profile", help="profile 名称")

    codeup_parser = subparsers.add_parser("codeup", help="代码管理操作")
    codeup_subparsers = _add_subparsers(codeup_parser, dest="codeup_command")

    # repo
    codeup_repo_parser = codeup_subparsers.add_parser("repo", help="仓库操作")
    codeup_repo_subparsers = _add_subparsers(codeup_repo_parser, dest="codeup_repo_command")
    codeup_repo_list = codeup_repo_subparsers.add_parser("list", help="列出仓库", description="列出组织下的代码仓库。")
    codeup_repo_list.add_argument("--profile", help="profile 名称")
    codeup_repo_list.add_argument("--search", help="按仓库名搜索")
    codeup_repo_get = codeup_repo_subparsers.add_parser("get", help="查看仓库详情", description="查看指定仓库的详细信息。")
    codeup_repo_get.add_argument("repo_id", help="仓库 ID 或 orgId/repoName 格式")
    codeup_repo_get.add_argument("--profile", help="profile 名称")

    # branch
    codeup_branch_parser = codeup_subparsers.add_parser("branch", help="分支操作")
    codeup_branch_subparsers = _add_subparsers(codeup_branch_parser, dest="codeup_branch_command")
    codeup_branch_list = codeup_branch_subparsers.add_parser("list", help="列出分支", description="列出仓库下的分支。")
    codeup_branch_list.add_argument("repo_id", help="仓库 ID")
    codeup_branch_list.add_argument("--profile", help="profile 名称")
    codeup_branch_list.add_argument("--search", help="按分支名搜索")

    # file
    codeup_file_parser = codeup_subparsers.add_parser("file", help="文件操作")
    codeup_file_subparsers = _add_subparsers(codeup_file_parser, dest="codeup_file_command")
    codeup_file_list = codeup_file_subparsers.add_parser("list", help="浏览文件树", description="列出仓库中的文件和目录。")
    codeup_file_list.add_argument("repo_id", help="仓库 ID")
    codeup_file_list.add_argument("--profile", help="profile 名称")
    codeup_file_list.add_argument("--path", help="目录路径，如 src/main")
    codeup_file_list.add_argument("--ref", help="分支或标签名，默认为默认分支")
    codeup_file_list.add_argument("--recursive", action="store_true", help="递归列出所有文件")
    codeup_file_get = codeup_file_subparsers.add_parser("get", help="读取文件内容", description="读取仓库中指定文件的内容。")
    codeup_file_get.add_argument("repo_id", help="仓库 ID")
    codeup_file_get.add_argument("file_path", help="文件路径，如 src/main/App.java")
    codeup_file_get.add_argument("--profile", help="profile 名称")
    codeup_file_get.add_argument("--ref", default="master", help="分支或标签名，默认 master")

    # commit
    codeup_commit_parser = codeup_subparsers.add_parser("commit", help="提交操作")
    codeup_commit_subparsers = _add_subparsers(codeup_commit_parser, dest="codeup_commit_command")
    codeup_commit_list = codeup_commit_subparsers.add_parser("list", help="列出提交历史", description="列出仓库的提交历史。")
    codeup_commit_list.add_argument("repo_id", help="仓库 ID")
    codeup_commit_list.add_argument("--profile", help="profile 名称")
    codeup_commit_list.add_argument("--ref", default="master", help="分支名，默认 master")
    codeup_commit_list.add_argument("--path", help="按文件路径过滤")
    codeup_commit_list.add_argument("--search", help="按关键字搜索提交信息")
    codeup_commit_list.add_argument("--since", help="起始时间，格式 YYYY-MM-DDTHH:MM:SSZ")
    codeup_commit_list.add_argument("--until", help="截止时间，格式 YYYY-MM-DDTHH:MM:SSZ")
    codeup_commit_get = codeup_commit_subparsers.add_parser("get", help="查看提交详情", description="查看指定提交的详细信息。")
    codeup_commit_get.add_argument("repo_id", help="仓库 ID")
    codeup_commit_get.add_argument("sha", help="提交 SHA 值")
    codeup_commit_get.add_argument("--profile", help="profile 名称")

    # compare
    codeup_compare = codeup_subparsers.add_parser("compare", help="代码比较", description="比较两个分支/标签/提交之间的差异。")
    codeup_compare.add_argument("repo_id", help="仓库 ID")
    codeup_compare.add_argument("--profile", help="profile 名称")
    codeup_compare.add_argument("--from", dest="from_ref", required=True, help="比较起点（分支/标签/SHA）")
    codeup_compare.add_argument("--to", dest="to_ref", required=True, help="比较终点（分支/标签/SHA）")

    # mr (change request)
    codeup_mr_parser = codeup_subparsers.add_parser("mr", help="合并请求操作")
    codeup_mr_subparsers = _add_subparsers(codeup_mr_parser, dest="codeup_mr_command")
    codeup_mr_list = codeup_mr_subparsers.add_parser("list", help="列出合并请求", description="列出合并请求，支持按状态和关键字过滤。")
    codeup_mr_list.add_argument("--profile", help="profile 名称")
    codeup_mr_list.add_argument("--repo", help="仓库 ID 过滤")
    codeup_mr_list.add_argument("--state", help="状态过滤：opened、merged、closed")
    codeup_mr_list.add_argument("--search", help="按标题关键字搜索")
    codeup_mr_get = codeup_mr_subparsers.add_parser("get", help="查看合并请求详情", description="查看指定合并请求的详细信息。")
    codeup_mr_get.add_argument("repo_id", help="仓库 ID")
    codeup_mr_get.add_argument("local_id", help="合并请求局部 ID")
    codeup_mr_get.add_argument("--profile", help="profile 名称")
    codeup_mr_create = codeup_mr_subparsers.add_parser("create", help="创建合并请求", description="创建 Codeup 合并请求。")
    codeup_mr_create.add_argument("repo_id", help="仓库 ID 或 orgId/repoName 格式")
    codeup_mr_create.add_argument("--profile", help="profile 名称")
    codeup_mr_create.add_argument("--title", required=True, help="合并请求标题")
    codeup_mr_create.add_argument("--source", required=True, help="源分支")
    codeup_mr_create.add_argument("--target", required=True, help="目标分支")
    codeup_mr_create.add_argument("--desc", help="合并请求描述")
    codeup_mr_create.add_argument("--desc-file", help="从文件读取合并请求描述")
    codeup_mr_create.add_argument("--source-project-id", help="源仓库数字 ID；不传时按仓库 ID 推断")
    codeup_mr_create.add_argument("--target-project-id", help="目标仓库数字 ID；不传时按仓库 ID 推断")
    codeup_mr_create.add_argument("--reviewer", action="append", help="评审人 userId，可重复或用逗号分隔")
    codeup_mr_create.add_argument("--workitem", action="append", help="关联工作项 ID，可重复或用逗号分隔")
    codeup_mr_create.add_argument(
        "--create-from",
        choices=["WEB"],
        default="WEB",
        help="创建来源，当前仅支持 WEB",
    )
    codeup_mr_create.add_argument("--ai-review", action="store_true", help="触发 AI 评审")
    codeup_mr_comments = codeup_mr_subparsers.add_parser("comments", help="查看 MR 评论", description="查看合并请求的评论和代码审查意见。")
    codeup_mr_comments.add_argument("repo_id", help="仓库 ID")
    codeup_mr_comments.add_argument("local_id", help="合并请求局部 ID")
    codeup_mr_comments.add_argument("--profile", help="profile 名称")
    codeup_mr_merge = codeup_mr_subparsers.add_parser("merge", help="合并 MR", description="通过 Codeup OpenAPI 合并合并请求。")
    codeup_mr_merge.add_argument("repo_id", help="仓库 ID")
    codeup_mr_merge.add_argument("local_id", help="合并请求局部 ID")
    codeup_mr_merge.add_argument("--profile", help="profile 名称")
    codeup_mr_merge.add_argument("--merge-type", default="no-fast-forward", help="合并方式，默认 no-fast-forward")
    codeup_mr_merge.add_argument("--message", dest="merge_message", help="合并提交信息")
    codeup_mr_merge.add_argument("--remove-source-branch", action="store_true", help="合并后删除源分支")
    codeup_mr_comment = codeup_mr_subparsers.add_parser(
        "comment",
        help="发表 MR 评论",
        description="给合并请求发表全局评论或行内评论；版本 ID 默认自动解析，无需手动传。",
    )
    codeup_mr_comment.add_argument("repo_id", help="仓库 ID")
    codeup_mr_comment.add_argument("local_id", help="合并请求局部 ID")
    codeup_mr_comment.add_argument("--profile", help="profile 名称")
    codeup_mr_comment.add_argument("--content", help="评论内容，支持 Markdown")
    codeup_mr_comment.add_argument("--content-file", help="从文件读取评论内容，推荐多行 Markdown 使用")
    codeup_mr_comment.add_argument("--file", dest="file_path", help="行内评论的文件路径，如 src/main.py")
    codeup_mr_comment.add_argument("--line", dest="line_number", type=int, help="行内评论的行号")
    codeup_mr_comment.add_argument("--reply", dest="reply_to", help="要回复的评论 ID（parent_comment_biz_id）")
    codeup_mr_comment.add_argument("--resolved", action="store_true", help="同时标记为已解决")
    codeup_mr_comment.add_argument("--from-patchset", help="比较起始版本 ID；默认自动取合并目标版本")
    codeup_mr_comment.add_argument("--to-patchset", help="比较目标版本 ID；默认自动取最新合并源版本")
    codeup_mr_review_context = codeup_mr_subparsers.add_parser(
        "review",
        help="获取本地 agent 审核上下文",
        description="获取合并请求详情、版本、评论和代码差异，用于本地 agent 审核。",
    )
    codeup_mr_review_context.add_argument("repo_id", help="仓库 ID")
    codeup_mr_review_context.add_argument("local_id", help="合并请求局部 ID")
    codeup_mr_review_context.add_argument("--profile", help="profile 名称")

    _configure_parser_tree(parser)
    return parser
