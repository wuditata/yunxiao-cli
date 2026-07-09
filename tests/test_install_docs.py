import unittest
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallDocsTest(unittest.TestCase):
    def test_skill_index_lists_yunxiao_workflow(self):
        content = (ROOT / "skills" / "SKILLS.md").read_text(encoding="utf-8")
        self.assertIn("yunxiao-workflow", content)

    def test_pyproject_exposes_short_and_legacy_entrypoints(self):
        data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        scripts = data["project"]["scripts"]
        self.assertEqual("yunxiao_cli.main:main", scripts["yunxiao"])
        self.assertEqual("yunxiao_cli.main:main", scripts["yunxiao_cli"])

    def test_skill_doc_references_yunxiao_commands(self):
        skill_dir = ROOT / "skills" / "yunxiao-workflow"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "references" / "commands.md").read_text(encoding="utf-8")
        combined = skill + reference
        self.assertIn("yunxiao workitem", skill)
        self.assertIn("yunxiao workitem attachment upload", combined)
        self.assertIn("--attachment", combined)
        # 摘要 vs 详情契约与参考文件指引必须留在主 SKILL.md
        self.assertIn("摘要", skill)
        self.assertIn("knowledge context", skill)
        self.assertIn("references/commands.md", skill)
        self.assertIn("yunxiao codeup mr comment", skill)

    def test_install_script_mentions_yunxiao_cli_entrypoint(self):
        content = (ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertIn("yunxiao --help", content)
        self.assertIn("yunxiao_cli", content)
        self.assertIn("pip install -e", content)

    def test_windows_install_script_mentions_yunxiao_cli_entrypoint(self):
        content = (ROOT / "install.bat").read_text(encoding="utf-8")
        self.assertIn("yunxiao --help", content)
        self.assertIn("yunxiao_cli", content)
        self.assertIn("pip install -e", content)

    def test_readme_contains_basic_usage(self):
        content = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("yunxiao login token", content)
        self.assertIn("yunxiao profile add", content)
        self.assertIn("yunxiao context init", content)
        self.assertIn("yunxiao workitem attachment upload", content)
        self.assertIn("兼容旧命令 `yunxiao_cli`", content)
        self.assertIn("--attachment", content)

    def test_template_file_exists_and_readme_mentions_it(self):
        template = ROOT / ".yunxiao.json.temple"
        self.assertTrue(template.exists())
        template_content = template.read_text(encoding="utf-8")
        self.assertIn('"profile"', template_content)
        self.assertIn('"assignee"', template_content)
        self.assertIn('"project"', template_content)
        self.assertNotIn('"token"', template_content)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(".yunxiao.json.temple", readme)


if __name__ == "__main__":
    unittest.main()
