#!/bin/bash
#
# AI Agent Skills 安装脚本
# 策略: 统一中心 ~/.agents/skills/ + 分发到各编辑器
#

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SOURCE_DIR="${SCRIPT_DIR}/skills"
AGENTS_SKILLS_DIR="${HOME}/.agents/skills"

# 格式: key:name:skills_dir
EDITORS=(
  "kimi:Kimi Code CLI:${HOME}/.config/agents/skills"
  "codex:OpenAI Codex CLI:${HOME}/.codex/skills"
  "claude:Claude Code:${HOME}/.claude/skills"
  "gemini:Gemini CLI:${HOME}/.gemini/skills"
)

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "${CYAN}[STEP]${NC} $1"; }

get_skills() {
  local skills=()
  local dir
  for dir in "${SKILLS_SOURCE_DIR}"/*; do
    [ -d "$dir" ] || continue
    local name
    name="$(basename "$dir")"
    [[ "$name" == .* ]] && continue
    skills+=("$name")
  done
  echo "${skills[@]}"
}

ensure_editor_exists() {
  local key="$1"
  local config
  for config in "${EDITORS[@]}"; do
    IFS=':' read -r editor_key _ _ <<< "$config"
    if [ "$editor_key" = "$key" ]; then
      return 0
    fi
  done
  return 1
}

create_symlink() {
  local source="$1"
  local target="$2"
  local context="$3"

  if [ ! -e "$source" ]; then
    print_error "[${context}] source not found: ${source}"
    return 1
  fi

  mkdir -p "$(dirname "$target")"
  if [ -L "$target" ]; then
    local current
    current="$(readlink "$target")"
    if [ "$current" = "$source" ]; then
      return 0
    fi
    rm -f "$target"
  elif [ -e "$target" ]; then
    local backup="${target}.bak.$(date +%s)"
    mv "$target" "$backup"
    print_warning "[${context}] existed target moved to: ${backup}"
  fi

  ln -s "$source" "$target"
}

install_to_agents() {
  local skill="$1"
  create_symlink "${SKILLS_SOURCE_DIR}/${skill}" "${AGENTS_SKILLS_DIR}/${skill}" "agents"
}

install_to_editor() {
  local skill="$1"
  local editor_name="$2"
  local editor_dir="$3"
  create_symlink "${AGENTS_SKILLS_DIR}/${skill}" "${editor_dir}/${skill}" "$editor_name"
}

uninstall_from_editor() {
  local skill="$1"
  local editor_dir="$2"
  local target="${editor_dir}/${skill}"
  if [ -L "$target" ]; then
    rm -f "$target"
  fi
}

uninstall_from_agents() {
  local skill="$1"
  local target="${AGENTS_SKILLS_DIR}/${skill}"
  if [ -L "$target" ]; then
    rm -f "$target"
  fi
}

resolve_skills() {
  local specific_skill="${1:-}"
  local all_skills
  all_skills=($(get_skills))
  if [ -n "$specific_skill" ]; then
    local found=0
    local item
    for item in "${all_skills[@]}"; do
      if [ "$item" = "$specific_skill" ]; then
        found=1
        break
      fi
    done
    if [ "$found" -ne 1 ]; then
      print_error "skill not found: ${specific_skill}"
      exit 1
    fi
    echo "$specific_skill"
    return 0
  fi
  echo "${all_skills[@]}"
}

cmd_install() {
  local specific_editor="${1:-}"
  local specific_skill="${2:-}"
  local skills

  if [ -n "$specific_editor" ] && ! ensure_editor_exists "$specific_editor"; then
    print_error "unknown editor: ${specific_editor}"
    exit 1
  fi

  skills=($(resolve_skills "$specific_skill"))
  if [ "${#skills[@]}" -eq 0 ]; then
    print_error "no skills found under ${SKILLS_SOURCE_DIR}"
    exit 1
  fi

  print_step "=== Skill 安装流程 ==="
  print_info "策略: 项目 -> ~/.agents/skills -> 各编辑器"
  echo ""

  print_step "[1/2] 安装到统一中心: ${AGENTS_SKILLS_DIR}"
  local skill
  for skill in "${skills[@]}"; do
    install_to_agents "$skill"
    print_success "✓ ${skill}"
  done
  echo ""

  print_step "[2/2] 分发到编辑器"
  local editor_cfg editor_key editor_name editor_dir
  for editor_cfg in "${EDITORS[@]}"; do
    IFS=':' read -r editor_key editor_name editor_dir <<< "$editor_cfg"
    if [ -n "$specific_editor" ] && [ "$editor_key" != "$specific_editor" ]; then
      continue
    fi
    print_info "-> ${editor_name}"
    for skill in "${skills[@]}"; do
      install_to_editor "$skill" "$editor_name" "$editor_dir"
      echo -e "  ${GREEN}✓${NC} ${skill}"
    done
  done
  echo ""

  print_success "Skill 安装完成"
}

cmd_uninstall() {
  local specific_editor="${1:-}"
  local specific_skill="${2:-}"
  local skills

  if [ -n "$specific_editor" ] && ! ensure_editor_exists "$specific_editor"; then
    print_error "unknown editor: ${specific_editor}"
    exit 1
  fi

  skills=($(resolve_skills "$specific_skill"))

  print_step "=== Skill 卸载流程 ==="
  echo ""

  print_step "[1/2] 从编辑器卸载"
  local editor_cfg editor_key editor_name editor_dir skill
  for editor_cfg in "${EDITORS[@]}"; do
    IFS=':' read -r editor_key editor_name editor_dir <<< "$editor_cfg"
    if [ -n "$specific_editor" ] && [ "$editor_key" != "$specific_editor" ]; then
      continue
    fi
    print_info "-> ${editor_name}"
    for skill in "${skills[@]}"; do
      uninstall_from_editor "$skill" "$editor_dir"
      echo -e "  ${GREEN}✓${NC} ${skill}"
    done
  done
  echo ""

  if [ -z "$specific_editor" ]; then
    print_step "[2/2] 从统一中心卸载"
    for skill in "${skills[@]}"; do
      uninstall_from_agents "$skill"
      print_success "✓ ${skill}"
    done
  else
    print_step "[2/2] 跳过统一中心（仅卸载指定编辑器）"
  fi
  echo ""
  print_success "Skill 卸载完成"
}

cmd_status() {
  local skills
  skills=($(get_skills))

  print_step "=== Skill 安装状态 ==="
  echo ""
  print_info "统一中心: ${AGENTS_SKILLS_DIR}"
  printf "  %-35s %s\n" "Skill" "State"
  printf "  %-35s %s\n" "-----" "-----"

  local skill target
  for skill in "${skills[@]}"; do
    target="${AGENTS_SKILLS_DIR}/${skill}"
    if [ -L "$target" ]; then
      printf "  %-35s ${GREEN}%s${NC}\n" "$skill" "linked"
    elif [ -e "$target" ]; then
      printf "  %-35s ${YELLOW}%s${NC}\n" "$skill" "local"
    else
      printf "  %-35s ${RED}%s${NC}\n" "$skill" "missing"
    fi
  done
  echo ""

  print_info "编辑器分发状态"
  printf "  %-35s " "Skill"
  local editor_cfg editor_key editor_name editor_dir editor_keys=()
  for editor_cfg in "${EDITORS[@]}"; do
    IFS=':' read -r editor_key editor_name editor_dir <<< "$editor_cfg"
    editor_keys+=("$editor_key")
    printf "%-10s " "$editor_key"
  done
  echo ""
  printf "  %-35s " "-----"
  local key
  for key in "${editor_keys[@]}"; do
    printf "%-10s " "----"
  done
  echo ""

  local cell
  for skill in "${skills[@]}"; do
    printf "  %-35s " "$skill"
    for editor_cfg in "${EDITORS[@]}"; do
      IFS=':' read -r editor_key editor_name editor_dir <<< "$editor_cfg"
      target="${editor_dir}/${skill}"
      if [ -L "$target" ]; then
        cell="✓"
      elif [ -e "$target" ]; then
        cell="!"
      else
        cell="✗"
      fi
      printf "%-10s " "$cell"
    done
    echo ""
  done
  echo ""
  echo "图例: ✓=linked  !=local  ✗=missing"
}

show_help() {
  cat <<EOF
Skill 安装脚本（仅 skill 分发，不安装 CLI）
策略: 项目 skills/ -> ~/.agents/skills/ -> 各编辑器

用法:
  ./install_skill.sh <command> [editor] [skill]

命令:
  install [editor] [skill]    安装 Skill
  uninstall [editor] [skill]  卸载 Skill
  status                      查看安装状态
  help                        显示帮助

编辑器:
  kimi | codex | claude | gemini

示例:
  ./install_skill.sh install
  ./install_skill.sh install codex
  ./install_skill.sh install codex yunxiao-workflow
  ./install_skill.sh uninstall
  ./install_skill.sh status
EOF
}

main() {
  local cmd="${1:-help}"
  shift || true
  case "$cmd" in
    install)
      cmd_install "$@"
      ;;
    uninstall|remove)
      cmd_uninstall "$@"
      ;;
    status)
      cmd_status
      ;;
    help|--help|-h)
      show_help
      ;;
    *)
      print_error "unknown command: ${cmd}"
      show_help
      exit 1
      ;;
  esac
}

main "$@"
