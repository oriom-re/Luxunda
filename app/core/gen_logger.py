# soul: app/core/gen_logger.py

import datetime

def log(message, level="INFO", source="gen_logger"):
    now = datetime.datetime.now().isoformat()
    print(f"[{now}] [{level}] [{source}] {message}")
    return {
        "type": "log",
        "level": level,
        "message": message,
        "timestamp": now,
        "source": source
    }