def get_logging_config(level: str, apps: list[str]) -> dict:
    return {
        "version": 1,  # the dictConfig format version
        "disable_existing_loggers": False,  # retain the default loggers
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
        },
        "formatters": {
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "loggers": {
            logger_name: {
                "level": level,
                "handlers": ["console"],
                "propagate": True,
            }
            for logger_name in apps
        },
    }
