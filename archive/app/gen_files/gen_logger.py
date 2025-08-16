# app/gen_files/gen_logger.py
__name__ = "gen_logger"
__doc__ = "Prosty logger asynchroniczny"
__system__ = "app.core.gen_logger"
__version__ = "0.1.0"
__author__ = "filesystem"

import asyncio
import datetime

def log(message, level: str = "INFO", source: str = "gen_logger"):
    now = datetime.datetime.now().isoformat()
    print(f"[{now}] [{level}] [{source}] {message}")
    return {
        "type": "log",
        "level": level,
        "message": message,
        "timestamp": now,
        "source": source
    }

def init():
    """Inicjalizacja loggera"""
    log("Logger zainicjalizowany", "INFO")
    asyncio.create_task(start_logger())
    return {
        "type": "init",
        "message": "Logger initialized",
        "timestamp": datetime.datetime.now().isoformat()
    }
__init__ = init

async def start_logger():
    # to jest testowy kod, który będzie uruchamiany w kontekście gen_logger
    while True:
        log("Logger działa", "DEBUG")
        await asyncio.sleep(5)

__all__ = ["log", "init", "start_logger"]

