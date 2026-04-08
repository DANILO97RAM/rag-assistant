"""
Configuración centralizada de logging para el proyecto.

Se invoca una sola vez desde main.py al inicio del pipeline.
Cada módulo obtiene su propio logger con logging.getLogger(__name__),
heredando automáticamente el nivel y los handlers configurados aquí.
"""

import logging
import sys

_LOG_FORMAT = "%(asctime)s  %(levelname)-8s  %(name)-25s  %(message)s"
_LOG_DATEFMT = "%H:%M:%S"


def setup_logging(level: int = logging.INFO) -> None:
    """Configura el logger raíz del proyecto con un handler de consola.

    Args:
        level: Nivel de logging (logging.DEBUG, logging.INFO, etc.)
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATEFMT))

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)

