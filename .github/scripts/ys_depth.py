#!/usr/bin/env python3
"""유튜브 숏폼(ys) 「GPT 입체」 — 맥 GPT 장면 그림 한 장을 2.5D 시차 영상으로(운영자 260928 «GPT 이미지에 움직임 · 2.5D 입체 시차»).

  parallax_clip(img, out_mp4, w, h, dur, model)   → 그림 칸(w×h) 영상 · 소리 없음 · 30fps
  ys_depth.py <img> <out.mp4> <w> <h> <dur> [model.onnx]   (단독 점검)

방법: 깊이 추정(Depth Anything V2 Small · ONNX 양자화 27MB · CPU) → 가까운 곳일수록 크게 움직이는 역방향 워핑(cv2.remap)
  = 카메라가 옆으로 살짝 흐르며 다가가는 입체감. 그림 자체는 바꾸지 않는다(새로 그리지 않음 · 픽셀 이동만).
  · 이동 폭 = 화면 폭의 6% · 확대 = 가까운 곳 최대 16%(운영자 260928 «이미지가 움직이지 않네» — 옛 2.2%·6% = 0.5초당 평균 변화 1/255 실측 · 눈엔 정지)
    · 여유(OVER) 1.22 = 이동+확대가 원본 밖을 드러내지 않는 폭(가로 여유 11% ≥ 이동 6% + 위아래 2.5%).
  · 깊이 모델이 없거나 실패하면 = 평면 느린 확대(깊이 0)로 강하하고 사유를 돌려준다(영상은 항상 나온다).
모델 = 러너가 받아 둔 파일(YS_DEPTH_MODEL) · 출처 onnx-community/depth-anything-v2-small(Apache-2.0).
"""
import math
import os
import subprocess
import sys

import numpy as np

FPS = 30
SHIFT = 0.06       # 좌우 흐름 = 화면 폭 비율
LIFT = 0.025       # 위아래 흐름
ZOOM = 0.16        # 가까운 곳 확대 상한
OVER = 1.22        # 가장자리 여유(원본을 화면보다 22% 크게 잡아 흐름이 화면 밖을 드러내지 않게)
MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)


def _cover(img, w, h):
    import cv2
    ih, iw = img.shape[:2]
    s = max(w * OVER / iw, h * OVER / ih)
    img = cv2.resize(img, (int(math.ceil(iw * s)), int(math.ceil(ih * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    ih, iw = img.shape[:2]
    y0, x0 = (ih - int(h * OVER)) // 2, (iw - int(w * OVER)) // 2
    return img[y0:y0 + int(h * OVER), x0:x0 + int(w * OVER)]


def depth_map(rgb, model):
    """가까울수록 1에 가까운 깊이(0~1 · 부드럽게 흐림). 실패 = None."""
    import cv2
    try:
        import onnxruntime as ort
    except ImportError:
        print('::warning::입체 도구(onnxruntime) 설치 실패 — 평면 확대로 강하')
        return None
    try:
        sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
        x = cv2.resize(rgb, (518, 518), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255.0
        x = ((x - MEAN) / STD).transpose(2, 0, 1)[None]
        name = sess.get_inputs()[0].name
        d = np.squeeze(sess.run(None, {name: x})[0]).astype(np.float32)
    except Exception as e:  # noqa: BLE001
        print(f'::warning::깊이 추정 실패 — 평면 확대로 강하 ({type(e).__name__}: {str(e)[:120]})')
        return None
    d = cv2.resize(d, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_CUBIC)
    lo, hi = np.percentile(d, 2), np.percentile(d, 98)
    d = np.clip((d - lo) / max(1e-6, hi - lo), 0, 1)
    k = max(3, int(min(rgb.shape[:2]) * 0.03) | 1)
    return cv2.GaussianBlur(d, (k, k), 0)   # 경계 번짐 완화 = 깊이 경계를 부드럽게


def ease(p):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, p)))


def parallax_clip(img_path, out_mp4, w, h, dur, model=None):
    """반환 = (성공 여부, 사유 문자열 · 성공이면 '' 또는 강하 사유)."""
    try:
        import cv2
    except ImportError:
        return False, '입체 도구(opencv) 설치 실패'
    try:
        import onnxruntime  # noqa: F401
        has_ort = True
    except ImportError:
        has_ort = False
    src = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    if src is None:
        return False, '그림을 못 읽었어'
    src = _cover(cv2.cvtColor(src, cv2.COLOR_BGR2RGB), w, h)
    note = ''
    have = bool(model and os.path.exists(model))
    dep = depth_map(src, model) if have else None
    if dep is None:
        dep = np.zeros(src.shape[:2], np.float32)
        note = ('입체 도구(onnxruntime)가 없어 평면 확대로 만들었어' if not has_ort
                else '깊이 추정이 실패해 평면 확대로 만들었어' if have else '깊이 모델이 없어 평면 확대로 만들었어')
    sh, sw = src.shape[:2]
    cx, cy = sw / 2.0, sh / 2.0
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    ox, oy = (sw - w) / 2.0, (sh - h) / 2.0
    X, Y = xs + ox, ys + oy                          # 칸 좌표 → 원본 좌표(가운데 맞춤)
    D = cv2.remap(dep, X, Y, cv2.INTER_LINEAR)      # 칸 위치의 깊이(작은 이동이라 출력 좌표 근사로 충분)
    n = max(1, int(math.ceil(dur * FPS)))
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', str(out_mp4)], stdin=subprocess.PIPE)
    try:
        for k in range(n):
            e = ease(k / max(1, n - 1))
            dx = SHIFT * w * (2 * e - 1)             # 왼쪽 → 오른쪽으로 한 번 흐른다(왕복 없음 = 장면 컷과 어울림)
            dy = LIFT * h * (1 - 2 * e)
            z = 1.0 + ZOOM * e * (0.35 + 0.65 * D)   # 먼 곳도 조금 · 가까운 곳은 더 다가온다
            mx = cx + (X - cx) / z - dx * D
            my = cy + (Y - cy) / z - dy * D
            fr = cv2.remap(src, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            p.stdin.write(fr.tobytes())
        p.stdin.close()
        rc = p.wait()
    except Exception as e:  # noqa: BLE001
        p.kill()
        return False, f'입체 영상 만들기 실패({type(e).__name__})'
    return rc == 0 and os.path.exists(out_mp4), note


if __name__ == '__main__':
    a = sys.argv
    if len(a) < 6:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    ok, why = parallax_clip(a[1], a[2], int(a[3]), int(a[4]), float(a[5]), a[6] if len(a) > 6 else os.environ.get('YS_DEPTH_MODEL'))
    print('ok' if ok else 'fail', why)
    sys.exit(0 if ok else 1)
