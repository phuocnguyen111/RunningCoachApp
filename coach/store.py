import json
import os
import tempfile
import threading
from pathlib import Path

# Flask chạy đa luồng; một lock chung cho mọi thao tác ghi là đủ với app một người dùng.
LOCK = threading.RLock()


class StoreError(Exception):
    pass


class JsonStore:
    def __init__(self, root):
        self.root = Path(root).resolve()

    def path(self, *parts):
        p = self.root.joinpath(*parts).resolve()
        if p != self.root and not p.is_relative_to(self.root):
            raise StoreError(f"Đường dẫn không hợp lệ: {'/'.join(parts)}")
        return p

    def exists(self, *parts):
        return self.path(*parts).exists()

    def read(self, *parts, default=None):
        p = self.path(*parts)
        if not p.exists():
            return default
        with open(p, encoding="utf-8") as f:
            return json.load(f)

    def write(self, data, *parts):
        p = self.path(*parts)
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        with LOCK:
            p.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".tmp-", suffix=".json")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(payload)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, p)
            except BaseException:
                if os.path.exists(tmp):
                    os.unlink(tmp)
                raise

    def delete(self, *parts):
        with LOCK:
            p = self.path(*parts)
            if p.exists():
                p.unlink()

    def list_dir(self, *parts):
        d = self.path(*parts)
        if not d.is_dir():
            return []
        out = []
        for p in sorted(d.glob("*.json")):
            if p.name.startswith(".tmp-"):
                continue
            with open(p, encoding="utf-8") as f:
                out.append(json.load(f))
        return out
