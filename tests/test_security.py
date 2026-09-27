from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from microloan_checker.security import detect_prompt_injection  # noqa: E402


class PromptInjectionGuardrailTests(unittest.TestCase):
    def test_fixed_attack_and_benign_suite(self):
        path = PROJECT_ROOT / "data" / "security" / "prompt_injection_cases.jsonl"
        records = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(records), 12)
        for record in records:
            with self.subTest(case_id=record["case_id"]):
                detected = bool(detect_prompt_injection(record["text"]))
                self.assertEqual(detected, record["expected_detection"])

    def test_empty_input_is_not_an_attack(self):
        self.assertEqual(detect_prompt_injection(None), ())
        self.assertEqual(detect_prompt_injection(""), ())


if __name__ == "__main__":
    unittest.main()
