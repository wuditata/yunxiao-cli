from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ..domain.models import ProjectContextConfig
from ..domain.store import Store
from .auth_service import AuthService
from .errors import CliError


@dataclass(slots=True)
class ResolvedContext:
    profile: str | None = None
    assignee: str | None = None
    project: str | None = None
    token: str | None = None
    path: Path | None = None


class ContextService:
    FILE_NAME = ".yunxiao.json"

    def __init__(self, store: Store):
        self.store = store

    def init_project_context(
        self,
        *,
        profile: str,
        assignee: str,
        project: str,
        token: str | None = None,
        cwd: Path | None = None,
    ) -> tuple[ProjectContextConfig, Path]:
        config = ProjectContextConfig(
            profile=profile.strip(),
            assignee=assignee.strip(),
            project=project.strip(),
            token=(token or "").strip(),
        )
        path = (cwd or Path.cwd()) / self.FILE_NAME
        self._write_config(path, config)
        return config, path

    def resolve(
        self,
        *,
        profile: str | None = None,
        assignee: str | None = None,
        project: str | None = None,
        cwd: Path | None = None,
    ) -> ResolvedContext:
        config, path = self.load_project_context(cwd=cwd)
        use_project_context = bool(config) and (not profile or profile == config.profile)
        return ResolvedContext(
            profile=profile or (config.profile if use_project_context and config else None),
            assignee=assignee or (config.assignee if use_project_context and config else None),
            project=project or (config.project if use_project_context and config else None),
            token=config.token if use_project_context and config and config.token else None,
            path=path if use_project_context else None,
        )

    def load_project_context(self, *, cwd: Path | None = None) -> tuple[ProjectContextConfig | None, Path | None]:
        path = self.find_project_context(cwd=cwd)
        if path is None:
            return None, None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise CliError(f"invalid project context file: {path}") from error
        try:
            return ProjectContextConfig.from_dict(payload), path
        except ValueError as error:
            raise CliError(f"invalid project context file: {path}: {error}") from error

    def find_project_context(self, *, cwd: Path | None = None) -> Path | None:
        current = (cwd or Path.cwd()).resolve()
        for directory in (current, *current.parents):
            path = directory / self.FILE_NAME
            if path.exists():
                return path
        return None

    def refresh_login_if_needed(self, *, profile: str | None, token: str | None) -> None:
        if not profile or not token:
            return
        try:
            profile_config = self.store.get_profile(profile)
        except FileNotFoundError as error:
            raise CliError(f"profile not found: {profile}") from error
        AuthService(store=self.store).login_token(token=token, account_name=profile_config.account)

    @staticmethod
    def _write_config(path: Path, config: ProjectContextConfig) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(config.to_dict(), ensure_ascii=False, indent=2) + "\n"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(content)
            temp_path = Path(handle.name)
        os.replace(temp_path, path)
