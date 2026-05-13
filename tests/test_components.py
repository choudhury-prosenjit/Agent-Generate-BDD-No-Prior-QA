"""Unit tests for BDD generator components (no API calls required)."""

import unittest
from unittest.mock import patch, MagicMock
import base64

import requests

from src.github_fetcher import parse_github_url, fetch_repository_code
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


class TestFetchRepositoryCode(unittest.TestCase):
    """Tests for fetch_repository_code error paths (GitHub API mocked)."""

    def _make_tree_response(self, items):
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {"tree": items, "truncated": False}
        mock.raise_for_status.return_value = None
        return mock

    def _make_content_response(self, text):
        encoded = base64.b64encode(text.encode()).decode()
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {"content": encoded + "\n"}
        mock.raise_for_status.return_value = None
        return mock

    def _make_404_response(self):
        mock = MagicMock()
        mock.status_code = 404
        mock.raise_for_status.side_effect = requests.HTTPError("404")
        return mock

    @patch("src.github_fetcher.requests.get")
    def test_not_found_raises_value_error(self, mock_get):
        mock_get.return_value = self._make_404_response()
        with self.assertRaises(ValueError) as ctx:
            fetch_repository_code("https://github.com/a/b", "main")
        self.assertIn("not found", str(ctx.exception).lower())

    @patch("src.github_fetcher.requests.get")
    def test_no_matching_files_returns_empty(self, mock_get):
        # Tree contains only a README (unsupported extension)
        tree_resp = self._make_tree_response([
            {"type": "blob", "path": "README.md", "sha": "abc", "size": 100},
        ])
        mock_get.return_value = tree_resp
        result = fetch_repository_code("https://github.com/a/b", "main")
        self.assertEqual(result, {})

    @patch("src.github_fetcher.requests.get")
    def test_fetches_python_file(self, mock_get):
        tree_resp = self._make_tree_response([
            {"type": "blob", "path": "main.py", "sha": "abc", "size": 200},
        ])
        content_resp = self._make_content_response("print('hello')")
        mock_get.side_effect = [tree_resp, content_resp]
        result = fetch_repository_code("https://github.com/a/b", "main")
        self.assertIn("main.py", result)
        self.assertEqual(result["main.py"], "print('hello')")

    @patch("src.github_fetcher.requests.get")
    def test_skips_file_when_content_fetch_fails(self, mock_get):
        tree_resp = self._make_tree_response([
            {"type": "blob", "path": "main.py", "sha": "abc", "size": 200},
        ])
        error_resp = MagicMock()
        error_resp.raise_for_status.side_effect = requests.HTTPError("500")
        mock_get.side_effect = [tree_resp, error_resp]
        result = fetch_repository_code("https://github.com/a/b", "main")
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
