#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="yunxiao-workflow"
SKILL_SOURCE="${SCRIPT_DIR}/skills/${SKILL_NAME}"
AGENTS_SKILLS_DIR="${HOME}/.agents/skills"
EDITORS=(
    "${HOME}/.config/agents/skills"
    "${HOME}/.codex/skills"
    "${HOME}/.claude/skills"
    "${HOME}/.gemini/skills"
)

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

link_skill() {
    local source="$1"
    local target="$2"

    mkdir -p "$(dirname "$target")"
    if [ -L "$target" ] || [ -e "$target" ]; then
        rm -rf "$target"
    fi
    ln -s "$source" "$target"
}

PYTHON_BIN="$(find_python)"

echo "[1/2] install python package"
"${PYTHON_BIN}" -m pip install -e "${SCRIPT_DIR}"

echo "[2/2] install skill"
link_skill "${SKILL_SOURCE}" "${AGENTS_SKILLS_DIR}/${SKILL_NAME}"
for editor_dir in "${EDITORS[@]}"; do
    link_skill "${AGENTS_SKILLS_DIR}/${SKILL_NAME}" "${editor_dir}/${SKILL_NAME}"
done

echo "done"
echo "yunxiao_cli --help"
