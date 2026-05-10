#!/bin/bash
# run.sh – khởi động Running Coach App

echo ""
echo "═══════════════════════════════════════════"
echo "  🏃 RUNNING COACH APP"
echo "  Phân tích tracklog · So sánh giáo án · AI"
echo "═══════════════════════════════════════════"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
  echo "❌ Cần cài Python 3.8+"
  exit 1
fi

# Tạo thư mục cần thiết
mkdir -p plans data/groups data/athletes uploads data_backup

# Kiểm tra xem app đang chạy chưa
if [ -f ".app.pid" ]; then
  PID=$(cat .app.pid)
  if kill -0 "$PID" 2>/dev/null; then
    echo "⚠️  App đang chạy rồi (PID=$PID) tại http://localhost:5050"
    echo "   Chạy ./stop.sh trước nếu muốn restart."
    open http://localhost:5050 2>/dev/null || true
    exit 0
  else
    rm -f .app.pid
  fi
fi

# Install deps nếu chưa có (bỏ qua nếu đã có)
echo "📦 Kiểm tra dependencies..."
pip3 install flask fitparse gpxpy "pandas<2.0" anthropic \
  --trusted-host pypi.org --trusted-host files.pythonhosted.org \
  -q 2>/dev/null || true

echo ""
echo "🌐 Địa chỉ: http://localhost:5050"
echo "   Dùng ./stop.sh hoặc Ctrl+C để tắt an toàn"
echo ""

# Mở browser sau 1.5 giây (đủ để Flask khởi động)
(sleep 1.5 && open http://localhost:5050 2>/dev/null) &

python3 app.py

