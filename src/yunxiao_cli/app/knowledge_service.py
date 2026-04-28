from __future__ import annotations

from typing import Any

from ..domain.store import Store
from ..infra.projex import ProjexAPI
from .errors import CliError
from .meta_service import MetaService
from .profile_service import ProfileService
from .workitem_summary import WorkitemSummaryBuilder


class KnowledgeService:
    """聚合多个数据源，生成面向 AI 的知识上下文。"""

    def __init__(
        self,
        store: Store,
        profile_service: ProfileService,
        meta_service: MetaService,
    ):
        self.store = store
        self.profile_service = profile_service
        self.meta_service = meta_service
        self.summary_builder = WorkitemSummaryBuilder(meta_service)

    def context(
        self,
        *,
        profile_name: str | None,
        workitem_id: str,
        depth: int = 1,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """聚合单个工作项的所有相关知识。

        返回工作项详情、评论、附件、子项树（递归到 depth 层）、父项链。
        """
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile)
        workitem = api.get_work_item(profile.org, workitem_id)
        comments = api.list_comments(profile.org, workitem_id)
        attachments = api.list_workitem_attachments(profile.org, workitem_id)

        parent_chain = self._build_parent_chain(api, profile.org, workitem)
        children_tree = self._build_children_tree(api, profile.org, workitem_id, depth=depth)

        return {
            "workitem": workitem,
            "comments": comments,
            "attachments": attachments,
            "parentChain": parent_chain,
            "childrenTree": children_tree,
            "depth": depth,
        }, self._profile_dict(profile)

    def project_summary(
        self,
        *,
        profile_name: str | None,
        project: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """生成项目知识概览，包含迭代进度和各分类的工作项统计。"""
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile)
        projects = list(profile.projects) if not project else [project]

        summaries: list[dict[str, Any]] = []
        for project_id in projects:
            project_info = api.get_project(profile.org, project_id)
            sprints = api.list_sprints(profile.org, project_id)
            active_sprints = [s for s in sprints if self._is_active_sprint(s)]

            category_stats: dict[str, dict[str, int]] = {}
            for category in self.meta_service.CATEGORY_CHOICES:
                items = api.search_workitems(
                    org_id=profile.org,
                    project_id=project_id,
                    category=category,
                    per_page=1,
                )
                total = len(items) if items else 0
                category_stats[category] = {"total": total}

            summaries.append({
                "projectId": project_id,
                "projectName": project_info.get("name"),
                "activeSprints": [
                    {
                        "id": s.get("id"),
                        "name": s.get("name"),
                        "status": s.get("status"),
                        "startDate": s.get("startDate"),
                        "endDate": s.get("endDate"),
                    }
                    for s in active_sprints
                ],
                "categoryStats": category_stats,
            })

        return {
            "projects": summaries,
            "total": len(summaries),
        }, self._profile_dict(profile)

    def _build_parent_chain(
        self,
        api: ProjexAPI,
        org_id: str,
        workitem: dict[str, Any],
        *,
        max_depth: int = 10,
    ) -> list[dict[str, Any]]:
        """沿 parentId 向上追溯，返回从直接父到根的链。"""
        chain: list[dict[str, Any]] = []
        current = workitem
        for _ in range(max_depth):
            parent_id = current.get("parentId")
            if not parent_id:
                break
            try:
                parent = api.get_work_item(org_id, str(parent_id))
            except Exception:
                break
            chain.append({
                "id": parent.get("id"),
                "subject": parent.get("subject"),
                "serialNumber": parent.get("serialNumber"),
                "category": self._extract_category(parent),
            })
            current = parent
        return chain

    def _build_children_tree(
        self,
        api: ProjexAPI,
        org_id: str,
        workitem_id: str,
        *,
        depth: int,
        current_depth: int = 0,
    ) -> list[dict[str, Any]]:
        """递归获取子项树。"""
        if current_depth >= depth:
            return []
        try:
            children = api.search_workitems(
                org_id=org_id,
                project_id="",
                parent_id=workitem_id,
                per_page=100,
            )
        except Exception:
            return []

        tree: list[dict[str, Any]] = []
        for child in children:
            child_id = child.get("id")
            node: dict[str, Any] = {
                "id": child_id,
                "subject": child.get("subject"),
                "serialNumber": child.get("serialNumber"),
                "status": self._extract_status_name(child),
                "category": self._extract_category(child),
            }
            if child_id and current_depth + 1 < depth:
                node["children"] = self._build_children_tree(
                    api, org_id, str(child_id),
                    depth=depth, current_depth=current_depth + 1,
                )
            tree.append(node)
        return tree

    @staticmethod
    def _is_active_sprint(sprint: dict[str, Any]) -> bool:
        status = str(sprint.get("status", "")).lower()
        return status in ("doing", "active", "started", "in_progress")

    @staticmethod
    def _extract_category(item: dict[str, Any]) -> str | None:
        wt = item.get("workitemType")
        if isinstance(wt, dict):
            return wt.get("categoryId") or wt.get("category")
        return item.get("categoryId")

    @staticmethod
    def _extract_status_name(item: dict[str, Any]) -> str | None:
        status = item.get("status")
        if isinstance(status, dict):
            return status.get("displayName") or status.get("name")
        return None

    def _projex_api(self, profile) -> ProjexAPI:
        account = self.store.get_account(profile.account)
        return ProjexAPI(token=account.token)

    @staticmethod
    def _profile_dict(profile) -> dict[str, Any]:
        return {
            "name": profile.name,
            "account": profile.account,
            "org": profile.org,
            "project": profile.project,
            "projects": profile.projects,
        }
