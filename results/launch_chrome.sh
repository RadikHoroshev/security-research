#!/bin/bash
# Launch Chrome with remote debugging enabled
# This script opens Chrome so Playwright can connect to it

echo "============================================================"
echo "Launching Google Chrome with Remote Debugging"
echo "============================================================"
echo ""
echo "Chrome will open in a special mode that allows automation."
echo ""
echo "IMPORTANT:"
echo "  - Do NOT close this terminal while using Chrome"
echo "  - After Chrome opens, go to: https://huntr.com/login"
echo "  - Log in to your account"
echo "  - Then run: python3 save_huntr_cookies.py"
echo ""
echo "Press ENTER to launch Chrome..."
read

# Launch Chrome with debugging port
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-session \
  &

echo ""
echo "============================================================"
echo "Chrome is launching..."
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Wait for Chrome to open"
echo "  2. Go to https://huntr.com/login"
echo "  3. Log in with your credentials"
echo "  4. In another terminal, run: python3 save_huntr_cookies.py"
echo ""
echo "Keep this terminal open while using Chrome!"
echo ""
