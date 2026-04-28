import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yunxiao_cli",
        description="云效工作项协作 CLI，统一输出 JSON。",
    )
    subparsers = parser.add_subparsers(dest="command")

    login_parser = subparsers.add_parser("login", help="登录并保存账号")
    login_subparsers = login_parser.add_subparsers(dest="login_command")
    login_token_parser = login_subparsers.add_parser(
        "token",
        help="使用云效 token 登录",
        description="使用云效 token 登录并保存账号。",
    )
    login_token_parser.add_argument("token")
    login_token_parser.add_argument("--account", required=True, help="本地保存的账号名")

    profile_parser = subparsers.add_parser("profile", help="管理 profile")
    profile_subparsers = profile_parser.add_subparsers(dest="profile_command")
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
    context_subparsers = context_parser.add_subparsers(dest="context_command")
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
    meta_subparsers = meta_parser.add_subparsers(dest="meta_command")
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
    project_subparsers = project_parser.add_subparsers(dest="project_command")
    project_list_parser = project_subparsers.add_parser("list", help="列出项目", description="列出组织下可见项目。")
    project_list_parser.add_argument("--profile", help="profile 名称")
    project_list_parser.add_argument("--account", help="账号名")
    project_list_parser.add_argument("--org", help="组织 ID")
    project_get_parser = project_subparsers.add_parser("get", help="查看当前项目", description="查看当前 profile 绑定的项目信息。")
    project_get_parser.add_argument("--profile", help="profile 名称")

    workitem_parser = subparsers.add_parser("workitem", help="工作项相关操作")
    workitem_subparsers = workitem_parser.add_subparsers(dest="workitem_command")
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
    workitem_attachment_subparsers = workitem_attachment_parser.add_subparsers(dest="workitem_attachment_command")
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
    comment_subparsers = comment_parser.add_subparsers(dest="comment_command")
    comment_add_parser = comment_subparsers.add_parser("add", help="新增评论", description="给工作项新增评论。")
    comment_add_parser.add_argument("--profile", help="profile 名称")
    comment_add_parser.add_argument("--workitem", required=True, help="工作项 ID")
    comment_add_parser.add_argument("--content", required=True, help="评论内容")
    comment_list_parser = comment_subparsers.add_parser("list", help="列出评论", description="查看工作项评论列表。")
    comment_list_parser.add_argument("--profile", help="profile 名称")
    comment_list_parser.add_argument("--workitem", required=True, help="工作项 ID")

    relation_parser = subparsers.add_parser("relation", help="管理父子关系")
    relation_subparsers = relation_parser.add_subparsers(dest="relation_command")
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
    sprint_subparsers = sprint_parser.add_subparsers(dest="sprint_command")
    sprint_list_parser = sprint_subparsers.add_parser("list", help="列出迭代", description="列出项目下的迭代列表。")
    sprint_list_parser.add_argument("--profile", help="profile 名称")
    sprint_list_parser.add_argument("--project", help="项目 ID；不传时使用 profile 内全部项目")
    sprint_list_parser.add_argument("--status", help="迭代状态过滤，如 TODO、DOING、DONE")
    sprint_get_parser = sprint_subparsers.add_parser("get", help="查看迭代详情", description="查看指定迭代的详细信息。")
    sprint_get_parser.add_argument("sprint_id", help="迭代 ID")
    sprint_get_parser.add_argument("--profile", help="profile 名称")
    sprint_get_parser.add_argument("--project", required=True, help="项目 ID")

    version_parser = subparsers.add_parser("version", help="查看版本信息")
    version_subparsers = version_parser.add_subparsers(dest="version_command")
    version_list_parser = version_subparsers.add_parser("list", help="列出版本", description="列出项目下的版本列表。")
    version_list_parser.add_argument("--profile", help="profile 名称")
    version_list_parser.add_argument("--project", help="项目 ID；不传时使用 profile 内全部项目")
    version_list_parser.add_argument("--status", help="版本状态过滤，如 TODO、DOING、ARCHIVED")
    version_list_parser.add_argument("--name", help="按名称搜索版本")

    knowledge_parser = subparsers.add_parser("knowledge", help="知识库聚合查询")
    knowledge_subparsers = knowledge_parser.add_subparsers(dest="knowledge_command")
    knowledge_context_parser = knowledge_subparsers.add_parser(
        "context",
        help="聚合工作项上下文",
        description="聚合单个工作项的完整知识上下文：详情、评论、附件、父项链、子项树。",
    )
    knowledge_context_parser.add_argument("workitem_id", help="工作项 ID")
    knowledge_context_parser.add_argument("--profile", help="profile 名称")
    knowledge_context_parser.add_argument("--depth", type=int, default=1, help="子项递归深度，默认 1")
    knowledge_summary_parser = knowledge_subparsers.add_parser(
        "project-summary",
        help="项目知识概览",
        description="生成项目知识概览：活跃迭代、各分类工作项统计。",
    )
    knowledge_summary_parser.add_argument("--profile", help="profile 名称")
    knowledge_summary_parser.add_argument("--project", help="项目 ID；不传时使用 profile 内全部项目")
    knowledge_download_parser = knowledge_subparsers.add_parser(
        "download",
        help="下载知识库为 Markdown",
        description="根据工作区概览 URL 下载整个知识库，保持目录结构并导出为 Markdown。",
    )
    knowledge_download_parser.add_argument("--url", required=True, help="知识库工作区概览 URL")
    knowledge_download_parser.add_argument("--output", help="本地输出目录；不传时默认使用知识库名称")
    knowledge_download_parser.add_argument("--cookie", help="浏览器会话 Cookie 字符串，或导出的 Cookie JSON")
    knowledge_download_parser.add_argument("--cookie-file", help="Cookie 文件路径，支持浏览器导出的 JSON")
    knowledge_download_parser.add_argument(
        "--thread",
        dest="concurrency",
        metavar="THREAD",
        type=int,
        default=3,
        help="并发导出数，默认 3",
    )
    knowledge_download_parser.add_argument(
        "--browser",
        choices=["chrome", "edge", "brave", "firefox"],
        help="从本机浏览器导入 aliyun.com Cookie",
    )

    codeup_parser = subparsers.add_parser("codeup", help="代码管理操作")
    codeup_subparsers = codeup_parser.add_subparsers(dest="codeup_command")

    # repo
    codeup_repo_parser = codeup_subparsers.add_parser("repo", help="仓库操作")
    codeup_repo_subparsers = codeup_repo_parser.add_subparsers(dest="codeup_repo_command")
    codeup_repo_list = codeup_repo_subparsers.add_parser("list", help="列出仓库", description="列出组织下的代码仓库。")
    codeup_repo_list.add_argument("--profile", help="profile 名称")
    codeup_repo_list.add_argument("--search", help="按仓库名搜索")
    codeup_repo_get = codeup_repo_subparsers.add_parser("get", help="查看仓库详情", description="查看指定仓库的详细信息。")
    codeup_repo_get.add_argument("repo_id", help="仓库 ID 或 orgId/repoName 格式")
    codeup_repo_get.add_argument("--profile", help="profile 名称")

    # branch
    codeup_branch_parser = codeup_subparsers.add_parser("branch", help="分支操作")
    codeup_branch_subparsers = codeup_branch_parser.add_subparsers(dest="codeup_branch_command")
    codeup_branch_list = codeup_branch_subparsers.add_parser("list", help="列出分支", description="列出仓库下的分支。")
    codeup_branch_list.add_argument("repo_id", help="仓库 ID")
    codeup_branch_list.add_argument("--profile", help="profile 名称")
    codeup_branch_list.add_argument("--search", help="按分支名搜索")

    # file
    codeup_file_parser = codeup_subparsers.add_parser("file", help="文件操作")
    codeup_file_subparsers = codeup_file_parser.add_subparsers(dest="codeup_file_command")
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
    codeup_commit_subparsers = codeup_commit_parser.add_subparsers(dest="codeup_commit_command")
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
    codeup_mr_subparsers = codeup_mr_parser.add_subparsers(dest="codeup_mr_command")
    codeup_mr_list = codeup_mr_subparsers.add_parser("list", help="列出合并请求", description="列出合并请求，支持按状态和关键字过滤。")
    codeup_mr_list.add_argument("--profile", help="profile 名称")
    codeup_mr_list.add_argument("--repo", help="仓库 ID 过滤")
    codeup_mr_list.add_argument("--state", help="状态过滤：opened、merged、closed")
    codeup_mr_list.add_argument("--search", help="按标题关键字搜索")
    codeup_mr_get = codeup_mr_subparsers.add_parser("get", help="查看合并请求详情", description="查看指定合并请求的详细信息。")
    codeup_mr_get.add_argument("repo_id", help="仓库 ID")
    codeup_mr_get.add_argument("local_id", help="合并请求局部 ID")
    codeup_mr_get.add_argument("--profile", help="profile 名称")
    codeup_mr_comments = codeup_mr_subparsers.add_parser("comments", help="查看 MR 评论", description="查看合并请求的评论和代码审查意见。")
    codeup_mr_comments.add_argument("repo_id", help="仓库 ID")
    codeup_mr_comments.add_argument("local_id", help="合并请求局部 ID")
    codeup_mr_comments.add_argument("--profile", help="profile 名称")

    return parser
