from __future__ import annotations

import json
from collections.abc import Sequence

from .app.attachment_service import AttachmentService
from .app.auth_service import AuthService
from .app.comment_service import CommentService
from .app.context_service import ContextService
from .app.codeup_service import CodeupService
from .app.errors import CliError
from .app.knowledge_service import KnowledgeService
from .app.thoughts_service import ThoughtsKnowledgeService
from .app.meta_service import MetaService
from .app.profile_service import ProfileService
from .app.project_service import ProjectService
from .app.relation_service import RelationService
from .app.sprint_service import SprintService
from .app.workitem_service import WorkitemService
from .cli import build_parser
from .domain.store import Store
from .infra.base import YunxiaoAPIError
from .infra.config import CliConfig


def _services() -> tuple[
    Store,
    ContextService,
    ProfileService,
    MetaService,
    ProjectService,
    WorkitemService,
    AttachmentService,
    CommentService,
    RelationService,
    SprintService,
    KnowledgeService,
    CodeupService,
]:
    store = Store(root=CliConfig.data_root())
    context_service = ContextService(store=store)
    meta_service = MetaService(store=store)
    profile_service = ProfileService(store=store, meta_service=meta_service, context_service=context_service)
    project_service = ProjectService(store=store, profile_service=profile_service)
    attachment_service = AttachmentService(store=store, profile_service=profile_service)
    workitem_service = WorkitemService(
        store=store,
        profile_service=profile_service,
        meta_service=meta_service,
        attachment_service=attachment_service,
    )
    comment_service = CommentService(store=store, profile_service=profile_service)
    relation_service = RelationService(store=store, profile_service=profile_service, meta_service=meta_service)
    sprint_service = SprintService(store=store, profile_service=profile_service)
    knowledge_service = KnowledgeService(store=store, profile_service=profile_service, meta_service=meta_service)
    codeup_service = CodeupService(store=store, profile_service=profile_service)
    return (
        store,
        context_service,
        profile_service,
        meta_service,
        project_service,
        workitem_service,
        attachment_service,
        comment_service,
        relation_service,
        sprint_service,
        knowledge_service,
        codeup_service,
    )


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
        (
            store,
            context_service,
            profile_service,
            meta_service,
            project_service,
            workitem_service,
            attachment_service,
            comment_service,
            relation_service,
            sprint_service,
            knowledge_service,
            codeup_service,
        ) = _services()
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
        if args.command == "context" and args.context_command == "init":
            config, path = context_service.init_project_context(
                profile=args.profile,
                assignee=args.assignee,
                project=args.project,
                token=args.token,
            )
            _print_success(data={"path": str(path), "context": config.to_dict()})
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
        project_context = context_service.resolve(
            profile=getattr(args, "profile", None),
            assignee=getattr(args, "assigned_to", None),
            project=getattr(args, "project", None),
        )
        if (
            project_context.token
            and project_context.profile
            and (not getattr(args, "profile", None) or getattr(args, "profile", None) == project_context.profile)
        ):
            context_service.refresh_login_if_needed(profile=project_context.profile, token=project_context.token)
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
                assigned_to=project_context.assignee,
                attachments=args.attachment,
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
                assignee=project_context.assignee,
                category=args.category,
                project=project_context.project,
                sort=args.sort,
                raw=args.raw,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "workitem" and args.workitem_command == "search":
            data, profile = workitem_service.search(
                profile_name=args.profile,
                category=args.category,
                status=args.status,
                keyword=args.keyword,
                tag=args.tag,
                priority=args.priority,
                assigned_to=getattr(args, "assigned_to", None) or project_context.assignee if getattr(args, "assigned_to", None) else None,
                sprint=args.sprint,
                created_after=args.created_after,
                created_before=args.created_before,
                updated_after=args.updated_after,
                updated_before=args.updated_before,
                project=project_context.project,
                sort=args.sort,
                raw=args.raw,
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
                assigned_to=project_context.assignee,
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
        if args.command == "workitem" and args.workitem_command == "attachment":
            if args.workitem_attachment_command == "upload":
                data, profile = attachment_service.upload(
                    profile_name=args.profile,
                    workitem_id=args.workitem_id,
                    file_path=args.path,
                    operator_id=args.operator_id,
                )
                _print_success(data=data, profile=profile)
                return 0
            if args.workitem_attachment_command == "list":
                data, profile = attachment_service.list(
                    profile_name=args.profile,
                    workitem_id=args.workitem_id,
                )
                _print_success(data=data, profile=profile)
                return 0
            if args.workitem_attachment_command == "get":
                data, profile = attachment_service.get(
                    profile_name=args.profile,
                    workitem_id=args.workitem_id,
                    file_id=args.file,
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
        if args.command == "sprint" and args.sprint_command == "list":
            data, profile = sprint_service.list_sprints(
                profile_name=args.profile,
                project=getattr(args, "project", None) or project_context.project,
                status=args.status,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "sprint" and args.sprint_command == "get":
            data, profile = sprint_service.get_sprint(
                profile_name=args.profile,
                project=args.project,
                sprint_id=args.sprint_id,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "version" and args.version_command == "list":
            data, profile = sprint_service.list_versions(
                profile_name=args.profile,
                project=getattr(args, "project", None) or project_context.project,
                status=args.status,
                name=getattr(args, "name", None),
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "knowledge" and args.knowledge_command == "context":
            data, profile = knowledge_service.context(
                profile_name=args.profile,
                workitem_id=args.workitem_id,
                depth=args.depth,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "knowledge" and getattr(args, "knowledge_command", None) == "project-summary":
            data, profile = knowledge_service.project_summary(
                profile_name=args.profile,
                project=getattr(args, "project", None) or project_context.project,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "thoughts" and getattr(args, "thoughts_command", None) == "download":
            thoughts_knowledge_service = ThoughtsKnowledgeService()
            data = thoughts_knowledge_service.download(
                url=args.url,
                output_dir=args.output,
                cookie=args.cookie,
                cookie_file=getattr(args, "cookie_file", None),
                browser=args.browser,
                concurrency=args.concurrency,
            )
            _print_success(data=data)
            return 0
        # ── Codeup 路由 ──────────────────────────────────────
        if args.command == "codeup" and getattr(args, "codeup_command", None) == "repo":
            if getattr(args, "codeup_repo_command", None) == "list":
                data, profile = codeup_service.list_repos(
                    profile_name=args.profile,
                    search=getattr(args, "search", None),
                )
                _print_success(data=data, profile=profile)
                return 0
            if getattr(args, "codeup_repo_command", None) == "get":
                data, profile = codeup_service.get_repo(
                    profile_name=args.profile,
                    repo_id=args.repo_id,
                )
                _print_success(data=data, profile=profile)
                return 0
        if args.command == "codeup" and getattr(args, "codeup_command", None) == "branch":
            if getattr(args, "codeup_branch_command", None) == "list":
                data, profile = codeup_service.list_branches(
                    profile_name=args.profile,
                    repo_id=args.repo_id,
                    search=getattr(args, "search", None),
                )
                _print_success(data=data, profile=profile)
                return 0
        if args.command == "codeup" and getattr(args, "codeup_command", None) == "file":
            if getattr(args, "codeup_file_command", None) == "list":
                data, profile = codeup_service.list_files(
                    profile_name=args.profile,
                    repo_id=args.repo_id,
                    path=getattr(args, "path", None),
                    ref=getattr(args, "ref", None),
                    recursive=getattr(args, "recursive", False),
                )
                _print_success(data=data, profile=profile)
                return 0
            if getattr(args, "codeup_file_command", None) == "get":
                data, profile = codeup_service.get_file(
                    profile_name=args.profile,
                    repo_id=args.repo_id,
                    file_path=args.file_path,
                    ref=args.ref,
                )
                _print_success(data=data, profile=profile)
                return 0
        if args.command == "codeup" and getattr(args, "codeup_command", None) == "commit":
            if getattr(args, "codeup_commit_command", None) == "list":
                data, profile = codeup_service.list_commits(
                    profile_name=args.profile,
                    repo_id=args.repo_id,
                    ref=args.ref,
                    path=getattr(args, "path", None),
                    search=getattr(args, "search", None),
                    since=getattr(args, "since", None),
                    until=getattr(args, "until", None),
                )
                _print_success(data=data, profile=profile)
                return 0
            if getattr(args, "codeup_commit_command", None) == "get":
                data, profile = codeup_service.get_commit(
                    profile_name=args.profile,
                    repo_id=args.repo_id,
                    sha=args.sha,
                )
                _print_success(data=data, profile=profile)
                return 0
        if args.command == "codeup" and getattr(args, "codeup_command", None) == "compare":
            data, profile = codeup_service.compare(
                profile_name=args.profile,
                repo_id=args.repo_id,
                from_ref=args.from_ref,
                to_ref=args.to_ref,
            )
            _print_success(data=data, profile=profile)
            return 0
        if args.command == "codeup" and getattr(args, "codeup_command", None) == "mr":
            if getattr(args, "codeup_mr_command", None) == "list":
                data, profile = codeup_service.list_mrs(
                    profile_name=args.profile,
                    repo_id=getattr(args, "repo", None),
                    state=getattr(args, "state", None),
                    search=getattr(args, "search", None),
                )
                _print_success(data=data, profile=profile)
                return 0
            if getattr(args, "codeup_mr_command", None) == "get":
                data, profile = codeup_service.get_mr(
                    profile_name=args.profile,
                    repo_id=args.repo_id,
                    local_id=args.local_id,
                )
                _print_success(data=data, profile=profile)
                return 0
            if getattr(args, "codeup_mr_command", None) == "comments":
                data, profile = codeup_service.list_mr_comments(
                    profile_name=args.profile,
                    repo_id=args.repo_id,
                    local_id=args.local_id,
                )
                _print_success(data=data, profile=profile)
                return 0
        parser.print_help()
        return 0
    except CliError as error:
        _print_error(error, response=getattr(error, "response", None))
        return 1
    except YunxiaoAPIError as error:
        _print_error(error, status_code=error.status_code, response=error.response)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
