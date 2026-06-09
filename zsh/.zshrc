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
export PATH=/usr/local/bin:$PATH

typeset -a ZSH_SHORTCUTS=(
  "works:$HOME/Documents/Works" # Replace this with your shortcut directory
  "workshops:$HOME/Documents/Workshops"
)

typeset -a ZSH_GIT_PROFILES=(
  "Works/BVT:$HOME/.github/bvt_token"
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
        # Use global helper but project-specific user configurations
        git config --global credential.helper store
        git config --local user.name "$name"
        git config --local user.email "$email"
        
        # arxngr is passed explicitly here to satisfy the HTTPS remote request
        echo "https://arxngr:${token}@github.com" > "$HOME/.git-credentials"
        chmod 600 "$HOME/.git-credentials"
        export GITHUB_TOKEN="$token"
    else
        git config --local --unset user.name 2>/dev/null || true
        git config --local --unset user.email 2>/dev/null || true
        rm -f "$HOME/.git-credentials"
        unset GITHUB_TOKEN
    fi
}

load_github_token() {
    local current="$PWD"
    
    # Check if inside a Git repository before wasting cycles
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        return
    fi
    
    # 1. Check for specific matches first (BVT, etc.)
    for profile in "${ZSH_GIT_PROFILES[@]}"; do
        local match_path="${profile%%:*}"
        local file="${profile#*:}"
        
        [[ "$match_path" == "DEFAULT" ]] && continue
        
        if [[ "$current" == *"$match_path"* ]] && [[ -f "$file" ]]; then
            local tok=$(tr -d '[:space:]' < "$file")
            # Set your WORK specific Git Identity here
            configure_git_auth "Ardi Nugraha" "0x4rd1@gmail.com" "$tok"
            return
        fi
    done

    # 2. Fallback to DEFAULT if no specific folder matched
    for profile in "${ZSH_GIT_PROFILES[@]}"; do
        if [[ "${profile%%:*}" == "DEFAULT" ]] && [[ -f "${profile#*:}" ]]; then
            # Read the raw token from the file
            local tok=$(tr -d '[:space:]' < "${profile#*:}")
            configure_git_auth "Ardi Nugraha" "0x4rd1@gmail.com" "$tok"
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

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# opencode
export PATH=/home/ardinugraha/.opencode/bin:$PATH
