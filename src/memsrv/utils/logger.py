"""Common logger"""
import logging

# Configure logging once, globally
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def get_logger(name: str):
    """Common logger for all files"""
    return logging.getLogger(name)
