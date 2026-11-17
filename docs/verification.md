# 실제 실행 기록

2026-11-17 · Windows · 3.14.7

## python -X utf8 main.py --mode 1

```text
필터 A (3줄 입력, 공백 구분)
1/3행: 입력 형식 오류: 각 줄에 유한한 숫자 3개를 입력하세요.
1/3행: 입력 형식 오류: 각 줄에 유한한 숫자 3개를 입력하세요.
1/3행: 2/3행: 3/3행: 필터 B (3줄 입력, 공백 구분)
1/3행: 2/3행: 3/3행: 필터 A, B 저장 완료
패턴 (3줄 입력, 공백 구분)
1/3행: 2/3행: 3/3행: A 점수: 1
B 점수: 5
판정: B

성능 분석 (평균/1000회, 필터 1개 기준)
크기        평균 시간(ms)     연산 횟수(N²)
 3×3           0.001199          9
```

## python -X utf8 main.py --mode 2

```text
size_5 필터 로드 완료 (Cross, X)
size_13 필터 로드 완료 (Cross, X)
size_25 필터 로드 완료 (Cross, X)

--- size_5_1 ---
Cross 점수: 9 | X 점수: 1
판정: Cross | expected: Cross | PASS

--- size_5_2 ---
Cross 점수: 1 | X 점수: 9
판정: X | expected: X | PASS

--- size_5_3 ---
Cross 점수: 9 | X 점수: 1.2
판정: Cross | expected: Cross | PASS

--- size_13_1 ---
Cross 점수: 25 | X 점수: 1
판정: Cross | expected: Cross | PASS

--- size_13_2 ---
Cross 점수: 1 | X 점수: 25
판정: X | expected: X | PASS

--- size_13_3 ---
Cross 점수: 25 | X 점수: 1.2
판정: Cross | expected: Cross | PASS

--- size_25_1 ---
Cross 점수: 49 | X 점수: 1
판정: Cross | expected: Cross | PASS

--- size_25_2 ---
Cross 점수: 1 | X 점수: 49
판정: X | expected: X | PASS

--- size_25_3 ---
Cross 점수: 49 | X 점수: 1.2
판정: Cross | expected: Cross | PASS

성능 분석 (평균/1000회, 필터 1개 기준)
크기        평균 시간(ms)     연산 횟수(N²)
 3×3           0.001272          9
 5×5           0.002394         25
13×13          0.010836        169
25×25          0.035097        625

총 테스트: 9개
통과: 9개
실패: 0개
```

## python -X utf8 main.py --mode 2 --data docs/diagnostic-data.json

```text
size_5 필터 로드 완료 (Cross, X)
size_13 필터 로드 완료 (Cross, X)
size_25 필터 로드 완료 (Cross, X)

--- size_5_1 ---
Cross 점수: 9 | X 점수: 1
판정: Cross | expected: Cross | PASS

--- size_5_10 ---
FAIL (행 개수 불일치: 5행 필요)

--- size_5_11 ---
Cross 점수: 0 | X 점수: 0
판정: UNDECIDED | expected: X | FAIL (허용오차 이내 동점)

성능 분석 (평균/1000회, 필터 1개 기준)
크기        평균 시간(ms)     연산 횟수(N²)
 3×3           0.001267          9
 5×5           0.002514         25
13×13          0.010816        169
25×25          0.035208        625

총 테스트: 3개
통과: 1개
실패: 2개
실패 케이스:
- size_5_10: 행 개수 불일치: 5행 필요
- size_5_11: 허용오차 이내 동점: 판정 UNDECIDED, expected X
```
