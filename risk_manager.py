# import MetaTrader5 as mt5
 
# from config import (
#     MAGIC_NUMBER,
#     MAX_OPEN_TRADES_PER_SYMBOL,
#     DAILY_LOSS_LIMIT
# )
 
# from logger import (
#     pybot_logger,
#     error_logger
# )
 
 
# class RiskManager:
 
#     def __init__(self):
#         self.start_day_balance = 0
#         self.daily_loss_triggered = False
 
#     def init_balance(self):
#         """Gọi sau khi kết nối MT5 thành công.
#         Lấy balance đầu ngày thực sự (0h server time) thay vì
#         balance lúc khởi động — tránh bị reset sai khi restart."""

#         account = mt5.account_info()
#         if account is None:
#             return

#         # Lấy balance hiện tại làm fallback
#         current_balance = account.balance

#         # Tính balance đầu ngày bằng cách trừ lùi P&L hôm nay
#         from datetime import datetime, timezone
#         today_start = datetime.now(timezone.utc).replace(
#             hour=0, minute=0, second=0, microsecond=0
#         )

#         deals = mt5.history_deals_get(today_start, datetime.now(timezone.utc))

#         today_pnl = 0.0
#         if deals:
#             for deal in deals:
#                 if deal.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_IN):
#                     today_pnl += deal.profit + deal.commission + deal.swap

#         # Balance đầu ngày = balance hiện tại - P&L hôm nay
#         self.start_day_balance = round(current_balance - today_pnl, 2)

#         pybot_logger.info(
#             f"Balance hiện tại: {current_balance} | "
#             f"P&L hôm nay: {today_pnl:+.2f} | "
#             f"Balance đầu ngày: {self.start_day_balance}"
#         )
 
#     def can_open_trade(self, symbol):
#         """Kiểm tra có được mở lệnh mới cho symbol này không"""
 
#         # Kiểm tra lỗ ngày trước — áp dụng toàn bộ bot
#         if not self.check_daily_loss():
#             return False
 
#         # Kiểm tra riêng từng symbol
#         if not self.check_open_positions(symbol):
#             return False
 
#         return True
 
#     def check_open_positions(self, symbol):
 
#         positions = mt5.positions_get(symbol=symbol)
 
#         if not positions:
#             return True
 
#         count = sum(
#             1 for p in positions
#             if p.magic == MAGIC_NUMBER
#         )
 
#         if count >= MAX_OPEN_TRADES_PER_SYMBOL:
#             pybot_logger.warning(
#                 f"{symbol}: đang có {count} lệnh mở, chờ đóng trước"
#             )
#             return False
 
#         return True
 
#     def check_daily_loss(self):
 
#         if self.daily_loss_triggered:
#             return False
 
#         account = mt5.account_info()
 
#         if account is None:
#             error_logger.error("Không lấy được thông tin tài khoản")
#             return False
 
#         if self.start_day_balance <= 0:
#             return True
 
#         loss_percent = (
#             (self.start_day_balance - account.equity)
#             / self.start_day_balance
#         ) * 100
 
#         if loss_percent >= DAILY_LOSS_LIMIT:
#             self.daily_loss_triggered = True
#             pybot_logger.warning(
#                 f"Lỗ {loss_percent:.2f}% — vượt giới hạn {DAILY_LOSS_LIMIT}% "
#                 f"→ dừng bot cả ngày hôm nay"
#             )
#             return False
 
#         return True
 
 
# risk_manager = RiskManager()

from datetime import timedelta

import MetaTrader5 as mt5

from config import (
    MAGIC_NUMBER,
    MAX_OPEN_TRADES_PER_SYMBOL,
    DAILY_LOSS_LIMIT,
    WEEKLY_LOSS_LIMIT,
    MAX_CONSECUTIVE_LOSSES,
)

from logger import (
    pybot_logger,
    error_logger
)

from trade_history import server_now, get_closed_trades


class RiskManager:

    def __init__(self):
        self.start_day_balance = 0
        self.start_week_balance = 0
        self.current_day = None        # ngày giao dịch (theo giờ server)
        self.current_week = None       # (năm, tuần ISO) theo giờ server
        self.daily_loss_triggered = False
        self.weekly_loss_triggered = False
        self.consec_since = 0          # chỉ đếm lệnh đóng SAU mốc này (epoch)
        self.consec_logged = False

    # =========================
    # BALANCE ĐẦU NGÀY / ĐẦU TUẦN
    # =========================
    def _balance_at(self, since_dt):
        """Balance tại thời điểm since_dt = balance hiện tại - P&L (kể cả nạp/rút) từ đó."""

        account = mt5.account_info()
        if account is None:
            return None

        now = server_now()
        deals = mt5.history_deals_get(since_dt, now + timedelta(days=1))

        pnl = 0.0
        if deals:
            for deal in deals:
                if deal.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_IN):
                    pnl += deal.profit + deal.commission + deal.swap

        return round(account.balance - pnl, 2)

    def init_balance(self):
        """Gọi sau khi kết nối MT5 thành công (và tự gọi lại khi sang ngày/tuần mới)."""

        now = server_now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = day_start - timedelta(days=day_start.weekday())

        day_balance = self._balance_at(day_start)
        week_balance = self._balance_at(week_start)

        if day_balance is None or week_balance is None:
            error_logger.error("Không lấy được account để khởi tạo balance")
            return

        self.start_day_balance = day_balance
        self.start_week_balance = week_balance
        self.current_day = day_start.date()
        self.current_week = week_start.date()
        self.consec_since = int(now.timestamp())
        self.consec_logged = False

        pybot_logger.info(
            f"Balance đầu ngày: {self.start_day_balance} | "
            f"Balance đầu tuần: {self.start_week_balance}"
        )

    # =========================
    # GỌI MỖI VÒNG LẶP: reset theo ngày/tuần + kiểm tra lỗ
    # =========================
    def update(self):
        """Trả về True nếu bot đang bị khoá do vượt giới hạn lỗ ngày/tuần."""

        now = server_now()
        today = now.date()
        week = (now - timedelta(days=now.weekday())).date()

        if self.current_day is None:
            self.init_balance()

        elif today != self.current_day:
            self.daily_loss_triggered = False
            pybot_logger.info("Sang ngày giao dịch mới → reset giới hạn lỗ ngày")

            if week != self.current_week:
                self.weekly_loss_triggered = False
                pybot_logger.info("Sang tuần mới → reset giới hạn lỗ tuần")

            self.init_balance()

        self._check_loss_limits()

        return self.daily_loss_triggered or self.weekly_loss_triggered

    def _check_loss_limits(self):

        account = mt5.account_info()

        if account is None:
            error_logger.error("Không lấy được thông tin tài khoản")
            return

        if self.start_day_balance > 0 and not self.daily_loss_triggered:
            loss = (self.start_day_balance - account.equity) / self.start_day_balance * 100
            if loss >= DAILY_LOSS_LIMIT:
                self.daily_loss_triggered = True
                pybot_logger.warning(
                    f"Lỗ ngày {loss:.2f}% ≥ {DAILY_LOSS_LIMIT}% → đóng hết, nghỉ đến ngày mai"
                )

        if self.start_week_balance > 0 and not self.weekly_loss_triggered:
            loss = (self.start_week_balance - account.equity) / self.start_week_balance * 100
            if loss >= WEEKLY_LOSS_LIMIT:
                self.weekly_loss_triggered = True
                pybot_logger.warning(
                    f"Lỗ tuần {loss:.2f}% ≥ {WEEKLY_LOSS_LIMIT}% → đóng hết, nghỉ đến tuần sau"
                )

    # =========================
    # THUA LIÊN TIẾP
    # =========================
    def check_consecutive_losses(self):

        trades = get_closed_trades(days=7, closed_after=self.consec_since)

        if len(trades) < MAX_CONSECUTIVE_LOSSES:
            return True

        last = trades[-MAX_CONSECUTIVE_LOSSES:]

        if all(t["net"] < 0 for t in last):
            if not self.consec_logged:
                self.consec_logged = True
                pybot_logger.warning(
                    f"Thua liên tiếp {MAX_CONSECUTIVE_LOSSES} lệnh → "
                    f"ngừng mở lệnh mới đến ngày mai"
                )
            return False

        return True

    # =========================
    # ĐƯỢC PHÉP MỞ LỆNH MỚI?
    # =========================
    def can_open_trade(self, symbol):
        """Chỉ gọi khi symbol đang FLAT (chuẩn bị mở lệnh mới)."""

        if self.daily_loss_triggered or self.weekly_loss_triggered:
            return False

        if not self.check_consecutive_losses():
            return False

        return self.check_open_positions(symbol)

    def check_open_positions(self, symbol):

        positions = mt5.positions_get(symbol=symbol)

        if not positions:
            return True

        count = sum(1 for p in positions if p.magic == MAGIC_NUMBER)

        if count >= MAX_OPEN_TRADES_PER_SYMBOL:
            pybot_logger.warning(f"{symbol}: đang có {count} lệnh mở, chờ đóng trước")
            return False

        return True


risk_manager = RiskManager()