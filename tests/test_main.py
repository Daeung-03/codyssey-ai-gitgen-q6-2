"""Tests for Git input, output validation, and the COPA request shape."""

from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class GitInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.run_git("init", "-q")
        (self.root / "tracked.txt").write_text("before\n", encoding="utf-8")
        self.run_git("add", "tracked.txt")
        self.run_git(
            "-c", "user.name=Test", "-c", "user.email=test@example.com",
            "commit", "-qm", "initial",
        )

    def run_git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def test_no_changes(self) -> None:
        self.assertIsNone(main.collect_changes(self.root, safe_mode=False))

    def test_staged_unstaged_and_untracked_changes(self) -> None:
        tracked = self.root / "tracked.txt"
        tracked.write_text("staged\n", encoding="utf-8")
        self.run_git("add", "tracked.txt")
        tracked.write_text("unstaged\n", encoding="utf-8")
        (self.root / "new.txt").write_text("new file\n", encoding="utf-8")

        changes = main.collect_changes(self.root, safe_mode=False)

        self.assertIsNotNone(changes)
        assert changes is not None
        self.assertIn("tracked.txt", changes.files)
        self.assertIn("new.txt", changes.files)
        self.assertIn("[Staged changes]", changes.diff)
        self.assertIn("[Unstaged changes]", changes.diff)
        self.assertIn("[Untracked file]", changes.diff)

    def test_safe_mode_masks_secrets_and_excludes_env_file(self) -> None:
        (self.root / "notes.txt").write_text(
            "OPENAI_API_KEY=supersecret\nemail=person@example.com\n", encoding="utf-8"
        )
        (self.root / ".env").write_text("password=hunter2\n", encoding="utf-8")

        changes = main.collect_changes(self.root, safe_mode=True)

        self.assertIsNotNone(changes)
        assert changes is not None
        self.assertIn("[MASKED]", changes.diff)
        self.assertIn("[MASKED_EMAIL]", changes.diff)
        self.assertNotIn("supersecret", changes.diff)
        self.assertNotIn("person@example.com", changes.diff)
        self.assertNotIn("hunter2", changes.diff)
        self.assertNotIn(".env", changes.files)
        self.assertTrue(main.is_sensitive_path(".env"))


class OutputAndAPITests(unittest.TestCase):
    def test_copa_chat_completions_request(self) -> None:
        api_response = {"choices": [{"message": {"content": '{"title":"feat: add CLI"}'}}]}
        with patch("main.urllib.request.urlopen") as urlopen:
            urlopen.return_value = io.BytesIO(json.dumps(api_response).encode("utf-8"))
            result = main.call_api(
                "virtual-key", "gpt-5-mini", 1.0, 2048,
                [{"role": "user", "content": "test"}],
            )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, main.API_URL)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Authorization"), "Bearer virtual-key")
        self.assertEqual(payload["model"], "gpt-5-mini")
        self.assertEqual(payload["max_completion_tokens"], 2048)
        self.assertNotIn("temperature", payload)
        self.assertEqual(result, '{"title":"feat: add CLI"}')

    def test_commit_title_is_limited(self) -> None:
        output = main.render_result("commit", json.dumps({"title": "x" * 100, "body": ["change"]}))
        self.assertLessEqual(len(output.splitlines()[1]), 72)
        self.assertIn("- change", output)

    def test_pr_requires_a_bullet_in_every_section(self) -> None:
        with self.assertRaises(main.CLIError):
            main.render_result(
                "pr",
                json.dumps({"title": "PR", "why": ["reason"], "what": [], "how_to_test": ["run"]}),
            )

    def test_pr_sections_are_rendered(self) -> None:
        output = main.render_result(
            "pr",
            json.dumps({
                "title": "PR", "why": ["reason"], "what": ["change"],
                "how_to_test": ["run command"],
            }),
        )
        for heading in ("## Why", "## What", "## How to Test"):
            self.assertIn(heading, output)


if __name__ == "__main__":
    unittest.main()
