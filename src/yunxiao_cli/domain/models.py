from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class AccountConfig:
    name: str
    token: str
    user: dict[str, Any] = field(default_factory=dict)
    organizations: list[dict[str, Any]] = field(default_factory=list)
    cache_invalidated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AccountConfig":
        return cls(
            name=data["name"],
            token=data["token"],
            user=data.get("user") or {},
            organizations=data.get("organizations") or [],
            cache_invalidated=bool(data.get("cache_invalidated", False)),
        )


@dataclass(slots=True)
class ProfileConfig:
    name: str
    account: str
    org: str
    project: str
    projects: list[str] = field(default_factory=list)
    created_at: str = ""
    project_ref: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = self._normalize_projects(project=self.project, projects=self.projects)
        self.projects = normalized
        self.project = normalized[0]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProfileConfig":
        project = data.get("project")
        projects = data.get("projects") or []
        if isinstance(project, list):
            projects = project if not projects else projects
            project = project[0] if project else ""
        elif not project and projects:
            project = projects[0]
        return cls(
            name=data["name"],
            account=data["account"],
            org=data["org"],
            project=project,
            projects=projects,
            created_at=data.get("created_at") or "",
            project_ref=data.get("project_ref") or {},
        )

    @staticmethod
    def _normalize_projects(project: str | list[str] | None, projects: list[str] | str | None) -> list[str]:
        values: list[str] = []

        def append(raw: Any) -> None:
            text = str(raw).strip()
            if not text:
                return
            for item in text.split(","):
                value = item.strip()
                if value and value not in values:
                    values.append(value)

        if isinstance(project, list):
            for item in project:
                append(item)
        else:
            append(project)
        if isinstance(projects, list):
            for item in projects:
                append(item)
        elif projects:
            append(projects)

        if not values:
            raise ValueError("project is required")
        return values


@dataclass(slots=True)
class MetaCache:
    account: str
    org: str
    project: str
    project_info: dict[str, Any] = field(default_factory=dict)
    workitem_types: list[dict[str, Any]] = field(default_factory=list)
    statuses: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    fields: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    members: list[dict[str, Any]] = field(default_factory=list)
    updated_at: str = ""
    ttl_seconds: int = 0
    invalidated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MetaCache":
        return cls(
            account=data["account"],
            org=data["org"],
            project=data["project"],
            project_info=data.get("project_info") or {},
            workitem_types=data.get("workitem_types") or [],
            statuses=data.get("statuses") or {},
            fields=data.get("fields") or {},
            members=data.get("members") or [],
            updated_at=data.get("updated_at") or "",
            ttl_seconds=int(data.get("ttl_seconds", 0)),
            invalidated=bool(data.get("invalidated", False)),
        )

    def get_type(self, workitem_type_id: str) -> dict[str, Any] | None:
        for item in self.workitem_types:
            if item.get("id") == workitem_type_id:
                return item
        return None


@dataclass(slots=True)
class ProjectContextConfig:
    profile: str
    assignee: str
    project: str
    token: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = {
            "profile": self.profile,
            "assignee": self.assignee,
            "project": self.project,
        }
        if self.token:
            data["token"] = self.token
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectContextConfig":
        profile = str(data.get("profile") or "").strip()
        assignee = str(data.get("assignee") or "").strip()
        project = str(data.get("project") or "").strip()
        if not profile:
            raise ValueError("profile is required")
        if not assignee:
            raise ValueError("assignee is required")
        if not project:
            raise ValueError("project is required")
        return cls(
            profile=profile,
            assignee=assignee,
            project=project,
            token=str(data.get("token") or "").strip(),
        )
