from __future__ import annotations

import json
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
        projects = self.get(f"/oapi/v1/projex/organizations/{org_id}/projects")
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
            payload["parentIdentifier"] = parent_id
        if assigned_to is not None:
            payload["assignedTo"] = assigned_to
        return self.post(f"/oapi/v1/projex/organizations/{org_id}/workitems", data=payload)

    def update_work_item(self, org_id: str, workitem_id: str, update_fields: dict[str, Any]) -> dict:
        payload = dict(update_fields)
        custom_fields = payload.pop("customFieldValues", None)
        if isinstance(custom_fields, dict):
            payload.update(custom_fields)
        return self.put(f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}", data=payload)

    def search_workitems(
        self,
        *,
        org_id: str,
        project_id: str,
        category: str | None = None,
        status: str | None = None,
        subject: str | None = None,
        parent_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[dict]:
        filters = []
        if category:
            filters.append(self._search_condition("category", category, "list", "list"))
        if status:
            filters.append(self._search_condition("status", status, "status", "list"))
        if subject:
            filters.append(self._search_condition("subject", subject, "string", "input"))
        if parent_id:
            filters.append(self._search_condition("parentId", parent_id, "string", "input"))
        result = self.post(
            f"/oapi/v1/projex/organizations/{org_id}/workitems:search",
            data={
                "category": category,
                "spaceId": project_id,
                "page": page,
                "perPage": per_page,
                "conditions": json.dumps({"conditionGroups": [filters] if filters else []}, ensure_ascii=False),
            },
        )
        if isinstance(result, list):
            return result
        return result.get("result") or result.get("items") or []

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
