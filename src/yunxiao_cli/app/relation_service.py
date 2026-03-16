from __future__ import annotations

from ..domain.store import Store
from ..infra.projex import ProjexAPI
from .meta_service import MetaService
from .profile_service import ProfileService


class RelationService:
    def __init__(self, store: Store, profile_service: ProfileService, meta_service: MetaService):
        self.store = store
        self.profile_service = profile_service
        self.meta_service = meta_service

    def add(self, *, profile_name: str | None, parent_id: str, child_id: str) -> tuple[dict, dict]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile.account)
        relation = api.create_relation_record(profile.org, child_id, "PARENT", parent_id)
        return {"relation": relation}, self._profile_dict(profile)

    def children(self, *, profile_name: str | None, parent_id: str) -> tuple[dict, dict]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile.account)
        items = []
        for category in self.meta_service.CATEGORY_CHOICES:
            items.extend(
                api.search_workitems(
                    org_id=profile.org,
                    project_id=profile.project,
                    category=category,
                    parent_id=parent_id,
                )
            )
        return {"children": items}, self._profile_dict(profile)

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
