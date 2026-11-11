"""Tiện ích dùng chung: giờ server broker và lịch sử lệnh đã đóng của bot."""

from datetime import datetime, timedelta, timezone

import MetaTrader5 as mt5

from config import MAGIC_NUMBER, SYMBOLS, SERVER_UTC_OFFSET_HOURS

_cached_offset = None


def server_now():
    """Đồng hồ server broker (aware datetime, mã hoá như epoch UTC).
    Lấy từ tick mới nhất; fallback về giờ UTC máy nếu chưa có tick."""

    for symbol in SYMBOLS:
        tick = mt5.symbol_info_tick(symbol)
        if tick is not None and tick.time > 0:
            return datetime.fromtimestamp(tick.time, tz=timezone.utc)

    return datetime.now(timezone.utc)


def server_utc_offset_hours():
    """Chênh lệch giờ server so với UTC. Tự suy ra từ tick; nếu tick cũ
    (cuối tuần) thì dùng giá trị cấu hình."""

    global _cached_offset

    if _cached_offset is not None:
        return _cached_offset

    diff_hours = (server_now() - datetime.now(timezone.utc)).total_seconds() / 3600
    offset = round(diff_hours)

    if abs(diff_hours - offset) < 0.1 and -12 <= offset <= 14:
        _cached_offset = offset
        return offset

    return SERVER_UTC_OFFSET_HOURS


def get_closed_trades(symbol=None, days=7, closed_after=None):
    """Trả về list lệnh ĐÃ ĐÓNG của bot, sắp xếp theo THỜI GIAN ĐÓNG (cũ -> mới).

    Mỗi phần tử: {position_id, symbol, net, volume, close_time}
    net = profit + commission + swap của toàn bộ deal thuộc position.
    closed_after: epoch (giây) - chỉ lấy lệnh đóng sau mốc này."""

    now = server_now()
    deals = mt5.history_deals_get(now - timedelta(days=days), now + timedelta(days=1))

    if not deals:
        return []

    # Xác định position của bot qua deal MỞ (deal SL/TP của broker có thể không mang magic)
    bot_positions = {
        d.position_id for d in deals
        if d.magic == MAGIC_NUMBER and d.entry == mt5.DEAL_ENTRY_IN
    }

    grouped = {}
    for d in deals:
        if d.position_id in bot_positions:
            grouped.setdefault(d.position_id, []).append(d)

    trades = []
    for position_id, ds in grouped.items():

        outs = [d for d in ds if d.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_OUT_BY)]
        if not outs:
            continue  # chưa đóng

        sym = ds[0].symbol
        if symbol is not None and sym != symbol:
            continue

        close_time = max(d.time for d in outs)
        if closed_after is not None and close_time <= closed_after:
            continue

        trades.append({
            "position_id": position_id,
            "symbol": sym,
            "net": sum(d.profit + d.commission + d.swap for d in ds),
            "volume": sum(d.volume for d in outs),
            "close_time": close_time,
        })

    trades.sort(key=lambda t: t["close_time"])
    return trades