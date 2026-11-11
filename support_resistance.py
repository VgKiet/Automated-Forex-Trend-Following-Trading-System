from config import (
    SR_SWING_STRENGTH,
    SR_LOOKBACK,
    SR_ZONE_MERGE_DISTANCE,
    SR_BLOCK_DISTANCE,
    SR_MIN_TOUCHES,
    SR_DEFAULT_MERGE_DISTANCE,
    SR_DEFAULT_BLOCK_DISTANCE,
    SR_BREAKOUT_BUFFER,
    SR_DEFAULT_BREAKOUT_BUFFER,
    SR_RETEST_MAX_BARS,
)


class SupportResistance:

    # =========================
    # TÌM ĐỈNH / ĐÁY (SWING POINTS)
    # =========================

    def find_swing_highs(self, df):
        """Tìm các nến có high cao hơn N nến bên trái và N nến bên phải."""

        strength = SR_SWING_STRENGTH
        highs = df["high"].values
        n = len(highs)

        start = max(strength, n - SR_LOOKBACK)
        swing_highs = []

        for i in range(start, n - strength):

            left = highs[i - strength:i]
            right = highs[i + 1:i + 1 + strength]

            if highs[i] > left.max() and highs[i] > right.max():
                swing_highs.append(highs[i])

        return swing_highs

    def find_swing_lows(self, df):
        """Tìm các nến có low thấp hơn N nến bên trái và N nến bên phải."""

        strength = SR_SWING_STRENGTH
        lows = df["low"].values
        n = len(lows)

        start = max(strength, n - SR_LOOKBACK)
        swing_lows = []

        for i in range(start, n - strength):

            left = lows[i - strength:i]
            right = lows[i + 1:i + 1 + strength]

            if lows[i] < left.min() and lows[i] < right.min():
                swing_lows.append(lows[i])

        return swing_lows

    # =========================
    # GỘP THÀNH VÙNG (ZONE)
    # =========================

    def cluster_zones(self, points, symbol):
        """Gộp các đỉnh/đáy nằm gần nhau thành 1 vùng.
        Vùng có càng nhiều lần chạm (touches) thì càng đáng tin."""

        if not points:
            return []

        merge_distance = SR_ZONE_MERGE_DISTANCE.get(
            symbol, SR_DEFAULT_MERGE_DISTANCE
        )

        points = sorted(points)
        clusters = []
        current = [points[0]]

        for p in points[1:]:
            # So với current[0] (điểm gốc/nhỏ nhất của cụm) chứ KHÔNG phải
            # current[-1] (điểm vừa thêm) — tránh hiệu ứng "chuỗi domino"
            # khiến 1 vùng bị kéo dài vô hạn qua hàng loạt điểm liền kề.
            # Nhờ vậy chiều rộng tối đa của 1 vùng luôn <= merge_distance.
            if p - current[0] <= merge_distance:
                current.append(p)
            else:
                clusters.append(current)
                current = [p]

        clusters.append(current)

        zones = []
        for cluster in clusters:
            zones.append({
                "level": sum(cluster) / len(cluster),
                "touches": len(cluster),
            })

        return zones

    def get_resistance_zones(self, df, symbol):
        highs = self.find_swing_highs(df)
        zones = self.cluster_zones(highs, symbol)
        return [z for z in zones if z["touches"] >= SR_MIN_TOUCHES]

    def get_support_zones(self, df, symbol):
        lows = self.find_swing_lows(df)
        zones = self.cluster_zones(lows, symbol)
        return [z for z in zones if z["touches"] >= SR_MIN_TOUCHES]

    # =========================
    # PHÁ VÙNG (BREAKOUT) & RETEST
    # =========================

    def get_zone_status(self, df, zone, symbol, direction):
        """Xác định trạng thái của 1 vùng so với lịch sử giá gần đây.

        direction:
            "up"   → vùng kháng cự, phá lên trên
            "down" → vùng hỗ trợ, phá xuống dưới

        Trả về:
            "NONE"      → vùng chưa từng bị phá gần đây → chặn bình thường
            "CONFIRMED" → đã phá + hiện đang giữ được phía đã phá (kể cả đang
                           retest sát vùng) → KHÔNG chặn, cho vào lệnh
            "FAILED"    → đã phá nhưng giá đóng cửa quay ngược lại quá xa
                           (phá giả) → chặn lại như bình thường
        """

        level = zone["level"]
        buffer = SR_BREAKOUT_BUFFER.get(symbol, SR_DEFAULT_BREAKOUT_BUFFER)

        closes = df["close"].values
        n = len(closes)

        lookback = min(SR_RETEST_MAX_BARS, n - 1)
        start = n - 1 - lookback

        breakout_index = None

        for i in range(start, n):
            if direction == "up" and closes[i] > level + buffer:
                breakout_index = i
            elif direction == "down" and closes[i] < level - buffer:
                breakout_index = i

        if breakout_index is None:
            return "NONE"

        current_close = closes[-1]

        if direction == "up" and current_close < level - buffer:
            return "FAILED"

        if direction == "down" and current_close > level + buffer:
            return "FAILED"

        return "CONFIRMED"

    # =========================
    # KIỂM TRA GIÁ CÓ ÁP SÁT VÙNG KHÔNG
    # =========================

    def is_near_resistance(self, price, df, symbol):
        """True nếu giá đang áp sát 1 vùng kháng cự PHÍA TRÊN
        và vùng đó CHƯA được xác nhận phá (breakout) → không nên mở BUY."""

        block_distance = SR_BLOCK_DISTANCE.get(symbol, SR_DEFAULT_BLOCK_DISTANCE)
        zones = self.get_resistance_zones(df, symbol)

        for zone in zones:

            status = self.get_zone_status(df, zone, symbol, direction="up")

            # Đã phá vùng + đang giữ được (kể cả đang retest sát vùng) → bỏ qua, không chặn
            if status == "CONFIRMED":
                continue

            if zone["level"] >= price and (zone["level"] - price) <= block_distance:
                return True, zone

        return False, None

    def is_near_support(self, price, df, symbol):
        """True nếu giá đang áp sát 1 vùng hỗ trợ PHÍA DƯỚI
        và vùng đó CHƯA được xác nhận phá (breakout) → không nên mở SELL."""

        block_distance = SR_BLOCK_DISTANCE.get(symbol, SR_DEFAULT_BLOCK_DISTANCE)
        zones = self.get_support_zones(df, symbol)

        for zone in zones:

            status = self.get_zone_status(df, zone, symbol, direction="down")

            if status == "CONFIRMED":
                continue

            if zone["level"] <= price and (price - zone["level"]) <= block_distance:
                return True, zone

        return False, None


support_resistance = SupportResistance()