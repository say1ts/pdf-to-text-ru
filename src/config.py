import logging
import json
from logging import Formatter
from src.settings import Settings as BaseSettings

class JsonFormatter(Formatter):
    """
    JSON formatter for structured logging.
    Ensures the final output is a JSON string.
    """
    def format(self, record: logging.LogRecord) -> str:
        """Formats a log record into a JSON string."""
        record.message = record.getMessage()
        log_object = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.message,
        }
        if hasattr(record, 'context_module'):
            log_object['module'] = record.context_module

        standard_attrs = set(logging.LogRecord('', '', '', '', '', '', '', '').__dict__.keys())
        extra_fields = {key: value for key, value in record.__dict__.items() if key not in standard_attrs and key not in log_object}
        
        if extra_fields:
            log_object['extra'] = extra_fields

        return json.dumps(log_object, ensure_ascii=False)

class ConfigProvider:
	"""DI container for dependencies."""
	def __init__(self):
		self.settings = BaseSettings()
		self.logger = self._setup_logger()

	def _setup_logger(self) -> logging.Logger:
		logger = logging.getLogger(__name__)
		logger.setLevel(self.settings.LOG_LEVEL)

		if logger.hasHandlers():
			logger.handlers.clear()

		formatter = JsonFormatter()

		file_handler = logging.FileHandler(self.settings.LOG_FILE)
		file_handler.setFormatter(formatter)
		
		stream_handler = logging.StreamHandler()
		stream_handler.setFormatter(formatter)
		
		logger.addHandler(stream_handler)
		return logger

	def get_logger(self, module_name: str) -> logging.LoggerAdapter:
		"""Get logger with context."""
		return logging.LoggerAdapter(self.get_base_logger(), {"context_module": module_name})

	def get_base_logger(self) -> logging.Logger:
		return self.logger

	def get_settings(self) -> BaseSettings:
		return self.settings

config_provider = ConfigProvider()
