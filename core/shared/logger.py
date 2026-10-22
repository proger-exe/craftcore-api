import structlog
import logging
import sys
from structlog.processors import CallsiteParameter, CallsiteParameterAdder


def configure_divine_logging():
    # Кастомный процессор для выделения ошибок "божественным гневом"
    def sin_highlighter(logger, method_name, event_dict):
        if method_name in ("error", "critical", "exception"):
            event_dict["event"] = f"🔥 CRITICAL: {event_dict['event']}"
        elif method_name == "warning":
            event_dict["event"] = f"⚠️ WARNING: {event_dict['event']}"
        return event_dict

    # Конфигурация процессоров
    processors = [
        # Детализация места вызова (божественная всевидящность)
        CallsiteParameterAdder(
            [
                CallsiteParameter.FILENAME,
                CallsiteParameter.MODULE,
                CallsiteParameter.FUNC_NAME,
                CallsiteParameter.LINENO,
                # CallsiteParameter.THREAD,
                # CallsiteParameter.THREAD_NAME,
                # CallsiteParameter.PROCESS,
                # CallsiteParameter.PROCESS_NAME,
            ]
        ),
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.contextvars.merge_contextvars,  # Контекстные переменные
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S.%f", utc=False),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        sin_highlighter,  # Наш кастомный "индикатор греха"
        # Форматирование для смертных глаз
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(
            colors=True,
            force_colors=True,
            pad_event=40,  # Выравнивание для лучшей читаемости
            exception_formatter=structlog.dev.plain_traceback,
        ),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Настройка стандартного логгера — вешаем на root
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # убираем то, что навесил uvicorn/другие
    root_logger.setLevel(logging.INFO)

    # structlog-формат (для логов из core.shared.logger)
    structlog_handler = logging.StreamHandler(sys.stderr)
    structlog_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(colors=True, force_colors=True),
            ],
        )
    )
    root_logger.addHandler(structlog_handler)

    # Обычный формат для stdlib (api.request, api.profile) — чтобы точно видеть логи эндпоинтов
    plain_handler = logging.StreamHandler(sys.stderr)
    plain_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    plain_handler.addFilter(
        type(
            "",
            (logging.Filter,),
            {
                "filter": lambda self, r: r.name.startswith("api.")
                or r.name.startswith("core.managers")
            },
        )()
    )
    root_logger.addHandler(plain_handler)

    return structlog.get_logger()


# Инициализация божественного логгера
logger = configure_divine_logging()
