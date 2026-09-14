# 접속 원장 정체 알림의 조치 주체 판정 회귀(apps/insta/insta_signals.py online_stall_who).
# 계약: Meta 공회신(빈 value)은 STALL_ESC_DAYS 미만이면 발행 0(조치 없는 알림 = 알림 아님 · 운영자 260914) ·
#       장기화는 op 승격(영구 묵음 0) · 토큰 노후는 원인 선행이라 항상 op · 둘 다 아니면 코드 축(cc).
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'apps', 'insta'))

import insta_signals as S  # noqa: E402


class OnlineStallWho(unittest.TestCase):
    def test_short_lag_is_silent(self):
        for d in (None, 0, 1, S.STALL_DAYS - 1):
            self.assertIsNone(S.online_stall_who(d, 10, True))
            self.assertIsNone(S.online_stall_who(d, 10, False))

    def test_blank_short_is_silent(self):
        # 260914 실측: 3일째 공회신 · 토큰 29일 · dropped 무오류 → 발행 안 함
        self.assertIsNone(S.online_stall_who(3, 29, True))
        self.assertIsNone(S.online_stall_who(S.STALL_ESC_DAYS - 1, 29, True))

    def test_blank_long_escalates_to_op(self):
        self.assertEqual(S.online_stall_who(S.STALL_ESC_DAYS, 29, True), 'auto_esc')
        self.assertEqual(S.online_stall_who(40, None, True), 'auto_esc')

    def test_old_token_is_op_first(self):
        self.assertEqual(S.online_stall_who(3, S.TOKEN_AGE_D, True), 'op')
        self.assertEqual(S.online_stall_who(3, 80, False), 'op')

    def test_unknown_cause_is_cc(self):
        self.assertEqual(S.online_stall_who(3, 29, False), 'cc')
        self.assertEqual(S.online_stall_who(3, None, False), 'cc')


if __name__ == '__main__':
    unittest.main()
