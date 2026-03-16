from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .models import AccountConfig, MetaCache, ProfileConfig


class Store:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else Path.home() / ".yunxiao"
        self.accounts_dir = self.root / "accounts"
        self.profiles_dir = self.root / "profiles"
        self.cache_dir = self.root / "cache"
        self.default_profile_file = self.root / "default_profile"
        self._ensure_dirs()

    def save_account(self, account: AccountConfig) -> None:
        self._write_json(self.accounts_dir / f"{account.name}.json", account.to_dict())

    def get_account(self, name: str) -> AccountConfig:
        return AccountConfig.from_dict(self._read_json(self.accounts_dir / f"{name}.json"))

    def list_accounts(self) -> list[AccountConfig]:
        return [AccountConfig.from_dict(self._read_json(path)) for path in sorted(self.accounts_dir.glob("*.json"))]

    def save_profile(self, profile: ProfileConfig) -> None:
        self._write_json(self.profiles_dir / f"{profile.name}.json", profile.to_dict())

    def get_profile(self, name: str) -> ProfileConfig:
        return ProfileConfig.from_dict(self._read_json(self.profiles_dir / f"{name}.json"))

    def find_profile(self, name: str) -> ProfileConfig | None:
        path = self.profiles_dir / f"{name}.json"
        if not path.exists():
            return None
        return ProfileConfig.from_dict(self._read_json(path))

    def list_profiles(self) -> list[ProfileConfig]:
        items: list[tuple[tuple[str, str], ProfileConfig]] = []
        for path in self.profiles_dir.glob("*.json"):
            profile = ProfileConfig.from_dict(self._read_json(path))
            created = profile.created_at or ""
            items.append(((created, profile.name), profile))
        items.sort(key=lambda item: item[0])
        return [item[1] for item in items]

    def set_default_profile(self, name: str) -> None:
        self.default_profile_file.parent.mkdir(parents=True, exist_ok=True)
        self._atomic_write(self.default_profile_file, f"{name}\n")

    def get_default_profile_name(self) -> str | None:
        if not self.default_profile_file.exists():
            return None
        value = self.default_profile_file.read_text(encoding="utf-8").strip()
        return value or None

    def resolve_profile_name(self, specified: str | None = None) -> str | None:
        if specified:
            return specified
        default_name = self.get_default_profile_name()
        if default_name and (self.profiles_dir / f"{default_name}.json").exists():
            return default_name
        profiles = self.list_profiles()
        if not profiles:
            return None
        return profiles[0].name

    def save_meta_cache(self, cache: MetaCache) -> None:
        self._write_json(self._meta_path(cache.account, cache.org, cache.project), cache.to_dict())

    def get_meta_cache(self, account: str, org: str, project: str) -> MetaCache:
        return MetaCache.from_dict(self._read_json(self._meta_path(account, org, project)))

    def find_meta_cache(self, account: str, org: str, project: str) -> MetaCache | None:
        path = self._meta_path(account, org, project)
        if not path.exists():
            return None
        return MetaCache.from_dict(self._read_json(path))

    def invalidate_account_cache(self, account: str) -> None:
        account_root = self.cache_dir / account
        if not account_root.exists():
            return
        for path in account_root.glob("**/meta.json"):
            payload = self._read_json(path)
            payload["invalidated"] = True
            self._write_json(path, payload)

    def _meta_path(self, account: str, org: str, project: str) -> Path:
        return self.cache_dir / account / org / project / "meta.json"

    def _ensure_dirs(self) -> None:
        for path in (self.accounts_dir, self.profiles_dir, self.cache_dir):
            path.mkdir(parents=True, exist_ok=True)

    def _read_json(self, path: Path) -> dict:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def _atomic_write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(content)
            temp_path = Path(handle.name)
        os.replace(temp_path, path)
