import json
import os
import threading
from pathlib import Path


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.RLock()

    def read(self):
        with self.lock:
            return json.loads(self.path.read_text())

    def complete(self, task_id, done):
        if type(done) is not bool:
            raise ValueError("done must be boolean")
        with self.lock:
            state = self.read()
            task = next((t for t in state["tasks"] if t["id"] == task_id), None)
            if task is None:
                raise ValueError("Task not found")
            task["done"] = done
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2))
            temporary.chmod(self.path.stat().st_mode & 0o777)
            os.replace(temporary, self.path)
            return state
