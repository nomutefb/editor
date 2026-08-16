#!/usr/bin/env python3
# 편집 발사 자동 트래킹 — 편집 폼(기타 옵션)에서 켠 가림·키잉·크로마키를 **트래킹 탭을 안 거치고** 그 자리에서 적용.
#   사용: edit_track.py <id> <입력mp4> [pre|post]
#     pre  = **컴포즈 앞** — 픽셀에 굽는 계열(모자이크·핀셋). 산출 경로를 /tmp/edit_track_pre.txt 에 도장하면
#            워크플로가 그걸 EDIT_SRC로 갈아끼워 ly_burn이 그 위에 자막을 얹는다 = **자막이 모자이크보다 위**.
#     post = **컴포즈 뒤** — 알파를 만드는 계열(키잉·실루엣·크로마키). 알파 산출은 종점이라 자막 번인 뒤가 맞다.
#   env: OPTS = 편집 옵션 JSON — 이 스크립트가 읽는 축은 opts.xtr 하나뿐
#        R2_*  = 최종 산출 업로드(미설정 = ly_burn과 동일하게 git 폴백)
#
# 왜 이 파일이 있나(운영자 260808 "모자이크 누르고 옵션 선택한 다음에 생성 누르면 트래킹해서 모자이크까지 자동으로"):
#   구판 = 편집 폼의 기타 옵션은 **발사 옵션이 아니었다**(edit.html 650행 주석 "발사 옵션 아님"). 켜도 생성에 안 실리고,
#   [트래킹] 버튼으로 track.html에 넘어가 ① 영상을 **다시 첨부**하고 ② 분석을 기다렸다가 ③ 인물을 손으로 고르고
#   ④ 거기서 또 렌더를 눌러야 했다 — 편집 탭에서 켠 옵션이 그 화면에선 **아무 일도 안 하는 것처럼 보이는** 것이 사고의 실체.
#   이 스크립트가 ②③④를 자동으로 대신한다(인물 선택 = 검출된 전원 = 가림의 안전측 기본값).
#
# 계약:
#   · 대상 자동 선정 = 검출 전원(가림은 빠뜨리는 쪽이 사고 · track_render 원칙 ③ 과잉 커버 편향 계승)
#   · 체인 = 모자이크 → 핀셋 → (키잉|실루엣|크로마키 중 하나 = 알파 산출이라 종점)
#   · 전면 fail-soft = 트래킹이 실패해도 **편집 산출물은 그대로 살아 있다**(rc 0 · video.json의 url 무접촉 + xtr_note 기록)
#   · 순서 = 픽셀 번인(모자이크·핀셋)은 **자막보다 먼저** 구워야 한다(운영자 260809 "모자이크가 자막 위로 올라가버려서
#     자막이 가려져"). 구판은 컴포즈 뒤 한 지점에서 전부 처리해 **자막 위에 모자이크가 덮였다**.
#   · 좌표계 = pre는 원본 기준으로 분석·번인한다. 크롭·해상도가 뒤에 와도 **모자이크가 픽셀에 이미 구워져 있어 같이 변형**되므로
#     좌표가 어긋나지 않는다(구판 주석의 「원본 기준 분석은 크롭 시 어긋난다」는 가림을 컴포즈 뒤에 걸 때만 성립하던 이야기다)
# CONTRACT: check_edit_track_chain — 뷰어 xtr 송신 → api 화이트리스트 → 이 스크립트 → 워크플로 스텝이 한 벌로 살아 있어야 한다
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRACK_DIR = os.path.join(ROOT, "apps", "track")
sys.path.insert(0, os.path.join(ROOT, ".github", "scripts"))

MAX_KEEP = 4          # 키잉·실루엣 피사체 상한 = api/track.js·track_keying 동값(SAM2 패스 수 = 시간 비례)
MAX_TARGETS = 32      # 가림 대상 상한 = api/track.js 동값
GIT_FALLBACK_MAX = 30 * 1024 * 1024

# 모드별 로컬 산출 경로 — track_render/keying/chroma가 **R2 성공 여부와 무관하게** 먼저 만드는 파일(실측 고정 경로).
#   R2 업로드는 그 뒤 단계라, 여기서는 env에서 R2를 빼고 호출해 업로드를 건너뛰고 이 파일만 이어받는다(이중 업로드 0).
LOCAL_OUT = {
    "mosaic": ("/tmp/track_result.mp4", None),
    "pinset": ("/tmp/track_result.mp4", None),
    "maskfx": ("/tmp/maskfx_out.mp4", None),
    "keying": ("/tmp/key_master.mov", "/tmp/key_preview.webm"),
    "chroma": ("/tmp/chroma_out/chroma.mov", "/tmp/chroma_out/chroma_preview.webm"),
}


def log(m):
    print("[edit_track] " + m, flush=True)


def norm_xtr(o):
    """편집 폼 XTR → 정규화. 켠 게 없으면 None(= 무동작)."""
    x = o.get("xtr")
    if not isinstance(x, dict):
        return None
    on = {k: bool(x.get(k)) for k in ("mosaic", "pinset", "keying", "silh", "chroma")}
    if not any(on.values()):
        return None
    return on, x


def _num(v, lo, hi, dflt):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return dflt
    if f != f:   # NaN
        return dflt
    return max(lo, min(hi, f))


def run_py(script, args, env_extra=None, timeout=2400):
    """apps/track 스크립트 호출 — R2 자격증명을 **뺀** 환경(업로드 스킵 = 로컬 산출만 받는다)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("R2_")}
    env["NOMUTE_TRACK_MODELS"] = os.environ.get("NOMUTE_TRACK_MODELS", os.path.expanduser("~/.cache/nomute-track"))
    if env_extra:
        env.update(env_extra)
    r = subprocess.run([sys.executable, os.path.join(TRACK_DIR, script)] + args,
                       env=env, timeout=timeout)
    return r.returncode


def analyze(tid, src):
    rc = run_py("track_analyze.py", [tid, src], timeout=1800)
    doc_p = os.path.join("viewer", "track_out", tid, "tracks.json")
    if rc != 0 or not os.path.isfile(doc_p):
        return None
    try:
        return json.load(open(doc_p, encoding="utf-8"))
    except Exception:
        return None


def stub_tracks(tid, src):
    """크로마키 단독 = 인물 검출이 필요 없다(색만 뺀다) → 분석 스킵 + 최소 tracks.json.
    (track_render.main이 tracks.json 실존을 요구하는 계약만 충족 · 모델 다운·분석 시간 0)"""
    outdir = os.path.join("viewer", "track_out", tid)
    os.makedirs(outdir, exist_ok=True)
    ext = (os.path.splitext(src)[1].lstrip(".") or "mp4")
    shutil.copyfile(src, os.path.join(outdir, "src." + ext))
    doc = {"meta": {"src": f"track_out/{tid}/src.{ext}"}, "people": [], "subjects": []}
    json.dump(doc, open(os.path.join(outdir, "tracks.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return doc


def set_src(tid, doc, src):
    """체인 다음 단계의 입력 = 직전 단계 산출. tracks.json meta.src를 그 파일로 갈아끼운다
    (해상도·프레임수가 그대로라 분석 좌표는 유효 — 재분석 0)."""
    outdir = os.path.join("viewer", "track_out", tid)
    ext = (os.path.splitext(src)[1].lstrip(".") or "mp4")
    dst = os.path.join(outdir, "src." + ext)
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copyfile(src, dst)
    doc.setdefault("meta", {})["src"] = f"track_out/{tid}/src.{ext}"
    json.dump(doc, open(os.path.join(outdir, "tracks.json"), "w", encoding="utf-8"), ensure_ascii=False)


def render(tid, payload, mode):
    """track_render 1회 — 성공 판정은 video.json이 아니라 **로컬 산출 파일 실존**(R2를 뺐으므로
    업로드 단계에서 fail-soft 에러가 기록돼도 영상 자체는 이미 만들어져 있다)."""
    main_p, prev_p = LOCAL_OUT[mode]
    for p in (main_p, prev_p):
        if p and os.path.isfile(p):
            os.remove(p)   # 직전 단계 산출 제거 = 실패를 성공으로 오인 차단
    run_py("track_render.py", [tid], {"RENDER": json.dumps(payload, ensure_ascii=False)})
    if not (os.path.isfile(main_p) and os.path.getsize(main_p) > 1024):
        return None, None
    return main_p, (prev_p if (prev_p and os.path.isfile(prev_p)) else None)


ALPHA_NOOP_MIN = 254.5   # 알파 평균이 이 위 = 뺀 화소가 사실상 0(실측 근거 = 아래 _alpha_note 독스트링 표)
ALPHA_GONE_MAX = 0.5     # 이 아래 = 화면이 통째로 비었다(0 = 전 화소 투명 = 퇴화 끝점이라 보정이 필요한 값이 아니다)


def _alpha_mean(path):
    """알파 프리뷰(webm)의 알파 평면 평균(0~255). 못 재면 None(= 판정 유보).
    ⚠ `-vcodec libvpx-vp9` 명시가 실효 조건 — 기본 디코더는 WebM 알파(BlockAdditions)를 안 읽어
      **정상 알파 파일도 통계가 0줄**로 나온다(실측). 다행히 그건 조용한 거짓 255가 아니라 시끄러운 무출력이라
      「데이터 0줄 = 판정 유보」로 받으면 오판이 구조적으로 불가능하다.
    ⚠ 초당 2프레임 샘플링 = 전수 대비 값 차이가 소수점 둘째 자리까지 0인데 비용은 1/3.5(실측 10초 영상
      전수 2.5s → 샘플 0.72s ≈ 원본 1초당 0.07s). 300초 캡에서도 파이프 전체의 1~3%."""
    try:
        r = subprocess.run(["ffmpeg", "-v", "error", "-vcodec", "libvpx-vp9", "-i", path,
                            "-vf", "fps=2,alphaextract,signalstats,"
                                   "metadata=print:key=lavfi.signalstats.YAVG:file=-",
                            "-f", "null", "-"], capture_output=True, text=True, timeout=300)
    except Exception as e:
        log("알파 측정 건너뜀: " + str(e)[:80])
        return None
    vals = []
    for ln in ((r.stdout or "") + "\n" + (r.stderr or "")).splitlines():
        if "YAVG=" in ln:
            try:
                vals.append(float(ln.split("YAVG=", 1)[1].strip()))
            except ValueError:
                pass
    return (sum(vals) / len(vals)) if vals else None


def _alpha_note(path, mode):
    """「돌긴 돌았는데 아무것도 안 뺐다」를 말로 바꾼다. 할 말이 없으면 None.

    ⚠ 왜 필요한가(운영자 260816 "키잉, 하고 크로마키는 정상적으로 동작을 안해") = 크로마키는 **그린스크린으로 찍은
      영상에서만** 원리적으로 동작하는데, 일반 실사 영상에 걸면 지울 색이 화면에 없어서 **뺀 화소가 0인 채로
      성공**한다. 러너는 초록이고 산출물도 정상이고 화면에도 영상이 뜬다 — 원본과 똑같은 영상이. 그래서 어느
      층도 안 울리고 운영자 눈이 유일한 검출기였다(insta-thumb-miss·brk_misfire 동축).
      실측 = 운영자의 그 크로마키 산출은 알파 평균 **255.0이 400프레임 균일**이었다(= 한 화소도 안 뺐다).

    임계 254.5 근거(합성 8종 + 실제 산출 2종 실측 · 뺀 비율이 초록 면적과 1:1 선형이라 자가 검증됨):
      · 초록 0(일반 실사)        평균 255.00 · 뺀 비율 0.00%   ← 사고 축
      · 실제 사고분(운영자 산출)  평균 255.0 균일 · 0.00%       ← 사고 축
      · 자연 초록(잔디)          평균 254.88 · 0.05%           ← 야외 실사도 이쪽
      · 화면 0.3% 초록           평균 254.21 · 0.31%           ← 여기부터는 뭔가 뺐다
      · 그린스크린               평균  32.46 · 87.27%
      · 실제 정상 키잉(운영자)    평균  68.7~69.1 · 73%
      유효 구간 (254.21, 254.88) 의 중앙 = 254.5(양쪽 여유 0.29·0.38). 손실 인코딩 왕복 뒤에도 진짜
      무동작은 정확히 255.00으로 떨어져서(합성·실물 둘 다) 이 마진이면 충분하다.

    ⚠ 문구는 새로 짓지 않았다 — 앞절 골격은 216행 「영상에서 사람을 못 찾아서 …」, 꼬리는 193행 「 — …해줘」,
      기능 이름은 화면 라벨 그대로(크로마키 = 특정 색 빼기 · 키잉 = 피사체만 남김)를 가져왔다.
      ⚠ 대안으로 「실루엣」은 안 권한다 = 그 카드는 260728부터 화면에서 숨겨져 있어(edit.html) 없는 버튼을
      누르라는 오안내가 된다."""
    m = _alpha_mean(path)
    if m is None:
        log("알파 판정 유보 — 측정값 0줄(%s)" % os.path.basename(path))
        return None
    log("알파 평균 %.2f/255 (%s)" % (m, mode))
    if m >= ALPHA_NOOP_MIN:
        if mode == "chroma":
            return ("영상에서 지정한 색을 거의 못 찾아서 뺀 것 없이 그대로야 — "
                    "초록 배경으로 찍은 영상이 아니면 크로마키 대신 키잉(피사체만 남김)을 써줘.")
        return "영상에서 피사체를 못 가려내서 배경이 그대로 남았어 — 트래킹 탭에서 수동으로 해줘."
    if m <= ALPHA_GONE_MAX:
        if mode == "chroma":
            return ("지정한 색이 화면 거의 전부라 통째로 지워졌어 — 강도를 낮춰서 다시 해줘.")
        return "피사체를 못 붙잡아서 화면이 통째로 비었어 — 트래킹 탭에서 수동으로 해줘."
    return None


def main():
    if len(sys.argv) < 3:
        log("인자 부족 — 스킵")
        return 0
    vid_id, src = sys.argv[1], sys.argv[2]
    phase = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] in ("pre", "post") else "post"
    try:
        opts = json.loads(os.environ.get("OPTS") or "{}")
    except Exception:
        opts = {}
    if not isinstance(opts, dict):
        opts = {}
    nx = norm_xtr(opts)
    if not nx:
        log("xtr 없음 — 스킵")
        return 0
    on, x = nx
    if not os.path.isfile(src):
        log("입력 영상 없음 — 스킵: " + src)
        return 0

    outdir = os.path.join("viewer", "ly_out", vid_id)
    vj_p = os.path.join(outdir, "video.json")
    try:
        vj = json.load(open(vj_p, encoding="utf-8"))
    except Exception:
        vj = {}
    # ⚠ 컴포즈 error가 있어도 **진행한다** — 편집 축 없이 가림만 켜고 생성하면(운영자 주 시나리오) ly_burn은 합성할 게 없어
    #   "자막 타이밍 데이터 없음"을 error로 쓰고 끝난다(실측 260808). 그건 이 잡의 실패가 아니라 **컴포즈할 게 없었다**는 뜻이고,
    #   호출자가 유효한 입력 영상을 쥐어준 이상 가림 산출물이 곧 이 잡의 결과다. 성공하면 그 error를 걷어낸다(아래 vj.pop).
    #   실패하면 기존 error가 그대로 남아 화면 문구가 종전과 동일 = 회귀 0.
    if vj.get("error"):
        log("컴포즈 산출 없음(error=%s) — 입력 영상에 직접 적용" % str(vj.get("error"))[:40])

    tid = vid_id   # 트래킹 작업폴더 = 같은 id(viewer/track_out/<id> · 커밋 스텝은 ly_out만 add = 레포 무오염)
    order = [m for m in ("mosaic", "pinset") if on[m]] if phase == "pre" else []
    endpoint = ("chroma" if on["chroma"] else "keying" if on["keying"] else "maskfx" if on["silh"] else "") if phase == "post" else ""
    if not order and not endpoint:
        if phase == "post":   # 알파 축이 없어도 pre가 구운 게 있으면 최종 기록에 남긴다(컴포즈가 video.json을 새로 쓰므로 여기서만 가능)
            try:
                pre_done = json.load(open("/tmp/edit_track_done.json", encoding="utf-8"))
            except Exception:
                pre_done = []
            faces = _pre_faces()
            if pre_done or faces:
                if pre_done:
                    vj["xtr"] = pre_done
                if faces:
                    vj["faces"] = faces
                json.dump(vj, open(vj_p, "w", encoding="utf-8"), ensure_ascii=False)
                log("pre 적용분 기록: %s · 얼굴 %d" % (",".join(pre_done), len(faces)))
        log("이 단계(%s)에서 적용할 축 없음 — 스킵" % phase)
        return 0
    log("[%s] 적용 축: %s" % (phase, ",".join(order + ([endpoint] if endpoint else []))))

    need_analyze = bool(order) or endpoint in ("keying", "maskfx")
    doc = analyze(tid, src) if need_analyze else stub_tracks(tid, src)
    if doc is None:
        log("분석 실패 — 편집본 그대로 둔다")
        vj["xtr_note"] = "인물 분석에 실패해서 가림을 못 넣었어 — 트래킹 탭에서 수동으로 해줘."
        json.dump(vj, open(vj_p, "w", encoding="utf-8"), ensure_ascii=False)
        return 0

    pids = [p["pid"] for p in (doc.get("people") or []) if isinstance(p.get("pid"), int)][:MAX_TARGETS]
    sids = []
    for s in (doc.get("subjects") or []):
        try:
            sids.append(int(s.get("sid")))
        except (TypeError, ValueError):
            continue
    sids = sids[:MAX_KEEP]

    mo = {"shape": "ellipse" if x.get("shape") == "ellipse" else "rect",
          "pxw": int(_num(x.get("pxw"), 3, 20, 9)), "pxh": int(_num(x.get("pxh"), 3, 20, 9)),
          "size": round(_num(x.get("size"), 75, 250, 115) / 100.0, 3),   # 폼은 % 정수(115) · 러너는 배율(1.15)
          "feather": int(_num(x.get("feather"), 0, 40, 5))}

    cur, prev = src, None
    done = []
    for mode in order:
        if not pids:
            log(mode + " 스킵 — 검출된 인물 0명")
            vj["xtr_note"] = "영상에서 사람을 못 찾아서 가림을 못 넣었어."
            break
        set_src(tid, doc, cur)
        payload = {"mode": mode, "targets": pids, "invert": False, "opts": mo}
        if mode == "pinset":
            # 핀셋 대상 = **이름이 붙은 인물만**(track_render sel 산식 = names 키 기반 — 이름표 기능이라 이름이 없으면 그릴 라벨이 없다).
            #   ⚠ 이 배정이 없으면 sel이 공집합이라 "선택된 인물이 없어"로 그 단계가 통째로 스킵된다(실측 260808 체인 첫 실행).
            #   운영자가 넣은 이름(쉼표 구분)을 **등장 순서대로** 배정한다(운영자 260809 2트랙 ② — pids는 분석이 첫 등장 순으로 준다).
            #   모자란 자리는 track_render 폴백 표기 그대로 f"#{pid}"(문구 창작 0) = 1차 생성에서 누가 몇 번인지 확인하고 다시 넣으면 된다.
            # 이름 = **{pid: 이름} 맵**(운영자 260809 "같은 인물인데 #n개로 나올수도 있거든 · 이를 묶어서 하나의 이름으로").
            #   같은 사람이 화면 밖으로 나갔다 들어오면 분석은 그걸 **다른 pid로** 준다(#1·#3·#4가 사실 한 사람).
            #   여러 pid에 같은 이름을 주면 track_render가 그대로 묶어 그린다 = 묶음은 이 맵 하나로 표현된다.
            #   ⚠ 맵에 **없는 pid는 라벨을 안 그린다**(track_render sel = names 키 기반) = 「미지정 = 표기 안 함」이 곧 계약.
            #     구판은 남는 자리를 "#N"으로 채워서 **원치 않는 번호표가 강제로 붙었다** — 그 폴백을 없앤다.
            nm = x.get("names")
            got = {}
            if isinstance(nm, dict):
                for k, v in nm.items():
                    try:
                        pid_i = int(k)
                    except (TypeError, ValueError):
                        continue
                    lab = str(v).strip()[:24]
                    if lab and pid_i in pids:
                        got[str(pid_i)] = lab
            elif isinstance(nm, str) and nm.strip():   # 구판 쉼표 문자열 = 등장 순 배정(하위호환 · 직접 dispatch 경로)
                want = [n.strip()[:24] for n in nm.split(",") if n.strip()]
                got = {str(p): want[i] for i, p in enumerate(pids) if i < len(want)}
            if not got:   # 이름이 하나도 없으면 종전대로 전원 번호표(1차 생성 = 누가 몇 번인지 보는 단계)
                got = {str(p): "#%d" % p for p in pids}
            payload["names"] = got
            cm = x.get("colors")   # 이름표 글자색 {pid:#hex}(운영자 260810) — 미동봉 pid = 렌더 기본(흰) · 6자리 hex만(track_render hex_bgr 계약)
            if isinstance(cm, dict):
                cols = {}
                for k, v in cm.items():
                    try:
                        pid_i = int(k)
                    except (TypeError, ValueError):
                        continue
                    v = str(v).strip()
                    if pid_i in pids and len(v) == 7 and v[0] == "#" and all(c in "0123456789abcdefABCDEF" for c in v[1:]):
                        cols[str(pid_i)] = v
                if cols:
                    payload["colors"] = cols
        got, _p = render(tid, payload, mode)
        if not got:
            log(mode + " 렌더 실패 — 직전 산출로 계속")
            vj["xtr_note"] = f"{mode} 처리에 실패해서 그 단계는 빠졌어."
            break
        keep = f"/tmp/edit_track_{mode}.mp4"   # 체인 다음 단계가 같은 /tmp 경로를 덮어쓰므로 즉시 보존
        shutil.copyfile(got, keep)
        cur, done = keep, done + [mode]

    if endpoint:
        set_src(tid, doc, cur)
        if endpoint == "chroma":
            sim = _num(x.get("cksim"), 1, 50, 18) / 100.0   # 폼 강도 = % 정수(18) · ffmpeg chromakey similarity = 0~1
            payload = {"mode": "chroma", "opts": {
                "color": {"blue": "#0000FF"}.get(x.get("ckcolor"), "#00FF00"),
                "similarity": round(sim, 3), "choke": int(_num(x.get("ckchoke"), -4, 4, 0)),
                "feather": int(_num(x.get("ckfe"), 0, 10, 1)), "despill": 0.5, "blend": 0.05, "edge": "high"}}
        elif sids:
            payload = {"mode": endpoint, "keep": sids, "keepP": [], "extra": [],
                       "opts": {"feather": int(_num(x.get("sfe") if endpoint == "maskfx" else x.get("kfe"), 0, 40,
                                                    8 if endpoint == "maskfx" else 0))}}
            if endpoint == "maskfx":
                payload["fill"] = "image" if x.get("fill") == "image" else "mosaic"
                if payload["fill"] == "image":
                    payload["preset"] = x.get("preset") if x.get("preset") in ("smile", "black", "heart") else "smile"
        else:
            payload = None
            log(endpoint + " 스킵 — 대상 피사체 0개")
            vj["xtr_note"] = "영상에서 피사체를 못 찾아서 그 단계는 빠졌어."
        if payload:
            got, gotp = render(tid, payload, endpoint)
            if got:
                cur, prev, done = got, gotp, done + [endpoint]
            else:
                log(endpoint + " 렌더 실패 — 직전 산출로 계속")
                vj["xtr_note"] = f"{endpoint} 처리에 실패해서 그 단계는 빠졌어."

    if not done:
        if phase == "post":
            json.dump(vj, open(vj_p, "w", encoding="utf-8"), ensure_ascii=False)
        return 0

    if phase == "pre":
        _publish_faces(vid_id, tid, doc, outdir, vj, vj_p)   # 얼굴 썸네일 게시(운영자 260809 "아이디어대로가 100% 맞음")
        # 컴포즈 입력으로 넘긴다 = 워크플로가 EDIT_SRC를 이 경로로 갈아끼운다 → ly_burn이 **이 위에** 자막을 얹는다.
        #   video.json은 손대지 않는다(그건 뒤따르는 컴포즈가 쓴다) · 적용 축만 남겨 post가 최종 기록에 합친다.
        keep = "/tmp/edit_track_pre.mp4"
        if os.path.abspath(cur) != os.path.abspath(keep):
            shutil.copyfile(cur, keep)
        with open("/tmp/edit_track_pre.txt", "w", encoding="utf-8") as f:
            f.write(keep)
        with open("/tmp/edit_track_done.json", "w", encoding="utf-8") as f:
            json.dump(done, f, ensure_ascii=False)
        log("pre 완료 — " + ",".join(done) + " → 컴포즈 입력으로 전달")
        return 0

    try:   # pre 단계가 이미 구운 축을 최종 기록에 합친다(모자이크+키잉 동시 선택 시 둘 다 남아야 한다)
        done = json.load(open("/tmp/edit_track_done.json", encoding="utf-8")) + done
    except Exception:
        pass

    # ── 산출 교체 = 편집 결과 자리(ly_out/<id>)에 덮어쓴다. 뷰어·알림·결과 레일 배선은 종전 그대로(경로 불변).
    import time
    bust = int(time.time())
    alpha = cur.endswith(".mov")
    ext = "mov" if alpha else "mp4"
    ctype = "video/quicktime" if alpha else "video/mp4"
    url = ""
    try:
        url = _upload(cur, f"ly_out/{vid_id}/subbed.{ext}", ctype) or ""
    except Exception as e:
        log("R2 업로드 실패: " + str(e)[:120])
    if not url and os.path.getsize(cur) <= GIT_FALLBACK_MAX:
        shutil.copyfile(cur, os.path.join(outdir, f"subbed.{ext}"))
        url = f"ly_out/{vid_id}/subbed.{ext}"
    pv = ""
    if prev:   # 알파 산출(키잉·크로마키) = 뷰어 <video>가 재생할 수 있는 webm 프리뷰 동반(MOV는 브라우저 재생 불가)
        try:
            pv = _upload(prev, f"ly_out/{vid_id}/preview.webm", "video/webm") or ""
        except Exception:
            pv = ""
        if not pv and os.path.getsize(prev) <= GIT_FALLBACK_MAX:
            shutil.copyfile(prev, os.path.join(outdir, "preview.webm"))
            pv = f"ly_out/{vid_id}/preview.webm"
    if not url and not pv:
        log("업로드 실패 + git 폴백 초과 — 편집본 그대로 둔다")
        vj["xtr_note"] = "가림은 됐는데 결과를 못 올렸어 — 다시 생성해줘."
        json.dump(vj, open(vj_p, "w", encoding="utf-8"), ensure_ascii=False)
        return 0

    # ⚠ 화면 재생 = **webm 프리뷰 우선**(260809 실사고) — 알파 마스터는 ProRes 4444 MOV라 **브라우저가 재생을 못 한다**.
    #   러너 로그는 「크로마키 완료 · 마스터 71MB」로 성공인데 화면엔 아무것도 안 나와 운영자에겐 "작동 안 함"으로 보였다.
    #   url = 재생 가능한 프리뷰 / master = 편집용 알파 원본(다운로드·후속 배선용 보존) · 비알파(모자이크·핀셋)는 종전 그대로.
    if alpha and pv:
        vj["url"] = f"{pv}?v={bust}"
        if url:
            vj["master"] = f"{url}?v={bust}"
    else:
        vj["url"] = (f"{url}?v={bust}" if url else f"{pv}?v={bust}")   # 마스터 유실 = 프리뷰라도 살린다(track_keying "master-lost" 계승)
    vj["bytes"] = os.path.getsize(cur if url else prev)
    vj["xtr"] = done
    if pv:
        vj["preview"] = f"{pv}?v={bust}"
    if not url:
        vj["note"] = "master-lost"   # 뷰어가 정직 표시(다운로드용 알파 마스터 없음 · 화면 재생은 프리뷰) — track_keying·track_chroma 동일 문자열
    vj.pop("xtr_note", None)
    # ⚠ 「조용한 무동작」 검문 — 자리가 계약이다. 바로 윗줄 pop이 **성공 회차의 사유까지 지우므로**
    #   이 판정은 반드시 pop **뒤**에 와야 한다(앞에 두면 쓰자마자 지워져 화면에 영영 안 뜬다).
    #   대상 = 알파를 만드는 두 축(크로마키·키잉) — 한 자리로 둘 다 덮는다. 엔진 쪽(track_chroma·track_keying)에
    #   각각 넣으면 사본 2벌이 되고, 그건 이 레포가 반복해 겪은 「형제 한쪽만 낡는」 드리프트다.
    #   실루엣(maskfx)은 프리뷰가 없어(LOCAL_OUT) 자연 제외 = 알파가 없는 산출이라 이 축의 대상이 아니다.
    #   전면 fail-soft = 측정이 실패하든 값이 애매하든 산출물·url은 무접촉이고 rc는 그대로 0.
    #   끄기 = EDIT_ALPHA_PROBE=0(종전 동작 100% 복귀).
    if alpha and prev and endpoint in ("chroma", "keying") and os.environ.get("EDIT_ALPHA_PROBE", "1") != "0":
        try:
            _an = _alpha_note(prev, endpoint)
            if _an:
                vj["xtr_note"] = _an
        except Exception as e:
            log("알파 판정 건너뜀: " + str(e)[:80])
    _f = _pre_faces()
    if _f:
        vj["faces"] = _f
    vj.pop("error", None)   # 산출이 실제로 나왔으니 컴포즈 단계의 "합성할 게 없었다" 기록은 걷는다(남기면 뷰어가 실패로 표시 = 결과가 있는데 못 보는 사고)
    vj.pop("skip", None)
    json.dump(vj, open(vj_p, "w", encoding="utf-8"), ensure_ascii=False)
    _mirror_vj(vid_id, vj)
    log("완료 — " + ",".join(done) + " · " + str(os.path.getsize(cur) // 1048576) + "MB")
    return 0


def _pre_faces():
    """pre가 남긴 얼굴 목록(컴포즈가 video.json을 새로 쓰므로 최종 기록은 post 몫)."""
    try:
        return json.load(open("/tmp/edit_track_faces.json", encoding="utf-8")) or []
    except Exception:
        return []


def _publish_faces(vid_id, tid, doc, outdir, vj, vj_p):
    """분석이 뽑아둔 인물 크롭을 편집 결과 자리로 옮겨 화면이 읽게 한다(운영자 260809 승인).
    ⚠ 왜 필요한가 = 2트랙 ①에서 「#1이 누구냐」를 알려면 **영상을 재생해서 찾아야** 했다. 그런데 분석은
      이미 인물별 얼굴 크롭(crops/pN.jpg)을 뽑아두고도 아무도 안 읽고 있었다 — 새 분석·새 과금 0, 파일 옮기기뿐.
    ⚠ 거처가 ly_out인 이유 = edit-make의 Commit output은 `viewer/ly_out/<id>`만 add한다. track_out에 두면
      커밋이 안 돼 **화면에서 영영 안 보인다**(조용한 죽음) · R2가 있으면 R2 우선(배포 지연 회피 · 실패 = git 폴백)."""
    try:
        people = doc.get("people") or []
        if not people:
            return
        faces, fdir = [], os.path.join(outdir, "faces")
        for p_ in people[:MAX_TARGETS]:
            pid, rel = p_.get("pid"), p_.get("crop")
            if not isinstance(pid, int) or not rel:
                continue
            srcp = os.path.join("viewer", "track_out", tid, rel)
            if not os.path.isfile(srcp):
                continue
            key = "ly_out/%s/faces/p%d.jpg" % (vid_id, pid)
            url = ""
            try:
                url = _upload(srcp, key, "image/jpeg") or ""
            except Exception:
                url = ""
            if not url:
                os.makedirs(fdir, exist_ok=True)
                shutil.copyfile(srcp, os.path.join(fdir, "p%d.jpg" % pid))
                url = key
            faces.append({"pid": pid, "url": url,
                          "first": round(float(p_.get("first") or 0), 1), "dur": round(float(p_.get("dur") or 0), 1)})
        if faces:
            # ⚠ video.json에 **직접 쓰지 않는다** — 이 시점은 컴포즈 앞이라 뒤따르는 ly_burn이 video.json을 새로 쓰면서
            #   여기서 넣은 필드를 통째로 날린다(파일은 남고 목록만 사라져 화면엔 아무것도 안 뜨는 조용한 죽음).
            #   pre 적용 축과 같은 방식으로 /tmp에 남기고 post가 최종 기록에 병합한다.
            with open("/tmp/edit_track_faces.json", "w", encoding="utf-8") as f:
                json.dump(faces, f, ensure_ascii=False)
            log("얼굴 썸네일 %d명 게시" % len(faces))
    except Exception as e:   # fail-soft — 썸네일은 보조 표시라 실패해도 가림·편집은 그대로 간다
        log("얼굴 게시 실패(무해): " + str(e)[:80])


def _mirror_vj(vid_id, vj):
    """결과 쪽지를 보관함에도 다시 올린다 — **이 한 줄이 없으면 이 단계의 산출이 실시간 화면에 영영 안 온다.**

    ⚠ 260816 적대검증이 잡은 마지막 구멍이다. 체인 실측 =
      ⓐ 컴포즈(`ly_burn.py` 303~317행)가 `video.json` 을 **보관함에 미러**한다(배포를 안 기다리려고 260728 도입).
      ⓑ 이 단계(post)는 미디어만 올리고(398·407행) **쪽지는 로컬에만 썼다**.
      ⓒ 화면 조회(`functions/api/edit.js` `?stat=`)는 **보관함 원문**을 준다.
      ⓓ 폴은 `url` 이 있으면 거기서 멈춘다(`viewer/edit.html` pollEdit).
      → 폴이 집는 건 **컴포즈 시점 쪽지**라 이 단계가 더한 것(프리뷰 주소·실패 사유·무동작 사유)이 그 화면엔 안 온다.
      같은 세션이 그 위에 얹은 화면 봉합 3건(사유 표기·체커보드·자막 창 계승)이 **다시 열 때만** 살아 있었다.
    보관함 키·내용 타입은 `ly_burn.py` 미러 블록 사본(창작 0) · 올리는 수단은 **이 파일이 이미 쓰는 `_upload`**
    재사용(별도 업로더 창작 0 · 그쪽이 파일 경로를 받으므로 쪽지를 임시 파일로 한 번 떨군다) ·
    전면 fail-soft = 실패해도 종전 배포 경로가 그대로 폴백."""
    try:
        if not vid_id:
            return
        tmp = "/tmp/edit_track_vj.json"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(vj, f, ensure_ascii=False, separators=(",", ":"))
        if _upload(tmp, "ly_out/{}/video.json".format(vid_id), "application/json"):
            log("결과 쪽지 보관함 미러 완료")
        else:
            log("결과 쪽지 미러 건너뜀(보관함 미설정) — 배포 경로 폴백")
    except Exception as e:
        log("결과 쪽지 미러 실패(무해 — 배포 경로 폴백): " + str(e)[:100])


def _upload(path, key, ctype):
    """대용량 안전 업로드 — track_render._r2_upload_file **정본 재사용**(aws s3 cp 파일 직행 · 사본 창작 0).
    lazy import = cv2 스택이 없는 환경(xtr 미사용 발사)에선 여기까지 안 온다."""
    sys.path.insert(0, TRACK_DIR)
    import track_render as trr
    return trr._r2_upload_file(path, key, ctype)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:   # 전면 fail-soft — 자동 가림이 편집 잡을 죽이면 안 된다(ly_burn·track_render 동일 계약)
        print("::warning::자동 트래킹 실패(편집본은 정상): " + repr(e), flush=True)
        sys.exit(0)
