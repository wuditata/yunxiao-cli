from __future__ import annotations

from datetime import UTC, datetime

from ..domain.models import ProfileConfig
from ..domain.store import Store
from .context_service import ContextService
from .errors import CliError
from .meta_service import MetaService


class ProfileService:
    def __init__(self, store: Store, meta_service: MetaService, context_service: ContextService | None = None):
        self.store = store
        self.meta_service = meta_service
        self.context_service = context_service

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
        projects = self._parse_projects(project)
        profile = ProfileConfig(
            name=name,
            account=account_name,
            org=org,
            project=projects[0],
            projects=projects,
            created_at=created_at,
        )
        meta = self.meta_service.refresh(profile)
        profile.project_ref = {
            "id": meta.project_info.get("id", profile.project),
            "name": meta.project_info.get("name", ""),
        }
        self.store.save_profile(profile)
        if set_default:
            self.store.set_default_profile(name)
        return profile, meta.to_dict()

    @staticmethod
    def _parse_projects(project_value: str) -> list[str]:
        items = [item.strip() for item in str(project_value).split(",") if item.strip()]
        if not items:
            raise CliError("project is required")
        return items

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
        context = self.context_service.resolve(profile=name) if self.context_service else None
        profile_name = self.store.resolve_profile_name(context.profile if context else name)
        if not profile_name:
            raise CliError("missing profile, use --profile or `yunxiao_cli profile use`")
        try:
            profile = self.store.get_profile(profile_name)
        except FileNotFoundError as error:
            raise CliError(f"profile not found: {profile_name}") from error
        if context and context.project:
            return self._apply_project_override(profile, context.project)
        return profile

    @staticmethod
    def _apply_project_override(profile: ProfileConfig, project_id: str) -> ProfileConfig:
        if project_id not in profile.projects:
            raise CliError(f"project not found in profile: {project_id}")
        return ProfileConfig(
            name=profile.name,
            account=profile.account,
            org=profile.org,
            project=project_id,
            projects=list(profile.projects),
            created_at=profile.created_at,
            project_ref={"id": project_id},
        )
