import logging
import os
from datetime import datetime

class FileHandlerWithReopen(logging.FileHandler):
    def emit(self, record):
        self.stream.close()
        self.stream = self._open()
        super().emit(record)
        self.stream.close()
        self.stream = None

class LipSyncLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LipSyncLogger, cls).__new__(cls)
            cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self):
        log_dir = r"D:\Cache\Blender"
        log_filename = f"blender_lipsync_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file_path = os.path.join(log_dir, log_filename)

        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            print(f"无法创建日志目录：{e}")
            return

        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        try:
            file_handler = FileHandlerWithReopen(log_file_path)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(log_format))

            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(logging.Formatter(log_format))

            self.logger = logging.getLogger('LipSyncLogger')
            self.logger.setLevel(logging.DEBUG)
            self.logger.propagate = False  # 禁止传播到父logger

            if not self.logger.handlers:
                self.logger.addHandler(file_handler)
                self.logger.addHandler(console_handler)

            print(f"日志文件被创建在: {log_file_path}")
            self.logger.info("Lip sync & 3D digital human 插件日志系统初始化")

            # 添加测试日志
            self.logger.debug("这是一条测试 DEBUG 消息")
            self.logger.info("这是一条测试 INFO 消息")
            self.logger.warning("这是一条测试 WARNING 消息")
            self.logger.error("这是一条测试 ERROR 消息")

        except Exception as e:
            print(f"设置日志系统时出错：{e}")

    def get_logger(self):
        return self.logger

# 全局访问点
def get_logger():
    return LipSyncLogger().get_logger()

# 自定义 debug 和 info 方法，用于额外的控制台输出
def custom_debug(self, message):
    print(f"Debug: {message}")  # 直接打印到控制台
    self.debug(message)

def custom_info(self, message):
    print(f"Info: {message}")  # 直接打印到控制台
    self.info(message)

# 将自定义方法添加到 logger 实例
logger = get_logger()
logger.custom_debug = custom_debug.__get__(logger)
logger.custom_info = custom_info.__get__(logger)

if __name__ == "__main__":
    # 测试代码
    logger = get_logger()
    logger.debug("这是一个 debug 消息")
    logger.info("这是一个 info 消息")
    logger.warning("这是一个 warning 消息")
    logger.error("这是一个 error 消息")
    logger.custom_debug("这是一个自定义 debug 消息")
    logger.custom_info("这是一个自定义 info 消息")