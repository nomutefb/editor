"""모델 승격 치환기(shared/apply_models.py) + 드리프트 게이트(check_refs.check_model_ids) 회귀.
260923 실측 사고가 정답지: 옛 이름이 새 이름의 앞머리인 승격(claude-opus-5 → claude-opus-5-5 · Opus 5 → Opus 5.5)에서
게이트가 새 이름을 '구세대 잔존'으로 막고, 다음 승격에선 claude-opus-5-5-5가 되던 구멍 + 대행(follow) 시작·동기·해제."""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

_SHARED = Path(__file__).resolve().parents[1] / "shared"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _SHARED / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


AM = _load("apply_models")
sys.path.insert(0, str(_SHARED))
with contextlib.redirect_stdout(io.StringIO()):
    import check_refs as CR  # noqa: E402

REG = {
    "tiers": {
        "opus": {"id": "claude-opus-5", "en": "Opus 5", "ko": "오퍼스 5"},
        "sonnet": {"id": "claude-sonnet-5", "en": "Sonnet 5", "ko": "소넷 5"},
        "fable": {"id": "claude-fable-5", "en": "Fable 5", "ko": "페이블 5", "sites": ["src/kmake.sh"]},
    },
    "vendors": {},
    "retired": [],
    "keyed": {"ids": {"shared/model_env.sh": ["fable"], "src/gen.py": ["fable"]}, "labels": {"src/nm.js": ["fable", "opus"]}},
    "scan": {"include": ["src/*", "shared/*.sh"], "exclude": []},
}
FILES = {
    "shared/model_env.sh": 'PIPE_MODEL="${PIPE_MODEL:-claude-opus-5}"\nFABLE_MODEL="${FABLE_MODEL:-claude-fable-5}"\n',
    "src/kmake.sh": ('MODEL="${K_MODEL:-$FABLE_MODEL}"   # 페이블 티어(모델 = model_env.sh FABLE_MODEL)\nK_MODEL_FB="${K_MODEL_FB:-claude-opus-5}"\n'
                     '# 운영자 "opus 5.0 high로 항상" · 오퍼스 5명 참석 · claude-opus-5.\n'),
    "src/gen.py": ('MODEL = os.environ.get("FABLE_MODEL") or "claude-fable-5"\n'
                   'MODEL_FB = os.environ.get("PIPE_MODEL_FB", "claude-opus-5")\n# 운영자 "품질 차이 FABLE 5"\n'),
    "src/nm.js": "window.NM = {\n  fable: 'Fable 5',\n  opus: 'Opus 5',\n};\n",
    "src/judge.py": 'MODEL = os.environ.get("GATE_MODEL", "claude-opus-5")   # Opus 5 max\n',
}


class Guards(unittest.TestCase):
    def test_id_guard_skips_version_extension(self):
        rx = AM.id_rx("claude-opus-5")
        for s in ("claude-opus-5-5", "claude-opus-5.1", "claude-opus-50", "claude-opus-5-20260101"):
            self.assertIsNone(rx.search(s), s)
        for s in ('"claude-opus-5"', "claude-opus-5.", "(claude-opus-5)", "claude-opus-5 high", "claude-opus-5-기반"):
            self.assertIsNotNone(rx.search(s), s)

    def test_name_guard_skips_people_and_version(self):
        self.assertIsNone(AM.name_rx("Opus 5").search("Opus 5.5"))
        self.assertIsNone(AM.name_rx("Opus 5").search("Opus 50"))
        self.assertIsNone(AM.name_rx("오퍼스 5").search("오퍼스 5.5"))
        self.assertIsNone(AM.name_rx("오퍼스 5").search("오퍼스 5명"))
        self.assertIsNotNone(AM.name_rx("Opus 5").search("(Opus 5)"))
        self.assertIsNotNone(AM.name_rx("Opus 5").search("Opus 5."))
        self.assertIsNotNone(AM.name_rx("Opus 5.5").search("Opus 5.5인데"))     # 소수 버전 = 인원 아님
        self.assertIsNotNone(AM.name_rx("오퍼스 5.5").search("오퍼스 5.5인지"))
        self.assertIsNone(AM.name_rx("Opus 5.5").search("Opus 5.55"))

    def test_keyed_label_ignores_array_of_keys(self):
        # api/sb.js `SB_DIRECTORS = ['fable', 'opus']`는 라벨이 아니다 — 키 라벨은 `fable: '...'` 꼴만
        self.assertIsNone(AM.keyed_label_rx("fable").search("const SB_DIRECTORS = ['fable', 'opus', 'gpt'];"))
        self.assertEqual(AM.keyed_label_rx("fable").search("{ fable: 'Fable 5', opus: 'Opus 5' }").group(2), "Fable 5")


class Flow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        for rel, body in FILES.items():
            p = Path(self.tmp, rel)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        Path(self.tmp, "shared", "models.json").write_text(json.dumps(REG, ensure_ascii=False, indent=2), encoding="utf-8")
        self._old = (AM.ROOT, AM.REG, CR.ROOT)
        AM.ROOT, AM.REG, CR.ROOT = self.tmp, os.path.join(self.tmp, "shared", "models.json"), self.tmp

    def tearDown(self):
        AM.ROOT, AM.REG, CR.ROOT = self._old
        shutil.rmtree(self.tmp)

    def run_am(self, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            return AM.main(["apply_models.py"] + list(args))

    def gate(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            rc = CR.check_model_ids()
        return rc, out.getvalue()

    def f(self, rel):
        return Path(self.tmp, rel).read_text(encoding="utf-8")

    def reg(self):
        return json.loads(self.f("shared/models.json"))

    def test_prefix_promotion_passes_gate_and_repeats_cleanly(self):
        self.assertEqual(self.gate()[0], 0)
        self.assertEqual(self.run_am("opus", "claude-opus-5-5", "Opus 5.5", "오퍼스 5.5"), 0)
        k = self.f("src/kmake.sh")
        self.assertIn('K_MODEL_FB="${K_MODEL_FB:-claude-opus-5-5}"', k)
        self.assertIn('"opus 5.0 high로 항상"', k)          # 인용된 5.0 = 다른 말 · 손대지 않음
        self.assertIn("오퍼스 5명", k)                        # 인원 표기
        self.assertIn("claude-opus-5-5.", k)                  # 문장 끝 마침표 = 경계
        self.assertIn("# Opus 5.5 max", self.f("src/judge.py"))
        self.assertIn("claude-opus-5", self.reg()["retired"])
        rc, out = self.gate()
        self.assertEqual(rc, 0, out)                          # 새 이름을 구세대로 오판하지 않는다
        self.assertEqual(self.run_am("opus", "claude-opus-6", "Opus 6", "오퍼스 6"), 0)
        body = "".join(self.f(r) for r in FILES)
        self.assertNotIn("claude-opus-5-5", body)
        self.assertNotIn("claude-opus-6-5", body)             # 5-5-5류 누적 없음
        self.assertNotIn("Opus 6.5", body)
        self.assertEqual(self.gate()[0], 0)

    def test_follow_then_leader_promotion_then_unfollow(self):
        self.run_am("opus", "claude-opus-5-5", "Opus 5.5", "오퍼스 5.5")
        self.assertEqual(self.run_am("fable", "--follow", "opus"), 0)
        self.assertIn('FABLE_MODEL="${FABLE_MODEL:-claude-opus-5-5}"', self.f("shared/model_env.sh"))
        self.assertIn('os.environ.get("FABLE_MODEL") or "claude-opus-5-5"', self.f("src/gen.py"))
        self.assertIn('"품질 차이 FABLE 5"', self.f("src/gen.py"))   # 도입 이유(산문) = 보존
        self.assertIn("fable: 'Opus 5.5'", self.f("src/nm.js"))
        fb = self.reg()["tiers"]["fable"]
        self.assertEqual((fb["id"], fb["follow"], fb["원래"]["id"]), ("claude-opus-5-5", "opus", "claude-fable-5"))
        self.assertIn("claude-fable-5", self.reg()["retired"])
        self.assertNotIn("Fable 5", self.reg()["retired"])
        rc, out = self.gate()
        self.assertEqual(rc, 0, out)
        # 대상(오퍼스) 승격 = 대행 자리까지 같이 움직인다
        self.assertEqual(self.run_am("opus", "claude-opus-6", "Opus 6", "오퍼스 6"), 0)
        self.assertIn('FABLE_MODEL="${FABLE_MODEL:-claude-opus-6}"', self.f("shared/model_env.sh"))
        self.assertIn("fable: 'Opus 6'", self.f("src/nm.js"))
        self.assertEqual(self.reg()["tiers"]["fable"]["id"], "claude-opus-6")
        self.assertEqual(self.gate()[0], 0)
        # 새 페이블 티어 = 대행 해제 · 오퍼스 자리는 그대로
        self.assertEqual(self.run_am("fable", "claude-fable-7", "Fable 7", "페이블 7"), 0)
        self.assertIn('FABLE_MODEL="${FABLE_MODEL:-claude-fable-7}"', self.f("shared/model_env.sh"))
        self.assertIn('PIPE_MODEL="${PIPE_MODEL:-claude-opus-6}"', self.f("shared/model_env.sh"))
        self.assertIn('K_MODEL_FB="${K_MODEL_FB:-claude-opus-6}"', self.f("src/kmake.sh"))
        nm = self.f("src/nm.js")
        self.assertIn("fable: 'Fable 7'", nm)
        self.assertIn("opus: 'Opus 6'", nm)
        fb = self.reg()["tiers"]["fable"]
        self.assertNotIn("follow", fb)
        self.assertNotIn("claude-opus-6", self.reg()["retired"])
        rc, out = self.gate()
        self.assertEqual(rc, 0, out)

    def test_follow_refuses_when_a_site_hardcodes_old_id(self):
        Path(self.tmp, "src", "leftover.sh").write_text('MODEL="claude-fable-5"\n', encoding="utf-8")
        before = self.f("shared/model_env.sh")
        self.assertEqual(self.run_am("fable", "--follow", "opus"), 2)
        self.assertEqual(self.f("shared/model_env.sh"), before)
        self.assertNotIn("follow", self.reg()["tiers"]["fable"])

    def test_promotion_to_another_tiers_id_needs_follow(self):
        self.assertEqual(self.run_am("fable", "claude-opus-5"), 2)
        self.assertEqual(self.reg()["tiers"]["fable"]["id"], "claude-fable-5")

    def test_gate_catches_keyed_and_site_drift(self):
        self.run_am("fable", "--follow", "opus")
        self.assertEqual(self.gate()[0], 0)
        nm = self.f("src/nm.js")
        Path(self.tmp, "src", "nm.js").write_text(nm.replace("fable: 'Opus 5'", "fable: 'Fable 5'"), encoding="utf-8")
        self.assertEqual(self.gate()[0], 1)                   # 라벨 손 수정 = 정본 불일치
        Path(self.tmp, "src", "nm.js").write_text(nm, encoding="utf-8")
        Path(self.tmp, "src", "kmake.sh").write_text('MODEL="${K_MODEL:-claude-opus-5}"   # 모델 = model_env.sh FABLE_MODEL\n', encoding="utf-8")
        rc, out = self.gate()
        self.assertEqual(rc, 1)                               # 주석에 이름만 남기고 코드는 ID를 박음 = 차단
        self.assertIn("FABLE_MODEL", out)

    def test_gate_and_tool_fail_closed_on_missing_keyed_spot(self):
        Path(self.tmp, "src", "gen.py").write_text('MODEL = pick_fable()   # 한 줄 꼴이 깨짐\n', encoding="utf-8")
        self.assertEqual(self.gate()[0], 1)                   # 요구 티어 키 자리 0건 = 차단(조용한 건너뜀 금지)
        self.assertEqual(self.run_am("fable", "--follow", "opus"), 2)
        self.assertNotIn("follow", self.reg()["tiers"]["fable"])

    def test_gate_blocks_tier_var_override_outside_keyed(self):
        Path(self.tmp, "src", "flow.yml").write_text("env:\n  FABLE_MODEL: claude-fable-5\n", encoding="utf-8")
        rc, out = self.gate()
        self.assertEqual(rc, 1)
        self.assertIn("keyed.ids", out)

    def test_unfollow_requires_both_names_and_shared_name_is_refused(self):
        self.run_am("opus", "claude-opus-5-5", "Opus 5.5", "오퍼스 5.5")
        self.run_am("fable", "--follow", "opus")
        self.assertEqual(self.run_am("fable", "claude-fable-7", "Fable 7"), 2)      # 한글명 누락 = 오퍼스 이름 상속 차단
        self.assertEqual(self.reg()["tiers"]["fable"]["follow"], "opus")
        # 정본을 손으로 어긋나게(대행 아닌데 한글명 공유) → 승격이 공유 이름 글자 치환을 거부
        reg = self.reg(); fb = reg["tiers"]["fable"]
        fb.pop("follow"); fb.pop("원래"); fb.update(id="claude-fable-7", en="Fable 7")
        Path(self.tmp, "shared", "models.json").write_text(json.dumps(reg, ensure_ascii=False), encoding="utf-8")
        before = {r: self.f(r) for r in FILES}
        self.assertEqual(self.run_am("fable", "claude-fable-8", "Fable 8", "페이블 8"), 2)
        self.assertEqual({r: self.f(r) for r in FILES}, before)             # 거부 = 아무 파일도 안 바뀜
        self.assertEqual(self.reg()["tiers"]["fable"]["id"], "claude-fable-7")

    def test_id_only_promotion_keeps_names_and_return_unretires(self):
        self.assertEqual(self.run_am("sonnet", "claude-sonnet-6"), 0)             # 표시명은 그대로 = 은퇴 금지
        self.assertNotIn("Sonnet 5", self.reg()["retired"])
        self.assertEqual(self.gate()[0], 0)
        self.run_am("fable", "--follow", "opus")
        self.assertIn("claude-fable-5", self.reg()["retired"])
        self.assertEqual(self.run_am("fable", "claude-fable-5", "Fable 5", "페이블 5"), 0)   # 원래 모델로 복귀
        self.assertNotIn("claude-fable-5", self.reg()["retired"])                # 다시 쓰는 값 = 은퇴 해제
        rc, out = self.gate()
        self.assertEqual(rc, 0, out)

    def test_follow_resyncs_and_switches_target(self):
        self.run_am("fable", "--follow", "opus")
        reg = self.reg(); reg["tiers"]["fable"]["en"] = "손 수정"
        Path(self.tmp, "shared", "models.json").write_text(json.dumps(reg, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(self.gate()[0], 1)
        self.assertEqual(self.run_am("fable", "--follow", "opus"), 0)            # 같은 대상 재실행 = 재동기
        self.assertEqual(self.gate()[0], 0)
        self.assertEqual(self.run_am("fable", "--follow", "sonnet"), 0)          # 대상 교체 = 옛 대상 호출처 검사 안 함
        fb = self.reg()["tiers"]["fable"]
        self.assertEqual((fb["id"], fb["follow"], fb["원래"]["id"]), ("claude-sonnet-5", "sonnet", "claude-fable-5"))
        self.assertIn("fable: 'Sonnet 5'", self.f("src/nm.js"))
        rc, out = self.gate()
        self.assertEqual(rc, 0, out)

    def test_rollback_with_follower_warns(self):
        self.run_am("opus", "claude-opus-5-5", "Opus 5.5", "오퍼스 5.5")
        self.run_am("fable", "--follow", "opus")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            rc = AM.main(["apply_models.py", "opus", "claude-opus-5", "Opus 5", "오퍼스 5", "--dry"])
        self.assertEqual(rc, 0)
        self.assertIn("롤백", out.getvalue())
        self.assertEqual(AM.version_of("claude-opus-5-5"), (5, 5))
        self.assertLess(AM.version_of("claude-opus-5"), AM.version_of("claude-opus-5-5"))

    def test_unknown_flag_is_refused_without_writing(self):
        before = self.f("shared/model_env.sh")
        self.assertEqual(self.run_am("opus", "claude-opus-6", "Opus 6", "오퍼스 6", "--dry-run"), 2)
        self.assertEqual(self.f("shared/model_env.sh"), before)


if __name__ == "__main__":
    unittest.main()
