# EMA Trading Bot cho MetaTrader 5

Bot giao dịch Forex/Vàng tự động trên MetaTrader 5 (MT5), viết bằng Python. Bot vào lệnh theo **xu hướng 4 đường EMA**, lọc tín hiệu bằng **vùng Hỗ trợ / Kháng cự (S&R)**, quản lý vốn theo **% risk** (tuỳ chọn **Quarter Kelly**) và có nhiều lớp bảo vệ tài khoản.

> ⚠️ **Cảnh báo rủi ro:** Giao dịch có đòn bẩy có thể mất toàn bộ vốn. Hãy chạy trên **tài khoản demo** trước khi dùng tiền thật. Dự án này không phải lời khuyên đầu tư.

---

## 1. Tính năng chính

- Giao dịch 4 mã: `XAUUSD`, `GBPUSD`, `EURUSD`, `USDJPY` (khung `M15`, chỉnh trong `config.py`).
- Chỉ xử lý khi **nến mới đóng** (bỏ nến đang chạy) → tín hiệu không bị nhấp nháy.
- Lọc tín hiệu bằng S&R, có nhận diện **breakout + retest**.
- Tính lot theo % rủi ro dựa trên khoảng SL (không phụ thuộc pip/số chữ số của broker).
- Tuỳ chọn **Quarter Kelly** sizing dựa trên lịch sử lệnh đã đóng.
- Giới hạn lỗ **ngày / tuần**, **thua liên tiếp**, **cooldown** sau khi đóng lệnh, **lọc spread**.
- Ghi log nhiều file và (tuỳ chọn) đẩy từng lệnh đã đóng lên **Notion**.
- Mỗi symbol xử lý độc lập: 1 symbol lỗi không làm sập cả bot.

---

## 2. Logic chiến lược

### 2.1 Điều kiện EMA

Dùng 4 EMA: `5 / 9 / 13 / 21` (đổi trong `config.py`).

| Trạng thái | Điều kiện | Hành động |
|---|---|---|
| Xu hướng tăng | `EMA5 > EMA9 > EMA13 > EMA21` | Cho phép **BUY** |
| Xu hướng giảm | `EMA5 < EMA9 < EMA13 < EMA21` | Cho phép **SELL** |
| EMA rối | Không đúng thứ tự | Tín hiệu `CLOSE` → đóng lệnh đang giữ |

### 2.2 Các bộ lọc trước khi vào lệnh

1. **Giá gần EMA5:** khoảng cách `|close − EMA5|` phải nhỏ hơn ngưỡng (vd. vàng ≤ 2 USD, EURUSD ≤ 15 pip). Nếu xa → `SKIP` (chờ pullback).
2. **Vùng S&R:**
   - BUY bị chặn nếu giá áp sát **kháng cự** phía trên (chưa được xác nhận phá).
   - SELL bị chặn nếu giá áp sát **hỗ trợ** phía dưới (chưa được xác nhận phá).
3. **Spread:** spread hiện tại phải ≤ `MAX_SPREAD` của symbol.
4. **Risk manager:** chưa vượt giới hạn lỗ, chưa thua liên tiếp quá mức, chưa có lệnh mở cho symbol.
5. **Cooldown:** sau khi lệnh đóng, chờ `COOLDOWN_BARS` nến mới được vào lại.

### 2.3 Tín hiệu `SKIP` khi đang giữ lệnh

Nếu đang giữ lệnh **ngược** với hướng EMA hiện tại (vd. đang SELL nhưng EMA đã chuyển sang xu hướng tăng) → bot đóng lệnh dù chưa có tín hiệu vào mới.

### 2.4 Đảo chiều

Khi có tín hiệu ngược với lệnh đang giữ: đóng lệnh cũ → chờ 2 giây → mở lệnh mới (nếu qua hết bộ lọc).

### 2.5 Vùng Hỗ trợ / Kháng cự (`support_resistance.py`)

1. Tìm **swing high / swing low** (đỉnh/đáy được xác nhận bởi `SR_SWING_STRENGTH` nến mỗi bên) trong `SR_LOOKBACK` nến gần nhất.
2. **Gộp** các điểm gần nhau thành vùng (`SR_ZONE_MERGE_DISTANCE`), vùng rộng tối đa bằng khoảng gộp.
3. Chỉ giữ vùng có ≥ `SR_MIN_TOUCHES` lần chạm.
4. Trạng thái vùng so với giá gần đây:
   - `NONE`: chưa bị phá → chặn lệnh bình thường nếu giá áp sát.
   - `CONFIRMED`: đã đóng cửa vượt vùng + `SR_BREAKOUT_BUFFER` và đang giữ được → **không chặn** (cho phép vào lệnh, kể cả khi retest).
   - `FAILED`: đã phá nhưng giá đóng cửa quay ngược lại → coi là phá giả, chặn như bình thường.
   - Chỉ xét breakout trong `SR_RETEST_MAX_BARS` nến gần nhất.

---

## 3. Quản lý vốn & rủi ro

### 3.1 Stop Loss

SL đặt theo **khoảng giá** (`SL_DISTANCE`), không dùng pip để tránh lệch theo broker:

| Symbol | SL |
|---|---|
| XAUUSD | 15.0 USD |
| GBPUSD | 0.0030 |
| EURUSD | 0.0025 |
| USDJPY | 0.35 |

### 3.2 Tính lot

```
risk_money = balance × risk% / 100
lot        = risk_money / (SL_distance × giá trị mỗi đơn vị giá của 1 lot)
```

- Lot bị chặn bởi `volume_min`, `volume_max` của broker và `MAX_LOT_SIZE` (mặc định 0.05).
- Nếu lot tối thiểu khiến rủi ro thật vượt `risk mong muốn × MAX_RISK_OVERSHOOT` → **bỏ qua lệnh**.

### 3.3 Quarter Kelly (tuỳ chọn, `kelly_positon.py`)

Bật bằng `USE_KELLY_SIZING = True` (mặc định **tắt**).

```
Kelly f* = W − (1 − W) / R
risk%    = clamp(f* × KELLY_FRACTION × 100, KELLY_MIN_RISK_PERCENT, KELLY_MAX_RISK_PERCENT)
```

- `W` = win rate, `R` = lãi TB / lỗ TB; tính trên **lãi/lỗ mỗi lot** của tối đa `KELLY_LOOKBACK_TRADES` lệnh gần nhất.
- Chưa đủ `KELLY_MIN_TRADES` lệnh → dùng `RISK_PERCENT` cố định.
- Kelly ≤ 0 (chưa có edge) → dùng mức sàn `KELLY_MIN_RISK_PERCENT`.

### 3.4 Các giới hạn bảo vệ (`risk_manager.py`)

| Cơ chế | Cấu hình | Hành động khi kích hoạt |
|---|---|---|
| Lỗ ngày | `DAILY_LOSS_LIMIT` (% equity) | Đóng hết lệnh, nghỉ đến ngày giao dịch sau |
| Lỗ tuần | `WEEKLY_LOSS_LIMIT` (% equity) | Đóng hết lệnh, nghỉ đến tuần sau |
| Thua liên tiếp | `MAX_CONSECUTIVE_LOSSES` | Ngừng **mở** lệnh mới đến ngày mai |
| Số lệnh/symbol | `MAX_OPEN_TRADES_PER_SYMBOL` | Mỗi symbol 1 lệnh tại một thời điểm |
| Cooldown | `COOLDOWN_BARS` | Chờ N nến sau khi đóng lệnh |
| Spread | `MAX_SPREAD` | Không mở lệnh khi spread quá rộng |

Balance đầu ngày/đầu tuần được tính **lùi từ lịch sử deal** (theo giờ server broker) nên vẫn đúng khi khởi động lại bot giữa ngày.

---

## 4. Cấu trúc dự án

```
.
├── main.py               # Vòng lặp chính, xử lý từng symbol, cooldown, spread
├── config.py             # Toàn bộ tham số cấu hình
├── mt5_connect.py        # Kết nối MT5 (đọc tài khoản từ .env)
├── data_loader.py        # Tải nến, bỏ nến đang chạy
├── indicators.py         # Tính EMA
├── strategy.py           # Sinh tín hiệu BUY / SELL / SKIP / CLOSE
├── support_resistance.py # Phát hiện vùng S&R, breakout, retest
├── risk_manager.py       # Giới hạn lỗ ngày/tuần, thua liên tiếp
├── kelly_positon.py      # Quarter Kelly position sizing
├── execution.py          # Gửi lệnh, tính SL/lot, đóng lệnh, đồng bộ lệnh đóng
├── trade_history.py      # Giờ server broker + lịch sử lệnh đã đóng
├── notion_logger.py      # Ghi lệnh đã đóng lên Notion (tuỳ chọn)
├── logger.py             # Cấu hình các file log
├── .env                  # Thông tin đăng nhập (KHÔNG commit)
└── logs/                 # Tự tạo khi chạy
```

---

## 5. Cài đặt

### Yêu cầu

- **Windows** (thư viện `MetaTrader5` chỉ hỗ trợ Windows).
- **MetaTrader 5** đã cài, đăng nhập sẵn tài khoản, và bật nút **Algo Trading** (màu xanh).
- Python 3.9+.
- `curl` có trong PATH (dùng cho Notion; Windows 10/11 có sẵn).

### Cài thư viện

```bash
pip install MetaTrader5 pandas python-dotenv
```

### Tạo file `.env`

```env
LOGIN=12345678
PASS=mat_khau_cua_ban
SERVER=Ten-Server-Broker

# Tuỳ chọn - chỉ cần nếu muốn ghi log lên Notion
NOTION_TOKEN=secret_xxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxx
```

> Thêm `.env` và `logs/` vào `.gitignore` để không lộ mật khẩu.

---

## 6. Chạy bot

```bash
python main.py
```

Dừng bot bằng `Ctrl + C` (bot sẽ ngắt kết nối MT5 an toàn).

Mỗi vòng lặp (`CHECK_INTERVAL` giây), bot sẽ:

1. Đồng bộ các lệnh broker đã đóng (SL/TP/…) vào log.
2. Kiểm tra giới hạn lỗ ngày/tuần. Nếu bị khoá → đóng toàn bộ lệnh và nghỉ.
3. Với từng symbol: tải nến → chỉ xử lý khi có nến mới đóng → tính EMA → lấy tín hiệu → mở/đóng/đảo lệnh.

---

## 7. Cấu hình quan trọng (`config.py`)

| Nhóm | Tham số chính |
|---|---|
| Chung | `SYMBOLS`, `TIMEFRAME`, `CHECK_INTERVAL`, `MAGIC_NUMBER`, `HISTORY_BARS` |
| EMA | `EMA_FAST`, `EMA_MEDIUM_1`, `EMA_MEDIUM_2`, `EMA_SLOW` |
| Vốn | `RISK_PERCENT`, `SL_DISTANCE`, `MAX_LOT_SIZE`, `MAX_RISK_OVERSHOOT` |
| Giới hạn | `DAILY_LOSS_LIMIT`, `WEEKLY_LOSS_LIMIT`, `MAX_CONSECUTIVE_LOSSES`, `COOLDOWN_BARS` |
| Spread / giờ | `MAX_SPREAD`, `SERVER_UTC_OFFSET_HOURS` |
| S&R | `SR_SWING_STRENGTH`, `SR_LOOKBACK`, `SR_MIN_TOUCHES`, `SR_BLOCK_DISTANCE`, `SR_BREAKOUT_BUFFER`, `SR_RETEST_MAX_BARS` |
| Kelly | `USE_KELLY_SIZING`, `KELLY_FRACTION`, `KELLY_MIN_TRADES`, `KELLY_LOOKBACK_TRADES`, `KELLY_MAX_RISK_PERCENT`, `KELLY_MIN_RISK_PERCENT` |

**Lưu ý khi chỉnh:**

- `MAX_SPREAD` và `SERVER_UTC_OFFSET_HOURS` phụ thuộc broker — hãy kiểm tra lại theo broker của bạn.
- Tên symbol phải khớp với broker (một số broker thêm hậu tố như `XAUUSDm`, `EURUSD.a`).
- Bot nhận diện lệnh của mình qua `MAGIC_NUMBER`; đổi số này nếu chạy nhiều bot trên cùng tài khoản.

---

## 8. Hệ thống log (thư mục `logs/`)

| File | Nội dung |
|---|---|
| `pybot.log` | Hoạt động chung, quyết định chặn lệnh, thông tin balance |
| `trades.log` | Lệnh mở/đóng (giá, lot, SL, ticket) |
| `report.log` | Kết quả từng lệnh đã đóng (PROFIT/LOSS, net) |
| `errors.log` | Lỗi kết nối, lỗi gửi lệnh (kèm mã retcode), traceback |

### Ghi lên Notion (tuỳ chọn)

Mỗi lệnh đóng được tạo một dòng trong Notion database với các cột: `Name`, `Date`, `Direction`, `Profit/Loss`, `Session`, `Followed rules`, `Pairs`. Database cần có đúng các thuộc tính này (kiểu `title`, `date`, `select`, `number`, `checkbox`). Thiếu `NOTION_TOKEN` hoặc `NOTION_DATABASE_ID` thì bot bỏ qua bước này.

---

## 9. Khuyến nghị trước khi chạy thật

1. Chạy **demo ít nhất vài tuần** và đối chiếu `report.log` với lịch sử MT5.
2. Kiểm tra `MAX_SPREAD`, `SL_DISTANCE` và lot thực tế phù hợp với broker/vốn của bạn.
3. Giữ `USE_KELLY_SIZING = False` cho đến khi có đủ mẫu lệnh đáng tin.
4. Đảm bảo máy chạy bot ổn định (internet, nguồn điện, VPS nếu cần) vì bot cần chạy liên tục để quản lý lệnh.
5. Backtest chiến lược riêng — dự án này chưa có module backtest.

---

## 10. Giới hạn đã biết

- Chiến lược trend-following bằng EMA thường kém hiệu quả khi thị trường đi ngang.
- Chưa có Take Profit cố định; lệnh thoát khi chạm SL, EMA rối, hoặc đảo xu hướng.
- Không có lọc tin tức/phiên giao dịch.
- Chỉ hoạt động trên Windows với MT5 terminal đang mở.

---

## Miễn trừ trách nhiệm

Mã nguồn được cung cấp "như hiện có", phục vụ mục đích học tập và nghiên cứu. Bạn tự chịu trách nhiệm với mọi quyết định và kết quả giao dịch.
# XAUUSD-Quant-Trading-System
