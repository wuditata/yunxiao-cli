from __future__ import annotations

from typing import Any

from .meta_service import MetaService


class WorkitemSummaryBuilder:
    _PHASE_TODO = "todo"
    _PHASE_IN_PROGRESS = "in_progress"
    _PHASE_DONE = "done"
    _PHASE_CANCELED = "canceled"
    _PHASE_UNKNOWN = "unknown"

    _DONE_KEYWORDS = (
        "已完成",
        "完成",
        "已关闭",
        "关闭",
        "已修复",
        "已解决",
        "已发布",
        "done",
        "completed",
        "closed",
        "fixed",
        "resolved",
        "tested",
        "released",
        "published",
    )
    _CANCELED_KEYWORDS = (
        "已取消",
        "取消",
        "作废",
        "已拒绝",
        "暂不修复",
        "canceled",
        "cancelled",
        "aborted",
        "rejected",
        "won't fix",
    )
    _TODO_KEYWORDS = (
        "待处理",
        "待修复",
        "待评审",
        "待开始",
        "待确认",
        "待测试",
        "待发布",
        "需求创建",
        "已选择",
        "就绪",
        "重新打开",
        "todo",
        "to do",
        "open",
        "new",
        "backlog",
        "pending",
        "created",
        "ready",
        "selected",
        "reopened",
    )

    def __init__(self, meta_service: MetaService):
        self.meta_service = meta_service

    def build_payload(
        self,
        *,
        profile,
        projects: list[str],
        items: list[dict[str, Any]],
        filters: dict[str, Any],
    ) -> dict[str, Any]:
        project_meta = self._load_project_meta(profile, projects)
        summary_items = [self._build_item(item, project_meta=project_meta) for item in items]
        return {
            "items": summary_items,
            "total": len(summary_items),
            "summary": self._build_summary(summary_items),
            "filters": filters,
        }

    def _load_project_meta(self, profile, projects: list[str]) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for project_id in projects:
            meta = self.meta_service.get_meta_for_project(profile, project_id)
            result[project_id] = {
                "project": meta.project_info,
                "types": {str(item.get("id")): item for item in meta.workitem_types if item.get("id")},
                "statuses": meta.statuses,
            }
        return result

    def _build_item(self, item: dict[str, Any], *, project_meta: dict[str, dict[str, Any]]) -> dict[str, Any]:
        project_id = self._project_id(item)
        meta = project_meta.get(project_id) if project_id else None
        workitem_type = self._workitem_type(item, meta=meta)
        status = self._status(item, meta=meta, workitem_type_id=workitem_type["id"])
        assignee = self._assignee(item)
        return {
            "id": self._text(item.get("id")),
            "serial": self._text(item.get("serialNumber")),
            "subject": self._text(item.get("subject")),
            "category": workitem_type["category"],
            "type": workitem_type["name"],
            "projectId": project_id,
            "project": self._project_name(item, meta=meta),
            "statusId": status["id"],
            "status": status["name"],
            "statusPhase": status["phase"],
            "assigneeId": assignee["id"],
            "assignee": assignee["name"],
            "parentId": self._text(item.get("parentId")),
            "updatedAt": self._updated_at(item),
        }

    def _workitem_type(self, item: dict[str, Any], *, meta: dict[str, Any] | None) -> dict[str, str | None]:
        workitem_type = item.get("workitemType") if isinstance(item.get("workitemType"), dict) else {}
        workitem_type_id = self._text(workitem_type.get("id") or item.get("workitemTypeId"))
        meta_type = meta["types"].get(workitem_type_id) if meta and workitem_type_id else None
        category = self._text(item.get("categoryId")) or self._text(workitem_type.get("categoryId"))
        if not meta_type and meta and category:
            meta_type = self._match_type_by_category(meta=meta, category=category)
            if meta_type and not workitem_type_id:
                workitem_type_id = self._text(meta_type.get("id"))
        if not category and meta_type:
            category = self._text(meta_type.get("categoryId"))
        name = (
            self._text(workitem_type.get("displayName"))
            or self._text(workitem_type.get("name"))
            or self._text(workitem_type.get("nameEn"))
        )
        if not name and meta_type:
            name = self._text(meta_type.get("displayName")) or self._text(meta_type.get("name"))
        return {"id": workitem_type_id, "category": category, "name": name}

    def _status(
        self,
        item: dict[str, Any],
        *,
        meta: dict[str, Any] | None,
        workitem_type_id: str | None,
    ) -> dict[str, str | None]:
        status = item.get("status") if isinstance(item.get("status"), dict) else {}
        status_id = self._text(status.get("id") or item.get("statusId"))
        matched = self._match_status(meta=meta, workitem_type_id=workitem_type_id, status_id=status_id, raw_status=status)
        status_name = (
            self._text(status.get("displayName"))
            or self._text(status.get("name"))
            or self._text(status.get("nameEn"))
        )
        if not status_name and matched:
            status_name = (
                self._text(matched.get("displayName"))
                or self._text(matched.get("name"))
                or self._text(matched.get("nameEn"))
            )
        return {
            "id": status_id,
            "name": status_name,
            "phase": self._status_phase(raw_status=status, matched_status=matched),
        }

    def _match_status(
        self,
        *,
        meta: dict[str, Any] | None,
        workitem_type_id: str | None,
        status_id: str | None,
        raw_status: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not meta or not workitem_type_id:
            return None
        candidates = meta["statuses"].get(workitem_type_id) or []
        raw_names = {
            self._text(raw_status.get("id")),
            self._text(raw_status.get("displayName")),
            self._text(raw_status.get("name")),
            self._text(raw_status.get("nameEn")),
            status_id,
        }
        raw_names.discard(None)
        for candidate in candidates:
            candidate_names = {
                self._text(candidate.get("id")),
                self._text(candidate.get("displayName")),
                self._text(candidate.get("name")),
                self._text(candidate.get("nameEn")),
            }
            candidate_names.discard(None)
            if raw_names & candidate_names:
                return candidate
        return None

    @staticmethod
    def _match_type_by_category(meta: dict[str, Any], category: str) -> dict[str, Any] | None:
        fallback: dict[str, Any] | None = None
        for item in meta["types"].values():
            if item.get("categoryId") != category:
                continue
            if fallback is None:
                fallback = item
            if item.get("defaultType"):
                return item
        return fallback

    def _status_phase(self, *, raw_status: dict[str, Any], matched_status: dict[str, Any] | None) -> str:
        explicit = self._phase_from_explicit_fields(raw_status, matched_status)
        if explicit:
            return explicit
        texts = self._status_texts(raw_status, matched_status)
        for text in texts:
            lowered = text.lower()
            if any(keyword in lowered for keyword in self._DONE_KEYWORDS):
                return self._PHASE_DONE
            if any(keyword in lowered for keyword in self._CANCELED_KEYWORDS):
                return self._PHASE_CANCELED
            if any(keyword in lowered for keyword in self._TODO_KEYWORDS):
                return self._PHASE_TODO
        if texts:
            return self._PHASE_IN_PROGRESS
        return self._PHASE_UNKNOWN

    def _phase_from_explicit_fields(
        self,
        raw_status: dict[str, Any],
        matched_status: dict[str, Any] | None,
    ) -> str | None:
        for source in (matched_status or {}, raw_status):
            for key in ("stateCategory", "stateType", "statusCategory", "category", "type"):
                value = self._text(source.get(key))
                if not value:
                    continue
                mapped = self._map_explicit_phase(value)
                if mapped:
                    return mapped
        return None

    def _map_explicit_phase(self, value: str) -> str | None:
        normalized = value.strip().lower().replace(" ", "").replace("-", "").replace("_", "")
        if normalized in {"done", "completed", "closed", "fixed", "resolved"}:
            return self._PHASE_DONE
        if normalized in {"canceled", "cancelled", "aborted"}:
            return self._PHASE_CANCELED
        if normalized in {"todo", "new", "open", "backlog", "pending", "ready"}:
            return self._PHASE_TODO
        if normalized in {"doing", "inprogress", "active", "wip", "processing"}:
            return self._PHASE_IN_PROGRESS
        return None

    def _status_texts(self, raw_status: dict[str, Any], matched_status: dict[str, Any] | None) -> list[str]:
        values: list[str] = []
        for source in (matched_status or {}, raw_status):
            for key in ("displayName", "name", "nameEn"):
                text = self._text(source.get(key))
                if text and text not in values:
                    values.append(text)
        return values

    def _project_name(self, item: dict[str, Any], *, meta: dict[str, Any] | None) -> str | None:
        space = item.get("space") if isinstance(item.get("space"), dict) else {}
        name = self._text(space.get("name"))
        if name:
            return name
        if meta:
            return self._text(meta["project"].get("name"))
        return None

    def _project_id(self, item: dict[str, Any]) -> str | None:
        space = item.get("space") if isinstance(item.get("space"), dict) else {}
        return self._text(space.get("id") or item.get("spaceId"))

    def _assignee(self, item: dict[str, Any]) -> dict[str, str | None]:
        for key in ("assignedTo", "assignee", "owner"):
            value = item.get(key)
            if isinstance(value, dict):
                return {
                    "id": self._text(value.get("userId") or value.get("id")),
                    "name": self._text(
                        value.get("name")
                        or value.get("nickName")
                        or value.get("displayName")
                    ),
                }
            if isinstance(value, str) and value:
                return {"id": value, "name": value}
        return {
            "id": self._text(item.get("assignedToId") or item.get("assignedToUserId")),
            "name": self._text(item.get("assignedToName")),
        }

    def _updated_at(self, item: dict[str, Any]) -> str | None:
        for key in ("gmtModified", "updateStatusAt", "gmtCreate"):
            value = self._text(item.get(key))
            if value:
                return value
        return None

    def _build_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total": len(items),
            "byCategory": self._count(items, "category"),
            "byStatusPhase": self._count(items, "statusPhase"),
            "byProject": self._count(items, "project"),
        }

    @staticmethod
    def _count(items: list[dict[str, Any]], key: str) -> dict[str, int]:
        result: dict[str, int] = {}
        for item in items:
            value = item.get(key)
            if not value:
                continue
            text = str(value)
            result[text] = result.get(text, 0) + 1
        return result

    @staticmethod
    def _text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
