import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallDocsTest(unittest.TestCase):
    def test_skill_index_lists_yunxiao_workflow(self):
        content = (ROOT / "skills" / "SKILLS.md").read_text(encoding="utf-8")
        self.assertIn("yunxiao-workflow", content)

    def test_skill_doc_references_yunxiao_cli_commands(self):
        content = (ROOT / "skills" / "yunxiao-workflow" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("yunxiao_cli workitem", content)

    def test_install_script_mentions_yunxiao_cli_entrypoint(self):
        content = (ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertIn("yunxiao_cli", content)
        self.assertIn("pip install -e", content)

    def test_windows_install_script_mentions_yunxiao_cli_entrypoint(self):
        content = (ROOT / "install.bat").read_text(encoding="utf-8")
        self.assertIn("yunxiao_cli", content)
        self.assertIn("pip install -e", content)

    def test_readme_contains_basic_usage(self):
        content = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("yunxiao_cli login token", content)
        self.assertIn("yunxiao_cli profile add", content)


if __name__ == "__main__":
    unittest.main()
