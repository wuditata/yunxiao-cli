from __future__ import annotations

import json
from collections.abc import Sequence

from .app.auth_service import AuthService
from .app.comment_service import CommentService
from .app.errors import CliError
from .app.meta_service import MetaService
from .app.profile_service import ProfileService
from .app.project_service import ProjectService
from .app.relation_service import RelationService
from .app.workitem_service import WorkitemService
from .cli import build_parser
from .domain.store import Store
from .infra.base import YunxiaoAPIError
from .infra.config import CliConfig


def _services() -> tuple[Store, ProfileService, MetaService, ProjectService, WorkitemService, CommentService, RelationService]:
    store = Store(root=CliConfig.data_root())
    meta_service = MetaService(store=store)
    profile_service = ProfileService(store=store, meta_service=meta_service)
    project_service = ProjectService(store=store, profile_service=profile_service)
    workitem_service = WorkitemService(store=store, profile_service=profile_service, meta_service=meta_service)
    comment_service = CommentService(store=store, profile_service=profile_service)
    relation_service = RelationService(store=store, profile_service=profile_service, meta_service=meta_service)
    return store, profile_service, meta_service, project_service, workitem_service, comment_service, relation_service


def _print_success(*, data, profile=None, warnings=None):
    print(
        json.dumps(
            {
                "success": True,
                "profile": profile,
                "data": data,
                "warnings": warnings or [],
            },
            ensure_ascii=False,
        )
    )


def _print_error(error: Exception, *, status_code=None, response=None):
    print(
        json.dumps(
            {
                "success": False,
                "profile": None,
                "data": {},
                "warnings": [],
                "error": {
                    "message": str(error),
                    "status_code": status_code,
                    "response": response or {},
                },
            },
            ensure_ascii=False,
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        store, profile_service, meta_service, project_service, workitem_service, comment_service, relation_service = _services()
        if args.command == "login" and args.login_command == "token":
            account, organizations, projects, warnings = AuthService(store=store).login_token(
                token=args.token,
                account_name=args.account,
            )
            _print_success(
                data={
                    "account": account.to_dict(),
                    "organizations": organizations,
                    "projects": projects,
                },
                warnings=warnings,
            )
            return 0
        if args.command == "profile" and args.profile_command == "add":
            profile, meta = profile_service.add_profile(args.name, args.account, args.org, args.project)
            _print_success(data={"profile": profile.to_dict(), "meta": meta}, profile=profile.to_dict())
            return 0
        if args.command == "profile" and args.profile_command == "list":
            _print_success(data={"profiles": profile_service.list_profiles()})
            return 0
        if args.command == "profile" and args.profile_command == "show":
            profile = profile_service.show_profile(args.profile)
            _print_success(data={"profile": profile.to_dict()}, profile=profile.to_dict())
            return 0
        if args.command == "profile" and args.profile_command == "use":
            profile = profile_service.use_profile(args.name)
            _print_success(data={"profile": profile.to_dict()}, profile=profile.to_dict())
            return 0
        if args.command == "meta" and args.meta_command == "reload":
            profile = profile_service.get_profile(args.profile)
            meta = meta_service.refresh(profile)
            _print_success(data={"meta": meta.to_dict()}, profile=profile.to_dict())
            return 0
        if args.command == "meta" and args.meta_command == "types":
            profile = profile_service.get_profile(args.profile)
            _print_success(
                data={"types": meta_service.list_types(profile, category=args.category)},
                profile=profile.to_dict(),
            )
            return 0
        if args.command == "meta" and args.meta_command == "statuses":
            profile = profile_service.get_profile(args.profile)
            _print_success(
                data={"statuses": meta_service.list_statuses(profile, category=args.category)},
                profile=profile.to_dict(),
            )
            return 0
        if args.command == "meta" and args.meta_command == "fields":
            profile = profile_service.get_profile(args.profile)
            _print_success(
                data={"fields": meta_service.list_fields(profile, category=args.category)},
                profile=profile.to_dict(),
            )
            return 0
        if args.command == "project" and args.project_command == "list":
            projects, profile = project_service.list_projects(
                profile_name=args.profile,
                account_name=args.account,
                org=args.org,
            )
            _print_success(data={"projects": projects}, profile=profile)
            return 0
        if args.command == "project" and args.project_command == "get":
            project, profile = project_service.get_project(profile_name=args.profile)
            _print_success(data={"project": project}, profile=profile)
            return 0
        if args.command == "workitem" and args.workitem_command == "create":
            data, profile = workitem_service.create(
                profile_name=args.profile,
                category=args.category,
                subject=args.subject,
                type_value=args.type,
                desc=args.desc,
                desc_file=args.desc_file,
                parent=args.parent,
                assigned_to=args.assigned_to,
                field_pairs=args.field,
                field_json_pairs=args.field_json,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "workitem" and args.workitem_command == "get":
            data, profile = workitem_service.get(
                profile_name=args.profile,
                workitem_id=args.workitem_id,
                with_comments=not args.no_comments,
                with_parent=args.with_parent,
                with_attachments=not args.no_attachments,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "workitem" and args.workitem_command == "mine":
            data, profile = workitem_service.mine(
                profile_name=args.profile,
                category=args.category,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "workitem" and args.workitem_command == "search":
            data, profile = workitem_service.search(
                profile_name=args.profile,
                category=args.category,
                status=args.status,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "workitem" and args.workitem_command == "update":
            data, profile = workitem_service.update(
                profile_name=args.profile,
                workitem_id=args.workitem_id,
                subject=args.subject,
                desc=args.desc,
                desc_file=args.desc_file,
                assigned_to=args.assigned_to,
                status=args.status,
                field_pairs=args.field,
                field_json_pairs=args.field_json,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "workitem" and args.workitem_command == "transition":
            data, profile = workitem_service.transition(
                profile_name=args.profile,
                workitem_id=args.workitem_id,
                target_status=args.to,
                field_pairs=args.field,
                field_json_pairs=args.field_json,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "comment" and args.comment_command == "add":
            data, profile = comment_service.add(
                profile_name=args.profile,
                workitem_id=args.workitem,
                content=args.content,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "comment" and args.comment_command == "list":
            data, profile = comment_service.list(
                profile_name=args.profile,
                workitem_id=args.workitem,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "relation" and args.relation_command == "add":
            data, profile = relation_service.add(
                profile_name=args.profile,
                parent_id=args.parent,
                child_id=args.child,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "relation" and args.relation_command == "children":
            data, profile = relation_service.children(
                profile_name=args.profile,
                parent_id=args.parent,
            )
            _print_success(data=data, profile=profile)
            return 0
        parser.print_help()
        return 0
    except CliError as error:
        _print_error(error)
        return 1
    except YunxiaoAPIError as error:
        _print_error(error, status_code=error.status_code, response=error.response)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
