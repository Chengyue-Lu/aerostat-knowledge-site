from queue import Queue
from threading import Lock, Thread

from .mineru import run_mineru_parse


_parse_queue: Queue[int] = Queue()
_worker_lock = Lock()
_worker_started = False


def _parse_worker() -> None:
    while True:
        document_id = _parse_queue.get()
        try:
            run_mineru_parse(document_id)
        finally:
            _parse_queue.task_done()


def start_parse_worker() -> None:
    global _worker_started

    with _worker_lock:
        if _worker_started:
            return

        worker = Thread(target=_parse_worker, name="mineru-parse-worker", daemon=True)
        worker.start()
        _worker_started = True


def enqueue_parse(document_id: int) -> None:
    _parse_queue.put(document_id)
