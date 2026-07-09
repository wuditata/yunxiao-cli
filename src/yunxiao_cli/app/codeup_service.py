from __future__ import annotations

from pathlib import Path
from typing import Any

from ..domain.store import Store
from ..infra.codeup import CodeupAPI
from .errors import CliError
from .profile_service import ProfileService


class CodeupService:
    """代码管理服务层，面向 CLI 命令。"""

    def __init__(self, store: Store, profile_service: ProfileService):
        self.store = store
        self.profile_service = profile_service

    # ── 仓库 ──────────────────────────────────────────

    def list_repos(
        self,
        *,
        profile_name: str | None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        repos = api.list_repositories(profile.org, search=search, page=page, per_page=per_page)
        return {
            "repositories": repos,
            "total": len(repos),
        }, self._profile_dict(profile)

    def get_repo(
        self,
        *,
        profile_name: str | None,
        repo_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        repo = api.get_repository(profile.org, repo_id)
        return {"repository": repo}, self._profile_dict(profile)

    # ── 分支 ──────────────────────────────────────────

    def list_branches(
        self,
        *,
        profile_name: str | None,
        repo_id: str,
        search: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        branches = api.list_branches(profile.org, repo_id, search=search)
        return {
            "branches": branches,
            "total": len(branches),
        }, self._profile_dict(profile)

    # ── 文件 ──────────────────────────────────────────

    def list_files(
        self,
        *,
        profile_name: str | None,
        repo_id: str,
        path: str | None = None,
        ref: str | None = None,
        recursive: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        file_type = "RECURSIVE" if recursive else None
        files = api.list_files(profile.org, repo_id, path=path, ref=ref, type=file_type)
        return {
            "files": files,
            "total": len(files),
        }, self._profile_dict(profile)

    def get_file(
        self,
        *,
        profile_name: str | None,
        repo_id: str,
        file_path: str,
        ref: str = "master",
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        content = api.get_file_blobs(profile.org, repo_id, file_path, ref=ref)
        return {"file": content}, self._profile_dict(profile)

    # ── 提交 ──────────────────────────────────────────

    def list_commits(
        self,
        *,
        profile_name: str | None,
        repo_id: str,
        ref: str = "master",
        path: str | None = None,
        search: str | None = None,
        since: str | None = None,
        until: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        commits = api.list_commits(
            profile.org, repo_id,
            ref_name=ref, path=path, search=search,
            since=since, until=until, page=page, per_page=per_page,
        )
        return {
            "commits": commits,
            "total": len(commits),
        }, self._profile_dict(profile)

    def get_commit(
        self,
        *,
        profile_name: str | None,
        repo_id: str,
        sha: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        commit = api.get_commit(profile.org, repo_id, sha)
        return {"commit": commit}, self._profile_dict(profile)

    # ── 代码比较 ──────────────────────────────────────

    def compare(
        self,
        *,
        profile_name: str | None,
        repo_id: str,
        from_ref: str,
        to_ref: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        diff = api.compare(profile.org, repo_id, from_ref=from_ref, to_ref=to_ref)
        return {"compare": diff}, self._profile_dict(profile)

    # ── 合并请求 ──────────────────────────────────────

    def list_mrs(
        self,
        *,
        profile_name: str | None,
        repo_id: str | None = None,
        state: str | None = None,
        search: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        mrs = api.list_change_requests(
            profile.org, repo_id=repo_id, state=state, search=search,
        )
        return {
            "changeRequests": mrs,
            "total": len(mrs),
        }, self._profile_dict(profile)

    def get_mr(
        self,
        *,
        profile_name: str | None,
        repo_id: str,
        local_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        mr = api.get_change_request(profile.org, repo_id, local_id)
        return {"changeRequest": mr}, self._profile_dict(profile)

    def create_mr(
        self,
        *,
        profile_name: str | None,
        repo_id: str,
        title: str,
        source_branch: str,
        target_branch: str,
        description: str | None = None,
        desc_file: str | None = None,
        source_project_id: str | None = None,
        target_project_id: str | None = None,
        reviewer_ids: list[str] | None = None,
        work_item_ids: list[str] | None = None,
        create_from: str = "COMMAND_LINE",
        trigger_ai_review: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        mr = api.create_change_request(
            profile.org,
            repo_id,
            title=title,
            source_branch=source_branch,
            target_branch=target_branch,
            description=self._load_description(description, desc_file),
            source_project_id=source_project_id,
            target_project_id=target_project_id,
            reviewer_user_ids=self._split_values(reviewer_ids),
            work_item_ids=self._split_values(work_item_ids),
            create_from=create_from,
            trigger_ai_review=trigger_ai_review,
        )
        return {"changeRequest": mr}, self._profile_dict(profile)

    def list_mr_comments(
        self,
        *,
        profile_name: str | None,
        repo_id: str,
        local_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        comments = self._list_all_mr_comments(api, profile.org, repo_id, local_id)
        return {
            "comments": comments,
            "total": len(comments),
        }, self._profile_dict(profile)

    def add_mr_comment(
        self,
        *,
        profile_name: str | None,
        repo_id: str,
        local_id: str,
        content: str | None = None,
        content_file: str | None = None,
        file_path: str | None = None,
        line_number: int | None = None,
        reply_to: str | None = None,
        resolved: bool = False,
        from_patchset: str | None = None,
        to_patchset: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        text = self._load_description(content, content_file)
        if not text:
            raise CliError("评论内容为空：传 --content 或 --content-file")
        inline = bool(file_path or line_number is not None)
        if inline and (not file_path or line_number is None):
            raise CliError("行内评论必须同时传 --file 和 --line")

        # 全局评论挂最新合并源版本；行内评论 from=合并目标版本、to=最新合并源版本
        if not to_patchset or (inline and not from_patchset):
            source, target = self._latest_patchsets(api, profile.org, repo_id, local_id)
            to_patchset = to_patchset or source
            from_patchset = from_patchset or target
        comment = api.create_change_request_comment(
            profile.org,
            repo_id,
            local_id,
            content=text,
            comment_type="INLINE_COMMENT" if inline else "GLOBAL_COMMENT",
            patchset_biz_id=to_patchset,
            resolved=resolved,
            file_path=file_path,
            line_number=line_number,
            from_patchset_biz_id=from_patchset,
            to_patchset_biz_id=to_patchset,
            parent_comment_biz_id=reply_to,
        )
        return {"comment": comment}, self._profile_dict(profile)

    @staticmethod
    def _latest_patchsets(api: CodeupAPI, org_id: str, repo_id: str, local_id: str) -> tuple[str, str]:
        """返回 (最新合并源版本ID, 合并目标版本ID)。"""
        patch_sets = api.list_change_request_patch_sets(org_id, repo_id, local_id)
        sources = [p for p in patch_sets if p.get("relatedMergeItemType") == "MERGE_SOURCE"]
        targets = [p for p in patch_sets if p.get("relatedMergeItemType") == "MERGE_TARGET"]
        latest_source = max(sources, key=lambda p: p.get("versionNo") or 0, default=None)
        target = targets[0] if targets else None
        source_id = (latest_source or {}).get("patchSetBizId")
        target_id = (target or {}).get("patchSetBizId")
        if not source_id:
            raise CliError("未找到合并源版本（MERGE_SOURCE patchset），可用 --to-patchset 显式指定")
        return str(source_id), str(target_id) if target_id else str(source_id)

    def merge_mr(
        self,
        *,
        profile_name: str | None,
        repo_id: str,
        local_id: str,
        merge_type: str = "no-fast-forward",
        merge_message: str | None = None,
        remove_source_branch: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        mr = api.merge_change_request(
            profile.org,
            repo_id,
            local_id,
            merge_type=merge_type,
            merge_message=merge_message,
            remove_source_branch=remove_source_branch,
        )
        return {"changeRequest": mr}, self._profile_dict(profile)

    def get_mr_review_context(
        self,
        *,
        profile_name: str | None,
        repo_id: str,
        local_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        mr = api.get_change_request(profile.org, repo_id, local_id)
        patch_sets = api.list_change_request_patch_sets(profile.org, repo_id, local_id)
        comments = self._list_all_mr_comments(api, profile.org, repo_id, local_id)
        compare = api.compare(
            profile.org,
            repo_id,
            from_ref=self._mr_branch(mr, "targetBranch", "target_branch"),
            to_ref=self._mr_branch(mr, "sourceBranch", "source_branch"),
        )
        return {
            "changeRequest": mr,
            "patchSets": patch_sets,
            "comments": comments,
            "compare": compare,
        }, self._profile_dict(profile)

    # ── 内部 ──────────────────────────────────────────

    def _codeup_api(self, profile) -> CodeupAPI:
        account = self.store.get_account(profile.account)
        return CodeupAPI(token=account.token)

    @staticmethod
    def _list_all_mr_comments(
        api: CodeupAPI,
        org_id: str,
        repo_id: str,
        local_id: str,
    ) -> list[dict]:
        comments: list[dict] = []
        for comment_type in ("GLOBAL_COMMENT", "INLINE_COMMENT"):
            comments.extend(
                api.list_change_request_comments(
                    org_id,
                    repo_id,
                    local_id,
                    comment_type=comment_type,
                )
            )
        return comments

    @staticmethod
    def _mr_branch(change_request: dict[str, Any], *keys: str) -> str:
        for key in keys:
            value = change_request.get(key)
            if value:
                return str(value)
        raise CliError("MR 缺少源分支或目标分支，无法生成 review context")

    @staticmethod
    def _profile_dict(profile) -> dict[str, Any]:
        return {
            "name": profile.name,
            "account": profile.account,
            "org": profile.org,
            "project": profile.project,
            "projects": profile.projects,
        }

    @staticmethod
    def _load_description(description: str | None, desc_file: str | None) -> str | None:
        if description and desc_file:
            raise CliError("--desc 与 --desc-file 不能同时使用")
        if not desc_file:
            return description
        try:
            return Path(desc_file).read_text(encoding="utf-8")
        except OSError as error:
            raise CliError(f"读取描述文件失败：{desc_file}") from error

    @staticmethod
    def _split_values(values: list[str] | None) -> list[str] | None:
        if not values:
            return None
        result: list[str] = []
        for value in values:
            result.extend(item.strip() for item in value.split(",") if item.strip())
        return result or None
