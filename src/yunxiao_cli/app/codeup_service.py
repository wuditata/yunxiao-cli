from __future__ import annotations

from typing import Any

from ..domain.store import Store
from ..infra.codeup import CodeupAPI
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

    def list_mr_comments(
        self,
        *,
        profile_name: str | None,
        repo_id: str,
        local_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._codeup_api(profile)
        comments = api.list_change_request_comments(profile.org, repo_id, local_id)
        return {
            "comments": comments,
            "total": len(comments),
        }, self._profile_dict(profile)

    # ── 内部 ──────────────────────────────────────────

    def _codeup_api(self, profile) -> CodeupAPI:
        account = self.store.get_account(profile.account)
        return CodeupAPI(token=account.token)

    @staticmethod
    def _profile_dict(profile) -> dict[str, Any]:
        return {
            "name": profile.name,
            "account": profile.account,
            "org": profile.org,
            "project": profile.project,
            "projects": profile.projects,
        }
