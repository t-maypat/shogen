import logging
import logging.config


def configure_logging(log_level: str = "INFO", environment: str = "local") -> None:
    formatter_name = "json" if environment != "local" else "plain"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            },
            "json": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": formatter_name,
            }
        },
        "root": {
            "handlers": ["default"],
            "level": log_level.upper(),
        },
    }

    logging.config.dictConfig(logging_config)
