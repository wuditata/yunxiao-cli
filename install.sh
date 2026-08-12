#!/bin/bash
#
# 安装 Yunxiao CLI 和 Skill
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

echo "[1/2] install yunxiao package"
"${PYTHON_BIN}" -m pip install -e "${SCRIPT_DIR}"

echo "[2/2] install yunxiao skill"
bash "${SCRIPT_DIR}/install_skill.sh" install

echo "done"
echo "yunxiao --help"
echo "legacy command remains available:"
echo "  yunxiao_cli --help"
