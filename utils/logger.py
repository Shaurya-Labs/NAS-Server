import logging
from pathlib import Path
from flask import has_request_context, request
from flask_login import current_user

# Adding usernames into logs
class FlaskUserFilter(logging.Filter):
    def filter(self, record):
         
        # Setting a defalut value, so that if there's no user, it means it's a system log
        record.user = "System"

        # Checking if the log is happening inside a live browser HTTP request
        if has_request_context():

            # If the user is logged in
            if current_user.is_authenticated:
                record.user = current_user.username
            else:
                record.user = request.remote_addr
        
        return True


def setup_logger():
    
    log_format = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s [%(user)s] (%(filename)s) -> %(message)s',
            datefmt='%d-%m-%Y %H:%M:%S'
    )

    user_filter = FlaskUserFilter()

    # Setting up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.DEBUG)
    console_handler.addFilter(user_filter)

    # Initializing logs directory path and making logs directory if not already exists
    logs_folder_path = Path(__file__).parents[1] / "logs"
    logs_folder_path.mkdir(exist_ok=True)

    # Setting up file handler
    file_handler = logging.FileHandler(logs_folder_path / "log.log", encoding="utf-8")
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.DEBUG)
    file_handler.addFilter(user_filter)

    root_logger = logging.getLogger()

    # Removing any handler added by third party libraries
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

setup_logger()