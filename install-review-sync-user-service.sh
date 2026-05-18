#!/usr/bin/env bash
# install-review-sync-user-service.sh - installe le watcher user systemd de sync review
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_FILE="${REPO_DIR}/systemd/dict-ai-coding-review-sync-watch.service"
USER_SYSTEMD_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/systemd/user"
TARGET_FILE="${USER_SYSTEMD_DIR}/dict-ai-coding-review-sync-watch.service"
ENABLE_NOW=0

if [[ $# -gt 0 ]]; then
    case "$1" in
        --enable-now)
            ENABLE_NOW=1
            ;;
        *)
            echo "Usage: bash install-review-sync-user-service.sh [--enable-now]"
            exit 1
            ;;
    esac
fi

if [[ ! -f "$TEMPLATE_FILE" ]]; then
    echo "ERREUR: template absent: $TEMPLATE_FILE"
    exit 1
fi

mkdir -p "$USER_SYSTEMD_DIR"
sed -e "s#{{REPO_DIR}}#${REPO_DIR}#g" "$TEMPLATE_FILE" > "$TARGET_FILE"
chmod 0644 "$TARGET_FILE"

systemctl --user daemon-reload
echo "[OK] Installe: $TARGET_FILE"
echo "[OK] systemctl --user daemon-reload"

if (( ENABLE_NOW )); then
    systemctl --user enable --now dict-ai-coding-review-sync-watch.service
    echo "[OK] Active: dict-ai-coding-review-sync-watch.service"
else
    cat <<EOF

Etapes suivantes:
  systemctl --user enable --now dict-ai-coding-review-sync-watch.service
  systemctl --user status dict-ai-coding-review-sync-watch.service --no-pager
EOF
fi
