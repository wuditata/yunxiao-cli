import argparse
import contextlib
import io
import unittest

from tests import run_cli
from yunxiao_cli.cli import HELP_DETAILS, build_parser


def iter_parsers(parser: argparse.ArgumentParser, path: tuple[str, ...] = ()):
    yield path, parser
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, child in action.choices.items():
                yield from iter_parsers(child, (*path, name))


def iter_actions(parser: argparse.ArgumentParser):
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            continue
        yield action


class CliHelpTest(unittest.TestCase):
    def test_help_details_cover_every_command_path(self):
        parser = build_parser()
        for _, command_parser in iter_parsers(parser):
            with self.subTest(command=command_parser.prog):
                self.assertIn(command_parser.prog, HELP_DETAILS)
                self.assertTrue(command_parser.description)
                self.assertTrue(command_parser.epilog)

    def test_every_registered_command_accepts_help(self):
        parser = build_parser()
        for path, command_parser in iter_parsers(parser):
            with self.subTest(command=command_parser.prog):
                output = io.StringIO()
                with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as exit_context:
                    parser.parse_args([*path, "--help"])
                self.assertEqual(0, exit_context.exception.code)
                help_output = output.getvalue()
                self.assertIn(f"usage: {command_parser.prog}", help_output)
                self.assertIn("显示帮助并退出", help_output)
                self.assertIn("示例:", help_output)

    def test_every_argument_has_help_text(self):
        parser = build_parser()
        for _, command_parser in iter_parsers(parser):
            for action in iter_actions(command_parser):
                if isinstance(action, argparse._HelpAction):
                    continue
                with self.subTest(command=command_parser.prog, argument=action.dest):
                    self.assertTrue(action.help)

    def test_bare_group_command_prints_current_level_help(self):
        code, output = run_cli(["workitem"])

        self.assertEqual(0, code)
        self.assertIn("usage: yunxiao workitem", output)
        self.assertIn("attachment       管理工作项附件", output)
        self.assertNotIn("profile             管理 profile", output)

    def test_root_help_exposes_thoughts_not_knowledge(self):
        code, output = run_cli(["--help"])

        self.assertEqual(0, code)
        self.assertIn("thoughts         云效 Thoughts 知识库文档操作", output)
        self.assertNotIn("knowledge", output)

    def test_bare_nested_group_command_prints_current_level_help(self):
        code, output = run_cli(["codeup", "repo"])

        self.assertEqual(0, code)
        self.assertIn("usage: yunxiao codeup repo", output)
        self.assertIn("Codeup 仓库操作", output)
        self.assertIn("yunxiao codeup repo list --search api", output)

    def test_leaf_command_help_contains_examples_and_parameters(self):
        code, output = run_cli(["codeup", "mr", "create", "--help"])

        self.assertEqual(0, code)
        self.assertIn("--title", output)
        self.assertIn("--source", output)
        self.assertIn("--target", output)
        self.assertIn("示例:", output)
        self.assertIn("yunxiao codeup mr create <repo_id>", output)

    def test_knowledge_command_is_not_registered(self):
        code, output = run_cli(["knowledge", "--help"])

        self.assertEqual(2, code)
        self.assertIn("invalid choice: 'knowledge'", output)


if __name__ == "__main__":
    unittest.main()
