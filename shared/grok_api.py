"""grok_api — X(엑스) 구독 자격으로 xAI(그록)의 그림·영상을 굽는 단일 통로.

배경(260810 · 운영자 "이거로 편하게 만들 수 있으면 슈퍼그록까지 할 의사도 있음"):
  영상은 지금 `viewer/k.html` 이 **복붙용 프롬프트만** 뽑아주고 운영자가 그 글을 들고 클링 사이트로
  건너가 직접 만든다(`functions/api/k.js` 머리 = 「Kling 복붙 프롬프트」). 그록은 우리가 API 로
  직접 구울 수 있으므로 **건너가는 단계 자체가 사라진다** — 그게 이 모듈의 존재 이유다.

  자격 = API 키(종량제)가 아니라 **구독 OAuth**. 260810 실호출로 통과 확인(계정 muteno@pm.me ·
  grok-4.3 HTTP 200 · 판정기 = `scripts/노뮤트_그록자격_확인.bat`).

⚠ 이 모듈은 **프롬프트를 짓지 않는다.** 문장 설계는 별건(오퍼스 6인 수집 → 정제 → 페이블 검토 축)이고
  여기는 「받은 문장을 어떻게 보내고 어떻게 받아오는가」만 책임진다.

⚠ 계약 앵커(CONTRACT)는 짝 게이트를 만드는 커밋에 함께 단다 — 강제가 없는 선언은
  조용히 낡는다(`check_contract_anchors` 계약 = 고아 앵커 차단).

── 고정값(운영자 260810 "10초 720p는 고정(그록 선택 시), 비율만 선택할 수 있게")
  이 요금제(X Premium+)에서 실제로 도는 값만 화면이 약속한다 — 15초·1080p 를 옵션으로 열면
  거절이 **옵션 화면이 아니라 발사 뒤에** 터진다. 슈퍼그록 승급 시 아래 상수만 바꾼다.

── 260810 자료수집 실측이 잡은 **확정 결함 4종**(첫 판이 전부 틀렸다 · 전건 여기서 봉합)
  ⓐ `image`·`reference_images` 는 **문자열이 아니라 객체**(`{"url":…}` 또는 `{"file_id":…}`)
     → 문자열을 그대로 넣던 첫 판은 **무조건 거절**이었다.
  ⓑ **키가 틀리면 401 이 아니라 400**(`code:"invalid-argument"`) — 401 만 확정 실패로 잡으면
     키 오류를 영원히 재시도한다.
  ⓒ 폴링이 진행 중일 때 **202** 를 준다 — 200 만 정상으로 보면 분기가 어긋난다.
  ⓓ 완료 판정은 `status=="done"` 하나로 부족하다. **검열 차단분은 done 인데 url 이 빈다**
     → `respect_moderation` ∧ url 실존까지 **3겹**으로 봐야 빈 파일이 착지하지 않는다.
"""
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

# ── 자격(구독 OAuth) ───────────────────────────────────────────────────────────
AUTH_TOKEN_URL = "https://auth.x.ai/oauth2/token"
CLIENT_ID = os.environ.get("XAI_OAUTH_CLIENT_ID", "b1a00492-073a-47ea-816f-4c329264a828")
API_BASE = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1")

# ── 산출 규격(운영자 260810 확정) ─────────────────────────────────────────────
VID_MODEL = os.environ.get("GROK_VID_MODEL", "grok-imagine-video-1.5")
VID_SECONDS = int(os.environ.get("GROK_VID_SECONDS", "10"))     # 슈퍼그록 = 15 까지
VID_RES = os.environ.get("GROK_VID_RES", "720p")                # 슈퍼그록 = 1080p
VID_RES_REF = "720p"                                            # 참조 모드는 720p 가 상한(공식)
VID_RATIOS = ("16:9", "9:16", "1:1")                            # 화면이 고르게 하는 유일한 축
REF_MAX = 7                                                     # 참조 그림 장수 상한
IMG_MODEL = os.environ.get("GROK_IMG_MODEL", "grok-imagine-image")            # $0.02/장
IMG_MODEL_HQ = os.environ.get("GROK_IMG_MODEL_HQ", "grok-imagine-image-quality")  # $0.05/장

POLL_SEC = 5            # 공식 예제와 같은 간격(SDK 기본 100ms 는 우리 축에 과하다)
POLL_MAX_SEC = 900      # 15분 상한(러너 타임아웃보다 짧게)
USD_TICKS = 1e10        # 응답 usage.cost_in_usd_ticks ÷ 이 값 = 달러(추정 금지 = 실값 원장 기록)


class GrokError(RuntimeError):
    """호출 실패. code = HTTP 상태(0 = 네트워크), body = 서버가 한 말 원문.

    ⚠ 사유 원문을 반드시 들고 다닌다 — 260807 스모크 경보 사고(사유 0자 경보가 8일 살았다)와 같은 축.
    """

    def __init__(self, code, body, where=""):
        self.code, self.body, self.where = code, body, where
        super().__init__(f"[{where} HTTP {code}] {str(body)[:400]}")

    @property
    def dead_auth(self):
        """자격이 죽었다 = 재시도 무의미, 다시 로그인해야 한다.

        ⚠ 키 오류가 **400** 으로 온다(실측 `code:"invalid-argument"` + 「Incorrect API key」 문구)
          → 401 만 보면 무한 재시도에 빠진다.
        """
        b = str(self.body).lower()
        return self.code == 401 or (self.code == 400 and "api key" in b) or "invalid_grant" in b

    @property
    def tier_blocked(self):
        """자격은 살아 있는데 xAI 가 이 통로를 안 열어준 것(403).

        ⚠ **재시도·재로그인으로 안 풀린다.** 처방은 종량제 키 경로로 내려앉는 것뿐이라
          호출부가 이 축을 따로 알아야 한다(구독 자격 배선의 유일한 구조적 위험).
        """
        return self.code == 403


def _req(url, *, data=None, token=None, method=None, timeout=120):
    """(코드, 본문, 파싱된 json|None). 예외는 안 던진다 — 판정은 호출부 몫.

    ⚠ 없는 경로의 404 는 **본문이 text/plain** 이라 json 파싱이 실패한다 → 파싱 실패를 오류로
      올리지 않고 그대로 문자열로 돌려준다.
    """
    hdr = {}
    if token:
        hdr["Authorization"] = f"Bearer {token}"
    body = None
    if method == "FORM":
        body = urllib.parse.urlencode(data).encode()
        hdr["Content-Type"] = "application/x-www-form-urlencoded"
        method = "POST"
    elif isinstance(data, dict):
        body = json.dumps(data, ensure_ascii=False).encode()
        hdr["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=hdr,
                                 method=method or ("POST" if body else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read().decode("utf-8", "replace")
            code = r.getcode()
    except urllib.error.HTTPError as e:
        txt, code = e.read().decode("utf-8", "replace"), e.code
    except Exception as e:  # noqa: BLE001
        return 0, f"{type(e).__name__}: {e}", None
    try:
        return code, txt, json.loads(txt)
    except Exception:  # noqa: BLE001
        return code, txt, None


_B64SET = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r")


def _mime_of(b):
    """매직바이트로 형식을 가른다(허용 = JPEG·PNG·WebP).

    ⚠ 전부 jpeg 로 굽던 첫 판은 PNG·WebP 원본에 거짓 형식을 붙였다 — 이 레포가 이미 겪은
      「거짓 확장자」 사고와 같은 축이라 추측 대신 바이트를 본다.
    """
    if b[:2] == b"\xff\xd8":
        return "image/jpeg"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _imgref(v):
    """그림 입력을 API 가 받는 **객체** 로 정규화한다.

    받는 값 = 공개 주소 문자열 · `data:image/…;base64,…` · 원바이트 · 파일번호 · 이미 만든 객체.
    ⚠ 맨 base64 를 그대로 보내면 안 된다 — **`data:` 접두가 붙은 형태**여야 한다(공식 예제).
    ⚠ 해석 못 하는 문자열(로컬 경로 등)을 base64 로 넘겨짚지 않는다 — 그러면 서버가 400 을 주는데
      사유가 엉뚱한 곳을 가리켜 추적이 통째로 헛돈다.
    """
    if isinstance(v, dict):
        return v
    if isinstance(v, (bytes, bytearray)):
        b = bytes(v)
        return {"url": f"data:{_mime_of(b)};base64," + base64.b64encode(b).decode()}
    s = str(v).strip()
    if s.startswith("file_"):
        return {"file_id": s}
    if s.startswith("data:") or s.startswith("http://") or s.startswith("https://"):
        return {"url": s}
    if len(s) > 64 and not (set(s) - _B64SET):   # 맨 base64 로 확정될 때만 구제
        try:
            return {"url": f"data:{_mime_of(base64.b64decode(s[:64] + '=' * 4, validate=False))};base64," + s}
        except Exception:  # noqa: BLE001
            pass
    raise GrokError(0, f"그림 입력을 해석 못 했다(앞 40자: {s[:40]!r}) — 공개 주소·data URI·바이트·파일번호만 받는다",
                    "imgref")


def cost_usd(obj):
    """응답이 실어준 **실제 청구액**(달러). 추정하지 마라 — 서버가 값을 준다."""
    try:
        return float((obj.get("usage") or {}).get("cost_in_usd_ticks") or 0) / USD_TICKS
    except Exception:  # noqa: BLE001
        return 0.0


# ── 자격 갱신 ─────────────────────────────────────────────────────────────────
def access_token(refresh_token=None):
    """리프레시 토큰으로 액세스 토큰을 받아온다.

    ⚠ **그록은 갱신할 때마다 리프레시 토큰을 새것으로 바꿔준다(회전).** 그래서 반환값 두 번째를
    호출부가 **반드시 다시 저장**해야 다음 런이 산다 — 안 하면 며칠 뒤 조용히 끊긴다(화면 증상 0).
    죽은 토큰의 실측 응답 = HTTP 400 `{"error":"invalid_grant",…}`.

    반환 = (액세스 토큰, 새 리프레시 토큰 or None)
    """
    rt = refresh_token or os.environ.get("XAI_REFRESH_TOKEN") or ""
    if not rt:
        raise GrokError(0, "리프레시 토큰이 없다(XAI_REFRESH_TOKEN 미설정)", "auth")
    code, txt, obj = _req(AUTH_TOKEN_URL, method="FORM", data={
        "client_id": CLIENT_ID, "grant_type": "refresh_token", "refresh_token": rt,
    }, timeout=60)
    if code != 200 or not obj or not obj.get("access_token"):
        raise GrokError(code, txt, "auth")
    return obj["access_token"], obj.get("refresh_token")


TOKEN_STORE = os.environ.get("XAI_TOKEN_STORE") or os.path.join(
    os.environ.get("GITHUB_WORKSPACE") or os.path.expanduser("~"), ".nomute_grok_token.json")


def fresh_token(store=None):
    """쓸 수 있는 액세스 토큰을 돌려준다. **갱신과 저장을 한 몸으로 묶는다.**

    ⚠ 왜 한 함수인가 = 회전이 계약이라 「갱신했는데 저장을 안 한」 순간 그 자격은 죽는다.
      호출부에 저장을 맡기면 언젠가 한 곳이 빼먹고, 증상은 며칠 뒤 조용한 정지다.
    ⚠ 왜 잠그는가 = 이 레포는 이미 동시 3발사를 받는다(서버 rateGate cap=3 · 화면 다중 큐잉).
      두 러너가 같은 리프레시 토큰으로 동시에 갱신하면 한쪽이 받은 새 토큰이 다른 쪽 저장에
      덮여 **양쪽 다 죽는다**. 그래서 갱신 구간은 한 번에 한 명만 들어간다.
    ⚠ `invalid_grant` 는 곧바로 포기하지 않는다 — 다른 러너가 방금 회전시켰을 수 있어
      저장소를 다시 읽고 1회 재시도한다(그게 정확히 이 사고의 정상 복구 경로다).
    """
    path = store or TOKEN_STORE
    lock = path + ".lock"
    fd = None
    try:
        for _ in range(60):   # 최대 60초 대기(남의 갱신은 1~2초면 끝난다)
            try:
                fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                try:   # 죽은 락 회수(30초 넘게 남아 있으면 주인이 죽은 것)
                    if time.time() - os.path.getmtime(lock) > 30:
                        os.unlink(lock)
                        continue
                except OSError:
                    pass
                time.sleep(1)
        for attempt in (1, 2):
            data = _read_store(path)
            if data.get("access_token") and float(data.get("expires_at") or 0) - time.time() > 300:
                return data["access_token"]   # 아직 살아 있다 = 갱신 횟수 자체를 줄인다
            try:
                at, rt = access_token(data.get("refresh_token"))
            except GrokError as e:
                if attempt == 1 and "invalid_grant" in str(e.body).lower():
                    time.sleep(2)
                    continue   # 다른 러너가 방금 회전시켰을 수 있다 → 저장소 재독
                raise
            data["access_token"] = at
            data["expires_at"] = time.time() + 5 * 3600   # 실측 수명 약 6시간 · 여유 1시간
            if rt:
                data["refresh_token"] = rt
                # ⚠ 결과를 **버리지 않는다** — 되쓰기가 실패하면 이번 판은 멀쩡히 끝나는데
                #   다음 판이 확정으로 죽는다. 그 사실이 로그와 알림 양쪽에 남아야 한다.
                if not _persist_secret(rt):   # 러너 밖으로 살려 보낸다(이 한 줄이 있어야 두 번째 발사가 산다)
                    print("::warning::이번 판은 살지만 **다음 발사는 자격 오류로 죽는다** — 판정기로 열쇠를 갈아라")
            _write_store(path, data)
            return at
        raise GrokError(0, "자격 갱신 실패(다시 로그인해야 한다)", "auth")
    finally:
        if fd is not None:
            os.close(fd)
            try:
                os.unlink(lock)
            except OSError:
                pass


def _persist_alarm(name, why):
    """되쓰기가 실패했다는 사실을 **운영자 화면까지** 내보낸다.

    ⚠ 왜 필요했나(260812 8렌즈 검증) = 되쓰기 실패 경로가 전부 경고 한 줄이라 **런은 초록으로
      끝나는데 다음 런은 확정 사망**이다(갱신 순간 옛 열쇠는 이미 죽었고 새 열쇠는 러너와 함께
      사라진다). 증상이 「다음에 쐈더니 자격 오류」뿐이라 원인과 시점이 사람 눈에서 끊긴다.
    ⚠ 조치 주체가 **운영자**다(코드로는 못 고친다 = 다시 로그인해야 새 열쇠가 나온다) → 👉 문단을
      붙인다(안 붙이면 알림 분류가 「클로드가 볼 일」로 잘못 간다 = 알림 조치주체 계약).
    ⚠ 알림 이름은 열쇠 이름별로 갈라 둔다 — 두 통로가 같은 칸을 쓰면 한쪽이 다른 쪽을 덮는다.
    """
    try:
        import subprocess, sys as _sys   # noqa: PLC0415,E401  실패 경로에서만 부른다
        msg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "msg.py")
        body = ("새 열쇠를 저장소 비밀값에 못 남겼어({}).\n"
                "사유: {}\n"
                "지금 상태 = 방금 쓴 열쇠는 이미 죽었고 새 열쇠는 어디에도 안 남았어. "
                "다음 발사는 자격 오류로 죽어."
                "\n\n👉 네가 할 일: 판정기(노뮤트_힉스필드자격_확인.bat 또는 그록 판정기)를 한 번 "
                "돌려서 새 열쇠를 그 비밀값에 덮어써 줘. 코드로는 못 고치는 자리야."
                ).format(name, str(why)[:200])
        subprocess.run([_sys.executable, msg, "set", "key-persist-" + str(name).lower(),
                        body, "warn"], check=False)
    except Exception:  # noqa: BLE001
        pass          # 알림 실패가 갱신 자체를 죽이지는 않는다


def _persist_secret(rt, name=None):
    """회전된 갱신 열쇠를 **레포 비밀값에 되써 넣는다** — 없으면 이 레인은 한 번만 쏠 수 있다.

    ⚠ 실사고(260811 · 런 31545525981) = 두 번째 발사가 `Refresh token has been revoked` 로
      죽었다. 그록은 갱신할 때마다 열쇠를 새것으로 바꾸고 옛것을 무효로 만드는데, 러너는
      작업이 끝나면 통째로 사라져 **새 열쇠가 어디에도 안 남는다** → 레포 비밀값은 이미 죽은
      값이 되고, 사람이 매번 판정기를 돌려 갈아 끼워야 했다.
    ⚠ 왜 비밀값이어야 하나 = 이 레포는 **공개**다. 러너가 판 사이에 값을 남길 자리는
      비밀값·변수·캐시·아티팩트·커밋인데 뒤 넷은 전부 읽힌다. 비밀값만이 유일한 안전한 자리다.
    ⚠ 왜 별도 토큰이 필요한가 = 깃허브가 기본 발급 토큰에는 비밀값 쓰기를 안 준다(권한 목록에
      아예 없다) → 비밀값 쓰기 권한을 가진 개인 토큰 `XAI_SECRET_PAT` 이 있어야 한다.
      **없으면 조용히 넘어간다**(종전 동작 = 사람이 갈아 끼우는 길) — 값이 있는데 죽는 것보다
      낫다. 다만 무성 스킵은 금지라 사유를 찍는다.
    ⚠ 암호화 = 깃허브 비밀값은 레포 공개키로 봉인해서 넣어야 한다(libsodium sealed box).
    """
    pat = os.environ.get("XAI_SECRET_PAT") or ""
    repo = os.environ.get("GITHUB_REPOSITORY") or ""
    # ⚠ 저장할 비밀값 이름은 **인자가 1순위**다(260812 페이블 검증) — 두 번째 통로가 인자 없이
    #   부르면 기본값(그록 열쇠)을 덮어써 그록 레인이 그 자리에서 죽는다. env 는 폴백일 뿐이다.
    name = name or os.environ.get("XAI_SECRET_NAME") or "XAI_REFRESH_TOKEN"
    # ── 맥 2선 레인 로컬 되쓰기(260815 코워크) — 깃허브 정지 중 맥 잡워커는 비밀값 API 대신
    #    환경변수 파일에 새 열쇠를 남긴다: NOMUTE_SECRET_FILE(드라이브 정본) + NOMUTE_SECRET_FILE_2(로컬 캐시).
    #    ⚠ 정본 쓰기 성공만 True — 캐시만 성공은 다음 env-sync(정본→캐시)가 옛값으로 덮어 다음 발사가 죽는다.
    #    미설정(=러너)이면 아래 종전 비밀값 경로 그대로(동작 무변).
    lf = os.environ.get("NOMUTE_SECRET_FILE") or ""
    if lf:
        ok0 = False
        for i, p in enumerate([lf, os.environ.get("NOMUTE_SECRET_FILE_2") or ""]):
            if not p:
                continue
            try:
                lines, hit = [], False
                if os.path.isfile(p):
                    with open(p, encoding="utf-8") as f:
                        lines = f.read().splitlines()
                for j, ln in enumerate(lines):
                    if ln.startswith(name + "="):
                        lines[j] = name + "=" + rt
                        hit = True
                if not hit:
                    lines.append(name + "=" + rt)
                tmp = p + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")
                os.replace(tmp, p)   # 원자 교체 — 부분 쓰기 잔존 차단(ly 편집 반영과 같은 관례)
                if i == 0:
                    ok0 = True
                print("새 갱신 열쇠 로컬 되쓰기 완료({}): {}".format(name, p))
            except Exception as e:  # noqa: BLE001
                print("::warning::로컬 열쇠 되쓰기 실패({}): {}".format(p, str(e)[:120]))
        if not ok0:
            _persist_alarm(name, "로컬 환경변수 파일(정본) 되쓰기 실패")
        return ok0
    if not pat or not repo:
        if os.environ.get("GITHUB_ACTIONS"):
            print("::warning::새 갱신 열쇠를 비밀값에 못 남긴다(XAI_SECRET_PAT 미등록) — "
                  "다음 발사 전에 판정기로 열쇠를 갈아 끼워야 한다")
            _persist_alarm(name, "비밀값 쓰기 권한 토큰(XAI_SECRET_PAT)이 없다")
        return False
    try:
        from nacl import encoding, public   # noqa: PLC0415  선택 의존(없으면 아래에서 사유와 함께 넘어간다)
    except Exception as e:  # noqa: BLE001
        print("::warning::비밀값 봉인 도구 없음(pynacl) — 열쇠 되쓰기 생략: {}".format(str(e)[:120]))
        _persist_alarm(name, "봉인 도구(pynacl) 설치 실패")
        return False
    api = "https://api.github.com/repos/{}/actions/secrets".format(repo)
    hdr = {"Authorization": "Bearer " + pat, "Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28"}

    def _gh(url, payload=None, method="GET"):   # 이 파일은 urllib 로만 산다(requests 미import)
        raw = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=raw, method=method)
        for k2, v2 in hdr.items():
            req.add_header(k2, v2)
        if raw:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", "replace")
                return resp.status, (json.loads(body) if body.strip() else {})
        except urllib.error.HTTPError as e:
            return e.code, {}

    try:
        code, k = _gh(api + "/public-key")
        if code != 200 or not k.get("key"):
            print("::warning::비밀값 공개키를 못 받았다(HTTP {}) — 열쇠 되쓰기 생략".format(code))
            _persist_alarm(name, "저장소 공개키를 못 받았다(HTTP {})".format(code))
            return False
        sealed = public.SealedBox(public.PublicKey(k["key"].encode(), encoding.Base64Encoder))
        code2, _ = _gh("{}/{}".format(api, name), method="PUT", payload={
            "encrypted_value": base64.b64encode(sealed.encrypt(rt.encode())).decode(),
            "key_id": k["key_id"]})
        if code2 not in (201, 204):
            print("::warning::비밀값 쓰기 거절(HTTP {}) — 토큰 권한 Secrets:Read and write 확인".format(code2))
            _persist_alarm(name, "저장소가 쓰기를 거절했다(HTTP {}) — 토큰 권한·만료 확인".format(code2))
            return False
        print("갱신 열쇠를 비밀값 {} 에 되썼다(다음 발사부터 손 안 대도 된다)".format(name))
        return True
    except Exception as e:  # noqa: BLE001
        print("::warning::열쇠 되쓰기 실패(비치명): {}".format(str(e)[:160]))
        _persist_alarm(name, str(e)[:160])
        return False


def _read_store(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        rt = os.environ.get("XAI_REFRESH_TOKEN") or ""
        return {"refresh_token": rt} if rt else {}


def _write_store(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)   # 원자적 교체 = 반쯤 쓰인 파일을 남기지 않는다
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def open_models(token, kind="video"):
    """**이 자격에 실제로 열린 모델 목록**을 실측한다(공식 용도가 정확히 이것).

    ⚠ 이게 배선의 첫 관문이다 — 구독 자격으로 챗이 통과했다고 그림·영상까지 열린 건 아니다.
      xAI 백엔드가 이 통로에 자체 허용목록을 걸고 구독이 살아 있어도 거절한 사례가 보고돼 있다.
    """
    path = "video-generation-models" if kind == "video" else "image-generation-models"
    code, txt, obj = _req(f"{API_BASE}/{path}", token=token, method="GET", timeout=60)
    if code != 200 or not obj:
        raise GrokError(code, txt, f"models-{kind}")
    return [m.get("id") for m in (obj.get("models") or obj.get("data") or []) if m.get("id")]


# ── 그림 ──────────────────────────────────────────────────────────────────────
def make_image(prompt, *, token, n=1, hq=False, ratio="auto", res="1k", fmt="b64_json"):
    """그림 생성(동기 = 폴링 없음). 반환 = [{bytes|url, mime}] n개.

    ⚠ 크기는 `width`/`height` 가 아니라 **비율 + 해상도 두 축**이다(1k · 2k).
    ⚠ 응답이 `mime_type` 을 준다 → **확장자를 추측하지 말고 그 값을 써라.** 이 레포가 겪은
      「거짓 확장자」 사고(png 로 굽는데 실물은 jpeg = 6주 무증상)와 같은 축이다.
    """
    body = {"model": IMG_MODEL_HQ if hq else IMG_MODEL, "prompt": prompt,
            "n": max(1, min(10, int(n))), "response_format": fmt,
            "aspect_ratio": ratio, "resolution": res}
    code, txt, obj = _req(f"{API_BASE}/images/generations", data=body, token=token, timeout=180)
    if code != 200 or not obj:
        raise GrokError(code, txt, "image")
    out = []
    for d in (obj.get("data") or []):
        mime = d.get("mime_type") or "image/jpeg"
        if d.get("b64_json"):
            out.append({"bytes": base64.b64decode(d["b64_json"]), "mime": mime})
        elif d.get("url"):
            out.append({"url": d["url"], "mime": mime})
    if not out:
        raise GrokError(code, txt, "image-empty")
    return out


# ── 영상 ──────────────────────────────────────────────────────────────────────
def start_video(prompt, *, token, ratio="16:9", image=None, refs=None,
                seconds=None, res=None, store_as=None):
    """영상 발사(비동기). 반환 = 작업 번호(request_id).

    image = 첫 프레임으로 삼을 그림. 그 그림이 **1프레임 그대로** 나오고 거기서부터 움직인다.
    refs  = 참조 그림 1~7장. 첫 프레임을 **고정하지 않고** 얼굴·물건·장소 같은 축만 가져온다
            (프롬프트 지목 = **0부터** 센다: 첫 장 `<IMAGE_0>` · 둘째 `<IMAGE_1>`).
    store_as = 파일명. 주면 산출을 xAI 쪽에 **영구 보관**시킨다.

    ⚠ **image 와 refs 는 한 요청에 같이 못 보낸다**(공식 명시) — 선택 축이 아니라 **분기**다.
    ⚠ 이미지→영상은 기본으로 그림 비율을 따르는데, **비율을 보내면 무시가 아니라 그림을 그 비율로
      잡아 늘인다**(공식 원문 "override this and stretch the image"). 즉 「무해한 무시」가 아니라
      **얼굴이 늘어난 산출**이다 → 그림이 있으면 비율을 안 보낸다(이 분기를 지우면 그 사고가 난다).
    ⚠ 참조 모드는 **720p 가 상한**(공식).
    ⚠ 결과 주소는 **임시**이고 정확한 수명이 공식에 없다 → 받는 즉시 우리 저장소로 옮기거나
      store_as 로 영구 보관을 켠다(둘 중 하나는 반드시 · 안 하면 나중에 조용히 죽는다).
    """
    refs = list(refs) if refs else None
    if image and refs:
        raise GrokError(0, "첫 프레임 그림과 참조 그림은 한 번에 못 보낸다(공식 제약) — 하나만 골라라",
                        "video-start")
    if refs and len(refs) > REF_MAX:
        raise GrokError(0, f"참조 그림은 최대 {REF_MAX}장(받은 값 {len(refs)})", "video-start")
    body = {
        "model": VID_MODEL,
        "prompt": prompt,
        "duration": int(seconds or VID_SECONDS),
        "resolution": res or (VID_RES_REF if refs else VID_RES),
    }
    if not image:
        if ratio not in VID_RATIOS:
            raise GrokError(0, f"비율 {ratio} 는 화면 계약 밖이다(허용 {VID_RATIOS})", "video-start")
        body["aspect_ratio"] = ratio
    if image:
        body["image"] = _imgref(image)
    if refs:
        body["reference_images"] = [_imgref(x) for x in refs]
    if store_as:
        body["storage_options"] = {"filename": store_as, "public_url": True}   # 공개 주소 없이 보관하면 무토큰으로 못 꺼낸다
    code, txt, obj = _req(f"{API_BASE}/videos/generations", data=body, token=token, timeout=120)
    if code != 200 or not obj or not obj.get("request_id"):
        raise GrokError(code, txt, "video-start")
    return obj["request_id"]


def wait_video(request_id, *, token, on_tick=None, max_sec=POLL_MAX_SEC):
    """완료까지 기다린다. 반환 = {url, duration, ...} + `cost_usd` 첨부.

    ⚠ 진행 중이면 **202**, 완료·실패는 **200** 이다 — 둘 다 정상 응답으로 받는다.
    ⚠ 완료 판정은 **3겹**이다: status 가 done · 검열을 통과했고(respect_moderation) · 주소가 있다.
      검열 차단분은 **done 인데 주소가 빈다** → 한 겹만 보면 빈 파일이 그대로 착지한다.
    ⚠ 폴링 중 일시 오류(5xx·네트워크)는 삼키고 계속 돈다 — 몇 분짜리 작업을 딸꾹질 한 번으로
      버리면 그 판이 통째로 날아간다. 자격 죽음·미존재만 즉시 예외로 올린다.
    """
    t0 = time.time()
    while time.time() - t0 < max_sec:
        time.sleep(POLL_SEC)
        code, txt, obj = _req(f"{API_BASE}/videos/{request_id}", token=token, timeout=60)
        if code in (400, 401, 403, 404):   # 400 = 영구 오류(재시도로 안 변한다) · 사유 소실 차단
            raise GrokError(code, txt, "video-poll")
        if code not in (200, 202) or not obj:
            continue
        st = obj.get("status")
        if callable(on_tick):
            try:
                on_tick(st, int(obj.get("progress") or 0), int(time.time() - t0))
            except Exception:  # noqa: BLE001
                pass
        if st == "done":
            v = dict(obj.get("video") or {})
            if v.get("respect_moderation") is False:
                raise GrokError(code, "검열에 걸려 산출이 안 나왔다(프롬프트를 고쳐 다시 발사)",
                                "video-moderated")
            if not v.get("url") and not ((v.get("file_output") or {}).get("public_url")):
                raise GrokError(code, txt, "video-done-nourl")
            v["cost_usd"] = cost_usd(obj)
            if not v.get("url"):   # null 로 실려오는 경우가 있다 → setdefault 로는 안 덮인다
                v["url"] = (v.get("file_output") or {}).get("public_url")
            if v.get("storage_error"):   # 보관 실패를 삼키면 「보관됐다」고 믿고 산출을 잃는다
                v["storage_error"] = v["storage_error"]
            return v
        if st == "failed":
            err = (obj.get("error") or {})
            raise GrokError(code, f"{err.get('code') or st}: {err.get('message') or txt}", "video-failed")
    raise GrokError(0, f"{max_sec}초 안에 안 끝났다(작업번호 {request_id})", "video-timeout")


def fetch(url, *, timeout=300):
    """완성된 영상·그림 바이트를 받아온다(결과 주소는 수명이 있다 = 받는 즉시 우리 쪽으로 옮긴다)."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        raise GrokError(e.code, e.read().decode("utf-8", "replace")[:300], "fetch") from None
    except Exception as e:  # noqa: BLE001
        raise GrokError(0, f"{type(e).__name__}: {e}", "fetch") from None
