#!/bin/zsh
set -euo pipefail

cd "$(dirname "$0")"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This build script must be run on macOS."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 was not found. Install Python 3 first, then run this script again."
  exit 1
fi

if ! python3 -m pip --version >/dev/null 2>&1; then
  echo "pip was not found. Trying to enable it with ensurepip..."
  python3 -m ensurepip --upgrade
fi

python3 -m pip install --upgrade pyinstaller

python3 -m PyInstaller \
  --windowed \
  --name DST-Zhipu-Proxy \
  --paths proxy \
  --distpath dist-macos \
  --workpath build-macos \
  --specpath build-macos \
  proxy/zhipu_proxy_gui.py

echo
echo "Build complete: dist-macos/DST-Zhipu-Proxy.app"
echo "Keep this app open while hosting the DST world."

if [[ -t 0 ]]; then
  echo
  read "reply?Press Enter to close this window..."
fi
