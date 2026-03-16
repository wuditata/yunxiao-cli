from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..domain.store import Store
from ..infra.projex import ProjexAPI
from .errors import CliError
from .meta_service import MetaService
from .profile_service import ProfileService


class WorkitemService:
    def __init__(self, store: Store, profile_service: ProfileService, meta_service: MetaService):
        self.store = store
        self.profile_service = profile_service
        self.meta_service = meta_service

    def create(
        self,
        *,
        profile_name: str | None,
        category: str,
        subject: str,
        type_value: str | None = None,
        desc: str | None = None,
        desc_file: str | None = None,
        parent: str | None = None,
        assigned_to: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        workitem_type = self.meta_service.resolve_workitem_type(profile, category=category, type_value=type_value)
        description = self._read_description(desc, desc_file)
        assignee = self.meta_service.resolve_member(profile, assigned_to) if assigned_to else None
        api = self._projex_api(profile)
        created = api.create_work_item(
            org_id=profile.org,
            project_id=profile.project,
            subject=subject,
            workitem_type_id=workitem_type["id"],
            description=description,
            parent_id=parent,
            assigned_to=assignee,
        )
        return created, self._profile_dict(profile)

    def get(
        self,
        *,
        profile_name: str | None,
        workitem_id: str,
        with_comments: bool = True,
        with_parent: bool = False,
        with_attachments: bool = True,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile)
        workitem = api.get_work_item(profile.org, workitem_id)
        data: dict[str, Any] = {"workitem": workitem}
        if with_comments:
            data["comments"] = api.list_comments(profile.org, workitem_id)
        if with_parent and workitem.get("parentId"):
            data["parent"] = api.get_work_item(profile.org, str(workitem["parentId"]))
        if with_attachments:
            data["attachments"] = workitem.get("attachments") or []
            data["description_images"] = self._extract_description_images(workitem.get("description"))
        return data, self._profile_dict(profile)

    def mine(
        self,
        *,
        profile_name: str | None,
        category: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        account = self.store.get_account(profile.account)
        user_id = str(account.user.get("id") or account.user.get("userId") or "")
        user_name = str(account.user.get("name") or "")
        categories = self._resolve_categories(category)

        api = self._projex_api(profile)
        items: list[dict[str, Any]] = []
        for category_name in categories:
            items.extend(self._search_all_by_category(api, profile.org, profile.project, category_name))

        mine_items = [item for item in items if self._is_assigned_to_self(item, user_id=user_id, user_name=user_name)]
        return {
            "items": mine_items,
            "total": len(mine_items),
            "filters": {
                "category": category or "all",
                "assignedTo": "self",
            },
        }, self._profile_dict(profile)

    def search(
        self,
        *,
        profile_name: str | None,
        category: str | None = None,
        status: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        resolved_status = None
        if status and category:
            resolved_status = self.meta_service.resolve_status(profile, status, category=category)
        elif status:
            resolved_status = status
        api = self._projex_api(profile)
        result = api.search_workitems(
            org_id=profile.org,
            project_id=profile.project,
            category=category,
            status=resolved_status,
        )
        return {"items": result}, self._profile_dict(profile)

    def update(
        self,
        *,
        profile_name: str | None,
        workitem_id: str,
        subject: str | None = None,
        desc: str | None = None,
        desc_file: str | None = None,
        assigned_to: str | None = None,
        status: str | None = None,
        field_pairs: list[str] | None = None,
        field_json_pairs: list[str] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile)
        current = api.get_work_item(profile.org, workitem_id)
        workitem_type_id = current.get("workitemType", {}).get("id")
        if not workitem_type_id:
            raise CliError("workitem type missing")

        update_data: dict[str, Any] = {}
        if subject is not None:
            update_data["subject"] = subject
        description = self._read_description(desc, desc_file)
        if description is not None:
            update_data["description"] = description
            update_data["formatType"] = "MARKDOWN"
        if assigned_to:
            update_data["assignedTo"] = self.meta_service.resolve_member(profile, assigned_to)
        if status:
            update_data["status"] = self.meta_service.resolve_status(
                profile, status, workitem_type_id=workitem_type_id
            )
        custom_fields = self._parse_custom_fields(profile, workitem_type_id, field_pairs or [], field_json_pairs or [])
        if custom_fields:
            update_data["customFieldValues"] = custom_fields
        result = api.update_work_item(profile.org, workitem_id, update_data)
        return {"workitem": result, "changes": update_data}, self._profile_dict(profile)

    def transition(
        self,
        *,
        profile_name: str | None,
        workitem_id: str,
        target_status: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        return self.update(profile_name=profile_name, workitem_id=workitem_id, status=target_status)

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
        }

    @staticmethod
    def _read_description(desc: str | None, desc_file: str | None) -> str | None:
        if desc_file:
            return Path(desc_file).read_text(encoding="utf-8")
        return desc

    def _parse_custom_fields(
        self,
        profile,
        workitem_type_id: str,
        field_pairs: list[str],
        field_json_pairs: list[str],
    ) -> dict[str, Any]:
        items: dict[str, Any] = {}
        if field_pairs:
            parsed = [self._split_pair(item) for item in field_pairs]
            field_ids = self.meta_service.resolve_field_ids(profile, workitem_type_id, [key for key, _ in parsed])
            for key, value in parsed:
                items[field_ids[key]] = value
        if field_json_pairs:
            parsed = [self._split_pair(item) for item in field_json_pairs]
            field_ids = self.meta_service.resolve_field_ids(profile, workitem_type_id, [key for key, _ in parsed])
            for key, value in parsed:
                items[field_ids[key]] = json.loads(value)
        return items

    @staticmethod
    def _split_pair(value: str) -> tuple[str, str]:
        if "=" not in value:
            raise CliError(f"invalid field pair: {value}")
        key, raw = value.split("=", 1)
        return key, raw

    def _search_all_by_category(
        self,
        api: ProjexAPI,
        org_id: str,
        project_id: str,
        category: str,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        per_page = 100
        for page in range(1, 101):
            batch = api.search_workitems(
                org_id=org_id,
                project_id=project_id,
                category=category,
                page=page,
                per_page=per_page,
            )
            if not batch:
                break
            items.extend(batch)
            if len(batch) < per_page:
                break
        return items

    def _resolve_categories(self, category: str | None) -> list[str]:
        if not category or category.lower() == "all":
            return list(self.meta_service.CATEGORY_CHOICES)
        if category not in self.meta_service.CATEGORY_CHOICES:
            raise CliError(f"invalid category: {category}")
        return [category]

    @staticmethod
    def _is_assigned_to_self(item: dict[str, Any], *, user_id: str, user_name: str) -> bool:
        candidates = WorkitemService._collect_assignee_candidates(item)
        if user_id and user_id in candidates:
            return True
        if user_name and user_name in candidates:
            return True
        return False

    @staticmethod
    def _collect_assignee_candidates(item: dict[str, Any]) -> set[str]:
        values: set[str] = set()

        def collect(value: Any) -> None:
            if value is None:
                return
            if isinstance(value, str):
                if value:
                    values.add(value)
                return
            if isinstance(value, dict):
                for key in ("id", "userId", "name", "nickName", "displayName"):
                    text = value.get(key)
                    if text:
                        values.add(str(text))
                return
            if isinstance(value, list):
                for child in value:
                    collect(child)

        for key in (
            "assignedTo",
            "assignedToId",
            "assignedToUserId",
            "assignedToName",
            "assignee",
            "assignees",
            "assignedUsers",
            "owners",
            "owner",
        ):
            collect(item.get(key))
        return values

    @staticmethod
    def _extract_description_images(description: Any) -> list[str]:
        if not isinstance(description, str) or not description:
            return []
        markdown_images = re.findall(r"!\[[^\]]*]\(([^)]+)\)", description)
        html_images = re.findall(r"<img[^>]+src=[\"']([^\"']+)[\"']", description, flags=re.IGNORECASE)
        urls: list[str] = []
        seen: set[str] = set()
        for url in [*markdown_images, *html_images]:
            if url not in seen:
                seen.add(url)
                urls.append(url)
        return urls
