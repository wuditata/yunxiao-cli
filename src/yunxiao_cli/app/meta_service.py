from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..domain.models import MetaCache, ProfileConfig
from ..domain.store import Store
from ..infra.projex import ProjexAPI
from .errors import CliError


class MetaService:
    CATEGORY_CHOICES = ("Req", "Task", "Bug")
    DEFAULT_TTL_SECONDS = 3600

    def __init__(self, store: Store):
        self.store = store

    def get_meta(self, profile: ProfileConfig) -> MetaCache:
        cache = self.store.find_meta_cache(profile.account, profile.org, profile.project)
        if cache is None or self._should_refresh(cache):
            return self.refresh(profile)
        return cache

    def refresh(self, profile: ProfileConfig) -> MetaCache:
        account = self.store.get_account(profile.account)
        api = ProjexAPI(token=account.token)
        project_info = api.get_project(profile.org, profile.project)
        workitem_types: list[dict[str, Any]] = []
        statuses: dict[str, list[dict[str, Any]]] = {}
        fields: dict[str, list[dict[str, Any]]] = {}

        for category in self.CATEGORY_CHOICES:
            category_types = api.get_work_item_types(profile.org, profile.project, category=category)
            workitem_types.extend(category_types)
            for item in category_types:
                type_id = item.get("id")
                if not type_id:
                    continue
                statuses[type_id] = api.get_work_item_workflow_statuses(profile.org, profile.project, type_id)
                fields[type_id] = api.get_work_item_type_fields(profile.org, profile.project, type_id)

        cache = MetaCache(
            account=profile.account,
            org=profile.org,
            project=profile.project,
            project_info=project_info,
            workitem_types=workitem_types,
            statuses=statuses,
            fields=fields,
            members=api.list_organization_members(profile.org),
            updated_at=datetime.now(UTC).isoformat(),
            ttl_seconds=self.DEFAULT_TTL_SECONDS,
            invalidated=False,
        )
        self.store.save_meta_cache(cache)
        return cache

    def list_types(self, profile: ProfileConfig, category: str | None = None) -> list[dict[str, Any]]:
        items = self.get_meta(profile).workitem_types
        if not category:
            return items
        return [item for item in items if item.get("categoryId") == category]

    def list_statuses(
        self,
        profile: ProfileConfig,
        *,
        category: str | None = None,
        workitem_type_id: str | None = None,
    ) -> list[dict[str, Any]]:
        meta = self.get_meta(profile)
        type_id = workitem_type_id or self.resolve_workitem_type(profile, category=category)["id"]
        return meta.statuses.get(type_id, [])

    def list_fields(
        self,
        profile: ProfileConfig,
        *,
        category: str | None = None,
        workitem_type_id: str | None = None,
    ) -> list[dict[str, Any]]:
        meta = self.get_meta(profile)
        type_id = workitem_type_id or self.resolve_workitem_type(profile, category=category)["id"]
        return meta.fields.get(type_id, [])

    def resolve_workitem_type(
        self,
        profile: ProfileConfig,
        *,
        category: str | None = None,
        type_value: str | None = None,
    ) -> dict[str, Any]:
        candidates = self.list_types(profile, category=category)
        if type_value:
            matched = [
                item for item in candidates
                if type_value in {item.get("id"), item.get("name")}
            ]
            if not matched:
                raise CliError(f"workitem type not found: {type_value}")
            if len(matched) > 1:
                raise CliError(f"workitem type is ambiguous: {type_value}")
            return matched[0]

        for item in candidates:
            if item.get("defaultType"):
                return item
        if candidates:
            return candidates[0]
        raise CliError(f"workitem type not found for category: {category}")

    def resolve_status(
        self,
        profile: ProfileConfig,
        status_value: str,
        *,
        workitem_type_id: str | None = None,
        category: str | None = None,
    ) -> str:
        candidates = self.list_statuses(profile, category=category, workitem_type_id=workitem_type_id)
        if any(status_value == item.get("id") for item in candidates):
            return status_value

        matched = []
        for item in candidates:
            names = {item.get("name"), item.get("displayName"), item.get("nameEn")}
            if status_value in names:
                matched.append(item)
        if not matched:
            raise CliError(f"status not found: {status_value}")
        if len(matched) > 1:
            raise CliError(f"status is ambiguous: {status_value}")
        return matched[0]["id"]

    def resolve_member(self, profile: ProfileConfig, member_value: str) -> str:
        members = self.get_meta(profile).members
        exact = [
            item for item in members
            if member_value in {item.get("userId"), item.get("id")}
        ]
        if exact:
            user_id = exact[0].get("userId") or exact[0].get("id")
            if user_id:
                return user_id

        matched = [item for item in members if item.get("name") == member_value]
        if not matched:
            raise CliError(f"member not found: {member_value}")
        if len(matched) > 1:
            raise CliError(f"member is ambiguous: {member_value}")
        return matched[0].get("userId") or matched[0].get("id")

    def resolve_field_ids(
        self,
        profile: ProfileConfig,
        workitem_type_id: str,
        field_names: list[str],
    ) -> dict[str, str]:
        fields = self.list_fields(profile, workitem_type_id=workitem_type_id)
        index: dict[str, str] = {}
        for field in fields:
            field_id = field.get("id")
            if not field_id:
                continue
            field_id_text = str(field_id)
            index[field_id_text] = field_id_text
            for key in ("name", "displayName", "fieldName", "identifier", "fieldIdentifier"):
                value = field.get(key)
                if value:
                    index[str(value)] = field_id_text
        resolved = {name: index[name] for name in field_names if name in index}
        missing = [name for name in field_names if name not in resolved]
        if missing:
            raise CliError(f"field not found: {', '.join(missing)}")
        return resolved

    @staticmethod
    def _should_refresh(cache: MetaCache) -> bool:
        if cache.invalidated:
            return True
        if not cache.updated_at or not cache.ttl_seconds:
            return True
        updated_at = datetime.fromisoformat(cache.updated_at)
        return (datetime.now(UTC) - updated_at).total_seconds() >= cache.ttl_seconds
