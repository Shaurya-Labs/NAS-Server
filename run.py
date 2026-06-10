from app import create_app
from utils import logger
import logging

logging.info("Creating flask application")
app = create_app()
logging.info("flask application created successfully")

if __name__ == "__main__":
    logger.setup_logger()

    logging.info("Starting Server")
    app.run("0.0.0.0", debug=True)
    logging.info("Server started successfully")