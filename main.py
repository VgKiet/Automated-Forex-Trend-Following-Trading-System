# import time
# from config import CHECK_INTERVAL, DAILY_LOSS_LIMIT, SYMBOLS
# from mt5_connect import mt5_connect
# from data_loader import data_loader
# from indicators import indicators
# from strategy import strategy
# from execution import execution
# from risk_manager import risk_manager


# def process_symbol(symbol):

#     # Load dữ liệu
#     df = data_loader.get_data(symbol)

#     if df is None:
#         print(f"  [{symbol}] Không lấy được dữ liệu")
#         return

#     # Tính EMA
#     df = indicators.add_ema(df)

#     # Tín hiệu
#     signal = strategy.get_signal(df, symbol=symbol)

#     # Vị thế hiện tại
#     position = execution.get_position(symbol)

#     print(f"  [{symbol}] Signal={signal} | Position={position}")

#     # EMA rối → đóng lệnh ngay nếu đang có
#     if signal == "CLOSE":
#         if position is not None:
#             print(f"  [{symbol}] EMA không theo thứ tự → đóng lệnh")
#             execution.close_positions(symbol)
#         return

#     # Nến xa EMA5 → không mở lệnh mới
#     # Nhưng nếu đang có lệnh NGƯỢC chiều → đóng ngay vì xu hướng đã đổi
#     if signal == "SKIP":
#         if position == "SELL" and strategy.last_direction(df) == "BUY":
#             print(f"  [{symbol}] Xu hướng đổi sang BUY, nến chưa gần EMA5 → đóng SELL, chờ vào BUY")
#             execution.close_positions(symbol)
#         elif position == "BUY" and strategy.last_direction(df) == "SELL":
#             print(f"  [{symbol}] Xu hướng đổi sang SELL, nến chưa gần EMA5 → đóng BUY, chờ vào SELL")
#             execution.close_positions(symbol)
#         else:
#             print(f"  [{symbol}] Nến xa EMA5 → chờ pullback")
#         return

#     # Kiểm tra risk manager cho symbol này
#     if not risk_manager.can_open_trade(symbol):
#         return

#     # Xử lý tín hiệu
#     if signal == "BUY":
#         if position == "SELL":
#             closed = execution.close_positions(symbol)
#             if closed:
#                 time.sleep(2)
#                 execution.open_buy(symbol)
#             else:
#                 print(f"  [{symbol}] Đóng SELL thất bại → không mở BUY")
#         elif position is None:
#             execution.open_buy(symbol)

#     elif signal == "SELL":
#         if position == "BUY":
#             closed = execution.close_positions(symbol)
#             if closed:
#                 time.sleep(2)
#                 execution.open_sell(symbol)
#             else:
#                 print(f"  [{symbol}] Đóng BUY thất bại → không mở SELL")
#         elif position is None:
#             execution.open_sell(symbol)


# def main():

#     print("Chuẩn bị kết nối")

#     if not mt5_connect.connect():
#         print("Kết nối thất bại")
#         return

#     print("Kết nối thành công")

#     # Khởi tạo balance đầu ngày sau khi connect xong
#     risk_manager.init_balance()

#     try:
#         while True:

#             print(f"\n{'='*40}")

#             # Kiểm tra daily loss — nếu triggered thì dừng hết
#             if risk_manager.daily_loss_triggered:
#                 print(f"Lỗ quá {DAILY_LOSS_LIMIT}% hôm nay → dừng bot")
#                 execution.close_all_symbols(SYMBOLS)
#                 break

#             # Quét từng symbol
#             for symbol in SYMBOLS:
#                 process_symbol(symbol)

#             print(f"Chờ {CHECK_INTERVAL}s...")
#             time.sleep(CHECK_INTERVAL)

#     except KeyboardInterrupt:
#         print("Dừng bot theo yêu cầu người dùng (Ctrl + C)")

#     finally:
#         mt5_connect.disconnect()
#         print("Đã ngắt kết nối MT5")


# if __name__ == "__main__":
#     main()

import time
import traceback

from dotenv import load_dotenv

load_dotenv()  # phải chạy trước khi import các module đọc biến môi trường

from config import (
    CHECK_INTERVAL,
    DAILY_LOSS_LIMIT,
    COOLDOWN_BARS,
    MAX_SPREAD,
    MAX_SPREAD_DEFAULT,
    SYMBOLS,
)
import MetaTrader5 as mt5
from mt5_connect import mt5_connect
from data_loader import data_loader
from indicators import indicators
from strategy import strategy
from execution import execution
from risk_manager import risk_manager
from logger import error_logger


class SymbolState:
    """Trạng thái theo từng symbol."""

    def __init__(self):
        self.last_bar_time = None   # nến đã xử lý gần nhất
        self.was_in_position = False
        self.cooldown = 0           # số nến còn phải chờ trước khi được vào lại


states = {symbol: SymbolState() for symbol in SYMBOLS}


def spread_ok(symbol):
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return False

    spread = tick.ask - tick.bid
    limit = MAX_SPREAD.get(symbol, MAX_SPREAD_DEFAULT)

    if spread > limit:
        print(f"  [{symbol}] Spread {spread:.5f} > {limit} → không mở lệnh")
        return False

    return True


def open_trade(symbol, direction):
    if not risk_manager.can_open_trade(symbol):
        return
    if not spread_ok(symbol):
        return
    if direction == "BUY":
        execution.open_buy(symbol)
    else:
        execution.open_sell(symbol)


def process_symbol(symbol):

    state = states[symbol]

    df = data_loader.get_data(symbol)

    if df is None:
        print(f"  [{symbol}] Không lấy được dữ liệu")
        return

    # Chỉ xử lý khi có nến MỚI đóng — tránh tín hiệu nhấp nháy giữa nến
    bar_time = df["time"].iloc[-1]

    if state.last_bar_time == bar_time:
        return

    position = execution.get_position(symbol)

    # Lệnh vừa bị broker đóng (SL/TP/stop-out) → vào cooldown
    if state.was_in_position and position is None:
        state.cooldown = COOLDOWN_BARS
        print(f"  [{symbol}] Lệnh đã đóng bởi broker (SL/TP) → cooldown {COOLDOWN_BARS} nến")

    state.was_in_position = position is not None

    in_cooldown = state.cooldown > 0
    if state.cooldown > 0:
        state.cooldown -= 1

    df = indicators.add_ema(df)
    signal = strategy.get_signal(df, symbol=symbol)

    print(f"  [{symbol}] Nến {bar_time} | Signal={signal} | Position={position}")

    # EMA rối → đóng lệnh nếu đang có
    if signal == "CLOSE":
        if position is not None:
            print(f"  [{symbol}] EMA không theo thứ tự → đóng lệnh")
            if execution.close_positions(symbol):
                state.was_in_position = False
                state.cooldown = COOLDOWN_BARS
        state.last_bar_time = bar_time
        return

    # Nến xa EMA5 / sát S&R → không mở lệnh mới.
    # Đang giữ lệnh NGƯỢC xu hướng EMA → đóng.
    if signal == "SKIP":
        direction = strategy.last_direction(df)
        if (position == "SELL" and direction == "BUY") or \
           (position == "BUY" and direction == "SELL"):
            print(f"  [{symbol}] Xu hướng đổi sang {direction} → đóng lệnh ngược chiều")
            if execution.close_positions(symbol):
                state.was_in_position = False
        else:
            print(f"  [{symbol}] Chờ pullback")
        state.last_bar_time = bar_time
        return

    # signal là BUY hoặc SELL
    if position == signal:
        pass  # đang giữ đúng chiều, không làm gì (không spam log)

    elif position is None:
        if in_cooldown:
            print(f"  [{symbol}] Đang cooldown → chưa vào lại")
        else:
            open_trade(symbol, signal)

    else:
        # Đang giữ lệnh ngược chiều → đảo: đóng rồi mở (đây là nhánh đảo chiều thật sự)
        if execution.close_positions(symbol):
            state.was_in_position = False
            time.sleep(2)
            open_trade(symbol, signal)
        else:
            print(f"  [{symbol}] Đóng {position} thất bại → không mở {signal}")

    state.last_bar_time = bar_time


def main():

    print("Chuẩn bị kết nối")

    if not mt5_connect.connect():
        print("Kết nối thất bại")
        return

    print("Kết nối thành công")

    risk_manager.init_balance()
    execution.init_logged_history()

    limit_closed = False

    try:
        while True:

            print(f"\n{'='*40}")

            # Ghi log các lệnh broker đã đóng (SL/TP...) — kể cả khi đang bị khoá
            try:
                execution.sync_closed_trades()
            except Exception:
                error_logger.error(f"sync_closed_trades lỗi:\n{traceback.format_exc()}")

            # Kiểm tra giới hạn lỗ MỖI vòng lặp (tự reset khi sang ngày/tuần mới)
            try:
                locked = risk_manager.update()
            except Exception:
                error_logger.error(f"risk_manager.update lỗi:\n{traceback.format_exc()}")
                locked = True  # an toàn: không mở lệnh khi không kiểm tra được

            if locked:
                if not limit_closed:
                    print("Vượt giới hạn lỗ → đóng toàn bộ lệnh, nghỉ cho đến kỳ sau")
                    execution.close_all_symbols(SYMBOLS)
                    limit_closed = True
                print(f"Đang nghỉ (lỗ ngày > {DAILY_LOSS_LIMIT}% hoặc lỗ tuần)...")
                time.sleep(CHECK_INTERVAL)
                continue

            limit_closed = False

            # Mỗi symbol độc lập: 1 symbol lỗi không làm sập cả bot
            for symbol in SYMBOLS:
                try:
                    process_symbol(symbol)
                except Exception:
                    error_logger.error(
                        f"{symbol}: lỗi trong process_symbol:\n{traceback.format_exc()}"
                    )
                    print(f"  [{symbol}] Có lỗi, xem logs/errors.log")

            print(f"Chờ {CHECK_INTERVAL}s...")
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("Dừng bot theo yêu cầu người dùng (Ctrl + C)")

    finally:
        mt5_connect.disconnect()
        print("Đã ngắt kết nối MT5")


if __name__ == "__main__":
    main()