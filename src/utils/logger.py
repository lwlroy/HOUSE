import logging
import os
from datetime import datetime
from typing import Optional


class Logger:
    """日誌管理類別"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """設定日誌系統"""
        from .config import get_config
        
        config = get_config()
        log_config = config.get_logging_config()
        
        # 建立logs目錄
        log_dir = os.path.dirname(log_config.get('file', './logs/crawler.log'))
        os.makedirs(log_dir, exist_ok=True)
        
        # 設定日誌格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 建立logger
        self._logger = logging.getLogger('house_crawler')
        self._logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))
        
        # 避免重複添加handler
        if not self._logger.handlers:
            # 檔案handler
            file_handler = logging.FileHandler(
                log_config.get('file', './logs/crawler.log'),
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
            
            # 控制台handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)
    
    def get_logger(self):
        """取得logger實例"""
        return self._logger
    
    def info(self, message: str):
        """記錄資訊日誌"""
        self._logger.info(message)
    
    def warning(self, message: str):
        """記錄警告日誌"""
        self._logger.warning(message)
    
    def error(self, message: str):
        """記錄錯誤日誌"""
        self._logger.error(message)
    
    def debug(self, message: str):
        """記錄除錯日誌"""
        self._logger.debug(message)
    
    def critical(self, message: str):
        """記錄嚴重錯誤日誌"""
        self._logger.critical(message)


# 全域logger實例
logger = Logger()


def get_logger():
    """取得logger實例"""
    return logger
