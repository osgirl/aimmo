import logging
import logging.config

_CONFIG = {
    'version': 1,
    'formatters': {
        'default': {'format': '%(asctime)s - %(levelname)s - %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'default': {
            'level': 'DEBUG',
            'handlers': ['console']
        }
    },
    'disable_existing_loggers': False
}


def configure_logger():
    logging.config.dictConfig(_CONFIG)
