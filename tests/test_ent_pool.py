# 연예 전문지 부착 풀(ENT pool) · 연합 전재 셈 회귀(운영자 260929 «수집 넓히기는 다 반영») — 네트워크 0
#   풀 = 묶기 불참 · 기존 묶음 한 곳에만 부착 · 풀 단독 사건 버림 · 홍보/사진 제외 · 스타뉴스=머니투데이 · 대표에 px 만
#   전재 = 연합과 같은 제목 + 연합 본문 첫머리 그대로 → 교차·burst 셈을 연합뉴스로(제목만 같은 재작성·[속보]는 별개)
import contextlib, csv, importlib.util, io, json, os, sys, tempfile, types, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scraper"))
for _name in ("feedparser", "requests"):
    try:
        __import__(_name)
    except ImportError:
        sys.modules[_name] = types.ModuleType(_name)
KST = timezone(timedelta(hours=9))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


K = _load("knews_pool", ROOT / "scraper" / "knews_scraper.py")
K.log = lambda msg: None
import daily_health as DH  # noqa: E402

_T = iter(range(10 ** 6))


def art(title, pub, link=None, summary="", **kw):
    i = next(_T)
    a = {"title": title, "link": link or f"https://x.kr/{i}", "publisher": pub,
         "published": "2026-09-29T0%d:%02d:00+00:00" % (1 + i // 60 % 8, i % 60), "summary": summary}
    a.update(kw)
    return a


NIT = "닛몰캐쉬 데이트 폭력 의혹 활동 중단"
GAME = "게임대상 대상 수상작 발표"


def base_arts():
    return [art(NIT, "TV리포트"), art(NIT + " 선언", "일간스포츠"), art(NIT + " 공식", "스포츠조선"),
            art(GAME, "연합뉴스"), art(GAME + " 현장", "뉴시스")]


def reps(arts):
    return {a["title"]: a for a in arts if a.get("is_cluster_rep")}


class PoolAttachTest(unittest.TestCase):
    def test_pool_adds_px_without_touching_cross_or_members(self):
        b0 = K.score_crosspost(base_arts())
        pool = [art("닛몰캐쉬 데이트 폭력 인정 활동 중단", "마이데일리"), art("닛몰캐쉬 데이트 폭력 계정 삭제 활동 중단", "조이뉴스24")]
        b1 = K.score_crosspost(base_arts(), pool)
        r0, r1 = reps(b0), reps(b1)
        self.assertEqual(r1[NIT]["px"], 2)
        self.assertEqual(r1[NIT]["cross_score"], r0[NIT]["cross_score"])                 # cross 불변
        self.assertEqual(r1[NIT]["cluster_size"], r0[NIT]["cluster_size"])               # 멤버·arts 불변(rc 입력 무접촉)
        self.assertEqual(len(r1[NIT]["cluster_members"]), len(r0[NIT]["cluster_members"]))   # 풀 url 미직렬화(바이트 예산)
        self.assertNotIn("px", r1[GAME])                                                 # 0 이면 키 없음
        self.assertTrue(all("pool" not in a for a in b1))                                # 풀 기사는 산출에 섞이지 않는다

    def test_pool_does_not_bridge_two_clusters_and_attaches_once(self):
        # 두 묶음 모두와 같은 사건으로 판정되는 풀 기사 = 다리 금지(묶음 수 그대로) · cross 가 큰 한 곳에만 부착
        a = [art("가수 김철수 신곡 발표 차트 1위", "TV리포트"), art("가수 김철수 신곡 발표 음원 1위", "일간스포츠"),
             art("가수 김철수 신곡 발표 차트 정상", "스포츠경향"),
             art("배우 김철수 결혼 발표 공식 입장", "스포츠조선")]
        bridge = art("가수 김철수 신곡 차트 결혼 입장", "텐아시아")   # 두 묶음 모두와 같은 사건 판정(겹침 4 · 3)
        tb = K.tokenize(bridge["title"])
        self.assertTrue(K.same_topic(tb, K.tokenize(a[0]["title"])) and K.same_topic(tb, K.tokenize(a[3]["title"])))   # 전제 = 양쪽과 같은 사건
        before = K.score_crosspost([dict(x) for x in a])
        after = K.score_crosspost([dict(x) for x in a], [bridge])
        self.assertEqual(sum(1 for x in before if x.get("is_cluster_rep")), sum(1 for x in after if x.get("is_cluster_rep")))
        pxs = {x["title"]: x.get("px") for x in after if x.get("is_cluster_rep")}
        self.assertEqual(sorted(v for v in pxs.values() if v), [1])
        big = max((x for x in after if x.get("is_cluster_rep")), key=lambda x: x["cross_score"])
        self.assertEqual(big.get("px"), 1)

    def test_pool_only_event_is_dropped(self):
        pool = [art("아이돌 박영희 새 예능 합류 확정", "마이데일리"), art("아이돌 박영희 새 예능 합류 확정 소감", "텐아시아")]
        out = K.score_crosspost(base_arts(), pool)
        self.assertEqual(len(out), 5)
        self.assertFalse(any("박영희" in x["title"] for x in out))
        self.assertFalse(any(x.get("px") for x in out))

    def test_promo_and_photo_titles_do_not_count(self):
        pool = [art("[MD포토] 닛몰캐쉬 데이트 폭력 활동 중단", "마이데일리"), art("닛몰캐쉬 데이트 폭력 활동 중단 [★포토]", "스타뉴스"),
                art("[사진] 닛몰캐쉬 데이트 폭력 활동 중단", "헤럴드뮤즈"), art("닛몰캐쉬 데이트 폭력 활동 중단 쇼케이스", "싱글리스트")]
        out = K.score_crosspost(base_arts(), pool)
        self.assertNotIn("px", reps(out)[NIT])
        # 대표 제목이 사진·홍보인 기존 묶음(시사회 [사진] 묶음)엔 인터뷰 기사도 붙이지 않는다
        promo = [art("[사진] 김재원 최종면접 시사회 참석", "TV리포트"), art("김재원 최종면접 시사회 참석 소감", "일간스포츠")]
        out = K.score_crosspost(promo, [art("최종면접 김재원 시사회 참석 신승호 의지", "조이뉴스24")])
        self.assertFalse(any(x.get("px") for x in out))
        for t in ("[TEN포토] 배우 입국", "[★영상] 무대", "[MD현장] 제작발표회", "영화 티저 공개"):
            self.assertTrue(K.POOL_PROMO.search(t), t)
        for t in ("[MD이슈] 닛몰캐쉬 활동 중단", "[공식] 소속사 입장", "(종합) 결혼 발표"):
            self.assertFalse(K.POOL_PROMO.search(t), t)

    def test_pool_publisher_already_in_cluster_and_alias_do_not_count(self):
        # 스타뉴스 = 머니투데이 같은 보도국(같은 기사 번호) · 이미 기존 묶음에 있는 매체는 풀에서 다시 세지 않는다
        b = base_arts() + [art(NIT + " 머니", "머니투데이")]
        pool = [art("닛몰캐쉬 데이트 폭력 활동 중단 결정", "스타뉴스"), art("닛몰캐쉬 데이트 폭력 활동 중단 발표", "TV리포트"),
                art("닛몰캐쉬 데이트 폭력 활동 중단 인정", "마이데일리"), art("닛몰캐쉬 데이트 폭력 활동 중단 사과", "마이데일리")]
        out = K.score_crosspost(b, pool)
        self.assertEqual(reps(out)[NIT]["px"], 1)   # 마이데일리 1곳만(기사 2건이어도 매체 1)
        self.assertEqual(K._cross_key({"publisher": "스타뉴스"}), "머니투데이")

    def test_pool_feed_marker_and_collect_split(self):
        self.assertTrue(K.is_pool_feed({"categories": "entertainment|pool"}))
        self.assertFalse(K.is_pool_feed({"categories": "entertainment"}))
        self.assertFalse(K.is_pool_feed({"categories": "_all_"}))
        now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
        feeds = [{"publisher": "TV리포트", "title": "전체", "categories": "entertainment", "url": "https://t.kr/r"},
                 {"publisher": "마이데일리", "title": "연예", "categories": "entertainment|pool", "url": "https://m.kr/r"}]
        parsed = [types.SimpleNamespace(entries=[{"title": NIT, "link": "https://t.kr/1", "published": now}]),
                  types.SimpleNamespace(entries=[{"title": NIT + " 인정", "link": "https://m.kr/1", "published": now},
                                                 {"title": NIT, "link": "https://t.kr/1", "published": now}])]   # 같은 url = 먼저 온 기존 피드 소유
        with mock.patch.object(K, "prefetch", lambda f: parsed):
            arts, health = K.collect(feeds, 24)
        self.assertEqual([(a["publisher"], bool(a.get("pool"))) for a in arts], [("TV리포트", False), ("마이데일리", True)])
        self.assertEqual(len(health), 2)   # 풀 피드도 건강 원장(죽음·좀비)에 남는다

    def test_feeds_csv_pool_rows(self):
        with (ROOT / "scraper" / "feeds.csv").open(encoding="utf-8") as fp:
            rows = list(csv.DictReader(fp))
        pool = [r for r in rows if K.is_pool_feed(r)]
        self.assertEqual({r["publisher"] for r in pool}, {"조이뉴스24", "마이데일리", "텐아시아", "스타뉴스", "싱글리스트", "헤럴드뮤즈"})
        self.assertTrue(all(r["url"].startswith("https://") for r in pool))
        last_base = max(i for i, r in enumerate(rows) if not K.is_pool_feed(r))
        self.assertLess(last_base, min(i for i, r in enumerate(rows) if K.is_pool_feed(r)))   # 풀 행 = 맨 뒤(같은 url 은 기존 피드 소유)
        feeds = K.load_feeds(str(ROOT / "scraper" / "feeds.csv"), K.DEFAULT_CATEGORIES)
        self.assertFalse(any(K.is_pool_feed(f) for f in feeds))   # 주요 섹션 수집(major)엔 안 들어온다


class WireReprintTest(unittest.TestCase):
    Y = "(서울=연합뉴스) 홍길동 기자 = 이재명 대통령은 29일 자주국방의 핵심 열쇠인 핵잠수함 건조와 극초음속 미사일 등 기술의 첨단화에 속도를 내야 한다고 말했다."
    T = '李대통령 "자주국방 열쇠, 핵잠 및 극초음속 미사일 속도내야"'

    def test_verbatim_reprint_counts_as_yonhap(self):
        arts = [art(self.T, "연합뉴스", summary=self.Y),
                art(self.T, "세계일보", summary="이재명 대통령은 29일 자주국방의 핵심 열쇠인 핵잠수함 건조와 극초음속 미사일 등 기술의 첨단화에 속도를 내야 한다고 말했다."),
                art(self.T.replace('"', "“", 1).replace('"', "”", 1), "SBS", summary="▲ 발언하는 이 대통령이재명 대통령은 29일 자주국방의 핵심 열쇠인 핵잠수함 건조와 극초음속 미사일 등"),
                art(self.T, "뉴시스", summary="[서울=뉴시스] 김기자 = 이재명 대통령은 29일 국방 기술 첨단화를 주문했다.")]
        K.score_crosspost(arts)
        self.assertEqual([a.get("src") for a in arts], [None, "연합뉴스", "연합뉴스", None])
        self.assertEqual({a["cross_score"] for a in arts}, {2})   # 연합 · 뉴시스
        self.assertEqual({a["burst"] for a in arts}, {2})         # burst 도 같은 셈
        self.assertEqual({a["publisher"] for a in arts}, {"연합뉴스", "세계일보", "SBS", "뉴시스"})   # 표시·링크는 그대로

    def test_same_title_rewrite_and_flash_stay_separate(self):
        t = "'암살자(들)' 제작진, 허위사실 적시 명예훼손 혐의로 고발돼"
        arts = [art(t, "연합뉴스", summary="(서울=연합뉴스) 정윤주 기자 = 육영수 여사 피격 사건을 소재로 한 영화 '암살자(들)'의 제작진이 박정희 전 대통령이 시해 사건의 배후에 있는 것처럼"),
                art(t, "파이낸셜뉴스", summary="[파이낸셜뉴스] 역사 왜곡 논란에 휩싸인 영화 '암살자(들)' 제작진이 허위사실 적시 명예훼손 혐의로 고발당했다. 이날 연합뉴스에 따르면"),
                art("[속보]李대통령 \"안보에 여야 없다\"", "연합뉴스", summary="(서울=연합뉴스) 임형섭 기자 = "),
                art("[속보] 李대통령 \"안보에 여야 없다\"", "파이낸셜뉴스", summary="[파이낸셜뉴스] cjk@fnnews.com 최종근 기자")]
        self.assertEqual(K.mark_wire_reprints(arts), 0)
        self.assertTrue(all(a.get("src") is None for a in arts))

    def test_own_dateline_and_flash_body_stay_separate(self):
        # 평의회260929 #6 — 같은 보도자료 리드라도 자사 날짜머리(독립 보도국)는 전재 아님 · 연합 속보에 본문이 실려도 속보는 대조 안 함
        lead = "산업통상자원부는 29일 올해 3분기 수출이 전년 동기 대비 8.2% 증가해 분기 기준 역대 최대치를 기록했다고 밝혔다."
        t = "3분기 수출 역대 최대…전년 대비 8.2%↑"
        arts = [art(t, "연합뉴스", summary="(세종=연합뉴스) 김기자 = " + lead),
                art(t, "뉴시스", summary="[세종=뉴시스] 이기자 = " + lead)]
        self.assertEqual(K.mark_wire_reprints(arts), 0)
        f = "[속보] 李대통령 \"안보에 여야 없다…국방 예산 대폭 증액 추진하겠다\""
        body = "이재명 대통령은 29일 안보에 여야가 없다며 국방 예산을 대폭 증액하는 방안을 추진하겠다고 말했다."
        arts = [art(f, "연합뉴스", summary="(서울=연합뉴스) 임기자 = " + body), art(f, "JTBC", summary=body), art(f, "세계일보", summary=body)]
        self.assertEqual(K.mark_wire_reprints(arts), 0)

    def test_stock_code_and_hanja_title_key(self):
        y = "(서울=연합뉴스) 박기자 = OCI[010060]가 29일 폴리실리콘 공장 증설에 1조원을 투자한다고 밝혔다. 회사는 내년 하반기 가동을 목표로 한다."
        t = "OCI, 폴리실리콘 공장 증설에 1조원 투자"
        arts = [art(t, "연합뉴스", summary=y), art(t, "세계일보", summary="OCI가 29일 폴리실리콘 공장 증설에 1조원을 투자한다고 밝혔다. 회사는 내년 하반기 가동을 목표로 한다.")]
        self.assertEqual(K.mark_wire_reprints(arts), 1)                          # 종목코드 제거 뒤 대조
        a1 = [art('與 "특검 수용 불가"', "연합뉴스", summary="(서울=연합뉴스) 김기자 = " + "여야는 29일 특검 법안을 두고 정면으로 충돌하며 협상이 결렬됐다고 밝혔다."),
              art('野 "특검 수용 불가"', "세계일보", summary="여야는 29일 특검 법안을 두고 정면으로 충돌하며 협상이 결렬됐다고 밝혔다.")]
        self.assertEqual(K.mark_wire_reprints(a1), 0)                            # 제목 키 = 한자 보존

    def test_existing_author_src_is_not_overridden(self):
        arts = [art(self.T, "연합뉴스", summary=self.Y), art(self.T, "조선일보", summary=self.Y[20:], src="뉴시스")]
        K.mark_wire_reprints(arts)
        self.assertEqual(arts[1]["src"], "뉴시스")


def cand(url, cross, px=0, rc=1, pub_h=10.0, **kw):
    c = {"id": url, "url": url, "title": f"사건 {url}", "cross": cross, "report_count": rc,
         "published": (datetime.now(timezone.utc) - timedelta(hours=pub_h)).isoformat(),
         "first_seen": (datetime.now(KST) - timedelta(hours=pub_h)).strftime("%Y-%m-%dT%H:%M:%S%z")}
    if px:
        c["px"] = px
    c.update(kw)
    return c


class EffectiveCrossTest(unittest.TestCase):
    def test_cum_enter_uses_effective_cross(self):
        self.assertTrue(DH._cum_enter(cand("a", 7, px=2)))          # 7 + 0.5×2 = 8
        self.assertFalse(DH._cum_enter(cand("b", 7, px=1)))         # 7.5
        self.assertFalse(DH._cum_enter(cand("c", 7)))
        self.assertTrue(DH._cum_enter(cand("d", 3, px=2, rc=6)))    # followEnters 실효 4
        self.assertFalse(DH._cum_enter(cand("e", 3, px=1, rc=6)))
        self.assertEqual(DH._eff_cross({"cross": 7, "px": 4}), 9)

    def test_screen_merge_sums_px(self):
        m = DH.screen_merge([cand("g", 5, px=1, group_id="g"), cand("h", 2, px=2, group_id="g"), cand("i", 3)])
        anchor = [x for x in m if x["url"] == "g"][0]
        self.assertEqual((anchor["cross"], anchor["px"]), (7, 3))
        self.assertTrue(DH._cum_enter(anchor))   # 7 + 1.5

    def test_orphan_gauge_ignores_pool_feeds(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "scraper" / "obs").mkdir(parents=True)
            (root / "viewer").mkdir()
            (root / "scraper" / "feeds.csv").write_text(
                "publisher,title,categories,url\n연합뉴스,전체,_all_,https://y.kr/r\n마이데일리,연예,entertainment|pool,https://m.kr/r\n",
                encoding="utf-8")
            (root / "scraper" / "obs" / "feed_health.json").write_text(json.dumps({"ok": 2, "dead_feeds": [], "zombie_feeds": []}), encoding="utf-8")
            (root / "viewer" / "candidates.json").write_text(json.dumps([cand("z", 3, media="연합뉴스")], ensure_ascii=False), encoding="utf-8")
            with mock.patch.multiple(DH, ROOT=root, CAND=root / "viewer" / "candidates.json", SUBS=root / "push" / "s.json",
                                     SCRIPTS=root / "none", git=lambda *a: ""):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    DH.main()
        out = buf.getvalue()
        self.assertIn("RSS 피드 생존", out)
        self.assertNotIn("orphan", out)   # 부착 풀은 대표가 될 수 없는 설계 = orphan 경보 대상 아님


class CandidatesPxTest(unittest.TestCase):
    def run_tc(self, arts, existing):
        m = _load("tc_pool", ROOT / "scraper" / "to_candidates.py")
        with tempfile.TemporaryDirectory() as d:
            m.SRC = Path(d) / "articles.json"
            m.DST = Path(d) / "candidates.json"
            m.SRC.write_text(json.dumps(arts, ensure_ascii=False), encoding="utf-8")
            m.DST.write_text(json.dumps(existing, ensure_ascii=False), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                m.main()
            return {c["url"]: c for c in json.loads(m.DST.read_text(encoding="utf-8"))}

    def rep(self, url, cross, **kw):
        a = {"title": f"사건 {url}", "link": url, "publisher": "연합뉴스", "category": "_all_",
             "published": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
             "cross_score": cross, "cluster_size": cross, "is_cluster_rep": True, "burst": 1,
             "cluster_members": [url]}
        a.update(kw)
        return a

    def test_px_carried_only_when_positive_and_not_sticky(self):
        out = self.run_tc([self.rep("https://a.kr/1", 7, px=3), self.rep("https://a.kr/2", 5)], [])
        self.assertEqual(out["https://a.kr/1"]["px"], 3)
        self.assertNotIn("px", out["https://a.kr/2"])          # 0 = 키 없음(바이트 예산)
        prev = dict(out["https://a.kr/1"])
        out2 = self.run_tc([self.rep("https://a.kr/1", 7)], [prev])
        self.assertNotIn("px", out2["https://a.kr/1"])         # 이번 회차 부착 0 = 지난 px 소거
        self.assertEqual(out2["https://a.kr/1"]["report_count"], prev["report_count"])   # arts 불변 = rc 무증가


if __name__ == "__main__":
    unittest.main()
