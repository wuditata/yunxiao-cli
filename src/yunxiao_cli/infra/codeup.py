from __future__ import annotations

from typing import Any
from urllib.parse import quote

from .base import BaseAPI


class CodeupAPI(BaseAPI):
    """云效 Codeup 代码管理 API。"""

    @staticmethod
    def _encode_repo_id(repo_id: str) -> str:
        """处理 repositoryId 中未编码的斜杠。"""
        if "/" in repo_id:
            parts = repo_id.split("/", 1)
            if len(parts) == 2:
                return f"{parts[0]}%2F{quote(parts[1], safe='')}"
        return repo_id

    @staticmethod
    def _encode_path(file_path: str) -> str:
        """确保文件路径已被 URL 编码。"""
        if file_path.startswith("/"):
            file_path = file_path[1:]
        return quote(file_path, safe="")

    # ── 仓库 ──────────────────────────────────────────

    def list_repositories(
        self,
        org_id: str,
        *,
        search: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[dict]:
        params: dict[str, Any] = {"page": page, "perPage": per_page}
        if search:
            params["search"] = search
        items = self.get(
            f"/oapi/v1/codeup/organizations/{org_id}/repositories",
            params=params,
        )
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []

    def get_repository(self, org_id: str, repo_id: str) -> dict:
        encoded = self._encode_repo_id(repo_id)
        return self.get(f"/oapi/v1/codeup/organizations/{org_id}/repositories/{encoded}")

    # ── 分支 ──────────────────────────────────────────

    def list_branches(
        self,
        org_id: str,
        repo_id: str,
        *,
        search: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[dict]:
        encoded = self._encode_repo_id(repo_id)
        params: dict[str, Any] = {"page": page, "perPage": per_page}
        if search:
            params["search"] = search
        items = self.get(
            f"/oapi/v1/codeup/organizations/{org_id}/repositories/{encoded}/branches",
            params=params,
        )
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []

    # ── 文件 ──────────────────────────────────────────

    def list_files(
        self,
        org_id: str,
        repo_id: str,
        *,
        path: str | None = None,
        ref: str | None = None,
        type: str | None = None,
    ) -> list[dict]:
        encoded = self._encode_repo_id(repo_id)
        params: dict[str, Any] = {}
        if path:
            params["path"] = path
        if ref:
            params["ref"] = ref
        if type:
            params["type"] = type
        items = self.get(
            f"/oapi/v1/codeup/organizations/{org_id}/repositories/{encoded}/files/tree",
            params=params,
        )
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []

    def get_file_blobs(
        self,
        org_id: str,
        repo_id: str,
        file_path: str,
        *,
        ref: str = "master",
    ) -> dict:
        encoded_repo = self._encode_repo_id(repo_id)
        encoded_path = self._encode_path(file_path)
        return self.get(
            f"/oapi/v1/codeup/organizations/{org_id}/repositories/{encoded_repo}/files/{encoded_path}",
            params={"ref": ref},
        )

    # ── 提交 ──────────────────────────────────────────

    def list_commits(
        self,
        org_id: str,
        repo_id: str,
        *,
        ref_name: str = "master",
        path: str | None = None,
        search: str | None = None,
        since: str | None = None,
        until: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[dict]:
        encoded = self._encode_repo_id(repo_id)
        params: dict[str, Any] = {"refName": ref_name, "page": page, "perPage": per_page}
        if path:
            params["path"] = path
        if search:
            params["search"] = search
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        items = self.get(
            f"/oapi/v1/codeup/organizations/{org_id}/repositories/{encoded}/commits",
            params=params,
        )
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []

    def get_commit(self, org_id: str, repo_id: str, sha: str) -> dict:
        encoded = self._encode_repo_id(repo_id)
        return self.get(
            f"/oapi/v1/codeup/organizations/{org_id}/repositories/{encoded}/commits/{sha}"
        )

    # ── 代码比较 ──────────────────────────────────────

    def compare(
        self,
        org_id: str,
        repo_id: str,
        *,
        from_ref: str,
        to_ref: str,
    ) -> dict:
        encoded = self._encode_repo_id(repo_id)
        return self.get(
            f"/oapi/v1/codeup/organizations/{org_id}/repositories/{encoded}/diffs/compare",
            params={"from": from_ref, "to": to_ref},
        )

    # ── 合并请求 (Change Request / MR) ────────────────

    def list_change_requests(
        self,
        org_id: str,
        *,
        repo_id: str | None = None,
        state: str | None = None,
        search: str | None = None,
        author_ids: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[dict]:
        params: dict[str, Any] = {"page": page, "perPage": per_page}
        if repo_id:
            params["projectIds"] = repo_id
        if state:
            params["state"] = state
        if search:
            params["search"] = search
        if author_ids:
            params["authorIds"] = author_ids
        items = self.get(
            f"/oapi/v1/codeup/organizations/{org_id}/changeRequests",
            params=params,
        )
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []

    def get_change_request(self, org_id: str, repo_id: str, local_id: str) -> dict:
        encoded = self._encode_repo_id(repo_id)
        return self.get(
            f"/oapi/v1/codeup/organizations/{org_id}/repositories/{encoded}/changeRequests/{local_id}"
        )

    def list_change_request_comments(
        self,
        org_id: str,
        repo_id: str,
        local_id: str,
        *,
        comment_type: str | None = None,
        state: str | None = None,
        resolved: str | None = None,
    ) -> list[dict]:
        encoded = self._encode_repo_id(repo_id)
        params: dict[str, Any] = {}
        if comment_type:
            params["commentType"] = comment_type
        if state:
            params["state"] = state
        if resolved:
            params["resolved"] = resolved
        items = self.get(
            f"/oapi/v1/codeup/organizations/{org_id}/repositories/{encoded}/changeRequests/{local_id}/comments",
            params=params,
        )
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []
