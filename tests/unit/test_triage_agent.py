import json
import unittest
from mycoder.triage_agent import triage_issues


class TestTriageAgent(unittest.TestCase):
    def setUp(self):
        self.available_labels = [
            "kind/bug",
            "kind/enhancement",
            "documentation",
            "wontfix",
            "priority/high",
            "priority/low",
            "area/android",
            "area/docker",
        ]

    def test_crash_is_high_priority_bug(self):
        issues = [
            {
                "number": 1,
                "title": "App crashes on startup",
                "body": "NullPointerException in MainActivity when launching.",
            }
        ]
        results = triage_issues(issues, self.available_labels)
        self.assertEqual(len(results), 1)
        self.assertIn("kind/bug", results[0]["labels_to_set"])
        self.assertIn("priority/high", results[0]["labels_to_set"])
        self.assertIn("area/android", results[0]["labels_to_set"])

    def test_ugly_logs_is_low_priority_enhancement(self):
        issues = [
            {
                "number": 2,
                "title": "Logs are ugly",
                "body": "Please beautify the log output, style is bad.",
            }
        ]
        results = triage_issues(issues, self.available_labels)
        self.assertEqual(len(results), 1)
        self.assertIn("priority/low", results[0]["labels_to_set"])

    def test_feature_request(self):
        issues = [
            {
                "number": 3,
                "title": "Add new voice feature",
                "body": "We need to implement voice dictation support.",
            }
        ]
        results = triage_issues(issues, self.available_labels)
        self.assertIn("kind/enhancement", results[0]["labels_to_set"])

    def test_wontfix(self):
        issues = [
            {
                "number": 4,
                "title": "Run on toaster",
                "body": "Make it run on my toaster, hardware constraint is impossible to overcome.",
            }
        ]
        results = triage_issues(issues, self.available_labels)
        self.assertIn("wontfix", results[0]["labels_to_set"])

    def test_goat_principle_ignore_noise(self):
        issues = [
            {
                "number": 5,
                "title": "Just saying hello",
                "body": "Hi there",
            }
        ]
        results = triage_issues(issues, self.available_labels)
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
