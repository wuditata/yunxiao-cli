import tempfile
import unittest
from pathlib import Path

from yunxiao_cli.app.meta_service import MetaService
from yunxiao_cli.app.profile_service import ProfileService
from yunxiao_cli.domain.models import AccountConfig, ProfileConfig
from yunxiao_cli.domain.store import Store


class ProfileServiceTest(unittest.TestCase):
    def test_get_profile_uses_default_first(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = Store(root=Path(temp_dir))
            store.save_account(
                AccountConfig(
                    name="pm-a",
                    token="token-a",
                    user={"id": "user-1"},
                    organizations=[{"id": "org-1", "name": "FOXHIS"}],
                )
            )
            store.save_profile(
                ProfileConfig(name="first-login", account="pm-a", org="org-1", project="proj-1", created_at="2026-01-01T00:00:00+00:00")
            )
            store.save_profile(
                ProfileConfig(name="default", account="pm-a", org="org-1", project="proj-2", created_at="2026-01-02T00:00:00+00:00")
            )
            store.set_default_profile("default")

            profile_service = ProfileService(store=store, meta_service=MetaService(store=store))
            profile = profile_service.get_profile()

        self.assertEqual("default", profile.name)

    def test_get_profile_falls_back_to_first_login_profile(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = Store(root=Path(temp_dir))
            store.save_account(
                AccountConfig(
                    name="pm-a",
                    token="token-a",
                    user={"id": "user-1"},
                    organizations=[{"id": "org-1", "name": "FOXHIS"}],
                )
            )
            store.save_profile(
                ProfileConfig(
                    name="second",
                    account="pm-a",
                    org="org-1",
                    project="proj-2",
                    created_at="2026-01-02T00:00:00+00:00",
                )
            )
            store.save_profile(
                ProfileConfig(
                    name="first-login",
                    account="pm-a",
                    org="org-1",
                    project="proj-1",
                    created_at="2026-01-01T00:00:00+00:00",
                )
            )

            profile_service = ProfileService(store=store, meta_service=MetaService(store=store))
            profile = profile_service.get_profile()

        self.assertEqual("first-login", profile.name)


if __name__ == "__main__":
    unittest.main()
