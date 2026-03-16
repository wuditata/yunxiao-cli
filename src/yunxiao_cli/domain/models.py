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
    created_at: str = ""
    project_ref: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProfileConfig":
        return cls(
            name=data["name"],
            account=data["account"],
            org=data["org"],
            project=data["project"],
            created_at=data.get("created_at") or "",
            project_ref=data.get("project_ref") or {},
        )


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
