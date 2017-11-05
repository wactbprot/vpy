import logging
import logging.config
import coloredlogs

def log():
    """
    Based on http://docs.python.org/howto/logging.html#configuring-logging
    """
    dictLogConfig = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
    'standard': {
    'format':'%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    },
    },
    'handlers': {
    'default': {
    'level': 'INFO',
    'formatter': 'standard',
    'class': 'logging.StreamHandler',
    },
    },
    'loggers': {
    '': {
    'handlers': ['default'],
    'level': 'DEBUG',
    'propagate': True
    }
    }
    }



    logging.config.dictConfig(dictLogConfig)
    coloredlogs.install()

    return logging
