import tempfile
import unittest
from pathlib import Path

from yunxiao_cli.domain.models import AccountConfig, ProfileConfig
from yunxiao_cli.domain.store import Store


class StoreTest(unittest.TestCase):
    def test_store_supports_multiple_accounts_and_profiles(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = Store(root=Path(temp_dir))
            store.save_account(
                AccountConfig(
                    name="pm-a",
                    token="token-a",
                    user={"id": "user-1"},
                    organizations=[{"id": "123", "name": "FOXHIS"}],
                )
            )
            store.save_account(
                AccountConfig(
                    name="dev-a",
                    token="token-b",
                    user={"id": "user-2"},
                    organizations=[{"id": "456", "name": "LAB"}],
                )
            )
            store.save_profile(
                ProfileConfig(
                    name="pm-dev",
                    account="pm-a",
                    org="123",
                    project="456",
                )
            )
            store.save_profile(
                ProfileConfig(
                    name="dev-test",
                    account="dev-a",
                    org="456",
                    project="789",
                )
            )
            store.set_default_profile("pm-dev")

            self.assertEqual("456", store.get_profile("pm-dev").project)
            self.assertEqual("token-b", store.get_account("dev-a").token)
            self.assertEqual("pm-dev", store.get_default_profile_name())

    def test_profile_config_supports_multiple_projects(self):
        profile = ProfileConfig.from_dict(
            {
                "name": "pm-dev",
                "account": "pm-a",
                "org": "123",
                "project": "456,457",
            }
        )

        self.assertEqual("456", profile.project)
        self.assertEqual(["456", "457"], profile.projects)
        self.assertEqual(["456", "457"], profile.to_dict()["projects"])

    def test_profile_config_supports_project_list_value(self):
        profile = ProfileConfig.from_dict(
            {
                "name": "pm-dev",
                "account": "pm-a",
                "org": "123",
                "project": ["456", "457"],
            }
        )

        self.assertEqual("456", profile.project)
        self.assertEqual(["456", "457"], profile.projects)


if __name__ == "__main__":
    unittest.main()
