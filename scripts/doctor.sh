#!/usr/bin/env bash
set -euo pipefail
printf 'GoreeCloud Projects developer prerequisites\n'
for tool in python3 node npm git cargo rustc java; do
  if command -v "$tool" >/dev/null; then
    printf '  %-8s %s\n' "$tool" "$(command -v "$tool")"
  else
    printf '  %-8s missing\n' "$tool"
  fi
done
if [[ -n "${ANDROID_HOME:-}" ]]; then
  printf '  ANDROID_HOME %s\n' "$ANDROID_HOME"
else
  printf '  ANDROID_HOME not configured\n'
fi
printf '  No services started; no secrets accessed.\n'
