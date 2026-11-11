import os
import MetaTrader5 as mt5

from dotenv import load_dotenv
from logger import pybot_logger, error_logger


class MT5Connect:

    def __init__(self):

        load_dotenv()

        login = os.getenv("LOGIN")
        password = os.getenv("PASS")
        server = os.getenv("SERVER")

        if login is None:
            raise ValueError(
                "Không tìm thấy LOGIN trong file .env"
            )

        if password is None:
            raise ValueError(
                "Không tìm thấy PASS trong file .env"
            )

        if server is None:
            raise ValueError(
                "Không tìm thấy SERVER trong file .env"
            )

        self.login = int(login)
        self.password = password
        self.server = server

    def connect(self):

        pybot_logger.info(
            f"Đang kết nối tới {self.server}"
        )

        if not mt5.initialize(
            login=self.login,
            password=self.password,
            server=self.server
        ):

            error = mt5.last_error()

            print("Lỗi MT5:", error)

            error_logger.error(
                f"Kết nối MT5 thất bại: {error}"
            )

            return False

        account = mt5.account_info()

        if account is None:

            error_logger.error(
                "Không lấy được thông tin tài khoản"
            )

            mt5.shutdown()

            return False

        print("Kết nối thành công")
        print("Login:", account.login)
        print("Balance:", account.balance)
        print("Equity:", account.equity)

        pybot_logger.info(
            f"Đăng nhập thành công: {account.login}"
        )

        pybot_logger.info(
            f"Balance: {account.balance}"
        )

        pybot_logger.info(
            f"Equity: {account.equity}"
        )

        return True

    def disconnect(self):

        mt5.shutdown()

        pybot_logger.info(
            "Ngắt kết nối MT5"
        )

        print("Đã ngắt kết nối")


mt5_connect = MT5Connect()