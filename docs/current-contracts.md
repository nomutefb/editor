# 현재 검사 계약

현재 실행되는 검사의 목적만 찾는 색인이다. 조건과 임계값 정본은 `shared/check_refs.py`의 해당 함수다. 사고 이력을 지침에 다시 누적하지 않는다.

| 검사 | 보호하는 동작 |
|---|---|
| `check_paths` | 구현의 검사 조건 참조 |
| `check_versions` | 구현의 검사 조건 참조 |
| `check_viewer_js` | 구현의 검사 조건 참조 |
| `check_functions_js` | Pages Functions(ESM) 구문 하드 게이트 — functions/*.js 하나라도 SyntaxError면 wrangler 번들이 |
| `check_icon_ssot` | 공유 아이콘 SSOT 하드 게이트(운영자 260628 '하나 바꾸면 다 바뀜'). |
| `check_design` | 구현의 검사 조건 참조 |
| `check_palette_sync` | 구현의 검사 조건 참조 |
| `check_inject_dividers` | 구현의 검사 조건 참조 |
| `check_inject_markers` | 주입 지침 파일의 <!-- INJECT-SKIP-START/END --> 마커 짝 균형(260624 단일화 가드). |
| `check_sens_vocab` | 민감 통제어휘 미러 정합 — 드리프트 하드 게이트(260625 분신술 10인). |
| `check_curation_constants` | 큐레이션 랭킹 상수(viewer) ↔ docs/curation-algorithm.md §★ 정본값 정합 하드게이트. |
| `check_fast_max_h_parity` | FAST_MAX_H 크로스랭귀지 패리티(260710 · 검증6R FP-C로 분리) — viewer "단일출처" 주장과 달리 |
| `check_follow_enters_parity` | followEnters(누적 보조진입) 크로스랭귀지 패리티(260805 8인 평의회 · FAST_MAX_H 패리티와 동형) — |
| `check_sc_ts_contract` | 수집함 시간축(scTs) 계약 상비 게이트(운영자 260725 한 수 · Q522 회귀 실물발) — 나이 판정은 신규↔누적 |
| `check_shell_cache_parity` | SW 셸 캐시명 viewer/index.html(applyShellUpdate caches.open) ↔ viewer/sw.js(SHELL_CACHE) 패리티 |
| `check_thumb_chain` | 최근 게시물 커버 회수 체인 게이트(운영자 260803 "이번 문제 안일어나게 하면 더 좋을듯" — 260718 '무성 생략 2/25'가 |
| `check_idle_timer_guard` | 유휴 타이머 가드 게이트 — C16(런타임)의 정적 짝(운영자 260807 "정적 짝 게이트도 ㄱㄱ"). |
| `check_boot_bg_parity` | OS 스플래시→앱 배경 연속 3값 정합 게이트(운영자 260805 승인 "아이디어도 진행하구"). |
| `check_shell_put_integrity` | 셸캐시 put 절단 검문 의무 게이트(260802 '상단만 렌더' **재발** 실사고 — 1차 봉합이 sw.js put에만 </html> |
| `check_workflow_amend` | 워크플로 결과 커밋 `--amend` 금지 게이트(운영자 260803 6-4 승인 — filltest 동시 3발사 실사고의 구조 봉합). |
| `check_push_send_checkout` | 완료 푸시를 쏘는 워크플로는 구독자 명단·알림 아이콘을 **체크아웃 목록에 갖는다**(260816 실사고 봉합). |
| `check_roster_checkout` | 속보 판정 러너는 **메이저급 참조 명단을 실제로 손에 쥔다**(260818 실사고 봉합 · 운영자 «무조건 참조하게끔 해야함»). |
| `check_settings_checkout` | AI 썸네일 전역 설정을 읽는 러너는 **settings 폴더를 실제로 손에 쥔다**(260821 실사고 봉합 · |
| `check_claim_before_consume` | 요약 병렬화 = 기사 단위 선점이 소비보다 앞서고, 어느 갈래도 표식을 안 남기며, 선점 착지에 `-X theirs` 가 없다(260905 · 평의회 8인 #8 설계). |
| `check_guidelines_checkout` | 에디터 지침을 주입하는 러너는 **지침 폴더를 실제로 손에 쥔다**(260823 실사고 봉합 · |
| `check_push_abs_url` | 알림 딥링크는 **절대 주소로** 나간다(260816 3차 실사고 봉합 · 운영자 「알림이 다 구 주소로 가는거 같은데」). |
| `check_prompt_literal_quoting` | 다중라인 프롬프트 리터럴 = 인용 무결성 의무(하드 · 260805 실사고 `fail-2026-08-04-{1528,2211}` 봉합). |
| `check_pages_skip` | [CF-Pages-Skip] 오배선 차단 게이트(운영자 260803 평의회 · Q1331) — 접두가 금지 축(도장·제작 산출·뉴스 큐·메트로놈)에 |
| `check_coalesce_pair` | [CF-Pages-Skip] **짝** 게이트(운영자 260803 6-4 승인 · Q1343 실사고의 기계화) — 코얼레싱의 반대 방향을 본다. |
| `check_cat_kw` | CAT_KW 카테고리 키워드사전 py(to_candidates.py) ↔ js(viewer/index.html) 정합 하드게이트. |
| `check_issue_badge_parity` | ⚡이슈 배지 게이트 viewer(issCross) ↔ build-viewer(issEligible) 규칙 동일 하드게이트(260702 · 10인 검증7). |
| `check_force_parity` | 카테고리 강마커·오버라이드 정규식 py(to_candidates) ↔ js(viewer articleCat) 바이트 동기 하드게이트(260704). |
| `check_k_models` | /k 모델·설정 3면 패리티 하드게이트(개편 P1 · 260710 스키마 v2). 모델 id와 설정 축·칩 값이 |
| `check_autocomplete` | 평문 텍스트 입력칸 = OS 자동완성 끔 4종 세트 하드 게이트(§🎨 · 운영자 260628). |
| `check_clip_coverage` | 구현의 검사 조건 참조 |
| `check_input_canon` | 구현의 검사 조건 참조 |
| `check_url_placeholder` | 구현의 검사 조건 참조 |
| `check_x_char` | 구현의 검사 조건 참조 |
| `check_tokens_link` | 공유 구조토큰 tokens.css 배선 하드게이트(§🎨 STAGE3·분신술7·260628). |
| `check_dangling_var` | 댕글링 var() 하드게이트(평의회 Q165 게이트 갭 ① → Q169 신설). |
| `check_soremeori` | 소머리(구분자 •) 표준 강제 — 텍스트 흰색(--fg)·블릿 형광(--accent)·토큰 굵기(§📐·운영자 260629). |
| `check_claude_failover` | 모든 Claude 호출 스크립트는 폴오버 SSOT를 경유 — 계정 로테이션 통일(운영자 260629·§📰). |
| `check_judge_bare` | judge(gate_judge·breaking_judge)는 라이브·구독 OAuth 전용 파이프라인 → --bare 금지, --safe-mode만. |
| `check_playground` | 플레이그라운드 템플릿 게이트(하드 · 실행 계약 5 · §플레이그라운드 0-1 · 260713). |
| `check_candidates_size` | viewer/candidates.json 크기 가드(WARN-only·260714) — 3000개(3.45MB)로 비대해져 라이브 서빙 |
| `check_conflict_markers` | 병합 충돌 마커 잔존 게이트(평의회⑧ 260717 — #2368이 큐 원장에 마커 3줄 남긴 실사고 재발 방지). |
| `check_workflow_yaml` | 워크플로 YAML 유효성 게이트(260728 Q976 · 운영자 지시 "재발 안 하게"). |
| `check_git_idiom` | 봇커밋 git 관용구 게이트(260728 Q981 · 운영자 지시 "재발 안하게 조치"). |
| `check_qledger_unique` | 지시 원장(docs/요구사항_큐.md) Q번호 유일성 게이트(운영자 260717 Q29 승인 — 동시 세션이 각자 '다음 번호'를 |
| `check_anchor_liveness` | 기틀 문서 → 문서 한정(§) 앵커 생존 게이트(운영자 260718 Q146 승인 "차단되고 영향 100% 없음 증명"). |
| `check_html_charset` | 구현의 검사 조건 참조 |
| `check_fp_parity` | 지문(fp) 축 패리티 하드게이트(260720 평의회C M3 — 수동 미러 3면 감시). |
| `check_launch_spec` | 구현의 검사 조건 참조 |
| `check_imgstudio_dock_spec` | 구현의 검사 조건 참조 |
| `check_track_parity` | 자간 판정 = advance 단일 기준 + 한도 상수 py↔js 동일(운영자 260802 3차). 이탈 = rc=1. |
| `check_result_rail_parity` | 결과 레일 = 5탭 한 세트(운영자 260806 "왜 저게 계속 따로노는지 모르겟으유" · "정본에 정립해봣자 나중에 또 저렇게 따로노는거 아님?"). |
| `check_cap_rail_land` | 영상 스튜디오 완료 적재 = **화면 주인·강등 양쪽**(하드 · 운영자 260810 "방금 1개를 제작하고, 추가로 뭐 하나 더 제작하면 방금거가 유실된다"). |
| `check_trail_spec` | 미리보기 코너 옵션 레일 사본 동일성 게이트(운영자 260802). |
| `check_prev_center` | 미리보기 빈 상태 중앙 = 업로드 픽토 단독 게이트(운영자 260802). |
| `check_geni_scope` | geni 어휘 전역 질의 금지 게이트(운영자 260803 6차 "게이트 ㄱㄱ" · 평의회3 지적 반영 2차). |
| `check_onoff_literal` | 이진 토글 ON/OFF 리터럴 금지 게이트(운영자 260803 "off 이런거는 on off로 하는게 아니라 기능 워딩이 점등하냐 안하냐로 onoff"). |
| `check_axis_chip_home` | 다값 카드 헤더 축은 헤더 우측 칩(hdChips) 단일 문법 — 본문 행(segs) 혼용이면 rc=1. |
| `check_trail_decl_parity` | 레일 부품의 **정본 선언 집합**이 전 표면에 상속됐는지 대조(값 아님·존재 여부). |
| `check_affordance_inherit` | 어포던스 비계승 게이트 — cursor:pointer가 「누를 수 없는 노드」에 걸려 있는지 정적 검출. |
| `check_debt_ratchet` | 부채 래칫 — 면책표 총량이 원장보다 **늘면 FAIL**(줄면 낮추라고 알린다). |
| `check_model_names` | 모델 표시명 SSOT 게이트(운영자 260803 5차) — 위 주석 참조. rc=1 = 커밋 차단. |
| `check_twocol_breakpoint` | 스튜디오 결과 레일 2단 분기점 = 표면 간 한 값 게이트(운영자 260802 "일단 머지해주셈" 승인분). |
| `check_layout_transition` | 레이아웃 유발 transition 래칫(위 주석 참조). rc=1 = 커밋 차단. |
| `check_comment_seam` | CSS 주석 이음매 하드 0 — 「주석 안에서 새 주석이 열리는가 · 주석 밖에서 닫히는가」. |
| `check_keyframes_dup` | @keyframes 중복 정의 하드 0(위 주석 참조). rc=1 = 커밋 차단. |
| `check_css_dead_state` | 죽은 상태 오버라이드 래칫(위 주석 참조). 늘면 rc=1 = 커밋 차단. |
| `check_preview_perf` | 미리보기·타일 렌더 부담 예방 게이트(운영자 260819 «추후 미리보기에 뭘 띄우고 거기에 오버레이하게 되면 이렇게 렉걸릴수도 있으니 사전에 동일하게 수정»). |
| `check_cpv_paint_quiet` | 카드 제작 미리보기 = 타이핑 중 무대·사진 층 페인트 정숙 게이트(운영자 260821 «못살겠다 수정한 이래로 제일 심해»). |
| `check_shared_canon` | 공용 부품 CSS = nm-shared.css 단일정본 참조. rc=1 = 커밋 차단. |
| `check_clip_canon` | 클립 4문법 = 한 벌(nm-clip.css 단일정본 참조). rc=1 = 커밋 차단. |
| `check_anchor_menu_canon` | 앵커 메뉴 문법 = 한 벌(위 주석). rc=1 = 커밋 차단. |
| `check_component_lock` | 컴포넌트 작업 락 겹침 알림(운영자 260802 · WARN·비차단). 등재 = CLAUDE.md 이 레포 전용 절. |
| `check_label_fill` | 콘텐츠 라벨색(cat-*·bias-*) 솔리드 배경 필 금지 게이트(운영자 260721 Q345 · 평의회 Q329 채택 ④ = 감사 R5 절제축). |
| `check_loader_ssot` | 로딩 표기 SSOT 게이트(운영자 260723 Q461 — "전역 앱 세션에서 정해진 로딩만 쓰도록"). |
| `check_model_ids` | 모델 ID·표시명 드리프트 하드게이트(운영자 260725 한 수 · 정본 = `shared/models.json`). |
| `check_ssot_coverage` | 정본 커버리지 역방향 게이트(운영자 260725 한 수 · `check_gate_docs`의 반대 방향). |
| `check_drive_move_bundle` | 운영자 PC 배포 번들(더블클릭 .bat) ↔ ps1 정본 드리프트 차단(운영자 260801 · CLAUDE.md [9-1 납품]). |
| `check_font_shorthand` | `font:` 축약형 안 `inherit` 금지(운영자 260727 실사고 재발방지). |
| `check_form_font_inherit` | 폼 요소 활자 계승 리셋 존재(운영자 260727 "같은 형태에 있는 애들은 다 같아야함"). |
| `check_branch_freshness` | 브랜치 신선도 WARN(운영자 260727 재발방지 — 260726 평행 구현 사고: 착수 전 fetch를 안 해 |
| `check_nm_jobs` | 여러 작업 동시 추적 게이트(운영자 260810 "동시에 2가지 작업을 큐잉하면 첫번째거를 두번째꺼가 덮어씌워져") — |
| `check_nm_sync` | 동기화 생명선 상속 게이트(운영자 260803 4차 "다른 스튜디오 탭에도 전부 상속") — `viewer/nm-sync.js` SSOT(복귀 자동 재동기 · |
| `check_brk_misfire_chain` | 긴급 오발 신고 폐루프 게이트(하드 · 운영자 260803 4차 "누적될 때 활용을 안 하면 소용이 없다"). |
| `check_vote_btn_canon` | 👍/👎 선호 투표 부품 = 한 벌 계승(하드 · 운영자 260805 "고정으로 박아줘 다른데서 만들면 참조하도록"). |
| `check_cloud_action_chain` | 클라우드 액션 서버(구글 드라이브 「내 드라이브/action」 = git 액션 대체 · 운영자 260814 Q1482~Q1487 = |
| `check_secret_coverage_chain` | 빈 칸 점검 레인 5층 생존(운영자 260816 «응 해줘» · 계정 이관 후속). |
| `check_land_share` | 공유 착지 = 남의 것을 지우지 않는다(운영자 260816 「확인해서 머지」 · 별도 모델 교차검증 실증). |
| `check_transient_cases` | 일시 장애 재시도 판정 = 실측 실패 서명이 감지망에 있는가(260820 실사고 봉합). |
| `check_land_xours` | 착지 내용 소실 래칫 = 「올라갔는데 우리 변경이 빈 경우」(운영자 260816 「ㄱㄱ」 · 페이블 교차검증 지적 ⓒ). |
| `check_land_silence` | 착지 침묵 래칫 = 「본선에 올리는 데 실패했는데 초록으로 끝나는」 자리를 센다(운영자 260816 「조치해줘」). |
| `check_land_precommit` | 착지 위임 자리의 **선행 커밋** = 산출물이 러너 로컬 커밋에 갇히는 조용한 유실(260817 실사고 봉합). |
| `check_trend_alert_scope` | 급상승 알림은 **화면에 실제로 떠 있는 말만** 쏘고, 딥링크는 **살아있는 문법**으로 간다(260819 실사고 봉합). |
| `check_workflow_step_refs` | 워크플로가 **없는 스텝**을 가리키는가 = 「스텝이 통째로 사라졌다」의 유일한 기계 서명(260817 실사고 봉합). |
| `check_canon_host` | 화면 주소 정본 = 코드가 옛 화면을 직접 부르지 않는다(운영자 260816 「게이트 ㄱㄱ」). |
| `check_pc_lane_stages` | 액션 대체 레인의 스테이지 생존(운영자 260814 «깃허브 액션 없이도 정상 가동 모든 웹앱 내 기능이 돌도록»). |
| `check_sens_mask` | 민감어 마스킹 = 화면과 산출물이 같은 글자를 가린다(하드 · 운영자 260831 «썸네일 제작에서 자살 이라는 걸 |
| `check_grade_fix_chain` | grade 수기 교정 폐루프 게이트(하드 · 운영자 260807 "어긋났을 때 고칠 수 있게 · 12시간마다 고쳐진 것만 기록" — |
| `check_seal_completeness` | 봉합 완결성(WARN·비차단 · 운영자 260808 "idea go") — **「같은 병의 형제를 놓쳤나」를 커밋 그 자리에서 센다.** |
| `check_thumb_merge_canvas` | 저작권·안내문 합성 = 산출물 크기로 캔버스를 정한다(하드 · 260812 실사고 봉합). |
| `check_orig_title_restore` | 요약 제목 = 기자가 뽑은 원문이 화면까지 살아 온다(하드 · 260813 실사고 봉합). |
| `check_focus_contract` | 요약 보강 = 원문의 관점 축을 지킨다(하드 · 260824 실사고 봉합 · check_orig_title_restore 의 형제). |
| `check_paste_url_stamp` | 전문 붙여넣기 카드 = 원문 주소가 화면까지 온다(하드 · 260817 실사고 봉합 · check_orig_title_restore 의 짝). |
| `check_wrap_fence_strip` | 산출 랩퍼 코드펜스 = 두 요약 경로가 같은 정본으로 벗긴다(하드 · 260817 실사고 봉합). |
| `check_yt_cookie_slot_name` | 유튜브 쿠키 = 알림이 말하는 칸 이름이 실제 배선과 같다(하드 · 260812 실사고 봉합). |
| `check_claude_cli_install` | 클로드 도구 설치 = postinstall 허용 동반(하드 · 260820 실사고 봉합). |
| `check_smoke_chromium_path` | 스모크 크로미엄 경로 = 폴백 해석기 경유(하드 · 260808 실사고 봉합 · check_smoke_obs_chain 의 짝). |
| `check_grok_sb_chain` | 콘티 그록 레인 = 5층 생존(운영자 260811 「진행해보자」). |
| `check_fail_reason_visible` | 실패 사유가 화면까지 오는가(하드 · 260816 실사고의 일반화). |
| `check_edit_track_chain` | 편집 생성 = 자동 가림·키잉·크로마키 게이트(하드 · 운영자 260808 "모자이크 누르고 옵션 선택한 다음에 생성 누르면 |
| `check_smoke_obs_chain` | UI 스모크 관측·알림 체인 게이트(하드 · 운영자 260807 "알림 메세지에 그 내용이 쌓이게 · |
| `check_stt_engine_chain` | STT 엔진 교체 계약 게이트(하드 · 운영자 260808 "위험 점검 다 반영" · 평의회 8인 후속). |
| `check_thumb_vote_chain` | AI 썸네일 화풍 투표 폐루프 게이트(하드 · 운영자 260805 "그게 남게끔 해서 나중에 한번 보자" → "ㄱㄱ"). |
| `check_img_upsize` | 검색 이미지 화질 승격 체인 게이트(하드 · 운영자 260810 "고화질을 가져오게 · 최소 세로 720p 이상"). |
| `check_thumb_redo_append` | 썸네일 '수정 = 덮어쓰기 아닌 +1 슬롯' 체인 게이트(하드 · 운영자 260807 "수정하면 원래 이미지는 |
| `check_ask_img_legible` | 요약 요청에 붙인 사진 = 글자가 읽히는 크기로 나간다(하드 · 운영자 260812 "지금 된 부분을 앞으로 나올 수 있게 반영"). |
| `check_ask_srcimg_chain` | 출처 글 본문 이미지 수확 체인 게이트(하드 · 운영자 260804 "확인해줘" → 사고 fail-2026-08-04-0239-297it). |
| `check_subs_author_scope` | 구독 수집 = 작성자 검문 의무(하드 · 운영자 260804 "내가 구독한 애들이 아닌데"). |
| `check_rpt_origin_coverage` | 알림 리포트 출처표 = 뷰어 생산 알림 전건 커버(하드 · 260805 실사고 봉합). |
| `check_fail_msg_todo` | 구현의 검사 조건 참조 |
| `check_disaster_landmark_sign` | 구현의 검사 조건 참조 |
| `check_disaster_lm_stale` | ⑭-e 랜드마크 판정 = **박제 필드** → 코드 봉합만으론 화면이 안 낫는다(260805 2차 실사고 봉합). |
| `check_rubric_regress` | 루브릭 회귀 게이트(하드 · 운영자 260803 승인 — «대구 40.1도» 오발 봉합의 재발 방지 축). |
| `check_style_ratchet` | 요약 문체 회귀 래칫(WARN·비차단 · 운영자 260810 "ㄱㄱ" · 평의회 6 설계안 1안). |
| `check_grade_regress` | grade 룰북 회귀 게이트(하드 · 운영자 260807 "전부 반영" — 평의회 8인 · check_rubric_regress[breaking 전용]의 짝). |
| `check_gate_docs` | 구현의 검사 조건 참조 |
| `check_ssot_linkage` | 공유 부품 SSOT 링크 연결성 게이트(WARN·비차단 · 운영자 260723 Q466 · 디자인기틀 §0-17 5축 등재의 얕은 기계 보조). |
| `check_tabs_headers` | 도구 스튜디오 탭 src(.html)의 _headers no-cache 등재 게이트(운영자 260724 한 수 · 순수 인프라 · SSOT §6 등재). |
| `check_thumb_prompt_sanity` | 뉴스 픽 AI 썸네일 = **발사 프롬프트 자기모순 0**(하드 · 운영자 260805 "아이디어 ㄱㄱ"). |
| `check_ytdlp_aac` | yt-dlp 오디오 코덱 = AAC 강제(하드 · 운영자 260805 "유튜브를 편집가능한 자료까지 받아오게"). |
| `check_image_format` | 이미지 산출 포맷 게이트(하드 · 운영자 260805 "아이디어 ㄱ" — 같은 날 JPG q90 통일의 짝). |
| `check_contract_anchors` | 계약 앵커 게이트(하드 · 운영자 260805 "머지 ㄱ" — `check_image_format`의 짝). |
| `check_gate_hits` | 게이트 실효성 원장(WARN·비차단 · 운영자 260805 "돌리고 머지 ㄱㄱ" · `check_contract_anchors`의 짝). |
| `check_brief_lib` | 채널 요약 지식 라이브러리 층 생존(하드 · 운영자 260808 "매번 판단이 그때그때 참고 지식이 없어서 새로 시작하는 것 같다 · |
| `check_cover_title_chain` | 게시물 이름 = 표지에 박힌 제목(하드 · 운영자 260812 "기사 인트로 첫줄보다, 오버레이가 가장 정확한 내용이거든"). |
| `check_algo_ledger` | 알고리즘 인사이트 회차 원장 불변식(하드 · 운영자 260802 · 평의회 합의 — 정본 = `.github/scripts/algo_ledger.py` · |
| `check_ko_tone_ssot` | 한국어 결 정본 단일화(하드 · 운영자 260908 «반영하자») — 정본 실존·구간 순서·프로필 스코프(상한선 ⊂ card 스킵 · 윤문 추가축 ⊂ summary 스킵) · 주입기·tone_block·윤문 콜이 같은 파일을 읽음 · TONE_BLOCK 소비자 source · 규칙 불릿 사본 0(토큰 2개+ · 표기 독립). |
