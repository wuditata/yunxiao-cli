import unittest

from tests import run_cli


class CliBootstrapTest(unittest.TestCase):
    def test_cli_invokes_root_parser(self):
        code, output = run_cli(["--help"])
        self.assertEqual(0, code)
        self.assertIn("workitem", output)


if __name__ == "__main__":
    unittest.main()
