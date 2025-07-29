import inspect
import hashlib
from typing import Callable, Dict

LOADED_GENES: Dict[str, Callable] = {}

def lux_gene_loader(alias: str = None):
    def wrapper(func):
        source = inspect.getsource(func)
        uid = hashlib.sha256(source.encode()).hexdigest()
        LOADED_GENES[alias or uid] = func
        func.__gene_id__ = uid
        func.__alias__ = alias
        return func
    return wrapper

def get_gene(alias_or_uid: str):
    return LOADED_GENES.get(alias_or_uid)

def to_dict(gene):
    """Converts a gene function to a dictionary representation."""
    return {
        "id": getattr(gene, "__gene_id__", None),
        "alias": getattr(gene, "__alias__", None),
        "source": inspect.getsource(gene),
        "is_async": inspect.iscoroutinefunction(gene)
    }


@lux_gene_loader(alias="gen_logger")
def gen_logger(being_soul: str, log_file: str = "logs/gen_logger.log"):
    """Prosty logger asynchroniczny"""
    import asyncio
    from datetime import datetime
    from typing import Dict, Any

    class Logger:
        def __init__(self, being_soul: str, log_file: str):
            self.being_soul = being_soul
            self.log_file = log_file
            self.is_running = False
            self.log_queue = asyncio.Queue()

        async def start_logging(self):
            if self.is_running:
                return
            self.is_running = True
            await self._log_loop()

        async def _log_loop(self):
            import os
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

            try:
                import aiofiles
                use_aiofiles = True
            except ImportError:
                print("aiofiles not found, using standard file operations.")
                aiofiles = None
                use_aiofiles = False

            if use_aiofiles:
                async with aiofiles.open(self.log_file, 'a', encoding='utf-8') as f:
                    while self.is_running:
                        log_entry = await self.log_queue.get()
                        await f.write(log_entry + '\n')
            else:
                while self.is_running:
                    log_entry = await self.log_queue.get()
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        f.write(log_entry + '\n')
            self.is_running = False

logger = get_gene("gen_logger")
print(to_dict(logger))