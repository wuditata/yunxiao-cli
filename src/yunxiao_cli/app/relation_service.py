from __future__ import annotations

from ..domain.store import Store
from ..infra.projex import ProjexAPI
from .errors import CliError
from .meta_service import MetaService
from .profile_service import ProfileService


RELATION_TYPES = ("PARENT", "SUB", "ASSOCIATED", "DEPEND_ON", "DEPENDED_BY")


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

    def link(
        self,
        *,
        profile_name: str | None,
        workitem_id: str,
        related_workitem_id: str,
        relation_type: str,
        operator_id: str | None = None,
    ) -> tuple[dict, dict]:
        self._validate_relation_type(relation_type)
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile.account)
        relation = api.create_relation_record(
            profile.org,
            workitem_id,
            relation_type,
            related_workitem_id,
            operator_id=operator_id,
        )
        return {"relation": relation}, self._profile_dict(profile)

    def list(
        self,
        *,
        profile_name: str | None,
        workitem_id: str,
        relation_type: str,
    ) -> tuple[dict, dict]:
        self._validate_relation_type(relation_type)
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile.account)
        relations = api.list_relation_records(profile.org, workitem_id, relation_type)
        return {"relations": relations, "total": len(relations)}, self._profile_dict(profile)

    def delete(
        self,
        *,
        profile_name: str | None,
        workitem_id: str,
        related_workitem_id: str,
        relation_type: str,
        operator_id: str | None = None,
    ) -> tuple[dict, dict]:
        self._validate_relation_type(relation_type)
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile.account)
        api.delete_relation_record(
            profile.org,
            workitem_id,
            relation_type,
            related_workitem_id,
            operator_id=operator_id,
        )
        return {"success": True}, self._profile_dict(profile)

    @staticmethod
    def _validate_relation_type(relation_type: str) -> None:
        if relation_type not in RELATION_TYPES:
            raise CliError(f"不支持的关联类型：{relation_type}")

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
