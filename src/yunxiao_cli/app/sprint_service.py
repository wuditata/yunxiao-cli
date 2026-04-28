from __future__ import annotations

from typing import Any

from ..domain.store import Store
from ..infra.projex import ProjexAPI
from .profile_service import ProfileService


class SprintService:
    def __init__(self, store: Store, profile_service: ProfileService):
        self.store = store
        self.profile_service = profile_service

    def list_sprints(
        self,
        *,
        profile_name: str | None,
        project: str | None = None,
        status: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile)
        projects = list(profile.projects) if not project else [project]
        all_sprints: list[dict[str, Any]] = []
        for project_id in projects:
            sprints = api.list_sprints(profile.org, project_id, status=status)
            for sprint in sprints:
                sprint.setdefault("projectId", project_id)
            all_sprints.extend(sprints)
        return {
            "sprints": all_sprints,
            "total": len(all_sprints),
        }, self._profile_dict(profile)

    def get_sprint(
        self,
        *,
        profile_name: str | None,
        project: str,
        sprint_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile)
        sprint = api.get_sprint(profile.org, project, sprint_id)
        return {"sprint": sprint}, self._profile_dict(profile)

    def list_versions(
        self,
        *,
        profile_name: str | None,
        project: str | None = None,
        status: str | None = None,
        name: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile)
        projects = list(profile.projects) if not project else [project]
        all_versions: list[dict[str, Any]] = []
        for project_id in projects:
            versions = api.list_versions(profile.org, project_id, status=status, name=name)
            for version in versions:
                version.setdefault("projectId", project_id)
            all_versions.extend(versions)
        return {
            "versions": all_versions,
            "total": len(all_versions),
        }, self._profile_dict(profile)

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
