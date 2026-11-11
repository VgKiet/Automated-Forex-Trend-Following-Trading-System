# import os
# import subprocess
# import json
# from datetime import datetime

# from logger import error_logger

# NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# PAIRS_MAP = {
#     "XAUUSD": "XAUUSD",
#     "EURUSD": "EURUSD",
#     "USDJPY": "USDJPY",
#     "GBPUSD": "GBPUSD",
# }


# def get_session(dt: datetime) -> str:
#     hour = dt.hour
#     if 0 <= hour < 8:
#         return "Asian"
#     elif 8 <= hour < 13:
#         return "London"
#     else:
#         return "New York"


# def log_trade_to_notion(
#     symbol: str,
#     direction: str,
#     open_price: float,
#     close_price: float,
#     lot: float,
#     profit: float,
#     swap: float,
#     net: float,
#     ticket: int,
#     open_time: datetime = None,
# ):
#     """Ghi lệnh đã đóng vào Notion TRADES DB qua HTTP API"""

#     notion_token = os.getenv("NOTION_TOKEN")

#     if not notion_token or not NOTION_DATABASE_ID:
#         error_logger.warning("Thiếu NOTION_TOKEN hoặc NOTION_DATABASE_ID trong .env")
#         return

#     if open_time is None:
#         open_time = datetime.now()

#     notion_direction = "LONG" if direction == "BUY" else "SHORT"
#     session          = get_session(open_time)
#     pair             = PAIRS_MAP.get(symbol)
#     name             = f"{symbol} {notion_direction} #{ticket}"
#     result_tag       = "well-managed"  # bot luôn follow rules

#     properties = {
#         "Name": {
#             "title": [{"text": {"content": name}}]
#         },
#         "Date": {
#             "date": {"start": open_time.strftime("%Y-%m-%d")}
#         },
#         "Direction": {
#             "select": {"name": notion_direction}
#         },
#         "Profit/Loss": {
#             "number": round(net, 2)
#         },
#         "Session": {
#             "select": {"name": session}
#         },
#         "Followed rules": {
#             "checkbox": True
#         },
#     }

#     if pair:
#         properties["Pairs"] = {"select": {"name": pair}}

#     payload = json.dumps({
#         "parent": {"database_id": NOTION_DATABASE_ID},
#         "properties": properties
#     })

#     # Gọi curl thay vì requests để tránh cần cài thêm thư viện
#     cmd = [
#         "curl", "-s", "-X", "POST",
#         "https://api.notion.com/v1/pages",
#         "-H", f"Authorization: Bearer {notion_token}",
#         "-H", "Content-Type: application/json",
#         "-H", "Notion-Version: 2022-06-28",
#         "-d", payload
#     ]

#     try:
#         result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
#         response = json.loads(result.stdout)

#         if response.get("object") == "error":
#             error_logger.error(
#                 f"Notion ghi thất bại | {symbol} #{ticket} | "
#                 f"{response.get('code')}: {response.get('message')}"
#             )
#         else:
#             pass  # ghi thành công

#     except Exception as e:
#         error_logger.error(f"Notion lỗi kết nối | {symbol} #{ticket} | {e}")


import os
import subprocess
import json
from datetime import datetime, timedelta

from dotenv import load_dotenv

from logger import error_logger
from trade_history import server_utc_offset_hours

load_dotenv()  # tự nạp .env, không phụ thuộc thứ tự import

NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

PAIRS_MAP = {
    "XAUUSD": "XAUUSD",
    "EURUSD": "EURUSD",
    "USDJPY": "USDJPY",
    "GBPUSD": "GBPUSD",
}


def get_session(dt: datetime) -> str:
    hour = dt.hour
    if 0 <= hour < 8:
        return "Asian"
    elif 8 <= hour < 13:
        return "London"
    else:
        return "New York"


def log_trade_to_notion(
    symbol: str,
    direction: str,
    open_price: float,
    close_price: float,
    lot: float,
    profit: float,
    swap: float,
    net: float,
    ticket: int,
    open_time: datetime = None,
):
    """Ghi lệnh đã đóng vào Notion TRADES DB qua HTTP API"""

    notion_token = os.getenv("NOTION_TOKEN")

    if not notion_token or not NOTION_DATABASE_ID:
        error_logger.warning("Thiếu NOTION_TOKEN hoặc NOTION_DATABASE_ID trong .env")
        return

    # open_time là giờ SERVER broker → đổi sang UTC để gán phiên cho đúng
    if open_time is None:
        utc_time = datetime.utcnow()
    else:
        utc_time = open_time - timedelta(hours=server_utc_offset_hours())
    open_time = utc_time

    notion_direction = "LONG" if direction == "BUY" else "SHORT"
    session          = get_session(open_time)
    pair             = PAIRS_MAP.get(symbol)
    name             = f"{symbol} {notion_direction} #{ticket}"
    result_tag       = "well-managed"  # bot luôn follow rules

    properties = {
        "Name": {
            "title": [{"text": {"content": name}}]
        },
        "Date": {
            "date": {"start": open_time.strftime("%Y-%m-%d")}
        },
        "Direction": {
            "select": {"name": notion_direction}
        },
        "Profit/Loss": {
            "number": round(net, 2)
        },
        "Session": {
            "select": {"name": session}
        },
        "Followed rules": {
            "checkbox": True
        },
    }

    if pair:
        properties["Pairs"] = {"select": {"name": pair}}

    payload = json.dumps({
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties
    })

    # Gọi curl thay vì requests để tránh cần cài thêm thư viện
    cmd = [
        "curl", "-s", "-X", "POST",
        "https://api.notion.com/v1/pages",
        "-H", f"Authorization: Bearer {notion_token}",
        "-H", "Content-Type: application/json",
        "-H", "Notion-Version: 2022-06-28",
        "-d", payload
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        response = json.loads(result.stdout)

        if response.get("object") == "error":
            error_logger.error(
                f"Notion ghi thất bại | {symbol} #{ticket} | "
                f"{response.get('code')}: {response.get('message')}"
            )
        else:
            pass  # ghi thành công

    except Exception as e:
        error_logger.error(f"Notion lỗi kết nối | {symbol} #{ticket} | {e}")