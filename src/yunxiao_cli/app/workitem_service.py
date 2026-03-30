from __future__ import annotations

import json
import re
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from ..domain.store import Store
from ..infra.base import YunxiaoAPIError
from ..infra.projex import ProjexAPI
from .attachment_service import AttachmentService
from .errors import CliError
from .meta_service import MetaService
from .profile_service import ProfileService


class WorkitemService:
    def __init__(
        self,
        store: Store,
        profile_service: ProfileService,
        meta_service: MetaService,
        attachment_service: AttachmentService,
    ):
        self.store = store
        self.profile_service = profile_service
        self.meta_service = meta_service
        self.attachment_service = attachment_service

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
        attachments: list[str] | None = None,
        field_pairs: list[str] | None = None,
        field_json_pairs: list[str] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        attachment_paths = self.attachment_service.validate_paths(attachments)
        workitem_type = self.meta_service.resolve_workitem_type(profile, category=category, type_value=type_value)
        description = self._read_description(desc, desc_file)
        assignee = self.meta_service.resolve_member(profile, assigned_to) if assigned_to else None
        api = self._projex_api(profile)
        parent_id = self._resolve_parent_id(api, profile, parent) if parent else None
        custom_fields = self._parse_custom_fields(
            profile,
            workitem_type["id"],
            field_pairs or [],
            field_json_pairs or [],
        )
        created = api.create_work_item(
            org_id=profile.org,
            project_id=profile.project,
            subject=subject,
            workitem_type_id=workitem_type["id"],
            description=description,
            parent_id=parent_id,
            assigned_to=assignee,
            custom_field_values=custom_fields,
        )
        uploaded_attachments: list[dict[str, Any]] = []
        workitem_id = created.get("id")
        if attachment_paths:
            if not workitem_id:
                raise CliError("created workitem id missing, cannot upload attachments", response={"workitem": created})
            for attachment_path in attachment_paths:
                try:
                    uploaded_attachments.append(
                        self.attachment_service.upload_for_profile(
                            profile.account,
                            profile.org,
                            workitem_id=str(workitem_id),
                            file_path=attachment_path,
                        )
                    )
                except (CliError, YunxiaoAPIError) as error:
                    raise CliError(
                        f"attachment upload failed: {attachment_path}",
                        response={
                            "workitem": created,
                            "uploaded_attachments": uploaded_attachments,
                            "failed_attachment": attachment_path,
                            "attachment_error": {
                                "message": str(error),
                                "status_code": getattr(error, "status_code", None),
                                "response": getattr(error, "response", {}),
                            },
                        },
                    ) from error

        result = dict(created)
        if uploaded_attachments:
            result["attachments"] = uploaded_attachments
        return result, self._profile_dict(profile)

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
        project: str | None = None,
        sort: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        account = self.store.get_account(profile.account)
        user_id = str(account.user.get("id") or account.user.get("userId") or "")
        user_name = str(account.user.get("name") or "")
        categories = self._resolve_categories(category)
        projects = self._resolve_projects(profile, project)
        sort_value = self._resolve_sort(sort)

        api = self._projex_api(profile)
        items: list[dict[str, Any]] = []
        for project_id in projects:
            for category_name in categories:
                items.extend(self._search_all_by_category(api, profile.org, project_id, category_name))

        mine_items = [item for item in items if self._is_assigned_to_self(item, user_id=user_id, user_name=user_name)]
        mine_items = self._sort_items(mine_items, sort_value)
        return {
            "items": mine_items,
            "total": len(mine_items),
            "filters": {
                "category": category or "all",
                "assignedTo": "self",
                "projects": projects,
                "sort": sort_value,
            },
        }, self._profile_dict(profile)

    def search(
        self,
        *,
        profile_name: str | None,
        category: str | None = None,
        status: str | None = None,
        project: str | None = None,
        sort: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile)
        categories = self._resolve_categories(category)
        projects = self._resolve_projects(profile, project)
        sort_value = self._resolve_sort(sort)

        items: list[dict[str, Any]] = []
        for project_id in projects:
            for category_name in categories:
                resolved_status = status
                if status:
                    resolved_status = self.meta_service.resolve_status(
                        profile,
                        status,
                        category=category_name,
                        project_id=project_id,
                    )
                items.extend(
                    self._search_all_by_category(
                        api,
                        profile.org,
                        project_id,
                        category_name,
                        status=resolved_status,
                    )
                )

        result = self._sort_items(items, sort_value)
        return {
            "items": result,
            "total": len(result),
            "filters": {
                "category": category or "all",
                "status": status,
                "projects": projects,
                "sort": sort_value,
            },
        }, self._profile_dict(profile)

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
        try:
            result = api.update_work_item(profile.org, workitem_id, update_data)
        except YunxiaoAPIError as error:
            recovered = self._recover_readonly_estimated_effort(
                api=api,
                profile=profile,
                workitem_id=workitem_id,
                workitem_type_id=workitem_type_id,
                current=current,
                update_data=update_data,
                error=error,
            )
            if recovered is None:
                raise
            result, update_data = recovered
        return {"workitem": result, "changes": update_data}, self._profile_dict(profile)

    def transition(
        self,
        *,
        profile_name: str | None,
        workitem_id: str,
        target_status: str,
        field_pairs: list[str] | None = None,
        field_json_pairs: list[str] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        return self.update(
            profile_name=profile_name,
            workitem_id=workitem_id,
            status=target_status,
            field_pairs=field_pairs,
            field_json_pairs=field_json_pairs,
        )

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

    @staticmethod
    def _read_description(desc: str | None, desc_file: str | None) -> str | None:
        if desc_file:
            return Path(desc_file).read_text(encoding="utf-8")
        return WorkitemService._normalize_inline_description(desc)

    @staticmethod
    def _normalize_inline_description(desc: str | None) -> str | None:
        if desc is None:
            return None
        if any(separator in desc for separator in ("\r\n", "\n", "\r")):
            return desc
        return desc.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\r")

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
            parsed = self._parse_field_json_pairs(field_json_pairs)
            field_ids = self.meta_service.resolve_field_ids(profile, workitem_type_id, list(parsed.keys()))
            for key, value in parsed.items():
                items[field_ids[key]] = value
        return items

    def _parse_field_json_pairs(self, values: list[str]) -> dict[str, Any]:
        items: dict[str, Any] = {}
        for raw in values:
            if "=" in raw:
                key, value = self._split_pair(raw)
                try:
                    items[key] = json.loads(value)
                except JSONDecodeError as error:
                    raise CliError(f"invalid field json value: {value}") from error
                continue

            try:
                data = json.loads(raw)
            except JSONDecodeError as error:
                raise CliError(f"invalid field json object: {raw}") from error
            if not isinstance(data, dict):
                raise CliError(f"invalid field json object: {raw}")
            for key, value in data.items():
                items[str(key)] = value
        return items

    def _resolve_parent_id(self, api: ProjexAPI, profile, parent: str) -> str:
        parent_ref = str(parent).strip()
        if not parent_ref:
            raise CliError("parent workitem is empty")

        try:
            item = api.get_work_item(profile.org, parent_ref)
        except YunxiaoAPIError:
            item = self._find_workitem_by_serial_number(api, profile, parent_ref)
        if not item:
            raise CliError(f"parent workitem not found: {parent_ref}")

        workitem_id = item.get("id")
        if not workitem_id:
            raise CliError(f"parent workitem id missing: {parent_ref}")
        return str(workitem_id)

    def _find_workitem_by_serial_number(self, api: ProjexAPI, profile, serial_number: str) -> dict[str, Any] | None:
        for category in self.meta_service.CATEGORY_CHOICES:
            items = self._search_all_by_category(api, profile.org, profile.project, category)
            for item in items:
                if item.get("serialNumber") == serial_number:
                    return item
        return None

    @staticmethod
    def _split_pair(value: str) -> tuple[str, str]:
        if "=" not in value:
            raise CliError(f"invalid field pair: {value}")
        key, raw = value.split("=", 1)
        return key, raw

    def _recover_readonly_estimated_effort(
        self,
        *,
        api: ProjexAPI,
        profile,
        workitem_id: str,
        workitem_type_id: str,
        current: dict[str, Any],
        update_data: dict[str, Any],
        error: YunxiaoAPIError,
    ) -> tuple[dict[str, Any], dict[str, Any]] | None:
        custom_fields = update_data.get("customFieldValues")
        if not isinstance(custom_fields, dict) or not custom_fields:
            return None

        blocked_ids = self._extract_readonly_field_ids(str(error))
        if not blocked_ids:
            return None

        effort_field_ids = self._resolve_estimated_effort_field_ids(profile, workitem_type_id)
        target_ids = [field_id for field_id in blocked_ids if field_id in effort_field_ids and field_id in custom_fields]
        if not target_ids:
            return None

        retry_custom_fields = dict(custom_fields)
        for field_id in target_ids:
            self._upsert_estimated_effort(
                api=api,
                profile=profile,
                workitem_id=workitem_id,
                current=current,
                assigned_to=update_data.get("assignedTo"),
                raw_spent_time=retry_custom_fields[field_id],
            )
            retry_custom_fields.pop(field_id, None)

        retry_update_data = dict(update_data)
        if retry_custom_fields:
            retry_update_data["customFieldValues"] = retry_custom_fields
        else:
            retry_update_data.pop("customFieldValues", None)

        if not retry_update_data:
            return api.get_work_item(profile.org, workitem_id), retry_update_data
        return api.update_work_item(profile.org, workitem_id, retry_update_data), retry_update_data

    def _resolve_estimated_effort_field_ids(self, profile, workitem_type_id: str) -> set[str]:
        fields = self.meta_service.list_fields(profile, workitem_type_id=workitem_type_id)
        result: set[str] = set()
        for field in fields:
            field_id = field.get("id")
            if not field_id:
                continue
            texts = [
                field.get("name"),
                field.get("displayName"),
                field.get("fieldName"),
                field.get("nameEn"),
                field.get("identifier"),
                field.get("fieldIdentifier"),
            ]
            if any(self._is_estimated_effort_field_name(text) for text in texts if text):
                result.add(str(field_id))
        return result

    def _upsert_estimated_effort(
        self,
        *,
        api: ProjexAPI,
        profile,
        workitem_id: str,
        current: dict[str, Any],
        assigned_to: Any,
        raw_spent_time: Any,
    ) -> None:
        spent_time = self._parse_spent_time(raw_spent_time)
        owner = self._resolve_estimated_effort_owner(profile, current=current, assigned_to=assigned_to)
        estimated_efforts = api.list_estimated_efforts(profile.org, workitem_id)
        existing_id = self._find_estimated_effort_id_by_owner(estimated_efforts, owner)

        if existing_id:
            api.update_estimated_effort(
                profile.org,
                workitem_id,
                existing_id,
                owner=owner,
                spent_time=spent_time,
            )
            return

        api.create_estimated_effort(
            profile.org,
            workitem_id,
            owner=owner,
            spent_time=spent_time,
        )

    def _resolve_estimated_effort_owner(self, profile, *, current: dict[str, Any], assigned_to: Any) -> str:
        owner = self._extract_user_id(assigned_to)
        if not owner:
            owner = self._extract_user_id(current.get("assignedTo"))
        if owner:
            return owner

        account = self.store.get_account(profile.account)
        fallback = account.user.get("userId") or account.user.get("id")
        if fallback:
            return str(fallback)
        raise CliError("estimated effort owner is missing")

    @staticmethod
    def _extract_user_id(value: Any) -> str | None:
        if not value:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            user_id = value.get("userId") or value.get("id")
            if user_id:
                return str(user_id)
        return None

    @staticmethod
    def _find_estimated_effort_id_by_owner(items: list[dict[str, Any]], owner: str) -> str | None:
        for item in items:
            item_owner = WorkitemService._extract_user_id(item.get("owner"))
            if item_owner and item_owner == owner:
                effort_id = item.get("id")
                if effort_id:
                    return str(effort_id)
        if not items:
            return None
        effort_id = items[0].get("id")
        if effort_id:
            return str(effort_id)
        return None

    @staticmethod
    def _extract_readonly_field_ids(message: str) -> set[str]:
        return set(re.findall(r"fieldId\s*[:：]\s*([A-Za-z0-9_-]+)", message))

    @staticmethod
    def _is_estimated_effort_field_name(value: Any) -> bool:
        text = str(value).strip().lower().replace(" ", "")
        return (
            "预计工时" in text
            or "估算工时" in text
            or "spenttime" in text
            or "estimatedeffort" in text
        )

    @staticmethod
    def _parse_spent_time(value: Any) -> float:
        try:
            spent_time = float(value)
        except (TypeError, ValueError) as error:
            raise CliError(f"invalid estimated effort value: {value}") from error
        if spent_time <= 0:
            raise CliError("estimated effort must be greater than 0")
        return spent_time

    def _search_all_by_category(
        self,
        api: ProjexAPI,
        org_id: str,
        project_id: str,
        category: str,
        *,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        per_page = 100
        for page in range(1, 101):
            batch = api.search_workitems(
                org_id=org_id,
                project_id=project_id,
                category=category,
                status=status,
                page=page,
                per_page=per_page,
            )
            if not batch:
                break
            items.extend(batch)
        return items

    def _resolve_categories(self, category: str | None) -> list[str]:
        if not category or category.lower() == "all":
            return list(self.meta_service.CATEGORY_CHOICES)
        if category not in self.meta_service.CATEGORY_CHOICES:
            raise CliError(f"invalid category: {category}")
        return [category]

    @staticmethod
    def _resolve_projects(profile, project: str | None) -> list[str]:
        if not project:
            return list(profile.projects)
        values = [item.strip() for item in project.split(",") if item.strip()]
        if not values:
            raise CliError("project filter is empty")
        missing = [item for item in values if item not in profile.projects]
        if missing:
            raise CliError(f"project not found in profile: {', '.join(missing)}")
        return values

    @staticmethod
    def _resolve_sort(sort: str | None) -> str:
        if not sort:
            return "time"
        if sort != "time":
            raise CliError(f"invalid sort: {sort}")
        return sort

    @staticmethod
    def _sort_items(items: list[dict[str, Any]], sort: str) -> list[dict[str, Any]]:
        if sort == "time":
            return sorted(items, key=WorkitemService._sort_time_value, reverse=True)
        return items

    @staticmethod
    def _sort_time_value(item: dict[str, Any]) -> float:
        for key in ("gmtModified", "updateStatusAt", "gmtCreate"):
            value = item.get(key)
            if value is None:
                continue
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
                except ValueError:
                    continue
        return 0.0

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
