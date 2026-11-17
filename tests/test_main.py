"""Regression checks for the two program entry paths."""
import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from main import DATA, batch, compare, interactive, mac, make_pattern


class SimulatorTest(unittest.TestCase):
    def test_mac_and_epsilon(self) -> None:
        cross = make_pattern(3, "Cross")
        diagonal = make_pattern(3, "X")
        self.assertEqual(mac(cross, cross), 5)
        self.assertEqual(mac(cross, diagonal), 1)
        self.assertEqual(compare(0.3, 0.1 + 0.2, "A", "B"), "UNDECIDED")
        self.assertEqual(compare(1.0, 1.00000001, "A", "B"), "B")

    def test_interactive_retries_invalid_rows(self) -> None:
        answers = ["0 1", "bad 1 0", "nan 1 0", "0 1 0", "1 1 1",
                   "0 1 0", "1 0 1", "0 1 0", "1 0 1",
                   "1 0 1", "0 1 0", "1 0 1"]
        with patch("builtins.input", side_effect=answers):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(interactive(), 0)
        self.assertEqual(out.getvalue().count("입력 형식 오류"), 3)
        self.assertIn("A 점수: 1\nB 점수: 5\n판정: B", out.getvalue())

    def test_provided_data(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(batch(DATA), 0)
        self.assertIn("총 테스트: 9개\n통과: 9개\n실패: 0개", out.getvalue())

    def test_bad_cases_do_not_block_later_cases(self) -> None:
        data = json.loads(DATA.read_text(encoding="utf-8"))
        cases = {
            "wrong_key": data["patterns"]["size_5_1"],
            "size_5_10": {"input": [[1]], "expected": "+"},
            "size_5_11": {"input": [[0] * 5 for _ in range(5)],
                          "expected": "x"},
            "size_5_12": {"input": make_pattern(5, "Cross"),
                          "expected": "unknown"},
            "size_5_1": data["patterns"]["size_5_1"],
        }
        data["patterns"] = cases
        with patch.object(Path, "read_text", return_value=json.dumps(data)):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(batch(DATA), 1)
        report = out.getvalue()
        for message in ("지원하지 않는 패턴 키", "행 개수 불일치",
                        "허용오차 이내 동점", "지원하지 않는 라벨",
                        "총 테스트: 5개\n통과: 1개\n실패: 4개"):
            self.assertIn(message, report)

    def test_invalid_filter_group_is_local_to_its_size(self) -> None:
        data = json.loads(DATA.read_text(encoding="utf-8"))
        data["filters"]["size_13"]["x"] = [[1]]
        with patch.object(Path, "read_text", return_value=json.dumps(data)):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(batch(DATA), 1)
        self.assertIn("size_13 필터 오류", out.getvalue())
        self.assertIn("총 테스트: 9개\n통과: 6개\n실패: 3개", out.getvalue())

    def test_invalid_json_returns_load_error(self) -> None:
        with patch.object(Path, "read_text", return_value="{"):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(batch(DATA), 2)
        self.assertIn("JSON 로드 오류", out.getvalue())
