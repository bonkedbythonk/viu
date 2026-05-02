#!/usr/bin/env bash
APP_DIR="$(
  cd -- "$(dirname "$0")" >/dev/null 2>&1
  pwd -P
)"

# fish shell completions
_ANICAT_COMPLETE=fish_source anicat >"$APP_DIR/completions/anicat.fish"

# zsh completions
_ANICAT_COMPLETE=zsh_source anicat >"$APP_DIR/completions/anicat.zsh"

# bash completions
_ANICAT_COMPLETE=bash_source anicat >"$APP_DIR/completions/anicat.bash"
