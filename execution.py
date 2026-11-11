# # BẢN VERSION NÂNG CẤP

# import MetaTrader5 as mt5
# import time as time_module
# from datetime import datetime, timedelta

# from config import (
#     MAGIC_NUMBER,
#     RISK_PERCENT,
#     SL_PIPS,
#     SL_PIPS_MAP,
#     MAX_LOT_SIZE,
#     USE_KELLY_SIZING
# )

# from logger import (
#     trade_logger,
#     error_logger,
#     report_logger
# )

# from notion_logger import log_trade_to_notion
# from kelly_positon import kelly_position_sizing
 
 
# RETCODE_MESSAGES = {
#     10004: "Requote",
#     10006: "Request bị từ chối",
#     10007: "Request bị hủy bởi trader",
#     10008: "Đã đặt lệnh",
#     10009: "Request được xử lý",
#     10010: "Chỉ thực hiện một phần",
#     10011: "Lỗi xử lý request",
#     10012: "Request hết hạn",
#     10013: "Request không hợp lệ",
#     10014: "Volume không hợp lệ",
#     10015: "Giá không hợp lệ",
#     10016: "Stop không hợp lệ",
#     10017: "Trading bị tắt",
#     10018: "Thị trường đóng cửa",
#     10019: "Không đủ tiền",
#     10020: "Giá đã thay đổi",
#     10021: "Không có giá",
#     10022: "Ngày hết hạn không hợp lệ",
#     10023: "Trạng thái lệnh thay đổi",
#     10024: "Quá nhiều request",
#     10025: "Không có thay đổi nào",
#     10026: "AutoTrading bị tắt bởi server",
#     10027: "AutoTrading bị tắt trên MT5 — hãy bật nút 'Algo Trading' trên toolbar",
#     10028: "Request bị khóa",
#     10029: "Chỉ cho phép thay đổi dài hạn",
#     10030: "Chế độ fill không được hỗ trợ",
# }
 
 
# class Execution:
 
#     # =========================
#     # KIỂM TRA AUTOTRADING
#     # =========================
#     def check_autotrading(self):
 
#         terminal = mt5.terminal_info()
 
#         if terminal is None:
#             error_logger.error("Không lấy được thông tin terminal MT5")
#             return False
 
#         if not terminal.trade_allowed:
#             error_logger.error(
#                 "AutoTrading đang bị TẮT! "
#                 "Vào MT5 → bật nút 'Algo Trading' trên toolbar (phải có màu xanh)"
#             )
#             return False
 
#         return True
 
#     # =========================
#     # TỰ ĐỘNG CHỌN FILLING MODE
#     # =========================
#     def get_filling_mode(self, symbol):
 
#         symbol_info = mt5.symbol_info(symbol)
 
#         if symbol_info is None:
#             return mt5.ORDER_FILLING_IOC
 
#         filling = symbol_info.filling_mode
 
#         if filling & 1:  # FOK
#             return mt5.ORDER_FILLING_FOK
 
#         if filling & 2:  # IOC
#             return mt5.ORDER_FILLING_IOC
 
#         return mt5.ORDER_FILLING_RETURN
 
#     # =========================
#     # LẤY SL PIPS THEO SYMBOL
#     # =========================
#     def _get_sl_pips(self, symbol):
#         return SL_PIPS_MAP.get(symbol, SL_PIPS)

#     # =========================
#     # TÍNH GIÁ TRỊ 1 PIP THEO SYMBOL
#     # =========================
#     def _get_pip_size(self, symbol_info):
#         digits = symbol_info.digits
#         if digits == 2:    # XAUUSD, dầu...
#             return symbol_info.point * 1
#         elif digits == 3:  # USDJPY
#             return symbol_info.point * 100
#         else:              # GBPUSD, EURUSD (4/5 digits)
#             return symbol_info.point * 10

#     # =========================
#     # TÍNH GIÁ STOP LOSS
#     # =========================
#     def calculate_sl(self, symbol, price, order_type):

#         symbol_info = mt5.symbol_info(symbol)

#         if symbol_info is None:
#             return 0.0

#         sl_pips = self._get_sl_pips(symbol)
#         pip     = self._get_pip_size(symbol_info)

#         if order_type == "BUY":
#             return round(price - sl_pips * pip, symbol_info.digits)

#         if order_type == "SELL":
#             return round(price + sl_pips * pip, symbol_info.digits)

#         return 0.0
 
#     # =========================
#     # TÍNH LOT THEO RISK
#     # =========================
#     def calculate_lot(self, symbol, stop_loss_pips=None):
 
#         if stop_loss_pips is None:
#             stop_loss_pips = self._get_sl_pips(symbol)
 
#         account = mt5.account_info()
#         symbol_info = mt5.symbol_info(symbol)
 
#         if account is None or symbol_info is None:
#             return 0.01
 
#         balance = account.balance

#         if USE_KELLY_SIZING:
#             risk_percent = kelly_position_sizing.get_risk_percent(symbol)
#         else:
#             risk_percent = RISK_PERCENT

#         risk_money = balance * (risk_percent / 100)
 
#         tick_value = symbol_info.trade_tick_value
#         tick_size  = symbol_info.trade_tick_size
#         pip_size   = self._get_pip_size(symbol_info)
 
#         if tick_size == 0 or tick_value == 0 or pip_size == 0:
#             return symbol_info.volume_min
 
#         # Giá trị 1 pip cho 1 lot — tính đúng theo tick
#         pip_value_per_lot = tick_value * (pip_size / tick_size)
 
#         if stop_loss_pips <= 0:
#             stop_loss_pips = 50
 
#         raw_lot = risk_money / (stop_loss_pips * pip_value_per_lot)
 
#         lot = max(symbol_info.volume_min,
#                   min(raw_lot, symbol_info.volume_max))
 
#         # Giới hạn tối đa tuyệt đối — phòng tính sai
#         lot = min(lot, MAX_LOT_SIZE)
 
#         step = symbol_info.volume_step
#         lot  = int(lot / step) * step
 
#         if lot < symbol_info.volume_min:
#             lot = symbol_info.volume_min
 
#         return round(lot, 2)
 
#     # =========================
#     # BUY
#     # =========================
#     def open_buy(self, symbol):
 
#         if not self.check_autotrading():
#             return False
 
#         tick = mt5.symbol_info_tick(symbol)
 
#         if tick is None:
#             error_logger.error(f"Không lấy được tick của {symbol}")
#             return False
 
#         lot = self.calculate_lot(symbol)
#         sl  = self.calculate_sl(symbol, tick.ask, "BUY")
 
#         request = {
#             "action": mt5.TRADE_ACTION_DEAL,
#             "symbol": symbol,
#             "volume": lot,
#             "type": mt5.ORDER_TYPE_BUY,
#             "price": tick.ask,
#             "sl": sl,
#             "deviation": 20,
#             "magic": MAGIC_NUMBER,
#             "comment": "EMA BOT BUY",
#             "type_time": mt5.ORDER_TIME_GTC,
#             "type_filling": self.get_filling_mode(symbol)
#         }
 
#         result = mt5.order_send(request)
 
#         if result.retcode != mt5.TRADE_RETCODE_DONE:
#             msg = RETCODE_MESSAGES.get(result.retcode, "Lỗi không xác định")
#             error_logger.error(f"BUY {symbol} thất bại | RetCode={result.retcode} | {msg}")
#             return False
 
#         trade_logger.info(
#             f"BUY {symbol} | Lot={lot} | Price={tick.ask} | SL={sl} | Ticket={result.order}"
#         )
 
#         return True
 
#     # =========================
#     # SELL
#     # =========================
#     def open_sell(self, symbol):
 
#         if not self.check_autotrading():
#             return False
 
#         tick = mt5.symbol_info_tick(symbol)
 
#         if tick is None:
#             error_logger.error(f"Không lấy được tick của {symbol}")
#             return False
 
#         lot = self.calculate_lot(symbol)
#         sl  = self.calculate_sl(symbol, tick.bid, "SELL")
 
#         request = {
#             "action": mt5.TRADE_ACTION_DEAL,
#             "symbol": symbol,
#             "volume": lot,
#             "type": mt5.ORDER_TYPE_SELL,
#             "price": tick.bid,
#             "sl": sl,
#             "deviation": 20,
#             "magic": MAGIC_NUMBER,
#             "comment": "EMA BOT SELL",
#             "type_time": mt5.ORDER_TIME_GTC,
#             "type_filling": self.get_filling_mode(symbol)
#         }
 
#         result = mt5.order_send(request)
 
#         if result.retcode != mt5.TRADE_RETCODE_DONE:
#             msg = RETCODE_MESSAGES.get(result.retcode, "Lỗi không xác định")
#             error_logger.error(f"SELL {symbol} thất bại | RetCode={result.retcode} | {msg}")
#             return False
 
#         trade_logger.info(
#             f"SELL {symbol} | Lot={lot} | Price={tick.bid} | SL={sl} | Ticket={result.order}"
#         )
 
#         return True
 
#     # =========================
#     # GET POSITION
#     # =========================
#     def get_position(self, symbol):
 
#         positions = mt5.positions_get(symbol=symbol)
 
#         if not positions:
#             return None
 
#         for position in positions:
 
#             if position.magic != MAGIC_NUMBER:
#                 continue
 
#             if position.type == mt5.POSITION_TYPE_BUY:
#                 return "BUY"
 
#             if position.type == mt5.POSITION_TYPE_SELL:
#                 return "SELL"
 
#         return None
 
#     # =========================
#     # CLOSE
#     # =========================
#     def close_positions(self, symbol):

#         positions = mt5.positions_get(symbol=symbol)

#         if not positions:
#             return True

#         all_closed = True

#         for position in positions:

#             if position.magic != MAGIC_NUMBER:
#                 continue

#             tick = mt5.symbol_info_tick(symbol)

#             if tick is None:
#                 error_logger.error(f"Không lấy được tick của {symbol}")
#                 all_closed = False
#                 continue

#             if position.type == mt5.POSITION_TYPE_BUY:
#                 order_type = mt5.ORDER_TYPE_SELL
#                 price = tick.bid
#             else:
#                 order_type = mt5.ORDER_TYPE_BUY
#                 price = tick.ask

#             request = {
#                 "action":       mt5.TRADE_ACTION_DEAL,
#                 "symbol":       symbol,
#                 "volume":       position.volume,
#                 "type":         order_type,
#                 "position":     position.ticket,
#                 "price":        price,
#                 "deviation":    20,
#                 "magic":        MAGIC_NUMBER,
#                 "comment":      "EMA BOT CLOSE",
#                 "type_filling": self.get_filling_mode(symbol)
#             }

#             result = mt5.order_send(request)

#             if result.retcode != mt5.TRADE_RETCODE_DONE:
#                 msg = RETCODE_MESSAGES.get(result.retcode, "Lỗi không xác định")
#                 error_logger.error(
#                     f"Đóng lệnh thất bại | {symbol} | Ticket={position.ticket} | RetCode={result.retcode} | {msg}"
#                 )
#                 all_closed = False

#             else:
#                 direction  = "BUY" if position.type == mt5.POSITION_TYPE_BUY else "SELL"
#                 open_price = position.price_open
#                 volume     = position.volume

#                 trade_logger.info(f"CLOSE {symbol} | Ticket={position.ticket}")

#                 # Lấy P&L từ deal history — retry 3 lần (đợi deal được ghi vào lịch sử)
#                 profit = 0.0
#                 swap   = 0.0
#                 net    = 0.0
#                 found  = False

#                 for attempt in range(3):
#                     # Dùng cửa sổ RỘNG (±1 ngày) thay vì ±5 phút theo giờ local.
#                     # Lý do: timestamp deal trong lịch sử MT5 tính theo GIỜ SERVER
#                     # của broker, không phải giờ máy chạy bot. Nếu lệch múi giờ
#                     # (thường lệch vài tiếng), cửa sổ 5 phút theo giờ local sẽ
#                     # KHÔNG BAO GIỜ trùng với thời điểm deal thật → luôn "not found"
#                     # → report.log toàn ghi Profit=Swap=Net=0.00 dù lệnh lời/lỗ thật.
#                     # Lọc theo position_id + DEAL_ENTRY_OUT vẫn đảm bảo đúng deal,
#                     # nên nới rộng khung thời gian là an toàn.
#                     deals = mt5.history_deals_get(
#                         datetime.now() - timedelta(days=1),
#                         datetime.now() + timedelta(days=1)
#                     )
#                     if deals:
#                         for deal in deals:
#                             if (deal.position_id == position.ticket
#                                     and deal.entry == mt5.DEAL_ENTRY_OUT):
#                                 profit = deal.profit
#                                 swap   = deal.swap
#                                 net    = profit + swap + deal.commission
#                                 found  = True
#                                 break
#                     if found:
#                         break
#                     time_module.sleep(1)

#                 if not found:
#                     error_logger.warning(
#                         f"Không tìm được deal cho Ticket={position.ticket} sau 3 lần thử"
#                     )

#                 result_str = "PROFIT" if net >= 0 else "LOSS"

#                 report_logger.info(
#                     f"[{result_str}] {symbol} {direction} | "
#                     f"Ticket={position.ticket} | "
#                     f"Open={open_price:.5f} Close={price:.5f} | "
#                     f"Lot={volume} | "
#                     f"Profit={profit:+.2f} Swap={swap:+.2f} Net={net:+.2f} USD"
#                 )

#                 # Ghi vào Notion
#                 log_trade_to_notion(
#                     symbol      = symbol,
#                     direction   = direction,
#                     open_price  = open_price,
#                     close_price = price,
#                     lot         = volume,
#                     profit      = profit,
#                     swap        = swap,
#                     net         = net,
#                     ticket      = position.ticket,
#                     open_time   = datetime.fromtimestamp(position.time)
#                 )

#         return all_closed
 
#     def close_all_symbols(self, symbols):
#         for symbol in symbols:
#             self.close_positions(symbol)
 
 
# execution = Execution()




# Bản đã sửa
# import math
# import MetaTrader5 as mt5
# import time as time_module
# from datetime import datetime, timedelta, timezone

# from config import (
#     MAGIC_NUMBER,
#     RISK_PERCENT,
#     SL_DISTANCE,
#     SL_DISTANCE_DEFAULT,
#     MAX_LOT_SIZE,
#     MAX_RISK_OVERSHOOT,
#     USE_KELLY_SIZING
# )

# from logger import (
#     trade_logger,
#     error_logger,
#     report_logger,
#     pybot_logger
# )

# from notion_logger import log_trade_to_notion
# from kelly_positon import kelly_position_sizing


# RETCODE_MESSAGES = {
#     10004: "Requote",
#     10006: "Request bị từ chối",
#     10007: "Request bị hủy bởi trader",
#     10008: "Đã đặt lệnh",
#     10009: "Request được xử lý",
#     10010: "Chỉ thực hiện một phần",
#     10011: "Lỗi xử lý request",
#     10012: "Request hết hạn",
#     10013: "Request không hợp lệ",
#     10014: "Volume không hợp lệ",
#     10015: "Giá không hợp lệ",
#     10016: "Stop không hợp lệ",
#     10017: "Trading bị tắt",
#     10018: "Thị trường đóng cửa",
#     10019: "Không đủ tiền",
#     10020: "Giá đã thay đổi",
#     10021: "Không có giá",
#     10022: "Ngày hết hạn không hợp lệ",
#     10023: "Trạng thái lệnh thay đổi",
#     10024: "Quá nhiều request",
#     10025: "Không có thay đổi nào",
#     10026: "AutoTrading bị tắt bởi server",
#     10027: "AutoTrading bị tắt trên MT5 — hãy bật nút 'Algo Trading' trên toolbar",
#     10028: "Request bị khóa",
#     10029: "Chỉ cho phép thay đổi dài hạn",
#     10030: "Chế độ fill không được hỗ trợ",
# }

# DEAL_REASON_TEXT = {
#     mt5.DEAL_REASON_SL: "SL",
#     mt5.DEAL_REASON_TP: "TP",
#     mt5.DEAL_REASON_SO: "STOP-OUT",
#     mt5.DEAL_REASON_CLIENT: "MANUAL",
#     mt5.DEAL_REASON_EXPERT: "BOT",
# }


# def _server_ts_to_dt(ts):
#     """Timestamp của MT5 là 'giờ server' mã hoá như epoch.
#     fromtimestamp() sẽ cộng thêm múi giờ máy local → lệch.
#     Dùng UTC để lấy đúng đồng hồ của server (naive datetime)."""
#     return datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)


# class Execution:

#     def __init__(self):
#         # Các position đã được ghi report/Notion — tránh ghi trùng
#         self._logged_positions = set()

#     # =========================
#     # KIỂM TRA AUTOTRADING
#     # =========================
#     def check_autotrading(self):

#         terminal = mt5.terminal_info()

#         if terminal is None:
#             error_logger.error("Không lấy được thông tin terminal MT5")
#             return False

#         if not terminal.trade_allowed:
#             error_logger.error(
#                 "AutoTrading đang bị TẮT! "
#                 "Vào MT5 → bật nút 'Algo Trading' trên toolbar (phải có màu xanh)"
#             )
#             return False

#         return True

#     # =========================
#     # TỰ ĐỘNG CHỌN FILLING MODE
#     # =========================
#     def get_filling_mode(self, symbol):

#         symbol_info = mt5.symbol_info(symbol)

#         if symbol_info is None:
#             return mt5.ORDER_FILLING_IOC

#         filling = symbol_info.filling_mode

#         if filling & 1:  # FOK
#             return mt5.ORDER_FILLING_FOK

#         if filling & 2:  # IOC
#             return mt5.ORDER_FILLING_IOC

#         return mt5.ORDER_FILLING_RETURN

#     # =========================
#     # GỬI LỆNH AN TOÀN (xử lý result = None)
#     # =========================
#     def _send(self, request, label):

#         result = mt5.order_send(request)

#         if result is None:
#             error_logger.error(
#                 f"{label} thất bại | order_send trả về None | {mt5.last_error()}"
#             )
#             return None

#         if result.retcode != mt5.TRADE_RETCODE_DONE:
#             msg = RETCODE_MESSAGES.get(result.retcode, "Lỗi không xác định")
#             error_logger.error(
#                 f"{label} thất bại | RetCode={result.retcode} | {msg}"
#             )
#             return None

#         return result

#     # =========================
#     # STOP LOSS THEO KHOẢNG GIÁ (không dùng pip nữa)
#     # =========================
#     def _get_sl_distance(self, symbol):
#         return SL_DISTANCE.get(symbol, SL_DISTANCE_DEFAULT)

#     def calculate_sl(self, symbol, price, order_type):

#         symbol_info = mt5.symbol_info(symbol)

#         if symbol_info is None:
#             return 0.0

#         distance = self._get_sl_distance(symbol)

#         # Không đặt SL gần hơn mức tối thiểu broker cho phép
#         min_distance = symbol_info.trade_stops_level * symbol_info.point
#         if distance < min_distance:
#             pybot_logger.warning(
#                 f"{symbol}: SL {distance} < stops_level tối thiểu {min_distance} → nới SL"
#             )
#             distance = min_distance

#         if order_type == "BUY":
#             return round(price - distance, symbol_info.digits)

#         if order_type == "SELL":
#             return round(price + distance, symbol_info.digits)

#         return 0.0

#     # =========================
#     # TÍNH LOT THEO RISK
#     # =========================
#     def calculate_lot(self, symbol):
#         """Trả về 0.0 nếu không thể tính lot an toàn (→ bỏ qua lệnh)."""

#         account = mt5.account_info()
#         symbol_info = mt5.symbol_info(symbol)

#         if account is None or symbol_info is None:
#             error_logger.error(f"{symbol}: không lấy được account/symbol info để tính lot")
#             return 0.0

#         if USE_KELLY_SIZING:
#             risk_percent = kelly_position_sizing.get_risk_percent(symbol)
#         else:
#             risk_percent = RISK_PERCENT

#         risk_money = account.balance * (risk_percent / 100)

#         tick_value = symbol_info.trade_tick_value
#         tick_size = symbol_info.trade_tick_size

#         if tick_size <= 0 or tick_value <= 0:
#             error_logger.error(f"{symbol}: tick_size/tick_value không hợp lệ")
#             return 0.0

#         sl_distance = self._get_sl_distance(symbol)

#         # Số tiền mất cho 1 lot nếu chạm SL
#         loss_per_lot = (sl_distance / tick_size) * tick_value

#         if loss_per_lot <= 0:
#             error_logger.error(f"{symbol}: loss_per_lot không hợp lệ")
#             return 0.0

#         raw_lot = risk_money / loss_per_lot

#         step = symbol_info.volume_step

#         # Làm tròn XUỐNG theo step (epsilon tránh lỗi float: 0.29/0.01 = 28.999..)
#         lot = math.floor(raw_lot / step + 1e-9) * step

#         lot = min(lot, symbol_info.volume_max, MAX_LOT_SIZE)

#         # Lot tính ra nhỏ hơn lot tối thiểu → kiểm tra risk thật của lot min
#         if lot < symbol_info.volume_min:

#             min_lot_risk = symbol_info.volume_min * loss_per_lot

#             if min_lot_risk > risk_money * MAX_RISK_OVERSHOOT:
#                 pybot_logger.warning(
#                     f"{symbol}: lot tối thiểu {symbol_info.volume_min} sẽ rủi ro "
#                     f"${min_lot_risk:.2f} > mức cho phép ${risk_money * MAX_RISK_OVERSHOOT:.2f} "
#                     f"({risk_percent:.2f}% balance) → BỎ QUA lệnh"
#                 )
#                 return 0.0

#             lot = symbol_info.volume_min

#         decimals = max(0, int(round(-math.log10(step))))

#         return round(lot, decimals)

#     # =========================
#     # MỞ LỆNH (dùng chung BUY / SELL)
#     # =========================
#     def _open(self, symbol, direction):

#         if not self.check_autotrading():
#             return False

#         tick = mt5.symbol_info_tick(symbol)

#         if tick is None:
#             error_logger.error(f"Không lấy được tick của {symbol}")
#             return False

#         lot = self.calculate_lot(symbol)

#         if lot <= 0:
#             return False

#         if direction == "BUY":
#             order_type = mt5.ORDER_TYPE_BUY
#             price = tick.ask
#         else:
#             order_type = mt5.ORDER_TYPE_SELL
#             price = tick.bid

#         sl = self.calculate_sl(symbol, price, direction)

#         request = {
#             "action": mt5.TRADE_ACTION_DEAL,
#             "symbol": symbol,
#             "volume": lot,
#             "type": order_type,
#             "price": price,
#             "sl": sl,
#             "deviation": 20,
#             "magic": MAGIC_NUMBER,
#             "comment": f"EMA BOT {direction}",
#             "type_time": mt5.ORDER_TIME_GTC,
#             "type_filling": self.get_filling_mode(symbol)
#         }

#         result = self._send(request, f"{direction} {symbol}")

#         if result is None:
#             return False

#         fill_price = result.price if result.price else price

#         trade_logger.info(
#             f"{direction} {symbol} | Lot={lot} | Price={fill_price} | "
#             f"SL={sl} | Ticket={result.order}"
#         )

#         return True

#     def open_buy(self, symbol):
#         return self._open(symbol, "BUY")

#     def open_sell(self, symbol):
#         return self._open(symbol, "SELL")

#     # =========================
#     # GET POSITION
#     # =========================
#     def get_position(self, symbol):

#         positions = mt5.positions_get(symbol=symbol)

#         if not positions:
#             return None

#         for position in positions:

#             if position.magic != MAGIC_NUMBER:
#                 continue

#             if position.type == mt5.POSITION_TYPE_BUY:
#                 return "BUY"

#             if position.type == mt5.POSITION_TYPE_SELL:
#                 return "SELL"

#         return None

#     # =========================
#     # GHI LOG LỆNH ĐÃ ĐÓNG (report + Notion) — dùng chung
#     # =========================
#     def _record_closed_trade(self, symbol, direction, open_price, close_price,
#                              volume, profit, swap, net, ticket, open_time,
#                              reason="BOT"):

#         if ticket in self._logged_positions:
#             return

#         self._logged_positions.add(ticket)

#         result_str = "PROFIT" if net >= 0 else "LOSS"

#         report_logger.info(
#             f"[{result_str}] {symbol} {direction} | "
#             f"Ticket={ticket} | "
#             f"Open={open_price:.5f} Close={close_price:.5f} | "
#             f"Lot={volume} | "
#             f"Profit={profit:+.2f} Swap={swap:+.2f} Net={net:+.2f} USD | "
#             f"Reason={reason}"
#         )

#         log_trade_to_notion(
#             symbol=symbol,
#             direction=direction,
#             open_price=open_price,
#             close_price=close_price,
#             lot=volume,
#             profit=profit,
#             swap=swap,
#             net=net,
#             ticket=ticket,
#             open_time=open_time
#         )

#     # =========================
#     # LẤY DEAL ĐÓNG CỦA 1 POSITION
#     # =========================
#     def _get_close_deal(self, position_id, retries=3):
#         """Truy vấn theo position_id → không phụ thuộc múi giờ / cửa sổ thời gian.
#         Retry vì deal có thể chưa kịp xuất hiện trong lịch sử ngay sau khi đóng."""

#         for _ in range(retries):

#             deals = mt5.history_deals_get(position=position_id)

#             if deals:
#                 out_deals = [d for d in deals if d.entry == mt5.DEAL_ENTRY_OUT]
#                 if out_deals:
#                     return out_deals[-1], deals

#             time_module.sleep(1)

#         return None, None

#     # =========================
#     # CLOSE
#     # =========================
#     def close_positions(self, symbol):

#         positions = mt5.positions_get(symbol=symbol)

#         if not positions:
#             return True

#         all_closed = True

#         for position in positions:

#             if position.magic != MAGIC_NUMBER:
#                 continue

#             tick = mt5.symbol_info_tick(symbol)

#             if tick is None:
#                 error_logger.error(f"Không lấy được tick của {symbol}")
#                 all_closed = False
#                 continue

#             if position.type == mt5.POSITION_TYPE_BUY:
#                 order_type = mt5.ORDER_TYPE_SELL
#                 price = tick.bid
#                 direction = "BUY"
#             else:
#                 order_type = mt5.ORDER_TYPE_BUY
#                 price = tick.ask
#                 direction = "SELL"

#             request = {
#                 "action": mt5.TRADE_ACTION_DEAL,
#                 "symbol": symbol,
#                 "volume": position.volume,
#                 "type": order_type,
#                 "position": position.ticket,
#                 "price": price,
#                 "deviation": 20,
#                 "magic": MAGIC_NUMBER,
#                 "comment": "EMA BOT CLOSE",
#                 "type_filling": self.get_filling_mode(symbol)
#             }

#             result = self._send(
#                 request, f"Đóng lệnh {symbol} Ticket={position.ticket}"
#             )

#             if result is None:
#                 all_closed = False
#                 continue

#             trade_logger.info(f"CLOSE {symbol} | Ticket={position.ticket}")

#             close_deal, all_deals = self._get_close_deal(position.ticket)

#             if close_deal is None:
#                 error_logger.warning(
#                     f"Không tìm được deal đóng cho Ticket={position.ticket} sau 3 lần thử "
#                     f"→ KHÔNG ghi report (sẽ được sync_closed_trades ghi bù)"
#                 )
#                 continue

#             # Cộng toàn bộ deal của position (gồm commission lúc mở nếu có)
#             profit = sum(x.profit for x in all_deals)
#             swap = sum(x.swap for x in all_deals)
#             net = sum(x.profit + x.swap + x.commission for x in all_deals)

#             self._record_closed_trade(
#                 symbol=symbol,
#                 direction=direction,
#                 open_price=position.price_open,
#                 close_price=close_deal.price,
#                 volume=position.volume,
#                 profit=profit,
#                 swap=swap,
#                 net=net,
#                 ticket=position.ticket,
#                 open_time=_server_ts_to_dt(position.time),
#                 reason=DEAL_REASON_TEXT.get(close_deal.reason, "OTHER")
#             )

#         return all_closed

#     def close_all_symbols(self, symbols):
#         for symbol in symbols:
#             self.close_positions(symbol)

#     # =========================
#     # ĐỒNG BỘ LỆNH ĐÓNG BỞI BROKER (SL / TP / stop-out / tay)
#     # =========================
#     def _recent_out_deals(self, days=3):

#         deals = mt5.history_deals_get(
#             datetime.now() - timedelta(days=days),
#             datetime.now() + timedelta(days=1)
#         )

#         if not deals:
#             return []

#         return [
#             d for d in deals
#             if d.magic == MAGIC_NUMBER and d.entry == mt5.DEAL_ENTRY_OUT
#         ]

#     def init_logged_history(self):
#         """Gọi 1 lần sau khi kết nối MT5: đánh dấu các lệnh cũ là 'đã ghi'
#         để sync_closed_trades không ghi lại toàn bộ lịch sử khi bot khởi động."""

#         for d in self._recent_out_deals():
#             self._logged_positions.add(d.position_id)

#     def sync_closed_trades(self):
#         """Gọi mỗi vòng lặp: ghi report/Notion cho các lệnh đã đóng mà bot
#         KHÔNG tự đóng (điển hình là chạm SL)."""

#         for d in self._recent_out_deals():

#             if d.position_id in self._logged_positions:
#                 continue

#             all_deals = mt5.history_deals_get(position=d.position_id)

#             in_deal = None
#             if all_deals:
#                 for x in all_deals:
#                     if x.entry == mt5.DEAL_ENTRY_IN:
#                         in_deal = x
#                         break

#             if in_deal is None:
#                 # Chưa đủ dữ liệu → thử lại ở vòng sau
#                 continue

#             direction = "BUY" if in_deal.type == mt5.DEAL_TYPE_BUY else "SELL"

#             net = sum(x.profit + x.swap + x.commission for x in all_deals)
#             profit = sum(x.profit for x in all_deals)
#             swap = sum(x.swap for x in all_deals)

#             self._record_closed_trade(
#                 symbol=d.symbol,
#                 direction=direction,
#                 open_price=in_deal.price,
#                 close_price=d.price,
#                 volume=in_deal.volume,
#                 profit=profit,
#                 swap=swap,
#                 net=net,
#                 ticket=d.position_id,
#                 open_time=_server_ts_to_dt(in_deal.time),
#                 reason=DEAL_REASON_TEXT.get(d.reason, "OTHER")
#             )


# execution = Execution()


import math
import MetaTrader5 as mt5
import time as time_module
from datetime import datetime, timedelta, timezone

from config import (
    MAGIC_NUMBER,
    RISK_PERCENT,
    SL_DISTANCE,
    SL_DISTANCE_DEFAULT,
    MAX_LOT_SIZE,
    MAX_RISK_OVERSHOOT,
    USE_KELLY_SIZING
)

from logger import (
    trade_logger,
    error_logger,
    report_logger,
    pybot_logger
)

from notion_logger import log_trade_to_notion
from trade_history import server_now
from kelly_positon import kelly_position_sizing


RETCODE_MESSAGES = {
    10004: "Requote",
    10006: "Request bị từ chối",
    10007: "Request bị hủy bởi trader",
    10008: "Đã đặt lệnh",
    10009: "Request được xử lý",
    10010: "Chỉ thực hiện một phần",
    10011: "Lỗi xử lý request",
    10012: "Request hết hạn",
    10013: "Request không hợp lệ",
    10014: "Volume không hợp lệ",
    10015: "Giá không hợp lệ",
    10016: "Stop không hợp lệ",
    10017: "Trading bị tắt",
    10018: "Thị trường đóng cửa",
    10019: "Không đủ tiền",
    10020: "Giá đã thay đổi",
    10021: "Không có giá",
    10022: "Ngày hết hạn không hợp lệ",
    10023: "Trạng thái lệnh thay đổi",
    10024: "Quá nhiều request",
    10025: "Không có thay đổi nào",
    10026: "AutoTrading bị tắt bởi server",
    10027: "AutoTrading bị tắt trên MT5 — hãy bật nút 'Algo Trading' trên toolbar",
    10028: "Request bị khóa",
    10029: "Chỉ cho phép thay đổi dài hạn",
    10030: "Chế độ fill không được hỗ trợ",
}

DEAL_REASON_TEXT = {
    mt5.DEAL_REASON_SL: "SL",
    mt5.DEAL_REASON_TP: "TP",
    mt5.DEAL_REASON_SO: "STOP-OUT",
    mt5.DEAL_REASON_CLIENT: "MANUAL",
    mt5.DEAL_REASON_EXPERT: "BOT",
}


def _server_ts_to_dt(ts):
    """Timestamp của MT5 là 'giờ server' mã hoá như epoch.
    fromtimestamp() sẽ cộng thêm múi giờ máy local → lệch.
    Dùng UTC để lấy đúng đồng hồ của server (naive datetime)."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)


class Execution:

    def __init__(self):
        # Các position đã được ghi report/Notion — tránh ghi trùng
        self._logged_positions = set()

    # =========================
    # KIỂM TRA AUTOTRADING
    # =========================
    def check_autotrading(self):

        terminal = mt5.terminal_info()

        if terminal is None:
            error_logger.error("Không lấy được thông tin terminal MT5")
            return False

        if not terminal.trade_allowed:
            error_logger.error(
                "AutoTrading đang bị TẮT! "
                "Vào MT5 → bật nút 'Algo Trading' trên toolbar (phải có màu xanh)"
            )
            return False

        return True

    # =========================
    # TỰ ĐỘNG CHỌN FILLING MODE
    # =========================
    def get_filling_mode(self, symbol):

        symbol_info = mt5.symbol_info(symbol)

        if symbol_info is None:
            return mt5.ORDER_FILLING_IOC

        filling = symbol_info.filling_mode

        if filling & 1:  # FOK
            return mt5.ORDER_FILLING_FOK

        if filling & 2:  # IOC
            return mt5.ORDER_FILLING_IOC

        return mt5.ORDER_FILLING_RETURN

    # =========================
    # GỬI LỆNH AN TOÀN (xử lý result = None)
    # =========================
    def _send(self, request, label):

        result = mt5.order_send(request)

        if result is None:
            error_logger.error(
                f"{label} thất bại | order_send trả về None | {mt5.last_error()}"
            )
            return None

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            msg = RETCODE_MESSAGES.get(result.retcode, "Lỗi không xác định")
            error_logger.error(
                f"{label} thất bại | RetCode={result.retcode} | {msg}"
            )
            return None

        return result

    # =========================
    # STOP LOSS THEO KHOẢNG GIÁ (không dùng pip nữa)
    # =========================
    def _get_sl_distance(self, symbol):
        return SL_DISTANCE.get(symbol, SL_DISTANCE_DEFAULT)

    def calculate_sl(self, symbol, price, order_type):

        symbol_info = mt5.symbol_info(symbol)

        if symbol_info is None:
            return 0.0

        distance = self._get_sl_distance(symbol)

        # Không đặt SL gần hơn mức tối thiểu broker cho phép
        min_distance = symbol_info.trade_stops_level * symbol_info.point
        if distance < min_distance:
            pybot_logger.warning(
                f"{symbol}: SL {distance} < stops_level tối thiểu {min_distance} → nới SL"
            )
            distance = min_distance

        if order_type == "BUY":
            return round(price - distance, symbol_info.digits)

        if order_type == "SELL":
            return round(price + distance, symbol_info.digits)

        return 0.0

    # =========================
    # TÍNH LOT THEO RISK
    # =========================
    def calculate_lot(self, symbol):
        """Trả về 0.0 nếu không thể tính lot an toàn (→ bỏ qua lệnh)."""

        account = mt5.account_info()
        symbol_info = mt5.symbol_info(symbol)

        if account is None or symbol_info is None:
            error_logger.error(f"{symbol}: không lấy được account/symbol info để tính lot")
            return 0.0

        if USE_KELLY_SIZING:
            risk_percent = kelly_position_sizing.get_risk_percent(symbol)
        else:
            risk_percent = RISK_PERCENT

        risk_money = account.balance * (risk_percent / 100)

        tick_value = symbol_info.trade_tick_value
        tick_size = symbol_info.trade_tick_size

        if tick_size <= 0 or tick_value <= 0:
            error_logger.error(f"{symbol}: tick_size/tick_value không hợp lệ")
            return 0.0

        sl_distance = self._get_sl_distance(symbol)

        # Số tiền mất cho 1 lot nếu chạm SL
        loss_per_lot = (sl_distance / tick_size) * tick_value

        if loss_per_lot <= 0:
            error_logger.error(f"{symbol}: loss_per_lot không hợp lệ")
            return 0.0

        raw_lot = risk_money / loss_per_lot

        step = symbol_info.volume_step

        # Làm tròn XUỐNG theo step (epsilon tránh lỗi float: 0.29/0.01 = 28.999..)
        lot = math.floor(raw_lot / step + 1e-9) * step

        lot = min(lot, symbol_info.volume_max, MAX_LOT_SIZE)

        # Lot tính ra nhỏ hơn lot tối thiểu → kiểm tra risk thật của lot min
        if lot < symbol_info.volume_min:

            min_lot_risk = symbol_info.volume_min * loss_per_lot

            if min_lot_risk > risk_money * MAX_RISK_OVERSHOOT:
                pybot_logger.warning(
                    f"{symbol}: lot tối thiểu {symbol_info.volume_min} sẽ rủi ro "
                    f"${min_lot_risk:.2f} > mức cho phép ${risk_money * MAX_RISK_OVERSHOOT:.2f} "
                    f"({risk_percent:.2f}% balance) → BỎ QUA lệnh"
                )
                return 0.0

            lot = symbol_info.volume_min

        decimals = max(0, int(round(-math.log10(step))))

        return round(lot, decimals)

    # =========================
    # MỞ LỆNH (dùng chung BUY / SELL)
    # =========================
    def _open(self, symbol, direction):

        if not self.check_autotrading():
            return False

        tick = mt5.symbol_info_tick(symbol)

        if tick is None:
            error_logger.error(f"Không lấy được tick của {symbol}")
            return False

        lot = self.calculate_lot(symbol)

        if lot <= 0:
            return False

        if direction == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        else:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid

        sl = self.calculate_sl(symbol, price, direction)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "sl": sl,
            "deviation": 20,
            "magic": MAGIC_NUMBER,
            "comment": f"EMA BOT {direction}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self.get_filling_mode(symbol)
        }

        result = self._send(request, f"{direction} {symbol}")

        if result is None:
            return False

        fill_price = result.price if result.price else price

        trade_logger.info(
            f"{direction} {symbol} | Lot={lot} | Price={fill_price} | "
            f"SL={sl} | Ticket={result.order}"
        )

        return True

    def open_buy(self, symbol):
        return self._open(symbol, "BUY")

    def open_sell(self, symbol):
        return self._open(symbol, "SELL")

    # =========================
    # GET POSITION
    # =========================
    def get_position(self, symbol):

        positions = mt5.positions_get(symbol=symbol)

        if not positions:
            return None

        for position in positions:

            if position.magic != MAGIC_NUMBER:
                continue

            if position.type == mt5.POSITION_TYPE_BUY:
                return "BUY"

            if position.type == mt5.POSITION_TYPE_SELL:
                return "SELL"

        return None

    # =========================
    # GHI LOG LỆNH ĐÃ ĐÓNG (report + Notion) — dùng chung
    # =========================
    def _record_closed_trade(self, symbol, direction, open_price, close_price,
                             volume, profit, swap, net, ticket, open_time,
                             reason="BOT"):

        if ticket in self._logged_positions:
            return

        self._logged_positions.add(ticket)

        result_str = "PROFIT" if net >= 0 else "LOSS"

        report_logger.info(
            f"[{result_str}] {symbol} {direction} | "
            f"Ticket={ticket} | "
            f"Open={open_price:.5f} Close={close_price:.5f} | "
            f"Lot={volume} | "
            f"Profit={profit:+.2f} Swap={swap:+.2f} Net={net:+.2f} USD | "
            f"Reason={reason}"
        )

        log_trade_to_notion(
            symbol=symbol,
            direction=direction,
            open_price=open_price,
            close_price=close_price,
            lot=volume,
            profit=profit,
            swap=swap,
            net=net,
            ticket=ticket,
            open_time=open_time
        )

    # =========================
    # LẤY DEAL ĐÓNG CỦA 1 POSITION
    # =========================
    def _get_close_deal(self, position_id, retries=3):
        """Truy vấn theo position_id → không phụ thuộc múi giờ / cửa sổ thời gian.
        Retry vì deal có thể chưa kịp xuất hiện trong lịch sử ngay sau khi đóng."""

        for _ in range(retries):

            deals = mt5.history_deals_get(position=position_id)

            if deals:
                out_deals = [d for d in deals if d.entry == mt5.DEAL_ENTRY_OUT]
                if out_deals:
                    return out_deals[-1], deals

            time_module.sleep(1)

        return None, None

    # =========================
    # CLOSE
    # =========================
    def close_positions(self, symbol):

        positions = mt5.positions_get(symbol=symbol)

        if not positions:
            return True

        all_closed = True

        for position in positions:

            if position.magic != MAGIC_NUMBER:
                continue

            tick = mt5.symbol_info_tick(symbol)

            if tick is None:
                error_logger.error(f"Không lấy được tick của {symbol}")
                all_closed = False
                continue

            if position.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
                direction = "BUY"
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
                direction = "SELL"

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": position.volume,
                "type": order_type,
                "position": position.ticket,
                "price": price,
                "deviation": 20,
                "magic": MAGIC_NUMBER,
                "comment": "EMA BOT CLOSE",
                "type_filling": self.get_filling_mode(symbol)
            }

            result = self._send(
                request, f"Đóng lệnh {symbol} Ticket={position.ticket}"
            )

            if result is None:
                all_closed = False
                continue

            trade_logger.info(f"CLOSE {symbol} | Ticket={position.ticket}")

            close_deal, all_deals = self._get_close_deal(position.ticket)

            if close_deal is None:
                error_logger.warning(
                    f"Không tìm được deal đóng cho Ticket={position.ticket} sau 3 lần thử "
                    f"→ KHÔNG ghi report (sẽ được sync_closed_trades ghi bù)"
                )
                continue

            # Cộng toàn bộ deal của position (gồm commission lúc mở nếu có)
            profit = sum(x.profit for x in all_deals)
            swap = sum(x.swap for x in all_deals)
            net = sum(x.profit + x.swap + x.commission for x in all_deals)

            self._record_closed_trade(
                symbol=symbol,
                direction=direction,
                open_price=position.price_open,
                close_price=close_deal.price,
                volume=position.volume,
                profit=profit,
                swap=swap,
                net=net,
                ticket=position.ticket,
                open_time=_server_ts_to_dt(position.time),
                reason=DEAL_REASON_TEXT.get(close_deal.reason, "OTHER")
            )

        return all_closed

    def close_all_symbols(self, symbols):
        for symbol in symbols:
            self.close_positions(symbol)

    # =========================
    # ĐỒNG BỘ LỆNH ĐÓNG BỞI BROKER (SL / TP / stop-out / tay)
    # =========================
    def _recent_out_deals(self, days=3):

        deals = mt5.history_deals_get(
            server_now() - timedelta(days=days),
            server_now() + timedelta(days=1)
        )

        if not deals:
            return []

        return [
            d for d in deals
            if d.magic == MAGIC_NUMBER and d.entry == mt5.DEAL_ENTRY_OUT
        ]

    def init_logged_history(self):
        """Gọi 1 lần sau khi kết nối MT5: đánh dấu các lệnh cũ là 'đã ghi'
        để sync_closed_trades không ghi lại toàn bộ lịch sử khi bot khởi động."""

        for d in self._recent_out_deals():
            self._logged_positions.add(d.position_id)

    def sync_closed_trades(self):
        """Gọi mỗi vòng lặp: ghi report/Notion cho các lệnh đã đóng mà bot
        KHÔNG tự đóng (điển hình là chạm SL)."""

        for d in self._recent_out_deals():

            if d.position_id in self._logged_positions:
                continue

            all_deals = mt5.history_deals_get(position=d.position_id)

            in_deal = None
            if all_deals:
                for x in all_deals:
                    if x.entry == mt5.DEAL_ENTRY_IN:
                        in_deal = x
                        break

            if in_deal is None:
                # Chưa đủ dữ liệu → thử lại ở vòng sau
                continue

            direction = "BUY" if in_deal.type == mt5.DEAL_TYPE_BUY else "SELL"

            net = sum(x.profit + x.swap + x.commission for x in all_deals)
            profit = sum(x.profit for x in all_deals)
            swap = sum(x.swap for x in all_deals)

            self._record_closed_trade(
                symbol=d.symbol,
                direction=direction,
                open_price=in_deal.price,
                close_price=d.price,
                volume=in_deal.volume,
                profit=profit,
                swap=swap,
                net=net,
                ticket=d.position_id,
                open_time=_server_ts_to_dt(in_deal.time),
                reason=DEAL_REASON_TEXT.get(d.reason, "OTHER")
            )


execution = Execution()