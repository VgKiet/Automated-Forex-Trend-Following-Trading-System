# SYMBOLS = ["XAUUSD", "GBPUSD", "EURUSD", "USDJPY"]
# TIMEFRAME = "M15"
 
# # =========================
# # EMA STRATEGY
# # =========================
 
# EMA_FAST = 5
# EMA_MEDIUM_1 = 9
# EMA_MEDIUM_2 = 13
# EMA_SLOW = 21
 
# # =========================
# # QUẢN LÝ VỐN
# # =========================
 
# LOT_SIZE = 0.01
 
# RISK_PERCENT = 1
 
# # Stop loss mặc định (pip) — dùng khi symbol không có trong SL_PIPS_MAP
# SL_PIPS = 25
 
# # Stop loss riêng theo symbol (pip)
# SL_PIPS_MAP = {
#     "XAUUSD": 150,  # Vàng dao động mạnh, cần SL xa
#     "GBPUSD": 30,   # Cable biến động vừa
#     "EURUSD": 25,   # Ổn định nhất trong 4 mã
#     "USDJPY": 35,   # JPY đôi khi spike mạnh
# }
 
# # Giới hạn lot tối đa tuyệt đối (phòng tính sai)
# MAX_LOT_SIZE = 0.05
 
# # Stop loss khẩn cấp
# EMERGENCY_SL_USD = 10
 
# # =========================
# # GIỚI HẠN GIAO DỊCH
# # =========================
 
# # Mỗi symbol chỉ được 1 lệnh tại một thời điểm
# MAX_OPEN_TRADES_PER_SYMBOL = 1
 
# # =========================
# # GIỚI HẠN THUA LỖ
# # =========================
# DAILY_LOSS_LIMIT = 3
# WEEKLY_LOSS_LIMIT = 8
# MAX_CONSECUTIVE_LOSSES = 5
 
# # =========================
# # VÙNG HỖ TRỢ / KHÁNG CỰ (SUPPORT & RESISTANCE)
# # =========================

# # Số nến xác nhận 1 đỉnh/đáy (mỗi bên trái/phải)
# SR_SWING_STRENGTH = 3

# # Số nến gần nhất để tìm đỉnh/đáy
# SR_LOOKBACK = 150

# # Số lần chạm tối thiểu để 1 vùng được coi là đủ mạnh (lọc nhiễu)
# SR_MIN_TOUCHES = 2

# # Khoảng cách để gộp các đỉnh/đáy gần nhau thành 1 vùng
# SR_ZONE_MERGE_DISTANCE = {
#     "XAUUSD": 3.0,     # 3 USD
#     "GBPUSD": 0.0020,  # 20 pip
#     "EURUSD": 0.0020,  # 20 pip
#     "USDJPY": 0.20,    # 20 pip quy đổi JPY
# }
# SR_DEFAULT_MERGE_DISTANCE = 0.0020

# # Khoảng cách từ giá hiện tại đến vùng để coi là "đang áp sát biên"
# # → nếu vào trong khoảng này thì CHẶN lệnh dù EMA đã cho tín hiệu
# SR_BLOCK_DISTANCE = {
#     "XAUUSD": 3.0,
#     "GBPUSD": 0.0020,
#     "EURUSD": 0.0020,
#     "USDJPY": 0.20,
# }
# SR_DEFAULT_BLOCK_DISTANCE = 0.0020

# # Buffer để xác nhận giá ĐÃ PHÁ vùng thật sự
# # (đóng cửa phải vượt qua level + buffer mới tính là breakout, tránh phá giả do nhiễu)
# SR_BREAKOUT_BUFFER = {
#     "XAUUSD": 2.0,
#     "GBPUSD": 0.0015,
#     "EURUSD": 0.0015,
#     "USDJPY": 0.15,
# }
# SR_DEFAULT_BREAKOUT_BUFFER = 0.0015

# # Số nến tối đa kể từ lúc phá vùng để còn được tính là đang trong giai đoạn "retest"
# # Quá số nến này mà chưa quay lại test thì coi vùng đã cũ, quay về logic chặn bình thường
# SR_RETEST_MAX_BARS = 15

# # =========================
# # KELLY POSITION SIZING (QUARTER KELLY)
# # =========================

# # Bật/tắt Kelly sizing. False -> dùng RISK_PERCENT cố định như cũ (an toàn, mặc định khi mới chạy bot)
# USE_KELLY_SIZING = True

# # Hệ số Kelly áp dụng — 0.25 = Quarter Kelly
# # (Full Kelly (1.0) lý thuyết tối ưu tăng trưởng nhưng biến động rất mạnh,
# #  Quarter Kelly giảm rủi ro/drawdown đáng kể mà vẫn giữ phần lớn lợi thế tăng trưởng)
# KELLY_FRACTION = 0.25

# # Số lệnh ĐÃ ĐÓNG tối thiểu (theo symbol) cần có trước khi tin dùng Kelly.
# # Mẫu quá nhỏ thì win rate / payoff ratio ước lượng không đáng tin.
# KELLY_MIN_TRADES = 20

# # Lấy tối đa bao nhiêu lệnh gần nhất để tính (dữ liệu quá cũ không còn phản ánh
# # đúng hệ thống hiện tại — ví dụ sau khi bạn đã chỉnh EMA, S/R...)
# KELLY_LOOKBACK_TRADES = 50

# # Số ngày tối đa nhìn lại lịch sử deal trong MT5 để gom đủ KELLY_LOOKBACK_TRADES lệnh
# KELLY_LOOKBACK_DAYS = 180

# # Trần risk % tuyệt đối cho mỗi lệnh dù Kelly tính ra cao hơn (an toàn tuyệt đối)
# KELLY_MAX_RISK_PERCENT = 2.0

# # Sàn risk % tối thiểu khi Kelly <= 0 (hệ thống đang không có edge dương gần đây)
# # hoặc khi vừa đủ mẫu nhưng Kelly ra số quá nhỏ
# KELLY_MIN_RISK_PERCENT = 0.25

# # =========================
# # DATA LOADER
# # =========================
 
# HISTORY_BARS = 200
 
# # =========================
# # BOT SETTINGS
# # =========================
 
# # Chu kỳ kiểm tra tín hiệu (giây)
# CHECK_INTERVAL = 60
 
# # Magic Number MT5
# MAGIC_NUMBER = 123456
 
# # =========================
# # LOGGING
# # =========================
 
# LOG_FILE = "logs/trades.log"


# Bản đã fix
SYMBOLS = ["XAUUSD", "GBPUSD", "EURUSD", "USDJPY"]
TIMEFRAME = "M15"
 
# =========================
# EMA STRATEGY
# =========================
 
EMA_FAST = 5
EMA_MEDIUM_1 = 9
EMA_MEDIUM_2 = 13
EMA_SLOW = 21
 
# =========================
# QUẢN LÝ VỐN
# =========================
 
LOT_SIZE = 0.01
 
RISK_PERCENT = 1
 
# Stop loss theo KHOẢNG GIÁ (không dùng pip -> không lệch theo broker/số chữ số)
SL_DISTANCE = {
    "XAUUSD": 15.0,    # 15 USD (vàng M15 nhiễu 3-10 USD, SL phải xa hơn nhiễu)
    "GBPUSD": 0.0030,  # 30 pip
    "EURUSD": 0.0025,  # 25 pip
    "USDJPY": 0.35,    # 35 pip
}
SL_DISTANCE_DEFAULT = 0.0025

# Nếu lot tối thiểu làm risk thật vượt (risk mong muốn x hệ số này) -> bỏ qua lệnh
MAX_RISK_OVERSHOOT = 1.5

# Giới hạn lot tối đa tuyệt đối (phòng tính sai)
MAX_LOT_SIZE = 0.05
 
# =========================
# GIỚI HẠN GIAO DỊCH
# =========================
 
# Mỗi symbol chỉ được 1 lệnh tại một thời điểm
MAX_OPEN_TRADES_PER_SYMBOL = 1
 
# =========================
# GIỚI HẠN THUA LỖ
# =========================
DAILY_LOSS_LIMIT = 3          # % equity - vượt thì đóng hết, nghỉ đến ngày hôm sau
WEEKLY_LOSS_LIMIT = 8         # % equity - vượt thì đóng hết, nghỉ đến tuần sau
MAX_CONSECUTIVE_LOSSES = 5    # thua liên tiếp N lệnh -> ngừng MỞ lệnh mới đến ngày hôm sau

# Sau khi lệnh đóng (SL / EMA rối) bot ở trạng thái flat: chờ N nến mới được vào lại
COOLDOWN_BARS = 3

# Spread tối đa (đơn vị GIÁ) cho phép khi MỞ lệnh. Chỉnh theo broker của bạn!
MAX_SPREAD = {
    "XAUUSD": 0.50,
    "GBPUSD": 0.00020,
    "EURUSD": 0.00020,
    "USDJPY": 0.020,
}
MAX_SPREAD_DEFAULT = 0.00020

# Chênh lệch giờ server broker so với UTC (dùng khi không tự suy ra được từ tick)
SERVER_UTC_OFFSET_HOURS = 3
 
# =========================
# VÙNG HỖ TRỢ / KHÁNG CỰ (SUPPORT & RESISTANCE)
# =========================

# Số nến xác nhận 1 đỉnh/đáy (mỗi bên trái/phải)
SR_SWING_STRENGTH = 3

# Số nến gần nhất để tìm đỉnh/đáy
SR_LOOKBACK = 150

# Số lần chạm tối thiểu để 1 vùng được coi là đủ mạnh (lọc nhiễu)
SR_MIN_TOUCHES = 2

# Khoảng cách để gộp các đỉnh/đáy gần nhau thành 1 vùng
SR_ZONE_MERGE_DISTANCE = {
    "XAUUSD": 3.0,     # 3 USD
    "GBPUSD": 0.0020,  # 20 pip
    "EURUSD": 0.0020,  # 20 pip
    "USDJPY": 0.20,    # 20 pip quy đổi JPY
}
SR_DEFAULT_MERGE_DISTANCE = 0.0020

# Khoảng cách từ giá hiện tại đến vùng để coi là "đang áp sát biên"
# → nếu vào trong khoảng này thì CHẶN lệnh dù EMA đã cho tín hiệu
SR_BLOCK_DISTANCE = {
    "XAUUSD": 3.0,
    "GBPUSD": 0.0020,
    "EURUSD": 0.0020,
    "USDJPY": 0.20,
}
SR_DEFAULT_BLOCK_DISTANCE = 0.0020

# Buffer để xác nhận giá ĐÃ PHÁ vùng thật sự
# (đóng cửa phải vượt qua level + buffer mới tính là breakout, tránh phá giả do nhiễu)
SR_BREAKOUT_BUFFER = {
    "XAUUSD": 2.0,
    "GBPUSD": 0.0015,
    "EURUSD": 0.0015,
    "USDJPY": 0.15,
}
SR_DEFAULT_BREAKOUT_BUFFER = 0.0015

# Số nến tối đa kể từ lúc phá vùng để còn được tính là đang trong giai đoạn "retest"
# Quá số nến này mà chưa quay lại test thì coi vùng đã cũ, quay về logic chặn bình thường
SR_RETEST_MAX_BARS = 15

# =========================
# KELLY POSITION SIZING (QUARTER KELLY)
# =========================

# Bật/tắt Kelly sizing. False -> dùng RISK_PERCENT cố định như cũ (an toàn, mặc định khi mới chạy bot)
USE_KELLY_SIZING = False

# Hệ số Kelly áp dụng — 0.25 = Quarter Kelly
# (Full Kelly (1.0) lý thuyết tối ưu tăng trưởng nhưng biến động rất mạnh,
#  Quarter Kelly giảm rủi ro/drawdown đáng kể mà vẫn giữ phần lớn lợi thế tăng trưởng)
KELLY_FRACTION = 0.25

# Số lệnh ĐÃ ĐÓNG tối thiểu (theo symbol) cần có trước khi tin dùng Kelly.
# Mẫu quá nhỏ thì win rate / payoff ratio ước lượng không đáng tin.
KELLY_MIN_TRADES = 40

# Lấy tối đa bao nhiêu lệnh gần nhất để tính (dữ liệu quá cũ không còn phản ánh
# đúng hệ thống hiện tại — ví dụ sau khi bạn đã chỉnh EMA, S/R...)
KELLY_LOOKBACK_TRADES = 50

# Số ngày tối đa nhìn lại lịch sử deal trong MT5 để gom đủ KELLY_LOOKBACK_TRADES lệnh
KELLY_LOOKBACK_DAYS = 180

# Trần risk % tuyệt đối cho mỗi lệnh dù Kelly tính ra cao hơn (an toàn tuyệt đối)
KELLY_MAX_RISK_PERCENT = 2.0

# Sàn risk % tối thiểu khi Kelly <= 0 (hệ thống đang không có edge dương gần đây)
# hoặc khi vừa đủ mẫu nhưng Kelly ra số quá nhỏ
KELLY_MIN_RISK_PERCENT = 0.25

# =========================
# DATA LOADER
# =========================
 
HISTORY_BARS = 200
 
# =========================
# BOT SETTINGS
# =========================
 
# Chu kỳ kiểm tra tín hiệu (giây)
CHECK_INTERVAL = 60
 
# Magic Number MT5
MAGIC_NUMBER = 123456
 
# =========================
# LOGGING
# =========================
 
LOG_FILE = "logs/trades.log"