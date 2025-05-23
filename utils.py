# utils.py
import logging
import config
from logging.handlers import RotatingFileHandler

def setup_logging(log_level="DEBUG", log_level_console="WARNING", log_file="simulation.log"):
    """
    Set up logging configuration to output log messages both to a file and to the console.

    Parameters:
      log_level (str): Logging level for file output (default "DEBUG").
      log_level_console (str): Logging level for console output (default "WARNING").
      log_file (str): Filename for the log file (default "simulation.log").

    The function creates a logger, configures two handlers (one for file and one for console)
    with specified logging levels and format, and attaches them to the root logger.
    """
    # Create a custom logger by retrieving the root logger.
    logger = logging.getLogger()
    # Set the overall logging level.
    logger.setLevel(log_level)

    # # Create a file handler for logging messages to a file.
    # file_handler = logging.FileHandler(log_file)

    # Create a rotating file handler with max 10MB per file and up to 5 backup files.
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)

    # Create a stream handler for outputting log messages to the console.
    console_handler = logging.StreamHandler()

    # Set logging level for each handler individually.
    file_handler.setLevel(log_level)
    console_handler.setLevel(log_level_console)

    # Define a log format with timestamp, level, logger name, and the message.
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", 
                                  "%Y-%m-%d %H:%M:%S")
    # Apply the formatter to both the file and console handlers.
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add both handlers to the root logger.
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def write_config_description(output_file="config_description.txt"):
    with open(output_file, 'w') as f:
        f.write("Configuration Values:\n")
        f.write("=====================\n\n")
        
        for attr in sorted(dir(config)):
            # Consider only uppercase variables as configuration variables
            if attr.isupper():
                value = getattr(config, attr)
                f.write(f"{attr} = {repr(value)}\n")

