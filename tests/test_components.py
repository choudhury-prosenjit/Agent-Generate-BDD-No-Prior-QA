"""Unit tests for BDD generator components (no API calls required)."""

import unittest

from src.github_fetcher import parse_github_url
from src.bdd_generator import group_files_by_module, _clean_gherkin


class TestParseGithubUrl(unittest.TestCase):
    """Tests for parse_github_url."""

    def test_standard_url(self):
        owner, repo = parse_github_url("https://github.com/octocat/Hello-World")
        self.assertEqual(owner, "octocat")
        self.assertEqual(repo, "Hello-World")

    def test_url_with_git_suffix(self):
        owner, repo = parse_github_url("https://github.com/octocat/Hello-World.git")
        self.assertEqual(owner, "octocat")
        self.assertEqual(repo, "Hello-World")

    def test_url_with_trailing_slash(self):
        owner, repo = parse_github_url("https://github.com/octocat/Hello-World/")
        self.assertEqual(owner, "octocat")
        self.assertEqual(repo, "Hello-World")

    def test_url_with_http(self):
        owner, repo = parse_github_url("http://github.com/myorg/my-repo")
        self.assertEqual(owner, "myorg")
        self.assertEqual(repo, "my-repo")

    def test_invalid_url_raises(self):
        with self.assertRaises(ValueError):
            parse_github_url("https://gitlab.com/owner/repo")

    def test_empty_url_raises(self):
        with self.assertRaises(ValueError):
            parse_github_url("")

    def test_url_with_extra_path_raises(self):
        # URL with sub-path (e.g. blob/main/...) should not be accepted
        with self.assertRaises(ValueError):
            parse_github_url("https://github.com/owner/repo/blob/main/README.md")


class TestGroupFilesByModule(unittest.TestCase):
    """Tests for group_files_by_module."""

    def test_groups_by_top_level_dir(self):
        files = {
            "auth/login.py": "...",
            "auth/signup.py": "...",
            "api/users.py": "...",
        }
        groups = group_files_by_module(files)
        self.assertIn("auth", groups)
        self.assertIn("api", groups)
        self.assertIn("auth/login.py", groups["auth"])
        self.assertIn("auth/signup.py", groups["auth"])
        self.assertIn("api/users.py", groups["api"])

    def test_root_files_grouped_under_root(self):
        files = {"main.py": "...", "utils.py": "..."}
        groups = group_files_by_module(files)
        self.assertIn("root", groups)
        self.assertIn("main.py", groups["root"])

    def test_mixed_root_and_nested(self):
        files = {
            "app.py": "...",
            "services/email.py": "...",
        }
        groups = group_files_by_module(files)
        self.assertIn("root", groups)
        self.assertIn("services", groups)

    def test_empty_files(self):
        groups = group_files_by_module({})
        self.assertEqual(groups, {})


class TestCleanGherkin(unittest.TestCase):
    """Tests for _clean_gherkin."""

    def test_strips_gherkin_fence(self):
        raw = "```gherkin\nFeature: Login\n```"
        cleaned = _clean_gherkin(raw)
        self.assertTrue(cleaned.startswith("Feature:"))
        self.assertNotIn("```", cleaned)

    def test_strips_plain_fence(self):
        raw = "```\nFeature: Login\n```"
        cleaned = _clean_gherkin(raw)
        self.assertTrue(cleaned.startswith("Feature:"))
        self.assertNotIn("```", cleaned)

    def test_no_fence_unchanged(self):
        raw = "Feature: Login\n  Scenario: Valid login"
        cleaned = _clean_gherkin(raw)
        self.assertEqual(cleaned, raw)

    def test_strips_whitespace(self):
        raw = "  \n  Feature: Login\n  "
        cleaned = _clean_gherkin(raw)
        self.assertTrue(cleaned.startswith("Feature:"))


if __name__ == "__main__":
    unittest.main()
