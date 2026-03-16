from __future__ import annotations

from datetime import UTC, datetime

from ..domain.models import ProfileConfig
from ..domain.store import Store
from .errors import CliError
from .meta_service import MetaService


class ProfileService:
    def __init__(self, store: Store, meta_service: MetaService):
        self.store = store
        self.meta_service = meta_service

    def add_profile(self, name: str, account_name: str, org: str, project: str) -> tuple[ProfileConfig, dict]:
        return self.upsert_profile(name=name, account_name=account_name, org=org, project=project, set_default=False)

    def upsert_profile(
        self,
        *,
        name: str,
        account_name: str,
        org: str,
        project: str,
        set_default: bool = True,
    ) -> tuple[ProfileConfig, dict]:
        self.store.get_account(account_name)
        created_at = datetime.now(UTC).isoformat()
        existing = self.store.find_profile(name)
        if existing is not None and existing.created_at:
            created_at = existing.created_at
        profile = ProfileConfig(name=name, account=account_name, org=org, project=project, created_at=created_at)
        meta = self.meta_service.refresh(profile)
        profile.project_ref = {
            "id": meta.project_info.get("id", project),
            "name": meta.project_info.get("name", ""),
        }
        self.store.save_profile(profile)
        if set_default:
            self.store.set_default_profile(name)
        return profile, meta.to_dict()

    def list_profiles(self) -> list[dict]:
        default_name = self.store.get_default_profile_name()
        return [
            {
                **profile.to_dict(),
                "default": profile.name == default_name,
            }
            for profile in self.store.list_profiles()
        ]

    def show_profile(self, name: str | None = None) -> ProfileConfig:
        return self.get_profile(name)

    def use_profile(self, name: str) -> ProfileConfig:
        profile = self.store.get_profile(name)
        self.store.set_default_profile(name)
        return profile

    def get_profile(self, name: str | None = None) -> ProfileConfig:
        profile_name = self.store.resolve_profile_name(name)
        if not profile_name:
            raise CliError("missing profile, use --profile or `yunxiao_cli profile use`")
        try:
            return self.store.get_profile(profile_name)
        except FileNotFoundError as error:
            raise CliError(f"profile not found: {profile_name}") from error
