import logging
import logging.config
import coloredlogs

def log():
    """
    Based on http://docs.python.org/howto/logging.html#configuring-logging
    """
    dictLogConfig = {
        "version":1,
        "disable_existing_loggers": False,
        "handlers":{
                    "fileHandler":{
                        "class":"logging.FileHandler",
                        "formatter":"myFormatter",
                        "filename":"config2.log"
                        }
                    },
        "loggers":{
            "exampleApp":{
                "handlers":["fileHandler"],
                "level":"DEBUG",
                }
            },

        "formatters":{
            "myFormatter":{
                "format":"%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            }
        }

    coloredlogs.install()
    logging.config.dictConfig(dictLogConfig)

    return logging
