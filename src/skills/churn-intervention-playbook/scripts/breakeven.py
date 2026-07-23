#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G3 손익분기 계산기 (의존성 0 — Python 표준 라이브러리만).

모델: T = d/(m-d). d>=m 이면 자동 ⛔.

사용:  python breakeven.py <V> <m> <d>       예) python breakeven.py 40000 0.30 0.10
"""
import sys


def breakeven(V, m, d):
    if V <= 0:
        raise ValueError("V(객단가)는 0보다 커야 한다")
    if not (0 < m <= 1):
        raise ValueError("m(마진율)은 0<m<=1 이어야 한다")
    if not (0 < d < 1):
        raise ValueError("d(할인율)은 0<d<1 이어야 한다")

    disclaimer = ("이 값은 산수(항등식)이지 효과크기 주장이 아니다. "
                  "실제 증분은 고객사 holdout A/B로 측정하라.")

    if d >= m:
        return {
            "auto_block": True,
            "threshold": None,
            "V": V, "m": m, "d": d,
            "note": ("d>=m: 할인이 마진 이상 → 증분 판매조차 이익 0 이하, 팔수록 손실. "
                     "자동 ⛔ 후보. " + disclaimer),
        }

    T = d / (m - d)
    return {
        "auto_block": False,
        "threshold": T,
        "V": V, "m": m, "d": d,
        "note": (f"손익분기 임계치 T={T:.3g}: 쿠폰 상환한 '원래 살 사람' 대비 "
                 f"증분 구매자가 최소 {T:.3g}배({T*100:.1f}%) 이상 나와야 비잠식(본전). "
                 + disclaimer),
    }


def format_report(r):
    lines = [f"[G3 손익분기 계산] V={r['V']} m={r['m']} d={r['d']}"]
    if r["auto_block"]:
        lines.append("  결과: ⛔ 자동 개입금지 후보 (d>=m)")
    else:
        lines.append(f"  손익분기 임계치 T = {r['threshold']:.3g}")
    lines.append("  " + r["note"])
    return "\n".join(lines)


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if len(sys.argv) != 4:
        print("사용: python breakeven.py <V> <m> <d>")
        sys.exit(2)
    try:
        V, m, d = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
        print(format_report(breakeven(V, m, d)))
    except ValueError as e:
        print(f"입력 오류: {e}")
        sys.exit(2)
