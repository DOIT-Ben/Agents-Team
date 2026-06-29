import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.managed_block import ManagedBlockError, merge_agents_block  # noqa: E402


class ManagedBlockTests(unittest.TestCase):
    def test_adds_managed_block_without_changing_existing_text(self):
        existing = "# Project rules\n\nKeep this exact line.\n"
        merged = merge_agents_block(existing, "Use Goal issues.", "1.0.0")
        self.assertTrue(merged.startswith(existing))
        self.assertIn("<!-- TEAM-COLLABORATION:START protocol=1.0.0 -->", merged)
        self.assertIn("Use Goal issues.", merged)

    def test_replaces_only_existing_managed_block(self):
        existing = (
            "before\n"
            "<!-- TEAM-COLLABORATION:START protocol=1.0.0 -->\nold\n"
            "<!-- TEAM-COLLABORATION:END -->\n"
            "after\n"
        )
        merged = merge_agents_block(existing, "new", "1.1.0")
        self.assertEqual(
            merged,
            "before\n<!-- TEAM-COLLABORATION:START protocol=1.1.0 -->\nnew\n"
            "<!-- TEAM-COLLABORATION:END -->\nafter\n",
        )

    def test_rejects_unbalanced_markers(self):
        with self.assertRaises(ManagedBlockError):
            merge_agents_block("<!-- TEAM-COLLABORATION:START protocol=1.0.0 -->\nbroken", "new", "1.0.0")

    def test_repeated_merge_is_idempotent(self):
        first = merge_agents_block("base\n", "rules", "1.0.0")
        second = merge_agents_block(first, "rules", "1.0.0")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
