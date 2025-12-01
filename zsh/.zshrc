ZSH_PLUGIN_DIR="$HOME/.zsh-plugins"
mkdir -p "$ZSH_PLUGIN_DIR"

install_plugin() {
    local repo="$1"
    local dir="$ZSH_PLUGIN_DIR/$2"
    if [[ ! -d "$dir/.git" ]]; then
        rm -rf "$dir"
        git clone --depth 1 "$repo" "$dir" >/dev/null 2>&1
    fi
}

install_plugin "https://github.com/zsh-users/zsh-syntax-highlighting.git" "zsh-syntax-highlighting"
install_plugin "https://github.com/zsh-users/zsh-autosuggestions.git" "zsh-autosuggestions"
install_plugin "https://github.com/zsh-users/zsh-completions.git" "zsh-completions"

source "$ZSH_PLUGIN_DIR/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
source "$ZSH_PLUGIN_DIR/zsh-autosuggestions/zsh-autosuggestions.zsh"
fpath=("$ZSH_PLUGIN_DIR/zsh-completions/src" $fpath)

setopt histignorealldups sharehistory auto_cd interactivecomments
bindkey -e
HISTSIZE=5000
SAVEHIST=5000
HISTFILE="$HOME/.zsh_history"

autoload -Uz compinit
ZCDUMP="$HOME/.zcompdump"
if [[ ! -f $ZCDUMP.zwc || $ZCDUMP -nt $ZCDUMP.zwc ]]; then
    compinit -d "$ZCDUMP"
    zcompile "$ZCDUMP"
else
    compinit -C -d "$ZCDUMP"
fi

zstyle ':completion:*' menu select=long-list
zstyle ':completion:*' auto-expand yes
zstyle ':completion:*' verbose yes
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'

autoload -Uz widgets
accept-or-history-up() {
    if [[ -n $ZSH_AUTOSUGGEST_BUFFER ]]; then
        zle autosuggest-accept
    else
        zle up-line-or-history
    fi
}
zle -N accept-or-history-up
bindkey '^[[A' accept-or-history-up

export PATH="$PATH:/opt/nvim-linux-x86_64/bin:$HOME/.local/bin:$HOME/.cargo/bin"
export EDITOR="nvim"
export GO111MODULE=on
export PATH="$PATH:$(go env GOPATH)/bin"

typeset -a ZSH_SHORTCUTS=(
  "works:$HOME/Documents/Works" # Replace this with your shortcut directory
  "workshops:$HOME/Documents/Workshops"
)

typeset -a ZSH_GIT_PROFILES=(
  "DEFAULT:$HOME/.github/personal_token"
)

for entry in "${ZSH_SHORTCUTS[@]}"; do
    dir="${entry#*:}"
    [[ ! -d "$dir" ]] && mkdir -p "$dir"
done

for entry in "${ZSH_GIT_PROFILES[@]}"; do
    file="${entry#*:}"
    parent="$(dirname "$file")"
    [[ ! -d "$parent" ]] && mkdir -p "$parent"
done

[[ -f "$HOME/.zsh_user_config" ]] && source "$HOME/.zsh_user_config"

cd() {
    if [[ $# -eq 1 ]]; then
        for entry in "${ZSH_SHORTCUTS[@]}"; do
            local shortcut_key="${entry%%:*}"
            local shortcut_path="${entry#*:}"
            local key_lower="${shortcut_key:l}"
            local key_upper="${shortcut_key:u}"

            if [[ "$1" == "$key_lower" || "$1" == "$key_upper" ]]; then
                builtin cd "$shortcut_path"
                return
            fi
        done
    fi
    builtin cd "$@"
}

for entry in "${ZSH_SHORTCUTS[@]}"; do
    local alias_key="${entry%%:*}"
    alias "${alias_key:l}"="cd $alias_key"
    alias "${alias_key:u}"="cd $alias_key"
done

load_dotenv() {
    if [[ -f .env ]]; then
        set -a
        source .env
        set +a
    fi
}

configure_git_auth() {
    local name="$1"
    local email="$2"
    local token="$3"
    if [[ -n "$token" ]]; then
        git config --global credential.helper store
        git config --global user.name "$name"
        git config --global user.email "$email"
        echo "https://${token}@github.com" > "$HOME/.git-credentials"
        chmod 600 "$HOME/.git-credentials"
        export GITHUB_TOKEN="$token"
    else
        git config --global --unset credential.helper 2>/dev/null || true
        rm -f "$HOME/.git-credentials"
        unset GITHUB_TOKEN
    fi
}

load_github_token() {
    local current="$PWD"
    for profile in "${ZSH_GIT_PROFILES[@]}"; do
        local name="${profile%%:*}"
        local file="${profile#*:}"
        if [[ "$current" == *"/${name}"* ]] && [[ -f "$file" ]]; then
            source "$file"
            configure_git_auth "$GIT_CONFIG_NAME" "$GIT_CONFIG_EMAIL" "$GITHUB_TOKEN"
            return
        fi
    done
    for profile in "${ZSH_GIT_PROFILES[@]}"; do
        if [[ "${profile%%:*}" == "DEFAULT" ]] && [[ -f "${profile#*:}" ]]; then
            local tok=$(tr -d '[:space:]' < "${profile#*:}")
            configure_git_auth "User" "user@example.com" "$tok"
            return
        fi
    done
}

chpwd() {
    load_github_token
    load_dotenv
}

autoload -Uz add-zsh-hook
add-zsh-hook chpwd chpwd
chpwd

autoload -Uz vcs_info
autoload -Uz colors && colors
setopt prompt_subst

zstyle ':vcs_info:git:*' formats "%F{yellow}[%b]%f"

git_changes() {
  local ua ur sa sr
  ua=$(git diff --numstat 2>/dev/null | awk '{a+=$1} END {print a+0}')
  ur=$(git diff --numstat 2>/dev/null | awk '{r+=$2} END {print r+0}')
  sa=$(git diff --cached --numstat 2>/dev/null | awk '{a+=$1} END {print a+0}')
  sr=$(git diff --cached --numstat 2>/dev/null | awk '{r+=$2} END {print r+0}')

  local msg=""

  (( sa > 0 )) && msg+="%F{green}+${sa}%f "
  (( sr > 0 )) && msg+="%F{green}-${sr}%f "
  (( ua > 0 )) && msg+="%F{blue}+${ua}%f "
  (( ur > 0 )) && msg+="%F{red}-${ur}%f "

  [[ -n $msg ]] && echo "[${msg% }]"
}

precmd() {
  vcs_info
  GIT_CHANGES=$(git_changes)
}

PROMPT='%F{cyan}%n%f %F{12}%~%f ${vcs_info_msg_0_} ${GIT_CHANGES}
%F{magenta}❯%f '
