"""한국어 결 정본·측정기 회귀 — 정본 구간 추출·프로필 비대칭·스캐너 규칙별 양성/음성·윤문 검증기 실행·게이트 킬테스트. 모델 호출 0.
260908 리뷰(킬테스트 4/8 생존) 반영: 규칙 축 전 ID 를 표본으로 단언하고, 윤문 6축은 summary_polish.sh 의 검증기를 그대로 꺼내 실행하며,
check_ko_tone_ssot 는 임시 ROOT 사본을 변형해 실제로 빨강이 나는지 본다(자기 사본 술어 검사 금지)."""
import contextlib
import glob
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
import ko_tone_scan as kts  # noqa: E402


def _block(profile):
    return subprocess.run(["bash", "-c", "source shared/inject_guidelines.sh; guidelines_block %s" % profile],
                          cwd=ROOT, capture_output=True, text=True).stdout


class RulesFile(unittest.TestCase):
    def test_sections_and_profile_asymmetry(self):
        txt = (ROOT / "shared" / "ko_tone_rules.md").read_text(encoding="utf-8")
        for sec in ("COMMON", "NEWS-CAP", "POLISH"):
            self.assertEqual(txt.count("KO-TONE:%s-START" % sec), 1)
            self.assertEqual(txt.count("KO-TONE:%s-END" % sec), 1)
        self.assertEqual(txt.count("INJECT-SKIP-START"), txt.count("INJECT-SKIP-END"))
        card, summ = _block("card"), _block("summary")
        self.assertIn("[윤문 추가축 — 카드 초고", card)          # 카드 = 윤문체
        self.assertNotIn("기사체 보존이 위 규칙의 상한선", card)   # 카드 = 기사체 상한선 미적용
        self.assertIn("기사체 보존이 위 규칙의 상한선", summ)      # 요약 = 상한선
        self.assertNotIn("[윤문 추가축 — 카드 초고", summ)         # 요약 = 윤문 추가축 제외
        for b in (card, summ):
            self.assertIn("[한국어 결 — AI 번역투 소거(공용 문장축)]", b)
            self.assertNotIn("[미채택 · 근거", b)                  # 사람용 절 미주입
            self.assertNotIn("KO-TONE:", b)                        # 구간 마커 주석 미주입(260908 리뷰)
        self.assertNotIn("위 [기사체 상한선]", card)               # 카드 블록이 없는 절을 가리키지 않는다

    def test_tone_block_extracts_common_only_and_lane_neutral(self):
        r = subprocess.run(["bash", "-c", 'source shared/tone_block.sh; printf "%s\\n---\\n%s\\n---\\n%s" "$TONE_BLOCK" "$TONE_BLOCK_SENT" "$TONE_VER"'],
                           cwd=ROOT, capture_output=True, text=True)
        blk, sent, ver = r.stdout.split("\n---\n")
        self.assertTrue(blk.startswith("[한국어 결 — AI 번역투 소거(공용 문장축)]"))
        self.assertNotIn("기사체 보존", blk)
        self.assertIn("- [리듬]", blk)
        self.assertNotIn("- [리듬]", sent)
        self.assertTrue(re.fullmatch(r"[0-9a-f]{8}", ver.strip()), ver)
        # SNS·nbmake 레인에 그대로 붙는 블록 — 뉴스 전용 문맥으로 스스로를 제외하지 않는다(260908 리뷰)
        for bad in ("자유요약", "Thread 헤드", "[사실 무결성]"):
            self.assertNotIn(bad, blk)

    def test_tone_block_missing_file_marks_version(self):
        """정본 부재 = 'missing' 키(빈 규칙이 정상 해시로 캐시에 굳는 축 차단)."""
        d = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q", d], check=True)
        os.makedirs(os.path.join(d, "shared"))
        shutil.copy(ROOT / "shared" / "tone_block.sh", os.path.join(d, "shared", "tone_block.sh"))
        r = subprocess.run(["bash", "-c", 'source shared/tone_block.sh; printf "%s|%s" "$TONE_VER" "${#TONE_BLOCK}"'],
                           cwd=d, capture_output=True, text=True)
        self.assertEqual(r.stdout, "missing|0")
        self.assertIn("::error::", r.stderr)


class Scanner(unittest.TestCase):
    RULE_CASES = [   # (id, 양성 표본, 기대 수, 음성 표본 — 정본 유지 조건)
        ("A1", "경찰에 의해 확인된 사실이 발생되어진다.", 2, "경찰이 확인한 사실이 발생한다."),
        ("A2", "규제에 대해 논의했다. 절차를 통해 결정했다.", 2, "규제를 논의했다."),
        ("A3", "경쟁력을 가지고 있다. 합의가 이루어졌다.", 2, "경쟁력이 강하다. 합의했다."),
        ("D1", "결론적으로 주목할 만하다.", 2, "결론은 표준화다."),
        ("G1", "오를 가능성이 있을 수 있다.", 1, "오른다."),
        ("F1", "정말 큰 문제다. 매우 컸다.", 2, "\"정말 큰 문제\"라고 했다."),
        ("S5", "해결할 수 있는 방법이 없다.", 1, "남아 있는 재고가 있다."),
        ("S7", "사용자에게 있어 속도는 중요하다.", 1, "사회에 있어서는 안 될 일이다."),
        ("S4", "문제를 추가하는 것은 도움이 된다.", 1, "검토하는 것으로 파악됐다. 접수된 것은 22일이었다. 중요한 것은 속도다."),
    ]

    def test_each_rule_positive_and_negative(self):
        for rid, pos, n, neg in self.RULE_CASES:
            self.assertEqual(kts.scan(pos)[rid], n, rid)
            self.assertEqual(kts.scan(neg)[rid], 0, rid + " neg")

    def test_consecutive_rules_count_excess_only(self):
        """정본이 '연발·3회+'로 적은 규칙 = 초과분만(260908 리뷰: 건당 계수가 정상 기사문 점수를 부풀렸다)."""
        self.assertEqual(kts.scan("구조적·근본적·필연적 문제다.")["S1"], 1)          # 한 문장 3회 → 초과 1
        one = kts.scan("전략적 중요성이 크다. 법적 조치를 했다. 누적 적자가 컸다. 사적 모임이었다.")
        self.assertEqual((one["S1"], one["S1n"]), (0, 1))                          # 문장당 1회 = 규칙 0 · 관측 1(전략적)
        self.assertEqual(kts.scan("값이 올랐다. 또한 양도 늘었다. 하지만 질은 낮다.")["H1"], 1)   # 연속 2문장
        self.assertEqual(kts.scan("값이 올랐다. 또한 양도 늘었다. 질은 낮다.")["H1"], 0)          # 단발
        self.assertEqual(kts.scan("핵심은 표준화라는 점에 있다.")["I1"], 1)
        self.assertEqual(kts.scan("그가 한 것이다. 우리가 갈 것이다. 끝났다.")["I1"], 1)           # 종결 연속
        self.assertEqual(kts.scan("그가 한 것이다. 끝났다.")["I1"], 0)
        self.assertEqual(kts.scan("오를 것으로 보인다. 내릴 것으로 보인다.")["G1"], 1)           # 2회째부터
        self.assertEqual(kts.scan("오를 것으로 보인다고 밝혔다. 내릴 것으로 보인다고 말했다.")["G1"], 0)   # 귀속 발화
        self.assertEqual(kts.scan("갈 수 있다. 올 수 있다.")["A4"], 2)
        self.assertEqual(kts.score("갈 수 있다. 올 수 있다."), 0)                    # A4 임계 = 3회째부터
        self.assertEqual(kts.score("갈 수 있다. 올 수 있다. 볼 수 있다는 말이다."), 1)   # A4 초과 1 · 종결 변주라 R1 0
        self.assertEqual(kts.scan("값이 높았다. 양이 많았다. 질이 좋았다.")["R1"], 1)   # 종결 '았다' 3연속
        self.assertEqual(kts.scan("값이 높았다. 양이 는다. 질이 좋았다.")["R1"], 0)

    def test_allowlists_and_quotes(self):
        t = ("전략적 중요성을 가지고 있다. 법적 조치를 검토하는 것으로 파악됐다. 사용자들은 이 기능들을 자주 쓴다. "
             "전문가들은 환경 요인을 꼽는다. 누적 적자가 컸다. 사용자에게 있어 속도는 중요하다. "
             "\"정말 특별한 저녁이었다\"고 했다. 정말 큰 문제다. 해결할 수 있는 방법이 없다. 합의가 이루어졌다. "
             "문제를 추가하는 것은 도움이 된다. 사회에 있어서는 안 될 일이다. 접수된 것은 22일이었다.")
        h = kts.scan(t)
        self.assertEqual((h["S1"], h["S1n"]), (0, 1))   # 전략적 1회 = 관측만(법적=개념어 · 누적=명사 제외)
        self.assertEqual(h["S7"], 1)
        self.assertEqual(h["F1"], 1)                    # 인용 안 '정말' 제외
        self.assertEqual(h["S5"], 1)
        self.assertEqual(h["A3"], 2)
        self.assertEqual(h["S4"], 1)
        self.assertEqual((h["S3"], h["S3n"]), (2, 1))   # 사용자들·기능들 / 전문가들 = 기사 주체
        self.assertGreaterEqual(kts.score(t), 5)
        self.assertEqual(kts.score(t, lane="card"), kts.score(t) + 2)   # 카드 레인 = S3 도 규칙
        self.assertNotIn("S3", kts.rule_ids("summary"))
        self.assertIn("S3", kts.rule_ids("card"))
        self.assertEqual(kts.scan("\"매우 컸다\"고 했다.")["F1"], 0)
        self.assertEqual(kts.scan(kts.mask_quotes("\"매우 컸다\"고 했다.").replace(" ", "") and "매우 컸다고 했다.")["F1"], 1)

    def test_clean_news_text_scores_zero(self):
        t = ("7일 오후 7시께 중국 네이멍구자치구의 한 자동차 주행 시험장에서 트럭의 제동장치가 고장 났다. "
             "밀려 내려온 트럭이 승합차를 덮쳤고, 승합차에 타고 있던 5명이 숨진 것으로 집계됐다. 당국은 원인을 조사하고 있다.")
        self.assertEqual(kts.score(t), 0)

    def test_lane_text_picks_digest_blocks_drops_head_and_comments(self):
        md = ("---\ntitle: x\n---\n### [자유요약 — 약 100자]\n```text\n본문 A.\n```\n### [IG — 1/800자]\n```text\n본문 B.\n```\n"
              "### [Thread — 약 300자]\n```text\n헤드 라임 줄.\n\n📍 본문 T.\n```\n### 💡 이 기사의 시사점\n시사 C.\n<!-- rev 1 260908-1200: 에 대해 빼고 결론적으로 넣어 -->\n")
        lt = kts.lane_text(md)
        self.assertEqual(lt, "본문 A.\n본문 B.\n📍 본문 T.\n시사 C.")
        self.assertEqual(kts.score(lt), 0)              # 지시문(에 대해·결론적으로)이 채점되지 않는다


def _verifier_src():
    src = (ROOT / "shared" / "summary_polish.sh").read_text(encoding="utf-8")
    return src.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]


def _verify(orig, cand):
    d = tempfile.mkdtemp()
    fo, fc = os.path.join(d, "o.md"), os.path.join(d, "c.md")
    Path(fo).write_text(orig, encoding="utf-8")
    Path(fc).write_text(cand, encoding="utf-8")
    r = subprocess.run([sys.executable, "-", fo, fc], input=_verifier_src(), capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


class PolishGuard(unittest.TestCase):
    FM = "---\ntitle: t\n---\n"

    def test_verifier_runs_from_script(self):
        """summary_polish.sh 의 검증기 자체를 실행 — 자기 사본 술어 검사 금지(260908 리뷰)."""
        body = "기록을 삭제한 담당자는 3일 답하지 않았다. \"그대로\"라고 했다.\n"
        self.assertEqual(_verify(self.FM + body, self.FM + body), (0, "ok"))
        rc, why = _verify(self.FM + body, self.FM + "기록을 지울 맡은 이는 3일 답하지 않았다. \"그대로\"라고 했다.\n")
        self.assertEqual(rc, 1)
        self.assertTrue(why.startswith("격 하락(") and "삭제→지울" in why and "담당→맡은" in why, why)
        rc, why = _verify(self.FM + body, self.FM + body.replace("3일", "4일"))
        self.assertEqual((rc, why), (1, "숫자 집합 변경"))
        rc, why = _verify(self.FM + body, self.FM + body.replace("\"그대로\"", "\"그냥\""))
        self.assertEqual(rc, 1)
        self.assertTrue(why.startswith("인용 변경"), why)

    def test_default_off_and_lever(self):
        """기본 OFF = 모델 콜 0 · 파일 무변경 · 조건부 없음. SUMMARY_POLISH=1 이면 콜은 나가되 빈 출력 = 원본 유지(fail-soft)."""
        # 콜 스텁은 표식 파일로 호출 여부를 남긴다(스크립트가 claude_meter 의 stderr 를 /dev/null 로 버린다)
        script = ('source shared/summary_polish.sh; m=$(mktemp); claude_meter(){ echo CALLED > "$m"; cat >/dev/null; }; MODEL=x; '
                  'f=$(mktemp); printf -- "---\\nt: 1\\n---\\n본문.\\n" > "$f"; summary_polish "$f" test; cat "$f"; echo "[meter:$(cat "$m")]"')
        r = subprocess.run(["bash", "-c", "unset SUMMARY_POLISH; " + script], cwd=ROOT, capture_output=True, text=True)
        self.assertIn("본문.\n[meter:]", r.stdout)                 # 콜 0 · 파일 무변경
        r = subprocess.run(["bash", "-c", "export SUMMARY_POLISH=1; " + script], cwd=ROOT, capture_output=True, text=True)
        self.assertIn("원본 유지", r.stdout)
        self.assertIn("본문.\n[meter:CALLED]", r.stdout)           # 레버 ON = 콜은 나가고 빈 출력이면 원본 유지
        src = (ROOT / "shared" / "summary_polish.sh").read_text(encoding="utf-8")
        self.assertIn("SUMMARY_POLISH:-0", src)
        self.assertNotIn("auto", src.split("summary_polish()")[1][:400])
        awk_line = next(l for l in src.splitlines() if 'rules_txt="$(awk' in l)
        self.assertNotIn("POLISH", awk_line)   # 요약 대상 콜은 [윤문 추가축]을 읽지 않는다(상한선과 충돌 · 260908 리뷰)


class Wiring(unittest.TestCase):
    def test_revise_log_in_frontmatter_not_body(self):
        src = (ROOT / ".github" / "scripts" / "revise.sh").read_text(encoding="utf-8")
        self.assertIn("rev_log:", src)
        self.assertNotIn("<!-- rev %d", src)

    def test_cardmake_retry_excludes_tone_line(self):
        src = (ROOT / ".github" / "scripts" / "cardmake.sh").read_text(encoding="utf-8")
        self.assertIn("grep -v '^TONE '", src)

    def test_card_gate_uses_card_lane(self):
        src = (ROOT / ".github" / "scripts" / "card_gate.py").read_text(encoding="utf-8")
        self.assertIn("rule_ids('card')", src)
        self.assertIn("lane='card'", src)


class Gate(unittest.TestCase):
    """check_ko_tone_ssot 킬테스트 — 임시 ROOT 사본을 변형해 실제 빨강을 본다."""
    FILES = ("shared/ko_tone_rules.md", "shared/inject_guidelines.sh", "shared/tone_block.sh", "shared/summary_polish.sh",
             "prompts/polish-korean.md")

    def _tmp_root(self):
        d = tempfile.mkdtemp()
        for rel in self.FILES + tuple(os.path.relpath(p, ROOT) for p in glob.glob(str(ROOT / "apps" / "news" / "01_지침_에디터_뉴스_*.md"))):
            dst = os.path.join(d, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(ROOT / rel, dst)
        os.makedirs(os.path.join(d, ".github", "scripts"))
        for p in glob.glob(str(ROOT / ".github" / "scripts" / "*.sh")) + glob.glob(str(ROOT / "shared" / "*.sh")):
            shutil.copy(p, os.path.join(d, os.path.relpath(p, ROOT)))
        return d

    def _run(self, d):
        import check_refs
        old = check_refs.ROOT
        check_refs.ROOT = d
        try:
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                rc = check_refs.check_ko_tone_ssot()
            return rc, buf.getvalue()
        finally:
            check_refs.ROOT = old

    def _mut(self, d, rel, fn):
        p = os.path.join(d, rel)
        t = open(p, encoding="utf-8").read()
        open(p, "w", encoding="utf-8").write(fn(t))

    def test_gate_green_then_kills(self):
        d = self._tmp_root()
        self.assertEqual(self._run(d)[0], 0)
        cases = [
            ("옛 polish 규칙 목록 재작성(표기 다른 사본)", "prompts/polish-korean.md",
             lambda t: t + '\n- 이중 피동·"~에 의해" 피동 → 능동 · "가지고 있다" 명사화 → 동사\n'),
            ("정본 profile=card 스코프 제거", "shared/ko_tone_rules.md", lambda t: t.replace("profile=card", "profile=cardx")),
            ("상한선 구간 순서 역전", "shared/ko_tone_rules.md",
             lambda t: t.replace("KO-TONE:NEWS-CAP-START", "@@").replace("KO-TONE:NEWS-CAP-END", "KO-TONE:NEWS-CAP-START").replace("@@", "KO-TONE:NEWS-CAP-END")),
            ("윤문 콜이 정본을 안 읽음", "shared/summary_polish.sh", lambda t: t.replace("KO-TONE:", "XX:")),
            ("주입기에서 정본 제거", "shared/inject_guidelines.sh", lambda t: t.replace("shared/ko_tone_rules.md", "shared/none.md")),
        ]
        for name, rel, fn in cases:
            dd = self._tmp_root()
            self._mut(dd, rel, fn)
            rc, out = self._run(dd)
            self.assertEqual(rc, 1, name + "\n" + out)


if __name__ == "__main__":
    unittest.main()
