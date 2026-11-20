import os
import shutil
import signal
import sys
from datetime import datetime
from pathlib import Path

from coach import create_app
from coach.config import Config
from coach.migrate import migrate_all
from coach.plans import PlanCatalog

BASE_DIR = Path(__file__).resolve().parent
PID_FILE = BASE_DIR / ".app.pid"


def backup_data(config):
    if not config.data_dir.exists():
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = config.backup_dir / ts
    shutil.copytree(config.data_dir, dest)
    return dest


def main():
    config = Config(base_dir=BASE_DIR)
    print("\n🏃 Running Coach App đang khởi động...")

    report = migrate_all(config.data_dir, PlanCatalog(config.plans_dir), config.backup_dir)
    if report["backup"]:
        print(f"  ↳ Đã nâng cấp dữ liệu cũ (backup: data_backup/{report['backup']})")
    for w in report["warnings"]:
        print(f"  ⚠️  {w}")

    app = create_app(config)
    app.extensions["coach"].startup()

    PID_FILE.write_text(str(os.getpid()))

    def shutdown(sig, frame):
        print("\n⏹  Đang tắt app...")
        dest = backup_data(config)
        if dest:
            print(f"💾 Đã backup dữ liệu → {dest.relative_to(BASE_DIR)}/")
        PID_FILE.unlink(missing_ok=True)
        print("✅ Tắt an toàn.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(f"🌐 http://{config.host}:{config.port}")
    print("   Nhấn Ctrl+C hoặc chạy ./stop.sh để tắt an toàn\n")
    app.run(host=config.host, port=config.port, debug=False)


if __name__ == "__main__":
    main()
