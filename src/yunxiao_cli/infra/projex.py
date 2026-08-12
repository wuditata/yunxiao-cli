from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseAPI


class ProjexAPI(BaseAPI):
    def get_current_user(self) -> dict:
        return self.get("/oapi/v1/platform/user")

    def list_organizations(self) -> list[dict]:
        organizations = self.get("/oapi/v1/platform/organizations")
        if isinstance(organizations, list):
            return organizations
        return organizations.get("organizations") or organizations.get("items") or []

    def list_organization_members(self, org_id: str, page: int = 1, per_page: int = 100) -> list[dict]:
        members = self.get(
            f"/oapi/v1/platform/organizations/{org_id}/members",
            params={"page": page, "perPage": per_page},
        )
        if isinstance(members, list):
            return members
        return members.get("result") or members.get("items") or []

    def get_project(self, org_id: str, project_id: str) -> dict:
        return self.get(f"/oapi/v1/projex/organizations/{org_id}/projects/{project_id}")

    def list_projects(self, org_id: str) -> list[dict]:
        projects = self.post(f"/oapi/v1/projex/organizations/{org_id}/projects:search", data={})
        if isinstance(projects, list):
            return projects
        return projects.get("result") or projects.get("items") or []

    def get_work_item_types(self, org_id: str, project_id: str, *, category: str | None = None) -> list[dict]:
        items = self.get(
            f"/oapi/v1/projex/organizations/{org_id}/projects/{project_id}/workitemTypes",
            params={"category": category} if category else None,
        )
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []

    def get_work_item_type_fields(self, org_id: str, project_id: str, workitem_type_id: str) -> list[dict]:
        items = self.get(
            f"/oapi/v1/projex/organizations/{org_id}/projects/{project_id}/workitemTypes/{workitem_type_id}/fields"
        )
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []

    def get_work_item_workflow_statuses(self, org_id: str, project_id: str, workitem_type_id: str) -> list[dict]:
        workflow = self.get(
            f"/oapi/v1/projex/organizations/{org_id}/projects/{project_id}/workitemTypes/{workitem_type_id}/workflows"
        )
        if isinstance(workflow, list):
            return workflow
        return workflow.get("statuses") or workflow.get("states") or workflow.get("result", {}).get("statuses") or []

    def get_work_item(self, org_id: str, workitem_id: str) -> dict:
        return self.get(f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}")

    def list_workitem_attachments(self, org_id: str, workitem_id: str) -> list[dict]:
        items = self.get(f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}/attachments")
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []

    def get_workitem_file(self, org_id: str, workitem_id: str, file_id: str) -> dict:
        item = self.get(f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}/files/{file_id}")
        if isinstance(item, dict):
            return item.get("result") or item
        return {}

    def upload_workitem_attachment(
        self,
        org_id: str,
        workitem_id: str,
        *,
        file_path: str,
        operator_id: str | None = None,
    ) -> dict:
        path = Path(file_path)
        form_data: dict[str, Any] = {}
        if operator_id:
            form_data["operatorId"] = operator_id
        with path.open("rb") as handle:
            response = self.post_multipart(
                f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}/attachments",
                data=form_data or None,
                files={"file": (path.name, handle)},
            )
        if isinstance(response, dict):
            return response.get("result") or response
        return {"result": response}

    def create_work_item(
        self,
        *,
        org_id: str,
        project_id: str,
        subject: str,
        workitem_type_id: str,
        description: str | None = None,
        parent_id: str | None = None,
        assigned_to: str | None = None,
        custom_field_values: dict[str, Any] | None = None,
    ) -> dict:
        payload: dict[str, Any] = {
            "spaceId": project_id,
            "subject": subject,
            "workitemTypeId": workitem_type_id,
        }
        if description is not None:
            payload["description"] = description
            payload["formatType"] = "MARKDOWN"
        if parent_id is not None:
            payload["parentId"] = parent_id
        if assigned_to is not None:
            payload["assignedTo"] = assigned_to
        if isinstance(custom_field_values, dict) and custom_field_values:
            payload["customFieldValues"] = custom_field_values
        return self.post(f"/oapi/v1/projex/organizations/{org_id}/workitems", data=payload)

    def update_work_item(self, org_id: str, workitem_id: str, update_fields: dict[str, Any]) -> dict:
        payload = dict(update_fields)
        custom_fields = payload.pop("customFieldValues", None)
        if isinstance(custom_fields, dict):
            payload.update(custom_fields)
        return self.put(f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}", data=payload)

    def list_effort_records(self, org_id: str, workitem_id: str) -> list[dict]:
        items = self.get(f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}/effortRecords")
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []

    def create_effort_record(
        self,
        org_id: str,
        workitem_id: str,
        *,
        actual_time: float,
        gmt_start: str,
        gmt_end: str,
        description: str | None = None,
        work_type: str | None = None,
    ) -> dict:
        payload: dict[str, Any] = {
            "actualTime": actual_time,
            "gmtStart": gmt_start,
            "gmtEnd": gmt_end,
        }
        if description is not None:
            payload["description"] = description
        if work_type is not None:
            payload["workType"] = work_type
        return self.post(
            f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}/effortRecords",
            data=payload,
        )

    def list_estimated_efforts(self, org_id: str, workitem_id: str) -> list[dict]:
        items = self.get(f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}/estimatedEfforts")
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []

    def create_estimated_effort(
        self,
        org_id: str,
        workitem_id: str,
        *,
        owner: str,
        spent_time: float,
        description: str | None = None,
        operator_id: str | None = None,
        work_type: str | None = None,
    ) -> dict:
        payload: dict[str, Any] = {
            "owner": owner,
            "spentTime": spent_time,
        }
        if description is not None:
            payload["description"] = description
        if operator_id is not None:
            payload["operatorId"] = operator_id
        if work_type is not None:
            payload["workType"] = work_type
        return self.post(
            f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}/estimatedEfforts",
            data=payload,
        )

    def update_estimated_effort(
        self,
        org_id: str,
        workitem_id: str,
        effort_id: str,
        *,
        owner: str,
        spent_time: float,
        description: str | None = None,
        operator_id: str | None = None,
        work_type: str | None = None,
    ) -> dict:
        payload: dict[str, Any] = {
            "owner": owner,
            "spentTime": spent_time,
        }
        if description is not None:
            payload["description"] = description
        if operator_id is not None:
            payload["operatorId"] = operator_id
        if work_type is not None:
            payload["workType"] = work_type
        return self.put(
            f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}/estimatedEfforts/{effort_id}",
            data=payload,
        )

    def search_workitems(
        self,
        *,
        org_id: str,
        project_id: str,
        category: str | None = None,
        status: str | None = None,
        subject: str | None = None,
        parent_id: str | None = None,
        assigned_to: str | None = None,
        sprint: str | None = None,
        tag: str | None = None,
        priority: str | None = None,
        subject_description: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        order_by: str = "gmtCreate",
        sort: str = "desc",
        page: int = 1,
        per_page: int = 20,
    ) -> list[dict]:
        items, _ = self.search_workitems_page(
            org_id=org_id,
            project_id=project_id,
            category=category,
            status=status,
            subject=subject,
            parent_id=parent_id,
            assigned_to=assigned_to,
            sprint=sprint,
            tag=tag,
            priority=priority,
            subject_description=subject_description,
            created_after=created_after,
            created_before=created_before,
            updated_after=updated_after,
            updated_before=updated_before,
            order_by=order_by,
            sort=sort,
            page=page,
            per_page=per_page,
        )
        return items

    def search_workitems_page(
        self,
        *,
        org_id: str,
        project_id: str,
        category: str | None = None,
        status: str | None = None,
        subject: str | None = None,
        parent_id: str | None = None,
        assigned_to: str | None = None,
        sprint: str | None = None,
        tag: str | None = None,
        priority: str | None = None,
        subject_description: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        order_by: str = "gmtCreate",
        sort: str = "desc",
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict], dict[str, int | None]]:
        filters = []
        if category:
            filters.append(self._search_condition("category", category, "list", "list"))
        if status:
            filters.append(self._search_condition("status", status, "status", "list"))
        if subject:
            filters.append(self._search_condition("subject", subject, "string", "input"))
        if parent_id:
            filters.append(self._search_condition("parentId", parent_id, "string", "input"))
        if assigned_to:
            filters.append(self._search_condition("assignedTo", assigned_to, "user", "list"))
        if sprint:
            filters.append(self._search_condition("sprint", sprint, "sprint", "list"))
        if tag:
            filters.append(self._search_multi_condition("tag", tag, "tag", "multiList"))
        if priority:
            filters.append(self._search_condition("priority", priority, "option", "list"))
        if subject_description:
            filters.append(self._search_condition("subject-description", subject_description, "string", "input"))
        if created_after:
            to_value = self._date_time_bound(created_before, end=True)
            filters.append(self._search_range_condition("gmtCreate", self._date_time_bound(created_after), to_value, "dateTime"))
        if updated_after:
            to_value = self._date_time_bound(updated_before, end=True)
            filters.append(self._search_range_condition("gmtModified", self._date_time_bound(updated_after), to_value, "dateTime"))
        filters.append(self._search_multi_condition("logicalStatus", "NORMAL,ARCHIVED", "string", "list"))
        response = self._request_response(
            "POST",
            f"/oapi/v1/projex/organizations/{org_id}/workitems:search",
            data={
                "category": category,
                "spaceId": project_id,
                "orderBy": order_by,
                "sort": sort,
                "page": page,
                "perPage": per_page,
                "conditions": json.dumps({"conditionGroups": [filters] if filters else []}, ensure_ascii=False),
            },
        )
        result = self._parse_response(response)
        if isinstance(result, list):
            items = result
        else:
            items = result.get("result") or result.get("items") or []
        headers = getattr(response, "headers", {})
        pagination = {
            "page": self._header_int(headers, "x-page") or page,
            "per_page": self._header_int(headers, "x-per-page") or per_page,
            "total_pages": self._header_int(headers, "x-total-pages"),
            "total": self._header_int(headers, "x-total"),
            "next_page": self._header_int(headers, "x-next-page"),
        }
        return items, pagination

    def list_sprints(
        self,
        org_id: str,
        project_id: str,
        *,
        status: str | None = None,
        page: int = 1,
        per_page: int = 100,
    ) -> list[dict]:
        params: dict[str, Any] = {"page": page, "perPage": per_page}
        if status:
            params["status"] = status
        items = self.get(
            f"/oapi/v1/projex/organizations/{org_id}/projects/{project_id}/sprints",
            params=params,
        )
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []

    def get_sprint(self, org_id: str, project_id: str, sprint_id: str) -> dict:
        return self.get(f"/oapi/v1/projex/organizations/{org_id}/projects/{project_id}/sprints/{sprint_id}")

    def list_versions(
        self,
        org_id: str,
        project_id: str,
        *,
        status: str | None = None,
        name: str | None = None,
        page: int = 1,
        per_page: int = 100,
    ) -> list[dict]:
        params: dict[str, Any] = {"page": page, "perPage": per_page}
        if status:
            params["status"] = status
        if name:
            params["name"] = name
        items = self.get(
            f"/oapi/v1/projex/organizations/{org_id}/projects/{project_id}/versions",
            params=params,
        )
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []

    def list_comments(self, org_id: str, workitem_id: str, page: int = 1, per_page: int = 20) -> list[dict]:
        items = self.get(
            f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}/comments",
            params={"page": page, "perPage": per_page},
        )
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []

    def create_comment(self, org_id: str, workitem_id: str, content: str) -> dict:
        return self.post(
            f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}/comments",
            data={"content": content},
        )

    def create_relation_record(
        self,
        org_id: str,
        workitem_id: str,
        relation_type: str,
        related_workitem_id: str,
    ) -> dict:
        return self.post(
            f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}/relationRecords",
            data={"relationType": relation_type, "workitemId": related_workitem_id},
        )

    @staticmethod
    def _search_condition(field_identifier: str, value: str, class_name: str, format_type: str) -> dict[str, Any]:
        return {
            "fieldIdentifier": field_identifier,
            "operator": "CONTAINS",
            "value": [value],
            "toValue": None,
            "className": class_name,
            "format": format_type,
        }

    @staticmethod
    def _search_multi_condition(field_identifier: str, value: str, class_name: str, format_type: str) -> dict[str, Any]:
        values = [v.strip() for v in value.split(",")]
        return {
            "fieldIdentifier": field_identifier,
            "operator": "CONTAINS",
            "value": values,
            "toValue": None,
            "className": class_name,
            "format": format_type,
        }

    @staticmethod
    def _search_range_condition(field_identifier: str, from_value: str, to_value: str | None, class_name: str) -> dict[str, Any]:
        return {
            "fieldIdentifier": field_identifier,
            "operator": "BETWEEN",
            "value": [from_value],
            "toValue": to_value,
            "className": class_name,
            "format": "input",
        }

    @staticmethod
    def _date_time_bound(value: str | None, *, end: bool = False) -> str | None:
        if value is None or "T" in value or " " in value:
            return value
        return f"{value} {'23:59:59' if end else '00:00:00'}"

    @staticmethod
    def _header_int(headers: Any, name: str) -> int | None:
        value = headers.get(name) if hasattr(headers, "get") else None
        return int(value) if value not in (None, "") else None
