from __future__ import annotations

from pathlib import Path

from ..domain.store import Store
from ..infra.projex import ProjexAPI
from .errors import CliError
from .profile_service import ProfileService


class AttachmentService:
    def __init__(self, store: Store, profile_service: ProfileService):
        self.store = store
        self.profile_service = profile_service

    def list(self, *, profile_name: str | None, workitem_id: str) -> tuple[dict, dict]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile.account)
        attachments = api.list_workitem_attachments(profile.org, workitem_id)
        return {"attachments": attachments}, self._profile_dict(profile)

    def get(self, *, profile_name: str | None, workitem_id: str, file_id: str) -> tuple[dict, dict]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile.account)
        file_info = api.get_workitem_file(profile.org, workitem_id, file_id)
        return {"file": file_info}, self._profile_dict(profile)

    def upload(
        self,
        *,
        profile_name: str | None,
        workitem_id: str,
        file_path: str,
        operator_id: str | None = None,
    ) -> tuple[dict, dict]:
        profile = self.profile_service.get_profile(profile_name)
        attachment = self.upload_for_profile(
            profile.account,
            profile.org,
            workitem_id=workitem_id,
            file_path=file_path,
            operator_id=operator_id,
        )
        return {"attachment": attachment}, self._profile_dict(profile)

    def validate_paths(self, file_paths: list[str] | None) -> list[str]:
        if not file_paths:
            return []
        normalized: list[str] = []
        for raw_path in file_paths:
            path = Path(raw_path).expanduser()
            if not path.exists():
                raise CliError(f"attachment file not found: {raw_path}")
            if not path.is_file():
                raise CliError(f"attachment path is not a file: {raw_path}")
            normalized.append(str(path.resolve()))
        return normalized

    def upload_for_profile(
        self,
        account_name: str,
        org_id: str,
        *,
        workitem_id: str,
        file_path: str,
        operator_id: str | None = None,
    ) -> dict:
        validated_path = self.validate_paths([file_path])[0]
        api = self._projex_api(account_name)
        return api.upload_workitem_attachment(
            org_id,
            workitem_id,
            file_path=validated_path,
            operator_id=operator_id,
        )

    def _projex_api(self, account_name: str) -> ProjexAPI:
        account = self.store.get_account(account_name)
        return ProjexAPI(token=account.token)

    @staticmethod
    def _profile_dict(profile) -> dict:
        return {
            "name": profile.name,
            "account": profile.account,
            "org": profile.org,
            "project": profile.project,
        }
