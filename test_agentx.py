
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
