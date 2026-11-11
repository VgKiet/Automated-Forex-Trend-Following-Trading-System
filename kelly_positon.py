# from datetime import datetime, timedelta

# import MetaTrader5 as mt5

# from config import (
#     MAGIC_NUMBER,
#     RISK_PERCENT,
#     KELLY_FRACTION,
#     KELLY_MIN_TRADES,
#     KELLY_LOOKBACK_TRADES,
#     KELLY_LOOKBACK_DAYS,
#     KELLY_MAX_RISK_PERCENT,
#     KELLY_MIN_RISK_PERCENT,
# )

# from logger import pybot_logger


# class KellyPositionSizing:

#     # =========================
#     # LẤY LỊCH SỬ LỆNH ĐÃ ĐÓNG
#     # =========================

#     def get_closed_trades(self, symbol):
#         """Trả về list lãi/lỗ ròng (USD) của các lệnh ĐÃ ĐÓNG của bot
#         (lọc theo MAGIC_NUMBER + symbol), lấy tối đa KELLY_LOOKBACK_TRADES
#         lệnh gần nhất trong KELLY_LOOKBACK_DAYS ngày."""

#         from_date = datetime.now() - timedelta(days=KELLY_LOOKBACK_DAYS)
#         to_date = datetime.now()

#         deals = mt5.history_deals_get(from_date, to_date)

#         if not deals:
#             return []

#         # Gom net P&L theo position_id — 1 lệnh có thể gồm nhiều deal
#         # (deal mở + deal đóng, đôi khi commission tách riêng)
#         net_by_position = {}
#         closed_positions = set()

#         for deal in deals:

#             if deal.magic != MAGIC_NUMBER:
#                 continue

#             if deal.symbol != symbol:
#                 continue

#             net = deal.profit + deal.commission + deal.swap
#             net_by_position.setdefault(deal.position_id, 0.0)
#             net_by_position[deal.position_id] += net

#             if deal.entry == mt5.DEAL_ENTRY_OUT:
#                 closed_positions.add(deal.position_id)

#         # Chỉ lấy các position đã thật sự đóng (có deal OUT)
#         # Thứ tự dict ~ thứ tự deal trả về từ MT5 (tăng dần theo thời gian)
#         # nên lấy N phần tử cuối là N lệnh gần nhất.
#         trades = [
#             net for position_id, net in net_by_position.items()
#             if position_id in closed_positions
#         ]

#         return trades[-KELLY_LOOKBACK_TRADES:]

#     # =========================
#     # TÍNH KELLY FRACTION
#     # =========================

#     def calculate_kelly_fraction(self, trades):
#         """Kelly đầy đủ: f* = W - (1-W)/R
#         W = win rate, R = avg_win / avg_loss (payoff ratio)."""

#         wins = [t for t in trades if t > 0]
#         losses = [t for t in trades if t < 0]

#         if not wins or not losses:
#             return None  # cần có cả lệnh thắng lẫn thua mới tính được

#         win_rate = len(wins) / len(trades)
#         avg_win = sum(wins) / len(wins)
#         avg_loss = abs(sum(losses) / len(losses))

#         if avg_loss == 0:
#             return None

#         payoff_ratio = avg_win / avg_loss

#         kelly = win_rate - (1 - win_rate) / payoff_ratio

#         return kelly, win_rate, payoff_ratio

#     # =========================
#     # RISK % ÁP DỤNG CHO LỆNH TIẾP THEO
#     # =========================

#     def get_risk_percent(self, symbol):
#         """Trả về % risk nên dùng để tính lot cho symbol này.
#         Fallback về RISK_PERCENT cố định nếu chưa đủ lệnh lịch sử."""

#         trades = self.get_closed_trades(symbol)

#         if len(trades) < KELLY_MIN_TRADES:
#             pybot_logger.debug(
#                 f"{symbol}: Kelly cần tối thiểu {KELLY_MIN_TRADES} lệnh đã đóng, "
#                 f"hiện có {len(trades)} → dùng RISK_PERCENT mặc định {RISK_PERCENT}%"
#             )
#             return RISK_PERCENT

#         result = self.calculate_kelly_fraction(trades)

#         if result is None:
#             pybot_logger.warning(
#                 f"{symbol}: Không tính được Kelly (thiếu lệnh thắng hoặc thua) "
#                 f"→ dùng RISK_PERCENT mặc định {RISK_PERCENT}%"
#             )
#             return RISK_PERCENT

#         kelly, win_rate, payoff_ratio = result

#         if kelly <= 0:
#             pybot_logger.info(
#                 f"{symbol}: Kelly={kelly*100:.2f}% (<=0, hệ thống chưa có edge "
#                 f"dương trong {len(trades)} lệnh gần nhất — winrate={win_rate*100:.1f}%, "
#                 f"payoff={payoff_ratio:.2f}) → dùng risk sàn {KELLY_MIN_RISK_PERCENT}%"
#             )
#             return KELLY_MIN_RISK_PERCENT

#         quarter_kelly_percent = kelly * KELLY_FRACTION * 100

#         risk_percent = max(
#             KELLY_MIN_RISK_PERCENT,
#             min(quarter_kelly_percent, KELLY_MAX_RISK_PERCENT)
#         )

#         pybot_logger.info(
#             f"{symbol}: Kelly={kelly*100:.2f}% | 1/4 Kelly={quarter_kelly_percent:.2f}% | "
#             f"Risk áp dụng={risk_percent:.2f}% "
#             f"(winrate={win_rate*100:.1f}%, payoff={payoff_ratio:.2f}, "
#             f"mẫu={len(trades)} lệnh)"
#         )

#         return risk_percent


# kelly_position_sizing = KellyPositionSizing()


import MetaTrader5 as mt5

from config import (
    RISK_PERCENT,
    KELLY_FRACTION,
    KELLY_MIN_TRADES,
    KELLY_LOOKBACK_TRADES,
    KELLY_LOOKBACK_DAYS,
    KELLY_MAX_RISK_PERCENT,
    KELLY_MIN_RISK_PERCENT,
)

from logger import pybot_logger
from trade_history import get_closed_trades


class KellyPositionSizing:

    # =========================
    # LẤY LỊCH SỬ LỆNH ĐÃ ĐÓNG
    # =========================

    def get_closed_trades(self, symbol):
        """Trả về list lãi/lỗ ròng TRÊN MỖI LOT của các lệnh đã đóng
        (theo thứ tự thời gian ĐÓNG, lấy KELLY_LOOKBACK_TRADES lệnh gần nhất).

        Chuẩn hoá theo lot vì lot thay đổi theo risk % — nếu dùng USD thô,
        lệnh lot lớn sẽ bóp méo win rate / payoff. SL cố định theo symbol
        nên lãi/lỗ trên mỗi lot tỉ lệ thuận với R-multiple."""

        trades = get_closed_trades(symbol=symbol, days=KELLY_LOOKBACK_DAYS)

        per_lot = [
            t["net"] / t["volume"]
            for t in trades
            if t["volume"] > 0
        ]

        return per_lot[-KELLY_LOOKBACK_TRADES:]

    # =========================
    # TÍNH KELLY FRACTION
    # =========================

    def calculate_kelly_fraction(self, trades):
        """Kelly đầy đủ: f* = W - (1-W)/R
        W = win rate, R = avg_win / avg_loss (payoff ratio)."""

        wins = [t for t in trades if t > 0]
        losses = [t for t in trades if t < 0]

        if not wins or not losses:
            return None

        win_rate = len(wins) / len(trades)
        avg_win = sum(wins) / len(wins)
        avg_loss = abs(sum(losses) / len(losses))

        if avg_loss == 0:
            return None

        payoff_ratio = avg_win / avg_loss

        kelly = win_rate - (1 - win_rate) / payoff_ratio

        return kelly, win_rate, payoff_ratio

    # =========================
    # RISK % ÁP DỤNG CHO LỆNH TIẾP THEO
    # =========================

    def get_risk_percent(self, symbol):
        """Trả về % risk nên dùng để tính lot cho symbol này.
        Fallback về RISK_PERCENT cố định nếu chưa đủ lệnh lịch sử."""

        trades = self.get_closed_trades(symbol)

        if len(trades) < KELLY_MIN_TRADES:
            pybot_logger.debug(
                f"{symbol}: Kelly cần tối thiểu {KELLY_MIN_TRADES} lệnh đã đóng, "
                f"hiện có {len(trades)} → dùng RISK_PERCENT mặc định {RISK_PERCENT}%"
            )
            return RISK_PERCENT

        result = self.calculate_kelly_fraction(trades)

        if result is None:
            pybot_logger.warning(
                f"{symbol}: Không tính được Kelly (thiếu lệnh thắng hoặc thua) "
                f"→ dùng RISK_PERCENT mặc định {RISK_PERCENT}%"
            )
            return RISK_PERCENT

        kelly, win_rate, payoff_ratio = result

        if kelly <= 0:
            pybot_logger.info(
                f"{symbol}: Kelly={kelly*100:.2f}% (<=0, chưa có edge dương trong "
                f"{len(trades)} lệnh gần nhất — winrate={win_rate*100:.1f}%, "
                f"payoff={payoff_ratio:.2f}) → dùng risk sàn {KELLY_MIN_RISK_PERCENT}%"
            )
            return KELLY_MIN_RISK_PERCENT

        quarter_kelly_percent = kelly * KELLY_FRACTION * 100

        risk_percent = max(
            KELLY_MIN_RISK_PERCENT,
            min(quarter_kelly_percent, KELLY_MAX_RISK_PERCENT)
        )

        pybot_logger.info(
            f"{symbol}: Kelly={kelly*100:.2f}% | 1/4 Kelly={quarter_kelly_percent:.2f}% | "
            f"Risk áp dụng={risk_percent:.2f}% "
            f"(winrate={win_rate*100:.1f}%, payoff={payoff_ratio:.2f}, "
            f"mẫu={len(trades)} lệnh)"
        )

        return risk_percent


kelly_position_sizing = KellyPositionSizing()