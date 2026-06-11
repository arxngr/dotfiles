#!/usr/bin/env python3
"""
Ardi Nugraha dotfiles installer
Installs: dev deps, zsh + plugins, kitty + session manager, neovim + pena.Vim,
          JetBrainsMono Nerd Font, gridflux, and workspace directories.

Usage:
    python3 install.py            # full install
    python3 install.py --dry-run  # preview without changes
    python3 install.py --skip font zsh
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
    """Downloads a file and displays a terminal loading bar."""
    req = urllib.request.Request(url, headers={"User-Agent": "dotfiles-installer"})
    try:
        with urllib.request.urlopen(req) as response:
            total_size = int(response.info().get('Content-Length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(dest_path, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    f.write(buffer)
                    
                    if total_size > 0:
                        percent = int(downloaded * 100 / total_size)
                        bar_length = 30
                        filled_length = int(bar_length * downloaded // total_size)
                        bar = '█' * filled_length + '░' * (bar_length - filled_length)
                        sys.stdout.write(f"\r  {CYAN}{description}{RESET} [{bar}] {percent}%")
                        sys.stdout.flush()
                    else:
                        sys.stdout.write(f"\r  {CYAN}{description}{RESET} {downloaded // 1024} KB downloaded...")
                        sys.stdout.flush()
            print()  # New line after completion
    except Exception as e:
        print()
        raise e

def run(cmd, check=True, capture=False, **kwargs):
    display = cmd if isinstance(cmd, str) else " ".join(str(c) for c in cmd)
    if DRY_RUN:
        print(f"  [dry-run] {display}")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    
    subprocess_args = {
        "check": check,
        "capture_output": capture,
        "text": True,
        "shell": isinstance(cmd, str)
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

def copy_local(src_relative: str, dest: Path, required=True):
    src = (DOTFILES_DIR / src_relative).resolve()
    label = dest.name
    
    if DRY_RUN:
        print(f"  [dry-run] Link {src} → {dest}")
        return
        
    if not src.exists():
        if required:
            warn(f"{label}: source target not found at {src}")
        else:
            warn(f"{label} not found in dotfiles, skipping link")
        return
        
    if dest.is_symlink() and dest.readlink() == src:
        skip(f"{label} (correct symbolic link already managed)")
        return

    if dest.exists() or dest.is_symlink():
        backup = dest.with_suffix(dest.suffix + ".bak")
        try:
            if dest.is_dir() and not dest.is_symlink():
                shutil.move(dest, backup)
            else:
                os.remove(dest) if dest.is_symlink() else shutil.move(dest, backup)
            warn(f"Moved existing {label} out of the way to {backup.name}")
        except Exception as e:
            err(f"Could not handle existing path structural block for {label}: {e}")
            return
            
    ensure_dir(dest.parent)
    try:
        os.symlink(src, dest)
        ok(f"Linked config workspace: {label} → {src.name}")
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
        assets  = data.get("assets", [])
        for asset in assets:
            name = asset.get("name", "")
            if asset_keyword.lower() in name.lower():
                return version, asset["browser_download_url"]
        return version, None
    except Exception as e:
        warn(f"Could not fetch gridflux release info: {e}")
        return None, None


def install_dev_deps():
    log("Developer dependencies")

    if OS == "Windows":
        warn("On Windows: install deps via winget, scoop, or choco manually.")
        warn("    Required: cmake, gcc (MinGW), clang, golang, python3, nodejs")
        return

    pm = detect_pkg_manager()
    if pm is None:
        warn("No package manager detected. Install deps manually.")
        return

    dep_map = {
        "brew": {
            "cmake":   "cmake",
            "go":      "go",
            "clang":   "llvm",
            "gcc":     "gcc",
            "python3": "python@3",
            "node":    "node",
        },
        "apt-get": {
            "cmake":   "cmake",
            "go":      "golang-go",
            "clang":   "clang",
            "clangd":  "clangd",
            "gcc":     "gcc",
            "python3": "python3",
            "node":    "nodejs",
            "npm":     "npm",
        },
        "apt": {
            "cmake":   "cmake",
            "go":      "golang-go",
            "clang":   "clang",
            "clangd":  "clangd",
            "gcc":     "gcc",
            "python3": "python3",
            "node":    "nodejs",
            "npm":     "npm",
        },
        "dnf": {
            "cmake":   "cmake",
            "go":      "golang",
            "clang":   "clang",
            "clangd":  "clang-tools-extra",
            "gcc":     "gcc",
            "python3": "python3",
            "node":    "nodejs",
            "npm":     "npm",
        },
        "pacman": {
            "cmake":   "cmake",
            "go":      "go",
            "clang":   "clang",
            "clangd":  "clang",
            "gcc":     "gcc",
            "python3": "python",
            "node":    "nodejs",
            "npm":     "npm",
        },
        "zypper": {
            "cmake":   "cmake",
            "go":      "go",
            "clang":   "clang",
            "clangd":  "clang",
            "gcc":     "gcc",
            "python3": "python3",
            "node":    "nodejs",
            "npm":     "npm",
        },
    }

    tools = dep_map.get(pm, {})
    to_install = []

    checks = {
        "cmake":   "cmake",
        "go":      "go",
        "clang":   "clang",
        "clangd":  "clangd",
        "gcc":     "gcc",
        "python3": "python3",
        "node":    "node",
        "npm":     "npm",
    }

    for label, binary in checks.items():
        if cmd_exists(binary):
            skip(f"{label}")
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

    # Check for various variants of JetBrains Mono Nerd Font names
    font_exists = False
    if font_dir.exists():
        for item in font_dir.iterdir():
            name_lower = item.name.lower()
            if "jetbrains" in name_lower and ("nerd" in name_lower or "nf" in name_lower):
                font_exists = True
                break

    if font_exists:
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
            download_with_progress(FONT_URL, zip_path, description="Downloading JetBrainsMono Nerd Font")
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
        warn("If you're in WSL, re-run this script inside it.")
        return

    if not cmd_exists("zsh"):
        log("Installing zsh")
        pkg_install(["zsh"])
        ok("zsh installed")
    else:
        skip("zsh")

    zsh_path = shutil.which("zsh")
    current_shell = os.environ.get("SHELL", "")
    if zsh_path and zsh_path not in current_shell:
        log(f"Setting default shell to {zsh_path}")
        run(["chsh", "-s", zsh_path], check=False)
        ok("Default shell set to zsh")
    else:
        skip("Default shell already zsh")

    omz_dir = Path.home() / ".oh-my-zsh"
    if omz_dir.exists():
        skip("oh-my-zsh")
    else:
        log("Installing oh-my-zsh")
        if not DRY_RUN:
            run(
                'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended'
            )
        ok("oh-my-zsh installed")

    custom_dir = Path.home() / ".oh-my-zsh/custom/plugins"
    ensure_dir(custom_dir)
    for plugin, url in ZSH_PLUGINS.items():
        clone_or_skip(url, custom_dir / plugin, plugin)

    clone_or_skip(
        "https://github.com/romkatv/powerlevel10k",
        Path.home() / ".oh-my-zsh/custom/themes/powerlevel10k",
        "powerlevel10k"
    )

    copy_local("zsh/.zshrc",   Path.home() / ".zshrc")
    copy_local("zsh/.p10k.zsh", Path.home() / ".p10k.zsh", required=False)


def install_neovim():
    log("Neovim")

    if not cmd_exists("nvim"):
        log("Installing neovim")
        if OS == "Darwin":
            pkg_install(["neovim"], "brew")
        elif OS == "Linux":
            _install_nvim_linux()
        elif OS == "Windows":
            warn("Install neovim from https://github.com/neovim/neovim/releases")
            warn("Then re-run this script.")
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
    log("Downloading latest neovim…")
    if DRY_RUN:
        print(f"  [dry-run] Download {url}")
        return
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "nvim.tar.gz"
        try:
            download_with_progress(url, archive, description="Downloading Neovim binary")
        except Exception as e:
            err(f"Failed to download Neovim: {e}")
            return
        run(["tar", "-xzf", str(archive), "-C", tmp])
        extracted = next(Path(tmp).glob("nvim-linux*"), None)
        if extracted:
            run(f"cp -r {extracted}/. {Path.home() / '.local'}/", shell=True)
    ok("neovim installed to ~/.local/bin/nvim")


def install_kitty():
    log("Kitty terminal")

    if OS == "Windows":
        warn("Kitty doesn't run on Windows. Skipping.")
        return

    if not cmd_exists("kitty"):
        log("Installing kitty")
        run('curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin', shell=True)
        ok("kitty installed")
    else:
        skip("kitty")

    kitty_dir = Path.home() / ".config/kitty"
    ensure_dir(kitty_dir)

    copy_local("kitty/kitty.conf",        kitty_dir / "kitty.conf")
    copy_local("kitty/kitty-colors.conf", kitty_dir / "kitty-colors.conf", required=False)

    _patch_kitty_conf(kitty_dir / "kitty.conf")
    _install_kitty_session(kitty_dir)

def _patch_kitty_conf(conf_path: Path):
    if DRY_RUN or not conf_path.exists():
        return
    content = conf_path.read_text()
    changed = False

    correct_listen = "listen_on unix:/tmp/kitty-{kitty_pid}.sock"
    if "listen_on" not in content:
        content += f"\n# === Session auto-save (added by installer) ===\n{correct_listen}\n"
        changed = True
    elif UPDATE and correct_listen not in content:
        import re
        content = re.sub(r"listen_on\s+\S+", correct_listen, content)
        changed = True

    if "allow_remote_control" not in content:
        content += "allow_remote_control socket-only\n"
        changed = True
    elif "allow_remote_control yes" in content:
        content = content.replace("allow_remote_control yes", "allow_remote_control socket-only")
        changed = True

    if changed:
        conf_path.write_text(content)
        ok("Patched kitty.conf with session directives")
    else:
        skip("kitty.conf session directives already present")

def _install_kitty_session(kitty_dir: Path):
    log("kitty-save-session")
    session_dir = Path.home() / ".local/share/kitty-sessions"
    ensure_dir(session_dir)

    base_url = "https://raw.githubusercontent.com/dflock/kitty-save-session/main/"
    scripts   = [
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
            download_with_progress(base_url + script, dest, description=f"Fetching {script}")
        except Exception as e:
            warn(f"Could not download script {script}: {e}")
            continue

    sh = kitty_dir / "kitty-save-session-all.sh"
    py = kitty_dir / "kitty-convert-dump.py"
    if not DRY_RUN and sh.exists():
        sh.chmod(0o755)
    if not DRY_RUN and py.exists():
        py.chmod(0o755)

    # Verify all critical scripts were downloaded before continuing
    missing = [s for s in scripts if not (kitty_dir / s).exists()]
    if missing:
        err(f"Failed to download critical session scripts: {', '.join(missing)}")
        warn("Session save/restore will not work. Re-run the installer or download manually.")
        return

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
        ok("kitty-session wrapper installed → ~/.local/bin/kitty-session")
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
    if (svc.exists() or tmr.exists()) and UPDATE:
        run(["systemctl", "--user", "disable", "--now", "kitty-session-save.timer"], check=False)
    ensure_dir(sd)
    if not DRY_RUN:
        svc.write_text(
            "[Unit]\nDescription=Save kitty session\n\n"
            "[Service]\nType=oneshot\n"
            f"Environment=PATH={Path.home()}/.local/bin:/usr/local/bin:/usr/bin:/bin\n"
            f"Environment=KITTY_SESSION_SAVE_DIR={session_dir}\n"
            "Environment=KITTY_SESSION_SOCK_PATTERN=/tmp/kitty-{kitty_pid}.sock\n"
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
    if plist.exists() and UPDATE:
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

    workshops = Path.home() / "Documents/Workshops"
    ensure_dir(workshops)
    ensure_dir(Path.home() / "Documents/Works")

    dest = workshops / "gridflux"

    if OS == "Windows":
        _install_gridflux_windows(dest)
    elif OS == "Linux":
        _install_gridflux_linux(dest)

def _install_gridflux_windows(dest: Path):
    bin_path = dest / "gridflux.exe"
    if bin_path.exists():
        skip("gridflux already installed")
        return

    log("Fetching latest gridflux release for Windows…")
    version, url = fetch_latest_gridflux_asset("gridflux-x64.msi")

    if url:
        ok(f"Latest release: {version}")
        if DRY_RUN:
            print(f"  [dry-run] Download {url}")
            return
        ensure_dir(dest)
        msi_path = dest / "gridflux-x64.msi"
        try:
            download_with_progress(url, msi_path, description=f"Downloading gridflux {version} MSI")
        except Exception as e:
            err(f"Failed to download gridflux: {e}")
            return
        ok(f"Downloaded gridflux {version} msi → {msi_path}")
        warn("Run the MSI installer manually to complete setup.")
    else:
        warn(f"No Windows MSI asset found in release {version}.")
        warn("Download manually: https://github.com/arxngr/gridflux/releases")
        if not dest.exists():
            log("Cloning gridflux source as fallback")
            run(["git", "clone", "--depth=1", GRIDFLUX_REPO, str(dest)])
            if cmd_exists("cmake"):
                run(["cmake", "-B", "build"], cwd=dest)
                run(["cmake", "--build", "build"], cwd=dest)
                ok("gridflux built from source")

def _install_gridflux_linux(dest: Path):
    install_markers = [
        Path.home() / ".local/bin/gridflux",
        Path("/usr/local/bin/gridflux"),
        Path("/usr/bin/gridflux"),
        dest / "build" / "gridflux",
    ]
    already = next((p for p in install_markers if p.exists()), None)
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
        warn("scripts/install.sh not found in repo — falling back to manual cmake build")
        _build_gridflux_linux_manual(dest)
        return

    log("Running gridflux scripts/install.sh")
    if DRY_RUN:
        print(f"  [dry-run] chmod +x {install_sh} && bash {install_sh}")
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
        "brew":    ["cmake", "pkg-config", "json-c"],
    }
    if pm in dep_map:
        pkg_install(dep_map[pm], pm)
    local_bin = Path.home() / ".local/bin"
    ensure_dir(local_bin)
    run(["cmake", "-B", "build", f"-DCMAKE_INSTALL_PREFIX={Path.home() / '.local'}"], cwd=dest)
    run(["cmake", "--build", "build", "--parallel"], cwd=dest)
    for binary in ["gridflux", "gridflux-cli", "gridflux-gui"]:
        src = dest / "build" / binary
        if src.exists():
            if not DRY_RUN:
                shutil.copy(src, local_bin / binary)
                (local_bin / binary).chmod(0o755)
            ok(f"Installed {binary} → ~/.local/bin/{binary}")
    ok("gridflux built and installed")


def setup_workspace_dirs():
    log("Workspace directories")
    docs = Path.home() / "Documents"
    for name in ["Workshops", "Works"]:
        d = docs / name
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
        print("   • Restart your terminal:  exec zsh")
        print("   • Open kitty with session restore:")
        print("        kitty-session")
        print("    or add to ~/.zshrc:  alias kitty='kitty-session'")
        print()
        print("   • Launch neovim once to install plugins:")
        print("        nvim")
    if OS == "Linux":
        print()
        print("   • Start gridflux daemon:  gridflux &")
        print("   • Optional GUI:            gridflux-gui")
    if OS == "Windows":
        print("   • Run the MSI from ~/Documents/Workshops/gridflux/")
    print()



def set_kitty_as_default():
    if OS not in ("Linux", "Darwin"):
        warn(f"Default terminal configuration not supported on OS: {OS}")
        return

    wrapper_path = f"{Path.home()}/.local/bin/kitty-session"

    if OS == "Darwin":
        log("Configuring Kitty wrapper application bundle launcher for macOS")
        user_apps_dir = Path.home() / "Applications"
        ensure_dir(user_apps_dir)
        
        app_bundle = user_apps_dir / "KittySession.app"
        contents_dir = app_bundle / "Contents"
        macos_dir = contents_dir / "MacOS"
        resources_dir = contents_dir / "Resources"
        
        if app_bundle.exists():
            skip("KittySession.app launcher bundle already exists")
            return
            
        if DRY_RUN:
            print(f"  [dry-run] Create macOS App Bundle wrapper launcher at {app_bundle}")
            return
            
        ensure_dir(macos_dir)
        ensure_dir(resources_dir)
        
        app_binary = macos_dir / "KittySession"
        app_binary.write_text(
            "#!/usr/bin/env zsh\n"
            f"exec {wrapper_path} &>/dev/null &\n"
        )
        app_binary.chmod(0o755)
        
        info_plist = contents_dir / "Info.plist"
        info_plist.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0">\n<dict>\n'
            '  <key>CFBundleExecutable</key><string>KittySession</string>\n'
            '  <key>CFBundleIdentifier</key><string>com.arxngr.KittySession</string>\n'
            '  <key>CFBundleName</key><string>KittySession</string>\n'
            '  <key>CFBundlePackageType</key><string>APPL</string>\n'
            '  <key>CFBundleShortVersionString</key><string>1.0</string>\n'
            '  <key>LSUIElement</key><true/>\n'
            '</dict>\n</plist>\n'
        )
        
        src_app = Path("/Applications/kitty.app")
        if not src_app.exists():
            src_app = Path.home() / "Applications/kitty.app"
            
        if src_app.exists():
            src_icns = src_app / "Contents/Resources/kitty.icns"
            if src_icns.exists():
                shutil.copy(src_icns, resources_dir / "kitty.icns")
                plist_lines = info_plist.read_text().splitlines()
                plist_lines.insert(-2, '  <key>CFBundleIconFile</key><string>kitty.icns</string>')
                info_plist.write_text("\n".join(plist_lines))

        run(["touch", str(app_bundle)], check=False)
        ok(f"Created native launcher: {app_bundle}")
        return

    log("Configuring Kitty wrapper as default system & GNOME terminal environment")
    apps_dir = Path.home() / ".local/share/applications"
    ensure_dir(apps_dir)
    
    local_desktop = apps_dir / "kitty.desktop"
    sys_desktop = Path("/usr/share/applications/kitty.desktop")

    if DRY_RUN:
        print(f"  [dry-run] Patching system-wide defaults and GNOME settings for: {wrapper_path}")
        return

    if sys_desktop.exists() and not local_desktop.exists():
        shutil.copy(sys_desktop, local_desktop)
        content = local_desktop.read_text()
        content = content.replace("Exec=kitty", f"Exec={wrapper_path}")
        local_desktop.write_text(content)
        run(["update-desktop-database", str(apps_dir)], check=False)
        ok("Patched user desktop app entry icon link.")

    xdg_config_dir = Path.home() / ".config" / "xdg-terminals.prop"
    try:
        xdg_config_dir.write_text("kitty.desktop\n")
        ok("Set kitty as default via xdg-terminal-exec config.")
    except Exception as e:
        warn(f"Could not configure xdg-terminals.prop: {e}")

    if cmd_exists("gsettings"):
        run(["gsettings", "set", "org.gnome.desktop.default-terminal", "exec", f"'{wrapper_path}'"], check=False)
        run(["gsettings", "set", "org.gnome.desktop.default-terminal", "exec-arg", "'-e'"], check=False)
    
    if cmd_exists("xdg-mime"):
        run(["xdg-mime", "default", "kitty.desktop", "x-scheme-handler/terminal"], check=False)
    
    if cmd_exists("update-alternatives"):
        try:
            check_alt = run("update-alternatives --display x-terminal-emulator", capture=True, check=False)
            if wrapper_path not in check_alt.stdout:
                log("Elevating privileges to register system-wide x-terminal-emulator choice...")
                run([
                    "sudo", "update-alternatives", 
                    "--install", "/usr/bin/x-terminal-emulator", "x-terminal-emulator", 
                    wrapper_path, "50"
                ], check=False)
                run(["sudo", "update-alternatives", "--set", "x-terminal-emulator", wrapper_path], check=False)
                ok("Registered and set kitty-session wrapper inside update-alternatives.")
        except Exception as e:
            warn(f"Could not automatically set update-alternatives: {e}")
            
    ok("GNOME desktop preferences refreshed successfully.")

def main():
    global DRY_RUN, UPDATE

    parser = argparse.ArgumentParser(description="Ardi Nugraha dotfiles installer")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without making changes")
    parser.add_argument("--skip", nargs="*", default=[], metavar="STEP",
                        help="Steps to skip: deps font zsh nvim kitty gridflux dirs")
    parser.add_argument("--update", nargs="*", default=None, metavar="STEP",
                        help="Force re-apply configs even if already present (all steps if no args, or e.g. kitty zsh)")
    args     = parser.parse_args()
    DRY_RUN  = args.dry_run
    skip_set = set(args.skip or [])

    if DRY_RUN:
        print(f"{YELLOW}{BOLD}=== DRY RUN — nothing will be changed ==={RESET}\n")
    if args.update is not None:
        scope = ", ".join(args.update) if args.update else "all steps"
        print(f"{YELLOW}{BOLD}=== UPDATE MODE — re-applying configs: {scope} ==={RESET}\n")

    print(f"{BOLD}{CYAN}")
    print("  ██████╗  ██████╗ ████████╗███████╗██╗██╗     ███████╗███████╗")
    print("  ██╔══██╗██╔═══██╗╚══██╔══╝██╔════╝██║██║     ██╔════╝██╔════╝")
    print("  ██║  ██║██║   ██║   ██║   █████╗  ██║██║     █████╗  ███████╗")
    print("  ██║  ██║██║   ██║   ██║   ██╔══╝  ██║██║     ██╔══╝  ╚════██║")
    print("  ██████╔╝╚██████╔╝   ██║   ██║      ██║███████╗███████╗███████║")
    print("  ╚═════╝  ╚═════╝    ╚═╝   ╚═╝      ╚═╝╚══════╝╚══════╝╚══════╝")
    print(f"{RESET}")
    print(f"   Ardi Nugraha dotfiles installer  •  OS: {OS}\n")

    require_git()

    steps = [
        ("deps",    "Developer dependencies",         install_dev_deps),
        ("font",    "JetBrainsMono Nerd Font",         install_font),
        ("zsh",     "Zsh + oh-my-zsh + plugins",       install_zsh),
        ("nvim",    "Neovim + pena.Vim",                install_neovim),
        ("kitty",    "Kitty + session manager",         install_kitty),
        ("default",  "Set Kitty App Icon Default",      set_kitty_as_default),
        ("gridflux","Gridflux window manager",         install_gridflux),
        ("dirs",    "Workspace directories",            setup_workspace_dirs),
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
