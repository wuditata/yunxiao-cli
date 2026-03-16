from __future__ import annotations

from ..domain.store import Store
from ..infra.projex import ProjexAPI
from .errors import CliError
from .profile_service import ProfileService


class ProjectService:
    def __init__(self, store: Store, profile_service: ProfileService):
        self.store = store
        self.profile_service = profile_service

    def list_projects(
        self,
        *,
        profile_name: str | None = None,
        account_name: str | None = None,
        org: str | None = None,
    ) -> tuple[list[dict], dict | None]:
        if bool(account_name) != bool(org):
            raise CliError("account and org should be provided together")
        if account_name and org:
            api = self._projex_api(account_name)
            return api.list_projects(org), None
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile.account)
        return api.list_projects(profile.org), self._profile_dict(profile)

    def get_project(self, *, profile_name: str | None = None) -> tuple[dict, dict]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile.account)
        return api.get_project(profile.org, profile.project), self._profile_dict(profile)

    def _projex_api(self, account_name: str) -> ProjexAPI:
        account = self.store.get_account(account_name)
        return ProjexAPI(token=account.token)

    @staticmethod
    def _profile_dict(profile) -> dict:
        return {
            "name": profile.name,
            "account": profile.account,
            "org": profile.org,
            "project": profile.project,
        }
