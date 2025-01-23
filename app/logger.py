import logging
import sys

#get logger
logger = logging.getLogger('stock_management')

# create formatter

formater = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# create handlers

stream_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler('app.log')

#set formatter
file_handler.setFormatter(formater)
stream_handler.setFormatter(formater)

# add handlers to the logger
logger.handlers = [stream_handler, file_handler]

# set
