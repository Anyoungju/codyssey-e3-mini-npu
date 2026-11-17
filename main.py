"""Mini NPU simulator for the Codyssey E3 mission."""
import argparse
import json
import math
import re
from pathlib import Path
from time import perf_counter_ns
from typing import Dict, List, Tuple

Matrix = List[List[float]]
SIZES = (5, 13, 25)
EPSILON = 1e-9
REPEATS = 1000
DATA = Path(__file__).with_name("data.json")


def number(value: object) -> float:
    """Return a finite number from a JSON numeric value."""
    if type(value) not in (int, float):
        raise ValueError("숫자가 아닌 값")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError("표현 범위를 벗어난 숫자") from exc
    if not math.isfinite(result):
        raise ValueError("유한한 숫자만 허용됩니다")
    return result


def matrix(value: object, size: int) -> Matrix:
    """Validate dimensions and convert all cells."""
    if not isinstance(value, list) or len(value) != size:
        raise ValueError(f"행 개수 불일치: {size}행 필요")
    for index, row in enumerate(value, 1):
        if not isinstance(row, list) or len(row) != size:
            raise ValueError(f"{index}행 열 개수 불일치: {size}열 필요")
    return [[number(cell) for cell in row] for row in value]


def make_pattern(size: int, label: str) -> Matrix:
    """Generate a centered cross or diagonal X."""
    if size < 1 or size % 2 == 0 or label not in ("Cross", "X"):
        raise ValueError("양의 홀수 크기와 Cross 또는 X가 필요합니다")
    center = size // 2
    return [
        [
            float(row == center or col == center) if label == "Cross"
            else float(row == col or row + col == size - 1)
            for col in range(size)
        ]
        for row in range(size)
    ]


def normalize(label: object) -> str:
    """Translate filter keys and expected labels to a shared vocabulary."""
    if isinstance(label, str):
        key = label.strip().casefold()
        if key in ("+", "cross"):
            return "Cross"
        if key == "x":
            return "X"
    raise ValueError(f"지원하지 않는 라벨: {label!r}")


def mac(pattern: Matrix, kernel: Matrix) -> float:
    """Multiply corresponding cells and accumulate on validated matrices."""
    score = 0.0
    for row, weights in zip(pattern, kernel):
        for cell, weight in zip(row, weights):
            score += cell * weight
    return score


def compare(a: float, b: float, label_a: str, label_b: str) -> str:
    """Use absolute epsilon and reject nonfinite accumulated scores."""
    if not math.isfinite(a) or not math.isfinite(b):
        raise ValueError("MAC 누적 결과가 유한하지 않습니다")
    if abs(a - b) < EPSILON:
        return "UNDECIDED"
    return label_a if a > b else label_b


def benchmark(pattern: Matrix, kernel: Matrix) -> float:
    """Measure one MAC call in milliseconds without I/O or validation."""
    mac(pattern, kernel)
    start = perf_counter_ns()
    for _ in range(REPEATS):
        mac(pattern, kernel)
    return (perf_counter_ns() - start) / REPEATS / 1_000_000


def performance(
    samples: Dict[int, Tuple[Matrix, Matrix]],
) -> Dict[int, float]:
    """Print mean duration and cell pairs per call."""
    print(f"\n성능 분석 (평균/{REPEATS}회, 필터 1개 기준)")
    print("크기        평균 시간(ms)     연산 횟수(N²)")
    times = {}
    for size, (pattern, kernel) in sorted(samples.items()):
        times[size] = benchmark(pattern, kernel)
        print(f"{size:2}×{size:<2}      {times[size]:12.6f}     {size * size:6}")
    return times


def read_matrix(name: str) -> Matrix:
    """Collect exactly three valid rows, retrying the current row."""
    print(f"{name} (3줄 입력, 공백 구분)")
    rows = []
    while len(rows) < 3:
        parts = input(f"{len(rows) + 1}/3행: ").split()
        try:
            if len(parts) != 3:
                raise ValueError
            rows.append([number(float(part)) for part in parts])
        except ValueError:
            print("입력 형식 오류: 각 줄에 유한한 숫자 3개를 입력하세요.")
    return rows


def interactive() -> int:
    """Read A and B and classify one custom pattern."""
    a = read_matrix("필터 A")
    b = read_matrix("필터 B")
    print("필터 A, B 저장 완료")
    pattern = read_matrix("패턴")
    try:
        left, right = mac(pattern, a), mac(pattern, b)
        result = compare(left, right, "A", "B")
    except ValueError as exc:
        print(f"판정 불가: {exc}")
        return 1
    print(f"A 점수: {left:.17g}\nB 점수: {right:.17g}")
    print("판정: 판정 불가 (UNDECIDED)" if result == "UNDECIDED"
          else f"판정: {result}")
    performance({3: (pattern, a)})
    return 0


def load_filters(group: object, size: int) -> Dict[str, Matrix]:
    """Read exactly one filter for each canonical label."""
    if not isinstance(group, dict):
        raise ValueError("필터 그룹 누락 또는 잘못된 구조")
    result = {}
    for name, raw in group.items():
        name = normalize(name)
        if name in result:
            raise ValueError(f"중복 필터 라벨: {name}")
        result[name] = matrix(raw, size)
    if set(result) != {"Cross", "X"}:
        raise ValueError("Cross와 X 필터가 모두 필요합니다")
    return result


def batch(path: Path) -> int:
    """Analyze cases independently and summarize failures."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("최상위 JSON은 객체여야 합니다")
        patterns = payload.get("patterns")
        if not isinstance(patterns, dict) or not patterns:
            raise ValueError("patterns는 비어 있지 않은 객체여야 합니다")
    except (OSError, ValueError, RecursionError) as exc:
        print(f"JSON 로드 오류: {exc}")
        return 2

    raw_filters = payload.get("filters")
    filters = {}
    errors = {}
    for size in SIZES:
        try:
            group = raw_filters.get(f"size_{size}") if isinstance(
                raw_filters, dict
            ) else None
            filters[size] = load_filters(group, size)
        except ValueError as exc:
            errors[size] = str(exc)
            print(f"size_{size} 필터 오류: {exc}")
        else:
            print(f"size_{size} 필터 로드 완료 (Cross, X)")

    failures = {}
    samples = {size: (make_pattern(size, "Cross"), make_pattern(size, "X"))
               for size in (3, *SIZES)}
    for key, case in patterns.items():
        print(f"\n--- {key} ---")
        try:
            match = re.fullmatch(r"size_(5|13|25)_([0-9]+)", key)
            if not match:
                raise ValueError("지원하지 않는 패턴 키: size_{N}_{idx} 필요")
            size = int(match.group(1))
            if size in errors:
                raise ValueError(f"필터 오류: {errors[size]}")
            if not isinstance(case, dict):
                raise ValueError("케이스는 객체여야 합니다")
            pattern = matrix(case.get("input"), size)
            expected = normalize(case.get("expected"))
            kernels = filters[size]
            cross = mac(pattern, kernels["Cross"])
            diagonal = mac(pattern, kernels["X"])
            result = compare(cross, diagonal, "Cross", "X")
            samples[size] = (pattern, kernels["Cross"])
            print(f"Cross 점수: {cross:.17g} | X 점수: {diagonal:.17g}")
            if result == expected:
                print(f"판정: {result} | expected: {expected} | PASS")
                continue
            reason = ("허용오차 이내 동점" if result == "UNDECIDED"
                      else "예상 라벨과 불일치")
            failures[key] = f"{reason}: 판정 {result}, expected {expected}"
            print(f"판정: {result} | expected: {expected} | FAIL ({reason})")
        except ValueError as exc:
            failures[key] = str(exc)
            print(f"FAIL ({exc})")

    performance(samples)
    print(f"\n총 테스트: {len(patterns)}개")
    print(f"통과: {len(patterns) - len(failures)}개")
    print(f"실패: {len(failures)}개")
    if failures:
        print("실패 케이스:")
        for key, reason in failures.items():
            print(f"- {key}: {reason}")
    return 1 if failures or errors else 0


def main() -> int:
    """Select a mode and return a shell-friendly status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("1", "2"))
    parser.add_argument("--data", type=Path, default=DATA)
    args = parser.parse_args()
    try:
        mode = args.mode
        while mode not in ("1", "2"):
            print("=== Mini NPU Simulator ===")
            print("1. 사용자 입력 (3×3)\n2. data.json 분석")
            mode = input("선택: ").strip()
            if mode not in ("1", "2"):
                print("1 또는 2를 입력하세요.")
        return interactive() if mode == "1" else batch(args.data)
    except (EOFError, KeyboardInterrupt):
        print("\n입력이 끝나 프로그램을 종료합니다.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
