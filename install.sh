#!/bin/bash
#
# 安装 Yunxiao CLI（仅 CLI，不包含 skill 分发）
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return 0
  fi
  echo "python3 is required" >&2
  return 1
}

PYTHON_BIN="$(find_python)"

echo "[1/1] install yunxiao_cli package"
"${PYTHON_BIN}" -m pip install -e "${SCRIPT_DIR}"

echo "done"
echo "yunxiao_cli --help"
echo ""
echo "需要安装 skill 请执行:"
echo "  ./install_skill.sh install"
