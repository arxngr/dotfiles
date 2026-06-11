#!/usr/bin/env python3
"""
Ardi Nugraha dotfiles installer
Installs: dev deps, zsh + plugins, kitty + session manager, neovim + pena.Vim,
          JetBrainsMono Nerd Font, gridflux, and workspace directories.

Usage:
    python3 install.py            # full install
    python3 install.py --dry-run  # preview without changes
    python3 install.py --skip font zsh
    python3 install.py --update kitty zsh
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

DOTFILES_DIR  = Path(__file__).parent.resolve()
PENA_VIM_REPO = "https://github.com/arxngr/pena.Vim"
GRIDFLUX_REPO = "https://github.com/arxngr/gridflux"
GRIDFLUX_API  = "https://api.github.com/repos/arxngr/gridflux/releases/latest"

FONT_URL = (
    "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/"
    "JetBrainsMono.zip"
)

ZSH_PLUGINS = {
    "zsh-autosuggestions":          "https://github.com/zsh-users/zsh-autosuggestions",
    "zsh-syntax-highlighting":      "https://github.com/zsh-users/zsh-syntax-highlighting",
    "zsh-history-substring-search": "https://github.com/zsh-users/zsh-history-substring-search",
}

BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
RESET  = "\033[0m"

DRY_RUN = False
UPDATE  = False
OS      = platform.system()  # "Linux" | "Darwin" | "Windows"


def log(msg, color=CYAN):
    print(f"{color}{BOLD}==> {RESET}{color}{msg}{RESET}")

def ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")

def skip(msg):
    print(f"  {YELLOW}↷{RESET} {msg} (already installed, skipping)")

def warn(msg):
    print(f"  {YELLOW}⚠{RESET}  {msg}")

def err(msg):
    print(f"  {RED}✗{RESET} {msg}", file=sys.stderr)

def download_with_progress(url, dest_path: Path, description="Downloading"):
    req = urllib.request.Request(url, headers={"User-Agent": "dotfiles-installer"})
    with urllib.request.urlopen(req) as response:
        total_size = int(response.info().get("Content-Length", 0))
        block_size = 8192
        downloaded = 0
        with open(dest_path, "wb") as f:
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                f.write(buffer)
                if total_size > 0:
                    percent = int(downloaded * 100 / total_size)
                    bar_len = 30
                    filled  = int(bar_len * downloaded // total_size)
                    bar     = "█" * filled + "░" * (bar_len - filled)
                    sys.stdout.write(f"\r  {CYAN}{description}{RESET} [{bar}] {percent}%")
                else:
                    sys.stdout.write(f"\r  {CYAN}{description}{RESET} {downloaded // 1024} KB…")
                sys.stdout.flush()
    print()

def run(cmd, check=True, capture=False, **kwargs):
    display = cmd if isinstance(cmd, str) else " ".join(str(c) for c in cmd)
    if DRY_RUN:
        print(f"  [dry-run] {display}")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    subprocess_args = {
        "check": check,
        "capture_output": capture,
        "text": True,
        "shell": isinstance(cmd, str),
    }
    subprocess_args.update(kwargs)
    return subprocess.run(cmd, **subprocess_args)

def cmd_exists(name):
    return shutil.which(name) is not None

def ensure_dir(path: Path):
    if not DRY_RUN:
        path.mkdir(parents=True, exist_ok=True)

def clone_or_skip(url, dest: Path, name=""):
    name = name or dest.name
    if dest.exists():
        skip(f"{name} already cloned at {dest}")
        return False
    log(f"Cloning {name}")
    run(["git", "clone", "--depth=1", url, str(dest)])
    ok(f"Cloned {name}")
    return True

def symlink_config(src_relative: str, dest: Path, required=True):
    """
    Create a symlink: dest -> src (inside DOTFILES_DIR).

    Guards:
    - src does not exist          → warn/skip
    - src and dest are same path  → skip (would be self-referential)
    - dest is already the correct symlink → skip
    - dest exists (file/dir/bad symlink)  → back it up then re-link
    """
    src   = (DOTFILES_DIR / src_relative).resolve()
    label = dest.name

    if DRY_RUN:
        print(f"  [dry-run] symlink {dest} → {src}")
        return

    # Source must exist in the dotfiles repo
    if not src.exists():
        (warn if required else lambda m: warn(m + " (optional)"))(
            f"{label}: source not found at {src}"
        )
        return

    # Guard: dest would point to itself (src IS dest — same resolved path)
    try:
        if src.resolve() == dest.resolve():
            skip(f"{label} (source and destination are the same path)")
            return
    except OSError:
        pass

    # Guard: dest is already a correct symlink pointing to src
    if dest.is_symlink():
        try:
            if dest.resolve() == src.resolve():
                skip(f"{label} symlink already correct")
                return
        except OSError:
            pass
        # Wrong/dangling symlink — remove it
        warn(f"Removing stale symlink: {dest}")
        dest.unlink()

    # Guard: dest exists as a real file/dir — back it up
    elif dest.exists():
        # Make sure backup doesn't land inside DOTFILES_DIR
        backup = dest.with_name(dest.name + ".bak")
        try:
            shutil.move(str(dest), backup)
            warn(f"Backed up existing {label} → {backup.name}")
        except Exception as e:
            err(f"Could not back up {dest}: {e}")
            return

    ensure_dir(dest.parent)
    try:
        os.symlink(src, dest)
        ok(f"Linked {dest} → {src}")
    except OSError as e:
        err(f"Failed to symlink {label}: {e}")


def detect_pkg_manager():
    for pm in ("brew", "apt-get", "apt", "dnf", "pacman", "zypper"):
        if cmd_exists(pm):
            return pm
    return None

def pkg_install(packages: list, pkg_manager=None):
    pm = pkg_manager or detect_pkg_manager()
    if pm is None:
        warn("No supported package manager found. Install manually: " + ", ".join(packages))
        return
    cmd_map = {
        "brew":    ["brew", "install"] + packages,
        "apt-get": ["sudo", "apt-get", "install", "-y"] + packages,
        "apt":     ["sudo", "apt",     "install", "-y"] + packages,
        "dnf":     ["sudo", "dnf",     "install", "-y"] + packages,
        "pacman":  ["sudo", "pacman",  "-S", "--noconfirm"] + packages,
        "zypper":  ["sudo", "zypper",  "install", "-y"] + packages,
    }
    run(cmd_map[pm])

def require_git():
    log("Checking git")
    if not cmd_exists("git"):
        err("git is not installed.")
        if OS == "Windows":
            err("Download from https://git-scm.com/download/win")
        else:
            pkg_install(["git"])
    ok("git found")

def fetch_latest_gridflux_asset(asset_keyword: str):
    if DRY_RUN:
        print(f"  [dry-run] Fetch {GRIDFLUX_API}")
        return "v0.0.0-dry-run", f"https://example.com/gridflux-{asset_keyword}.fake"
    try:
        req = urllib.request.Request(GRIDFLUX_API, headers={"User-Agent": "dotfiles-installer"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        version = data.get("tag_name", "unknown")
        for asset in data.get("assets", []):
            if asset_keyword.lower() in asset.get("name", "").lower():
                return version, asset["browser_download_url"]
        return version, None
    except Exception as e:
        warn(f"Could not fetch gridflux release info: {e}")
        return None, None


def install_dev_deps():
    log("Developer dependencies")

    if OS == "Windows":
        warn("On Windows: install deps via winget, scoop, or choco manually.")
        warn("  Required: cmake, gcc (MinGW), clang, golang, python3, nodejs")
        return

    pm = detect_pkg_manager()
    if pm is None:
        warn("No package manager detected. Install deps manually.")
        return

    dep_map = {
        "brew": {
            "cmake": "cmake", "go": "go", "clang": "llvm",
            "gcc": "gcc", "python3": "python@3", "node": "node",
        },
        "apt-get": {
            "cmake": "cmake", "go": "golang-go", "clang": "clang",
            "clangd": "clangd", "gcc": "gcc", "python3": "python3",
            "node": "nodejs", "npm": "npm",
        },
        "apt": {
            "cmake": "cmake", "go": "golang-go", "clang": "clang",
            "clangd": "clangd", "gcc": "gcc", "python3": "python3",
            "node": "nodejs", "npm": "npm",
        },
        "dnf": {
            "cmake": "cmake", "go": "golang", "clang": "clang",
            "clangd": "clang-tools-extra", "gcc": "gcc", "python3": "python3",
            "node": "nodejs", "npm": "npm",
        },
        "pacman": {
            "cmake": "cmake", "go": "go", "clang": "clang",
            "clangd": "clang", "gcc": "gcc", "python3": "python",
            "node": "nodejs", "npm": "npm",
        },
        "zypper": {
            "cmake": "cmake", "go": "go", "clang": "clang",
            "clangd": "clang", "gcc": "gcc", "python3": "python3",
            "node": "nodejs", "npm": "npm",
        },
    }

    tools    = dep_map.get(pm, {})
    checks   = {
        "cmake": "cmake", "go": "go", "clang": "clang", "clangd": "clangd",
        "gcc": "gcc", "python3": "python3", "node": "node", "npm": "npm",
    }
    to_install = []
    for label, binary in checks.items():
        if cmd_exists(binary):
            skip(label)
        else:
            pkg = tools.get(label)
            if pkg and pkg not in to_install:
                to_install.append(pkg)
                log(f"Will install {label} ({pkg})")

    if to_install:
        log(f"Installing: {' '.join(to_install)}")
        pkg_install(to_install, pm)
        ok("Developer dependencies installed")
    else:
        ok("All developer dependencies already present")


def install_font():
    log("JetBrainsMono Nerd Font")

    if OS == "Darwin":
        font_dir = Path.home() / "Library/Fonts"
    elif OS == "Linux":
        font_dir = Path.home() / ".local/share/fonts"
    elif OS == "Windows":
        font_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts"
    else:
        warn(f"Unknown OS '{OS}', skipping font install")
        return

    if font_dir.exists():
        for f in font_dir.iterdir():
            n = f.name.lower()
            if "jetbrains" in n and ("nerd" in n or "nf" in n):
                skip("JetBrainsMono Nerd Font")
                return

    ensure_dir(font_dir)
    if DRY_RUN:
        print(f"  [dry-run] Download {FONT_URL} → {font_dir}")
        ok("Font installed (dry-run)")
        return

    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "JetBrainsMono.zip"
        try:
            download_with_progress(FONT_URL, zip_path, "Downloading JetBrainsMono Nerd Font")
        except Exception as e:
            err(f"Failed to download font: {e}")
            return
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                if member.endswith((".ttf", ".otf")) and ("NF" in member or "Nerd" in member):
                    zf.extract(member, tmp)
                    shutil.copy(Path(tmp) / member, font_dir / Path(member).name)

    if OS == "Linux":
        run(["fc-cache", "-f", "-v"], check=False)
    elif OS == "Windows":
        warn("Font files copied. You may need to right-click → 'Install for all users'.")
    ok("JetBrainsMono Nerd Font installed")


def install_zsh():
    log("Zsh")

    if OS == "Windows":
        warn("Zsh on Windows requires WSL. Skipping native zsh install.")
        return

    if not cmd_exists("zsh"):
        pkg_install(["zsh"])
        ok("zsh installed")
    else:
        skip("zsh")

    zsh_path     = shutil.which("zsh")
    current_shell = os.environ.get("SHELL", "")
    if zsh_path and zsh_path not in current_shell:
        run(["chsh", "-s", zsh_path], check=False)
        ok(f"Default shell set to {zsh_path}")
    else:
        skip("Default shell already zsh")

    omz_dir = Path.home() / ".oh-my-zsh"
    if omz_dir.exists():
        skip("oh-my-zsh")
    else:
        log("Installing oh-my-zsh")
        if not DRY_RUN:
            run('sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended')
        ok("oh-my-zsh installed")

    custom_dir = Path.home() / ".oh-my-zsh/custom/plugins"
    ensure_dir(custom_dir)
    for plugin, url in ZSH_PLUGINS.items():
        clone_or_skip(url, custom_dir / plugin, plugin)

    clone_or_skip(
        "https://github.com/romkatv/powerlevel10k",
        Path.home() / ".oh-my-zsh/custom/themes/powerlevel10k",
        "powerlevel10k",
    )

    symlink_config("zsh/.zshrc",    Path.home() / ".zshrc")
    symlink_config("zsh/.p10k.zsh", Path.home() / ".p10k.zsh", required=False)


def install_neovim():
    log("Neovim")

    if not cmd_exists("nvim"):
        if OS == "Darwin":
            pkg_install(["neovim"], "brew")
        elif OS == "Linux":
            _install_nvim_linux()
        elif OS == "Windows":
            warn("Install neovim from https://github.com/neovim/neovim/releases then re-run.")
            return
        ok("neovim installed")
    else:
        skip("neovim")

    nvim_config = Path.home() / ".config/nvim"
    if nvim_config.exists() and any(nvim_config.iterdir()):
        skip(f"nvim config at {nvim_config}")
    else:
        log("Installing pena.Vim")
        if nvim_config.exists():
            shutil.rmtree(nvim_config)
        run(["git", "clone", "--depth=1", PENA_VIM_REPO, str(nvim_config)])
        ok("pena.Vim cloned to ~/.config/nvim")

def _install_nvim_linux():
    nvim_bin = Path.home() / ".local/bin/nvim"
    if nvim_bin.exists():
        skip("nvim binary")
        return
    ensure_dir(nvim_bin.parent)
    url = "https://github.com/neovim/neovim/releases/latest/download/nvim-linux-x86_64.tar.gz"
    if DRY_RUN:
        print(f"  [dry-run] Download {url}")
        return
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "nvim.tar.gz"
        try:
            download_with_progress(url, archive, "Downloading Neovim")
        except Exception as e:
            err(f"Failed to download Neovim: {e}")
            return
        run(["tar", "-xzf", str(archive), "-C", tmp])
        extracted = next(Path(tmp).glob("nvim-linux*"), None)
        if extracted:
            run(f"cp -r {extracted}/. {Path.home() / '.local'}/")
    ok("neovim installed to ~/.local/bin/nvim")


def install_terminal():
    """Terminal Emulator Chooser Menu"""
    log("Terminal Emulator Setup")
    if OS == "Windows":
        warn("Terminal choices are managed natively or via WSL on Windows. Skipping.")
        return

    print(f"\n{BOLD}{CYAN}Select your preferred terminal emulator to configure:{RESET}")
    print("  1) Kitty (GPU-accelerated, includes Session Architecture)")
    print("  2) WezTerm (Lua-configurable, includes automatic directory Symlinking)")
    
    try:
        choice = input(f"\n  {BOLD}Choose terminal option (1 or 2): {RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        err("Terminal installation step aborted by user.")
        return

    if choice == "1":
        _setup_kitty()
    elif choice == "2":
        _setup_wezterm()
    else:
        warn("Invalid or empty choice selected. Skipping terminal setup step entirely.")


def _setup_wezterm():
    log("WezTerm Terminal")
    if cmd_exists("wezterm"):
        skip("wezterm binary")
    else:
        pm = detect_pkg_manager()
        if pm == "brew":
            run(["brew", "install", "--cask", "wezterm"])
        elif pm in ("apt", "apt-get"):
            log("Adding official WezTerm apt repository...")
            try:
                # Add the GPG key and add the repository source line
                run("curl -fsSL https://apt.fury.io/wez/gpg.key | sudo gpg --yes --dearmor -o /usr/share/keyrings/wezterm-fury.gpg")
                run("echo 'deb [signed-by=/usr/share/keyrings/wezterm-fury.gpg] https://apt.fury.io/wez/ * *' | sudo tee /etc/apt/sources.list.d/wezterm.list")
                # Refresh local apt caches
                run(["sudo", "apt-get", "update"])
                # Install the package safely
                pkg_install(["wezterm"], pm)
            except Exception as e:
                err(f"Failed to bootstrap WezTerm repository: {e}")
                warn("Please install WezTerm manually from https://wezfurlong.org/wezterm/install/linux.html")
                return
        elif pm in ("dnf", "pacman", "zypper"):
            pkg_install(["wezterm"])
        else:
            warn("No supported package manager found to automate WezTerm. Install manually.")
            return
        ok("wezterm binary installed")

    wezterm_config_dir = Path.home() / ".config/wezterm"
    ensure_dir(wezterm_config_dir)

    log("Configuring WezTerm environment target via symlink_config Engine")
    # Links your source `.wezterm.lua` to the exact name WezTerm expects inside .config
    symlink_config("wezterm/.wezterm.lua", wezterm_config_dir / "wezterm.lua")


def _setup_kitty():
    log("Kitty Terminal")
    if not cmd_exists("kitty"):
        run("curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin")
        ok("kitty installed")
    else:
        skip("kitty")

    kitty_config_dir = Path.home() / ".config/kitty"
    ensure_dir(kitty_config_dir)

    symlink_config("kitty/kitty.conf",        kitty_config_dir / "kitty.conf")
    symlink_config("kitty/kitty-colors.conf", kitty_config_dir / "kitty-colors.conf", required=False)

    _patch_kitty_conf(kitty_config_dir / "kitty.conf")
    _install_kitty_session(kitty_config_dir)

def _patch_kitty_conf(conf_path: Path):
    """Patch kitty.conf via the real file, even if conf_path is a symlink."""
    # Resolve to the actual file so we edit the source in dotfiles, not a copy
    if conf_path.is_symlink():
        real_path = conf_path.resolve()
    else:
        real_path = conf_path

    if DRY_RUN or not real_path.exists():
        return

    content = real_path.read_text()
    changed = False

    listen_line = "listen_on unix:/tmp/kitty-{kitty_pid}.sock"
    if "listen_on" not in content:
        content += f"\n# Session auto-save (added by installer)\n{listen_line}\n"
        changed = True

    if "allow_remote_control" not in content:
        content += "allow_remote_control socket-only\n"
        changed = True
    elif "allow_remote_control yes" in content:
        content = content.replace("allow_remote_control yes", "allow_remote_control socket-only")
        changed = True

    if changed:
        real_path.write_text(content)
        ok("Patched kitty.conf with session directives")
    else:
        skip("kitty.conf session directives already present")

def _install_kitty_session(kitty_dir: Path):
    log("kitty-save-session")
    session_dir = Path.home() / ".local/share/kitty-sessions"
    ensure_dir(session_dir)

    base_url = "https://raw.githubusercontent.com/dflock/kitty-save-session/main/"
    scripts  = [
        "kitty-convert-dump.py",
        "kitty-save-session-all.sh",
        "kitty-save-session-common.incl",
    ]
    for script in scripts:
        dest = kitty_dir / script
        if dest.exists():
            skip(script)
            continue
        if DRY_RUN:
            print(f"  [dry-run] Download {base_url + script} → {dest}")
            continue
        try:
            download_with_progress(base_url + script, dest, f"Fetching {script}")
        except Exception as e:
            warn(f"Could not download {script}: {e}")

    for name, mode in [("kitty-save-session-all.sh", 0o755), ("kitty-convert-dump.py", 0o755)]:
        p = kitty_dir / name
        if not DRY_RUN and p.exists():
            p.chmod(mode)

    wrapper = Path.home() / ".local/bin/kitty-session"
    ensure_dir(wrapper.parent)
    if not wrapper.exists():
        if not DRY_RUN:
            wrapper.write_text(
                "#!/usr/bin/env bash\n"
                f'SESSION_FILE=$(ls -t "{session_dir}"/*.kitty 2>/dev/null | head -1)\n'
                'if [[ -n "$SESSION_FILE" ]]; then\n'
                '    exec kitty --session "$SESSION_FILE" "$@"\n'
                'else\n'
                '    exec kitty "$@"\n'
                'fi\n'
            )
            wrapper.chmod(0o755)
        ok("kitty-session wrapper → ~/.local/bin/kitty-session")
    else:
        skip("kitty-session wrapper")

    if OS == "Linux" and cmd_exists("systemctl"):
        _setup_systemd_kitty_timer(kitty_dir, session_dir)
    elif OS == "Darwin":
        _setup_launchd_kitty_timer(kitty_dir, session_dir)
    else:
        warn("Auto-save timer not set up. Run kitty-save-session-all.sh manually.")

def _setup_systemd_kitty_timer(kitty_dir: Path, session_dir: Path):
    sd  = Path.home() / ".config/systemd/user"
    svc = sd / "kitty-session-save.service"
    tmr = sd / "kitty-session-save.timer"
    if svc.exists() and tmr.exists() and not UPDATE:
        skip("systemd kitty-session timer")
        return
    if UPDATE:
        run(["systemctl", "--user", "disable", "--now", "kitty-session-save.timer"], check=False)
    ensure_dir(sd)
    if not DRY_RUN:
        svc.write_text(
            "[Unit]\nDescription=Save kitty session\n\n"
            "[Service]\nType=oneshot\n"
            f"Environment=PATH={Path.home()}/.local/bin:/usr/local/bin:/usr/bin:/bin\n"
            f"Environment=KITTY_SESSION_SAVE_DIR={session_dir}\n"
            "Environment=KITTY_SESSION_SAVE_OPTS=--no-copy-env\n"
            f"ExecStart={kitty_dir}/kitty-save-session-all.sh\n"
        )
        tmr.write_text(
            "[Unit]\nDescription=Auto-save kitty session every 60s\n\n"
            "[Timer]\nOnBootSec=30s\nOnUnitActiveSec=60s\n\n"
            "[Install]\nWantedBy=timers.target\n"
        )
        run(["systemctl", "--user", "daemon-reload"], check=False)
        run(["systemctl", "--user", "enable", "--now", "kitty-session-save.timer"], check=False)
    ok("systemd kitty-session timer enabled")

def _setup_launchd_kitty_timer(kitty_dir: Path, session_dir: Path):
    plist_dir = Path.home() / "Library/LaunchAgents"
    plist     = plist_dir / "com.kitty.session-save.plist"
    if plist.exists() and not UPDATE:
        skip("launchd kitty-session agent")
        return
    if UPDATE:
        run(["launchctl", "unload", str(plist)], check=False)
    ensure_dir(plist_dir)
    if not DRY_RUN:
        plist.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"\n'
            '  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0"><dict>\n'
            '  <key>Label</key><string>com.kitty.session-save</string>\n'
            '  <key>ProgramArguments</key><array>\n'
            f'    <string>{kitty_dir}/kitty-save-session-all.sh</string>\n'
            '  </array>\n'
            '  <key>EnvironmentVariables</key><dict>\n'
            '    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>\n'
            f'    <key>KITTY_SESSION_SAVE_DIR</key><string>{session_dir}</string>\n'
            '    <key>KITTY_SESSION_SAVE_OPTS</key><string>--no-copy-env</string>\n'
            '  </dict>\n'
            '  <key>StartInterval</key><integer>60</integer>\n'
            '  <key>RunAtLoad</key><true/>\n'
            '</dict></plist>\n'
        )
        run(["launchctl", "load", str(plist)], check=False)
    ok("launchd kitty-session agent enabled")


def install_gridflux():
    log("Gridflux")

    if OS == "Darwin":
        warn("Gridflux does not support macOS yet. Skipping.")
        return

    ensure_dir(Path.home() / "Documents/Workshops")
    ensure_dir(Path.home() / "Documents/Works")
    dest = Path.home() / "Documents/Workshops/gridflux"

    if OS == "Windows":
        _install_gridflux_windows(dest)
    elif OS == "Linux":
        _install_gridflux_linux(dest)

def _install_gridflux_windows(dest: Path):
    if (dest / "gridflux.exe").exists():
        skip("gridflux already installed")
        return
    version, url = fetch_latest_gridflux_asset("gridflux-x64.msi")
    if url:
        ok(f"Latest release: {version}")
        if DRY_RUN:
            print(f"  [dry-run] Download {url}")
            return
        ensure_dir(dest)
        msi = dest / "gridflux-x64.msi"
        download_with_progress(url, msi, f"Downloading gridflux {version}")
        ok(f"Downloaded → {msi}")
        warn("Run the MSI installer manually to complete setup.")
    else:
        warn("No Windows MSI found. Download: https://github.com/arxngr/gridflux/releases")
        if not dest.exists():
            run(["git", "clone", "--depth=1", GRIDFLUX_REPO, str(dest)])
            if cmd_exists("cmake"):
                run(["cmake", "-B", "build"], cwd=dest)
                run(["cmake", "--build", "build"], cwd=dest)

def _install_gridflux_linux(dest: Path):
    markers = [
        Path.home() / ".local/bin/gridflux",
        Path("/usr/local/bin/gridflux"),
        Path("/usr/bin/gridflux"),
        dest / "build" / "gridflux",
    ]
    already = next((p for p in markers if p.exists()), None)
    if already:
        skip(f"gridflux already installed ({already})")
        return

    if dest.exists():
        skip(f"gridflux source already at {dest}")
    else:
        log("Cloning gridflux")
        run(["git", "clone", "--depth=1", GRIDFLUX_REPO, str(dest)])
        ok("gridflux cloned")

    install_sh = dest / "scripts" / "install.sh"
    if not install_sh.exists():
        warn("scripts/install.sh not found — falling back to manual cmake build")
        _build_gridflux_linux_manual(dest)
        return

    log("Running gridflux scripts/install.sh")
    if DRY_RUN:
        print(f"  [dry-run] bash {install_sh}")
        ok("gridflux installed (dry-run)")
        return
    install_sh.chmod(0o755)
    run(["bash", str(install_sh)], cwd=dest)
    ok("gridflux installed via scripts/install.sh")

def _build_gridflux_linux_manual(dest: Path):
    log("Building gridflux (cmake fallback)")
    pm = detect_pkg_manager()
    dep_map = {
        "apt-get": ["build-essential", "cmake", "pkg-config", "libx11-dev", "libjson-c-dev", "libdbus-1-dev", "libgtk-4-dev"],
        "apt":     ["build-essential", "cmake", "pkg-config", "libx11-dev", "libjson-c-dev", "libdbus-1-dev", "libgtk-4-dev"],
        "dnf":     ["gcc", "cmake", "pkg-config", "libX11-devel", "json-c-devel", "dbus-devel", "gtk4-devel"],
        "pacman":  ["base-devel", "cmake", "libx11", "json-c", "dbus", "gtk4"],
    }
    if pm in dep_map:
        pkg_install(dep_map[pm], pm)
    local_bin = Path.home() / ".local/bin"
    ensure_dir(local_bin)
    run(["cmake", "-B", "build", f"-DCMAKE_INSTALL_PREFIX={Path.home() / '.local'}"], cwd=dest)
    run(["cmake", "--build", "build", "--parallel"], cwd=dest)
    for binary in ["gridflux", "gridflux-cli", "gridflux-gui"]:
        src = dest / "build" / binary
        if src.exists() and not DRY_RUN:
            shutil.copy(src, local_bin / binary)
            (local_bin / binary).chmod(0o755)
            ok(f"Installed {binary} → ~/.local/bin/{binary}")
    ok("gridflux built and installed")


def setup_workspace_dirs():
    log("Workspace directories")
    for name in ["Workshops", "Works"]:
        d = Path.home() / "Documents" / name
        if d.exists():
            skip(f"~/Documents/{name}")
        else:
            ensure_dir(d)
            ok(f"Created ~/Documents/{name}")


def print_summary():
    print()
    print(f"{BOLD}{GREEN}{'─'*54}{RESET}")
    print(f"{BOLD}{GREEN}   ✅  Installation complete!{RESET}")
    print(f"{BOLD}{GREEN}{'─'*54}{RESET}")
    print()
    print("Next steps:")
    if OS != "Windows":
        print("  • Restart your terminal:       exec zsh")
        print("  • Open kitty with restore:     kitty-session")
        print("    or add to ~/.zshrc:           alias kitty='kitty-session'")
        print()
        print("  • First neovim launch (plugins install):  nvim")
    if OS == "Linux":
        print()
        print("  • Start gridflux:  gridflux &")
    if OS == "Windows":
        print("  • Run MSI from ~/Documents/Workshops/gridflux/")
    print()


def main():
    global DRY_RUN, UPDATE

    parser = argparse.ArgumentParser(description="Ardi Nugraha dotfiles installer")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without applying them")
    parser.add_argument("--skip", nargs="*", default=[], metavar="STEP",
                        help="Steps to skip: deps font zsh nvim kitty gridflux dirs")
    parser.add_argument("--update", nargs="*", default=None, metavar="STEP",
                        help="Force re-apply (all if no args, or e.g. --update kitty zsh)")
    args     = parser.parse_args()
    DRY_RUN  = args.dry_run
    skip_set = set(args.skip or [])

    if DRY_RUN:
        print(f"{YELLOW}{BOLD}=== DRY RUN — nothing will be changed ==={RESET}\n")
    if args.update is not None:
        scope = ", ".join(args.update) if args.update else "all steps"
        print(f"{YELLOW}{BOLD}=== UPDATE MODE — re-applying: {scope} ==={RESET}\n")

    print(f"{BOLD}{CYAN}")
    print("  ██████╗  ██████╗ ████████╗███████╗██╗██╗     ███████╗███████╗")
    print("  ██╔══██╗██╔═══██╗╚══██╔══╝██╔════╝██║██║     ██╔════╝██╔════╝")
    print("  ██║  ██║██║   ██║   ██║   █████╗  ██║██║     █████╗  ███████╗")
    print("  ██║  ██║██║   ██║   ██║   ██╔══╝  ██║██║     ██╔══╝  ╚════██║")
    print("  ██████╔╝╚██████╔╝   ██║   ██║     ██║███████╗███████╗███████║")
    print("  ╚═════╝  ╚═════╝    ╚═╝   ╚═╝     ╚═╝╚══════╝╚══════╝╚══════╝")
    print(f"{RESET}")
    print(f"  Ardi Nugraha dotfiles installer  •  OS: {OS}\n")

    require_git()

    steps = [
        ("deps",    "Developer dependencies",   install_dev_deps),
        ("font",    "JetBrainsMono Nerd Font",   install_font),
        ("zsh",     "Zsh + oh-my-zsh + plugins", install_zsh),
        ("nvim",    "Neovim + pena.Vim",          install_neovim),
        ("terminal",   "Terminal emulator",   install_terminal),
        ("gridflux","Gridflux window manager",   install_gridflux),
        ("dirs",    "Workspace directories",     setup_workspace_dirs),
    ]

    for key, label, fn in steps:
        if key in skip_set:
            warn(f"Skipping {label} (--skip {key})")
            continue
        UPDATE = args.update is not None and (not args.update or key in args.update)
        print()
        try:
            fn()
        except subprocess.CalledProcessError as e:
            err(f"Step '{label}' failed: {e}")
            err("Continuing with next step…")
        except Exception as e:
            err(f"Unexpected error in '{label}': {e}")
            err("Continuing with next step…")

    print_summary()


if __name__ == "__main__":
    main()
