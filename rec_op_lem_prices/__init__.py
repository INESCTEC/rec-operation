import os
import sys

from loguru import logger
from .optimization_functions import *
from .pricing_mechanisms_functions import *


LOG_FORMAT = \
	'<green>{time:YYYY-MM-DD HH:mm:ss}</green> | ' \
	'<level>{level: <7}</level> | ' \
	'<cyan>{name: <65}</cyan> | ' \
	'<cyan>{function: <47}</cyan> | ' \
	'<cyan>{line: >3}</cyan> | ' \
	'{message}'

logger.configure(handlers=[{'sink': sys.stderr, 'format': LOG_FORMAT, 'level': 'INFO'}])
