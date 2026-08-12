from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

from .infra.base import YunxiaoAPIError
from .infra.projex import ProjexAPI


class YunxiaoClientError(Exception):
    pass


class AuthenticationError(YunxiaoClientError):
    pass


class PermissionDeniedError(YunxiaoClientError):
    pass


class RateLimitError(YunxiaoClientError):
    pass


class NotFoundError(YunxiaoClientError):
    pass


class RemoteAPIError(YunxiaoClientError):
    pass


@dataclass(frozen=True, slots=True)
class User:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class Organization:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class Project:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class Session:
    user: User
    organization: Organization
    projects: tuple[Project, ...]


@dataclass(frozen=True, slots=True)
class Workitem:
    id: str
    project_id: str
    serial_number: str = ""
    subject: str = ""
    category: str = ""
    status: str = ""
    updated_at: str | int | float | None = None
    fields: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class Comment:
    id: str
    content: str
    created_at: str | int | float | None = None
    author: str = ""


@dataclass(frozen=True, slots=True)
class Attachment:
    id: str
    name: str
    url: str = ""
    size: int | None = None


@dataclass(frozen=True, slots=True)
class WorkitemDetail:
    workitem: Workitem
    comments: tuple[Comment, ...]
    attachments: tuple[Attachment, ...]


@dataclass(frozen=True, slots=True)
class WorkitemPage:
    items: tuple[Workitem, ...]
    page: int
    per_page: int
    total: int | None
    total_pages: int | None
    next_page: int | None


T = TypeVar("T")


class YunxiaoClient:
    CATEGORIES = ("Req", "Task", "Bug")

    def __init__(self, *, token: str, organization_id: str):
        if not token.strip():
            raise AuthenticationError("token is required")
        if not organization_id.strip():
            raise ValueError("organization_id is required")
        self.organization_id = organization_id.strip()
        self._api = ProjexAPI(token=token.strip())

    def validate(self) -> Session:
        user = self._call(self._api.get_current_user)
        organizations = self._call(self._api.list_organizations)
        organization = next(
            (item for item in organizations if self._id(item) == self.organization_id),
            None,
        )
        if organization is None:
            raise PermissionDeniedError(f"organization is not visible: {self.organization_id}")
        projects = self.list_projects()
        return Session(
            user=User(id=self._id(user), name=self._name(user)),
            organization=Organization(id=self._id(organization), name=self._name(organization)),
            projects=projects,
        )

    def list_projects(self) -> tuple[Project, ...]:
        items = self._call(self._api.list_projects, self.organization_id)
        return tuple(Project(id=self._id(item), name=self._name(item)) for item in items)

    def resolve_workitem(self, project_id: str, serial: str) -> Workitem:
        serial = serial.strip()
        if not project_id.strip() or not serial:
            raise ValueError("project_id and serial are required")
        for category in self.CATEGORIES:
            page = 1
            while page <= 100:
                items, pagination = self._call(
                    self._api.search_workitems_page,
                    org_id=self.organization_id,
                    project_id=project_id,
                    category=category,
                    page=page,
                    per_page=100,
                )
                for item in items:
                    if str(item.get("serialNumber") or "") == serial:
                        return self._workitem(item, project_id)
                next_page = pagination.get("next_page")
                if next_page is None and len(items) < 100:
                    break
                page = int(next_page) if next_page is not None else page + 1
        raise NotFoundError(f"workitem not found: {project_id}/{serial}")

    def get_workitem(self, workitem_id: str) -> WorkitemDetail:
        workitem_id = workitem_id.strip()
        if not workitem_id:
            raise ValueError("workitem_id is required")
        item = self._call(self._api.get_work_item, self.organization_id, workitem_id)
        comments = self._list_comments(workitem_id)
        attachments = self._call(self._api.list_workitem_attachments, self.organization_id, workitem_id)
        return WorkitemDetail(
            workitem=self._workitem(item),
            comments=tuple(self._comment(comment) for comment in comments),
            attachments=tuple(self._attachment(attachment) for attachment in attachments),
        )

    def query_workitems(
        self,
        project_id: str,
        *,
        category: str = "Task",
        updated_after: str | None = None,
        updated_before: str | None = None,
        page: int = 1,
        per_page: int = 100,
    ) -> WorkitemPage:
        if not project_id.strip():
            raise ValueError("project_id is required")
        if category not in self.CATEGORIES:
            raise ValueError(f"invalid category: {category}")
        if not 1 <= per_page <= 100:
            raise ValueError("per_page must be between 1 and 100")
        if page < 1:
            raise ValueError("page must be positive")
        items, pagination = self._call(
            self._api.search_workitems_page,
            org_id=self.organization_id,
            project_id=project_id,
            category=category,
            updated_after=updated_after,
            updated_before=updated_before,
            order_by="gmtModified",
            sort="asc",
            page=page,
            per_page=per_page,
        )
        normalized = sorted(
            (self._workitem(item, project_id) for item in items),
            key=lambda item: (self._sort_value(item.updated_at), item.id),
        )
        next_page = pagination.get("next_page")
        total_pages = pagination.get("total_pages")
        if next_page is not None and total_pages is not None and next_page > total_pages:
            next_page = None
        if next_page is None and len(items) == per_page and (total_pages is None or page < total_pages):
            next_page = page + 1
        return WorkitemPage(
            items=tuple(normalized),
            page=int(pagination.get("page") or page),
            per_page=int(pagination.get("per_page") or per_page),
            total=pagination.get("total"),
            total_pages=total_pages,
            next_page=int(next_page) if next_page is not None else None,
        )

    def _list_comments(self, workitem_id: str) -> list[dict[str, Any]]:
        comments: list[dict[str, Any]] = []
        for page in range(1, 101):
            batch = self._call(self._api.list_comments, self.organization_id, workitem_id, page, 100)
            comments.extend(batch)
            if len(batch) < 100:
                break
        return comments

    def _call(self, operation: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        try:
            return operation(*args, **kwargs)
        except YunxiaoAPIError as error:
            error_type = {
                401: AuthenticationError,
                403: PermissionDeniedError,
                404: NotFoundError,
                429: RateLimitError,
            }.get(error.status_code, RemoteAPIError)
            raise error_type(str(error)) from error

    @classmethod
    def _workitem(cls, item: dict[str, Any], project_id: str = "") -> Workitem:
        return Workitem(
            id=cls._id(item),
            project_id=str(item.get("spaceId") or item.get("projectId") or project_id),
            serial_number=str(item.get("serialNumber") or ""),
            subject=str(item.get("subject") or ""),
            category=cls._display(item.get("category") or item.get("categoryId")),
            status=cls._display(item.get("status")),
            updated_at=item.get("gmtModified") or item.get("updatedAt"),
            fields=dict(item),
        )

    @classmethod
    def _comment(cls, item: dict[str, Any]) -> Comment:
        author = item.get("creator") or item.get("author") or item.get("user")
        return Comment(
            id=cls._id(item),
            content=str(item.get("content") or ""),
            created_at=item.get("gmtCreate") or item.get("createdAt"),
            author=cls._display(author),
        )

    @classmethod
    def _attachment(cls, item: dict[str, Any]) -> Attachment:
        raw_size = item.get("size") or item.get("fileSize")
        return Attachment(
            id=cls._id(item),
            name=str(item.get("name") or item.get("fileName") or ""),
            url=str(item.get("url") or item.get("downloadUrl") or ""),
            size=int(raw_size) if raw_size is not None else None,
        )

    @staticmethod
    def _id(item: dict[str, Any]) -> str:
        return str(item.get("id") or item.get("identifier") or "")

    @staticmethod
    def _name(item: dict[str, Any]) -> str:
        return str(item.get("name") or item.get("displayName") or "")

    @staticmethod
    def _display(value: Any) -> str:
        if isinstance(value, dict):
            return str(value.get("displayName") or value.get("name") or value.get("id") or "")
        return str(value or "")

    @staticmethod
    def _sort_value(value: str | int | float | None) -> tuple[int, str]:
        if isinstance(value, (int, float)):
            return 0, f"{float(value):020.6f}"
        return 1, str(value or "")
