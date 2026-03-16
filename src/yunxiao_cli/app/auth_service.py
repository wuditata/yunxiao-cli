from __future__ import annotations

from ..domain.models import AccountConfig
from ..domain.store import Store
from ..infra.config import CliConfig
from ..infra.projex import ProjexAPI
from ..infra.base import YunxiaoAPIError


class AuthService:
    def __init__(self, store: Store | None = None):
        self.store = store or Store(root=CliConfig.data_root())

    def login_token(
        self,
        *,
        token: str,
        account_name: str,
    ) -> tuple[AccountConfig, list[dict], dict[str, list[dict]], list[str]]:
        api = ProjexAPI(token=token)
        user = api.get_current_user()
        organizations = api.list_organizations()

        self.store.invalidate_account_cache(account_name)
        account = AccountConfig(
            name=account_name,
            token=token,
            user=user,
            organizations=organizations,
            cache_invalidated=True,
        )
        self.store.save_account(account)
        projects_by_org: dict[str, list[dict]] = {}
        warnings: list[str] = []
        for org in organizations:
            org_id = str(org.get("id") or "")
            if not org_id:
                warnings.append("skip organization without id")
                continue
            try:
                projects_by_org[org_id] = api.list_projects(org_id)
            except YunxiaoAPIError as error:
                projects_by_org[org_id] = []
                warnings.append(f"list projects failed for org {org_id}: {error}")
        return account, organizations, projects_by_org, warnings
