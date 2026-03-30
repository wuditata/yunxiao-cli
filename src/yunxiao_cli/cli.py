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

    workitem_search_parser = workitem_subparsers.add_parser("search", help="搜索工作项", description="按分类和状态搜索工作项。")
    workitem_search_parser.add_argument("--profile", help="profile 名称")
    workitem_search_parser.add_argument("--category", help="工作项分类")
    workitem_search_parser.add_argument("--status", help="状态名称或状态 ID")
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

    return parser
