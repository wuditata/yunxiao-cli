from __future__ import annotations

from ..domain.store import Store
from ..infra.projex import ProjexAPI
from .profile_service import ProfileService


class CommentService:
    def __init__(self, store: Store, profile_service: ProfileService):
        self.store = store
        self.profile_service = profile_service

    def add(self, *, profile_name: str | None, workitem_id: str, content: str) -> tuple[dict, dict]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile.account)
        comment = api.create_comment(profile.org, workitem_id, content)
        return {"comment": comment}, self._profile_dict(profile)

    def list(self, *, profile_name: str | None, workitem_id: str) -> tuple[dict, dict]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._projex_api(profile.account)
        comments = api.list_comments(profile.org, workitem_id)
        return {"comments": comments}, self._profile_dict(profile)

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
