#!/bin/bash
# stop.sh – tắt Running Coach App an toàn

PID_FILE="$(dirname "$0")/.app.pid"

echo ""
echo "⏹  Đang tắt Running Coach App..."

if [ ! -f "$PID_FILE" ]; then
  echo "⚠️  Không tìm thấy .app.pid — thử tìm process..."
  PID=$(lsof -ti :5050 2>/dev/null)
  if [ -z "$PID" ]; then
    echo "✅ App không đang chạy."
    exit 0
  fi
else
  PID=$(cat "$PID_FILE")
fi

# Gửi SIGTERM để app tự backup rồi tắt
if kill -TERM "$PID" 2>/dev/null; then
  echo "   Đợi app lưu dữ liệu..."
  sleep 2
  # Nếu vẫn còn chạy thì force kill
  if kill -0 "$PID" 2>/dev/null; then
    kill -9 "$PID" 2>/dev/null
    echo "⚠️  Buộc tắt (force kill)."
  fi
  rm -f "$PID_FILE"
  echo "✅ Đã tắt. Dữ liệu được backup trong thư mục data_backup/"
else
  echo "⚠️  Không tìm thấy process PID=$PID"
  rm -f "$PID_FILE"
fi
echo ""
