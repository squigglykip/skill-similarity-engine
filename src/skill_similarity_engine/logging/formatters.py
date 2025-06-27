"""
logging.formatters

Defines log formatters for the centralised logging framework.
This module will provide detailed, console-friendly, and JSON formatters for log output.
"""

import logging
import json

class ConsoleFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

class DetailedFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(
            '%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        return json.dumps(log_record)

def get_console_formatter():
    return ConsoleFormatter()

def get_detailed_formatter():
    return DetailedFormatter()

def get_json_formatter():
    return JSONFormatter()
