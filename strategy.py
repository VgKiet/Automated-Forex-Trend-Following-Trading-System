from config import (
    EMA_FAST,
    EMA_MEDIUM_1,
    EMA_MEDIUM_2,
    EMA_SLOW
)

from support_resistance import support_resistance
from logger import pybot_logger

# Khoảng cách tối đa giữa giá ĐÓNG CỬA và EMA5
# để được phép mở lệnh MỚI
MAX_PRICE_EMA5_DISTANCE = {
    "XAUUSD": 2.0,    # Vàng: 2 USD
    "GBPUSD": 0.0015, # 15 pip
    "EURUSD": 0.0015, # 15 pip
    "USDJPY": 0.15,   # 15 pip quy đổi JPY
}

DEFAULT_DISTANCE = 0.0015


class Strategy:

    def is_close_near_ema5(self, df, symbol):
        """
        Kiểm tra giá đóng cửa nến hiện tại có gần EMA5 không.
        Râu nến không tính — chỉ close mới đại diện xu hướng thực.
        """

        last  = df.iloc[-1]
        ema5  = last[f"EMA{EMA_FAST}"]
        close = last["close"]

        distance = abs(close - ema5)

        max_distance = MAX_PRICE_EMA5_DISTANCE.get(
            symbol,
            DEFAULT_DISTANCE
        )

        return distance <= max_distance

    def last_direction(self, df):
        """Trả về hướng EMA hiện tại bất kể nến xa hay gần"""

        last  = df.iloc[-1]
        ema5  = last[f"EMA{EMA_FAST}"]
        ema9  = last[f"EMA{EMA_MEDIUM_1}"]
        ema13 = last[f"EMA{EMA_MEDIUM_2}"]
        ema21 = last[f"EMA{EMA_SLOW}"]

        if ema5 > ema9 > ema13 > ema21:
            return "BUY"

        if ema5 < ema9 < ema13 < ema21:
            return "SELL"

        return "NONE"

    def get_signal(self, df, symbol):

        last  = df.iloc[-1]
        ema5  = last[f"EMA{EMA_FAST}"]
        ema9  = last[f"EMA{EMA_MEDIUM_1}"]
        ema13 = last[f"EMA{EMA_MEDIUM_2}"]
        ema21 = last[f"EMA{EMA_SLOW}"]

        bullish = ema5 > ema9 > ema13 > ema21
        bearish = ema5 < ema9 < ema13 < ema21

        # Điều kiện 1: EMA phải đúng thứ tự
        if not bullish and not bearish:
            return "CLOSE"

        # Điều kiện 2: giá đóng cửa phải gần EMA5
        if not self.is_close_near_ema5(df, symbol):
            return "SKIP"

        close = last["close"]

        if bullish:

            near_res, zone = support_resistance.is_near_resistance(
                close, df, symbol
            )

            if near_res:
                pybot_logger.info(
                    f"{symbol}: EMA cho tín hiệu BUY nhưng giá đang áp sát "
                    f"vùng kháng cự {zone['level']:.5f} "
                    f"({zone['touches']} lần chạm) → chặn lệnh"
                )
                return "SKIP"

            return "BUY"

        # bearish
        near_sup, zone = support_resistance.is_near_support(
            close, df, symbol
        )

        if near_sup:
            pybot_logger.info(
                f"{symbol}: EMA cho tín hiệu SELL nhưng giá đang áp sát "
                f"vùng hỗ trợ {zone['level']:.5f} "
                f"({zone['touches']} lần chạm) → chặn lệnh"
            )
            return "SKIP"

        return "SELL"


strategy = Strategy()