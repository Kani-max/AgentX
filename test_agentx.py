
import unittest
from app import evaluate_action


class TestAgentXSafety(unittest.TestCase):

    def check_result(self, action, expected):
        result, reason = evaluate_action(action)
        self.assertEqual(result, expected, f"Action: {action}")

    def test_unsafe_actions(self):
        actions = [
            "delete all",
            "rm -rf",
            "drop table",
            "destroy everything",
            "terminate ec2",
        ]
        for action in actions:
            with self.subTest(action=action):
                self.check_result(action, "UNSAFE")

    def test_actions_needing_clarification(self):
        actions = [
            "password",
            "secret",
            "database_url",
            "send email",
            "transfer money",
        ]
        for action in actions:
            with self.subTest(action=action):
                self.check_result(action, "NEEDS CLARIFICATION")

    def test_safe_to_simulate(self):
        actions = [
            "list my documents",
            "create a new text file",
            "show my project folders",
        ]
        for action in actions:
            with self.subTest(action=action):
                self.check_result(action, "SAFE TO SIMULATE")

    def test_case_insensitivity(self):
        self.check_result("DELETE ALL", "UNSAFE")
        self.check_result("PASSWORD", "NEEDS CLARIFICATION")

    def test_unsafe_rule_has_priority(self):
        self.check_result("delete all passwords", "UNSAFE")

    def test_empty_input(self):
        self.check_result("", "NEEDS CLARIFICATION")

    def test_whitespace_input(self):
        self.check_result("   ", "NEEDS CLARIFICATION")

    def test_additional_unsafe_actions(self):
        """Detect additional destructive action patterns."""
        actions = [
            "truncate table orders",
            "drop database production",
            "delete from users",
            "delete from products",
            "terminate instance i-123456",
            "remove all files",
            "format disk",
        ]
        for action in actions:
            with self.subTest(action=action):
                self.check_result(action, "UNSAFE")

    def test_ordinary_actions_remain_safe_to_simulate(self):
        """Ordinary actions should not match destructive rules."""
        actions = [
            "show product list",
            "list files in my documents",
            "view order history",
            "search for a product",
        ]
        for action in actions:
            with self.subTest(action=action):
                self.check_result(action, "SAFE TO SIMULATE")

    def test_educational_mentions_of_unsafe_terms(self):
        """Educational questions should not automatically be treated as destructive."""
        result, _ = evaluate_action("Explain what DROP TABLE means")
        self.assertEqual(result, "SAFE TO SIMULATE")

    def test_destructive_request_inside_explanation(self):
        """Destructive requests remain flagged even when phrased as explanations."""
        result, _ = evaluate_action("Explain how to delete all files")
        self.assertEqual(result, "UNSAFE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
