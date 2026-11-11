# import MetaTrader5 as mt5
# import pandas as pd
 
# from config import TIMEFRAME, HISTORY_BARS
# from logger import pybot_logger, error_logger
 
 
# class DataLoader:
 
#     def get_timeframe(self):
 
#         timeframe_map = {
#             "M1":  mt5.TIMEFRAME_M1,
#             "M5":  mt5.TIMEFRAME_M5,
#             "M15": mt5.TIMEFRAME_M15,
#             "M30": mt5.TIMEFRAME_M30,
#             "H1":  mt5.TIMEFRAME_H1,
#             "H4":  mt5.TIMEFRAME_H4,
#             "D1":  mt5.TIMEFRAME_D1
#         }
 
#         return timeframe_map[TIMEFRAME]
 
#     def get_data(self, symbol):
 
#         pybot_logger.debug(
#             f"Đang tải {HISTORY_BARS} nến {symbol} {TIMEFRAME}"
#         )
 
#         rates = mt5.copy_rates_from_pos(
#             symbol,
#             self.get_timeframe(),
#             0,
#             HISTORY_BARS
#         )
 
#         if rates is None:
#             error_logger.error(
#                 f"Không lấy được dữ liệu nến {symbol}"
#             )
#             return None
 
#         df = pd.DataFrame(rates)
 
#         df["time"] = pd.to_datetime(df["time"], unit="s")
 
#         pybot_logger.info(
#             f"Tải thành công {len(df)} nến {symbol}"
#         )
 
#         return df
 
 
# data_loader = DataLoader()

import MetaTrader5 as mt5
import pandas as pd
 
from config import TIMEFRAME, HISTORY_BARS
from logger import pybot_logger, error_logger
 
 
class DataLoader:
 
    def get_timeframe(self):
 
        timeframe_map = {
            "M1":  mt5.TIMEFRAME_M1,
            "M5":  mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1":  mt5.TIMEFRAME_H1,
            "H4":  mt5.TIMEFRAME_H4,
            "D1":  mt5.TIMEFRAME_D1
        }
 
        return timeframe_map[TIMEFRAME]
 
    def get_data(self, symbol):
 
        pybot_logger.debug(
            f"Đang tải {HISTORY_BARS} nến {symbol} {TIMEFRAME}"
        )
 
        rates = mt5.copy_rates_from_pos(
            symbol,
            self.get_timeframe(),
            0,
            HISTORY_BARS
        )
 
        if rates is None:
            error_logger.error(
                f"Không lấy được dữ liệu nến {symbol}"
            )
            return None
 
        df = pd.DataFrame(rates)

        # Bỏ nến cuối = nến ĐANG CHẠY (chưa đóng). Từ đây df.iloc[-1] luôn là
        # nến ĐÃ ĐÓNG -> EMA/tín hiệu/S&R không còn nhấp nháy trong cùng một nến.
        df = df.iloc[:-1].reset_index(drop=True)
 
        df["time"] = pd.to_datetime(df["time"], unit="s")
 
        pybot_logger.info(
            f"Tải thành công {len(df)} nến {symbol}"
        )
 
        return df
 
 
data_loader = DataLoader()