#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
플레이북 자기검증 (의존성 0). 출처 검증 + 판단 무결성 린트.
사용: python check_playbook.py [플레이북.md]
"""
import os
import re
import sys
import datetime
import urllib.request

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

TODAY = datetime.date.today()
STALE_MONTHS = 12
UA = "Mozilla/5.0 (compatible; churn-playbook-checker/1.0)"
ID_RE = re.compile(r"[BCVP]\d+")


def _find(rel_parts):
    here = os.path.dirname(os.path.abspath(__file__))
    for base in (here, os.path.dirname(here), os.getcwd()):
        p = os.path.join(base, *rel_parts)
        if os.path.exists(p):
            return p
    return None


def parse_sources(md_path):
    rows = []
    with open(md_path, encoding="utf-8") as f:
        for line in f:
            if not re.match(r"\s*\|\s*[BCVP]\d", line):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 4:
                continue
            url_m = re.search(r"https?://[^\s)|]+", line)
            rows.append({"id": cells[0], "date": cells[-1], "url": url_m.group(0) if url_m else None})
    return rows


def _months_since(date_txt):
    m = re.search(r"(20\d\d)[-.](\d{1,2})", date_txt)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
    else:
        m2 = re.search(r"(19\d\d|20\d\d)", date_txt)
        if not m2:
            return None
        y, mo = int(m2.group(1)), 1
    return (TODAY.year - y) * 12 + (TODAY.month - mo)


def _probe_url(url):
    try:
        url.encode("ascii")
    except UnicodeEncodeError:
        return "BAD-URL(비ASCII)", "URL에 한글 등 — 정규 URL로 교체 필요"
    ALIVE_CODES = {401, 403, 405, 406, 409, 429}
    last = "unreachable"
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA}, method=method)
            resp = urllib.request.urlopen(req, timeout=15)
            if method == "GET":
                resp.read(64)
            return "OK", ""
        except urllib.error.HTTPError as e:
            if e.code in ALIVE_CODES:
                return "ALIVE", f"봇차단 {e.code}(수동 확인)"
            if e.code in (404, 410):
                return "DEAD-LINK", f"HTTP {e.code}"
            last = f"HTTP {e.code}"
            continue
        except Exception as e:
            last = str(e)[:60]
            continue
    return "DEAD-LINK", last


def check_sources(md_path):
    rows = parse_sources(md_path)
    print("=== [1] 출처 검증 ===")
    for r in rows:
        if r["url"]:
            status, note = _probe_url(r["url"])
        else:
            status, note = "NO-URL", "출처 URL 미기입"
        ms = _months_since(r["date"])
        stale = "  ⏳" if (ms is not None and ms >= STALE_MONTHS) else ""
        if r["id"].startswith("P") and stale:
            stale = "  ⏳(이론 근거 — 예외)"
        print(f"  [{r['id']}] {status}{stale} {note}")
    return rows


def _routing_rows(md_path):
    rows, in_table = [], False
    with open(md_path, encoding="utf-8") as f:
        for line in f:
            if "권고 개입" in line and "근거" in line:
                in_table = True
                continue
            if in_table:
                if not line.strip().startswith("|"):
                    if line.strip() == "":
                        continue
                    in_table = False
                    continue
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if all(set(c) <= set("-: ") for c in cells):
                    continue
                if len(cells) >= 6:
                    rows.append(cells)
    return rows


BE_RE = re.compile(r"손익분기|breakeven|BE\s*=|T\s*=", re.I)
NON_SELECTIVE = ("⛔", "🎙️", "🛠️")


def valid_source_ids():
    src = _find(["references", "public-sources.md"])
    if not src:
        return set()
    return {r["id"] for r in parse_sources(src)}


def _priority_rows(md_path):
    rows, in_table = [], False
    with open(md_path, encoding="utf-8") as f:
        for line in f:
            if "순위" in line and "회복가치" in line and line.strip().startswith("|"):
                in_table = True
                continue
            if in_table:
                if not line.strip().startswith("|"):
                    if line.strip() == "":
                        continue
                    in_table = False
                    continue
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if all(set(c) <= set("-: ") for c in cells):
                    continue
                rows.append(cells)
    return rows


def lint_playbook(md_path):
    fails = []
    with open(md_path, encoding="utf-8") as f:
        body = f.read()
    rows = _routing_rows(md_path)

    valid = valid_source_ids()
    if valid:
        cited = set(ID_RE.findall(body))
        for cid in sorted(cited - valid):
            fails.append(f"[출처] 인용 [{cid}]가 실존하지 않음(날조 의심)")

    if not rows:
        if "🎫" in body:
            fails.append("🎫쿠폰 표기가 있으나 라우팅 표를 찾지 못함")
    for cells in rows:
        seg, g1, g2, g3, action, src = cells[0], cells[1], cells[2], cells[3], cells[4], cells[5]
        if "🎫" not in action:
            continue
        rowtxt = action + " " + src
        for name, val in (("G1", g1), ("G2", g2), ("G3", g3)):
            if val in ("", "-"):
                fails.append(f"[{seg}] 🎫쿠폰인데 {name} 미평가")
        for name, val in (("G1", g1), ("G2", g2), ("G3", g3)):
            if "❌" in val:
                fails.append(f"[{seg}] 🎫쿠폰인데 {name} 미충족(❌)")
        if not ID_RE.search(src):
            fails.append(f"[{seg}] 근거 출처ID 없음")
        if not re.search(r"P\d", src):
            fails.append(f"[{seg}] P태그 없음")
        if "holdout" not in rowtxt.lower():
            fails.append(f"[{seg}] holdout 확인 병기 없음")
        if not BE_RE.search(rowtxt):
            fails.append(f"[{seg}] 손익분기 표기 없음")

    for pcells in _priority_rows(md_path):
        prow = " ".join(pcells)
        for emo in NON_SELECTIVE:
            if emo in prow:
                fails.append(f"[우선순위] '{emo}' 개입에 점수가 붙음")
                break
    return fails


if __name__ == "__main__":
    src = _find(["references", "public-sources.md"])
    if not src:
        print("public-sources.md 를 찾지 못함", file=sys.stderr)
        sys.exit(2)
    check_sources(src)

    pb = sys.argv[1] if len(sys.argv) > 1 else _find(["examples", "sample-playbook.md"])
    print("\n=== [2] 판단 무결성 린트 ===")
    if not pb or not os.path.exists(pb):
        print("  플레이북 파일 없음")
        sys.exit(0)
    fails = lint_playbook(pb)
    if fails:
        for m in fails:
            print("  FAIL:", m)
        print(f"  → {len(fails)}건 위반.")
        sys.exit(1)
    print("  PASS")
    sys.exit(0)
