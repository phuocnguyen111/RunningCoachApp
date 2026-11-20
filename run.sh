#!/bin/bash
# run.sh – khởi động Running Coach App
cd "$(dirname "$0")"

echo ""
echo "═══════════════════════════════════════════"
echo "  🏃 RUNNING COACH APP"
echo "═══════════════════════════════════════════"
echo ""

if ! command -v uv &> /dev/null; then
  USER_BIN="$(python3 -m site --user-base 2>/dev/null)/bin"
  if [ -x "$USER_BIN/uv" ]; then
    export PATH="$USER_BIN:$PATH"
  else
    echo "❌ Cần cài uv: pip3 install --user uv  (hoặc https://docs.astral.sh/uv/)"
    exit 1
  fi
fi

if [ -f ".app.pid" ]; then
  PID=$(cat .app.pid)
  if kill -0 "$PID" 2>/dev/null; then
    echo "⚠️  App đang chạy rồi (PID=$PID) tại http://127.0.0.1:5050"
    echo "   Chạy ./stop.sh trước nếu muốn restart."
    open http://127.0.0.1:5050 2>/dev/null || true
    exit 0
  fi
  rm -f .app.pid
fi

echo "📦 Đồng bộ dependencies (uv sync)..."
uv sync --quiet || exit 1

(sleep 2 && open http://127.0.0.1:5050 2>/dev/null) &

uv run python app.py
