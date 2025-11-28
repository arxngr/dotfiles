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

autoload -Uz vcs_info
precmd() { vcs_info }
autoload -Uz colors && colors
setopt prompt_subst
zstyle ':vcs_info:*' enable git
zstyle ':vcs_info:git:*' formats '%F{yellow}[%b]%f'
PROMPT='%F{cyan}%n%f %F{12}%~%f ${vcs_info_msg_0_}
%F{magenta}❯%f '

ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=8'

typeset -a ZSH_SHORTCUTS=(
  "works:$HOME/Documents/Works" # Replace this with your shortcut directory
  "workshops:$HOME/Documents/Workshops"
)

typeset -a ZSH_GIT_PROFILES=(
  "BVT:$HOME/.github/bvt_token" # Replace this with your git token 
  "DEFAULT:$HOME/.github/default_token"
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
    for entry in "${ZSH_SHORTCUTS[@]}"; do
        local key="${entry%%:*}"
        local path="${entry#*:}"
        if [[ "$1" =~ ^([${key^}${key}])$ ]]; then
            builtin cd "$path"
            return
        fi
    done
    builtin cd "$@"
}

for entry in "${ZSH_SHORTCUTS[@]}"; do
    key="${entry%%:*}"
    alias "$key"="cd $key"
    alias "${key^}"="cd $key"
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
    
    # This is for default token that mean your personal token
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
