local wezterm = require("wezterm")
local bar = wezterm.plugin.require("https://github.com/adriankarlen/bar.wezterm")

local config = wezterm.config_builder()

local home = wezterm.home_dir or os.getenv("HOME") or ""
local session_file = home .. "/.wezterm_session"
local session_state = {}
local last_save_time = 0

local function write_session()
	if next(session_state) == nil then return end
	local f, err = io.open(session_file, "w")
	if not f then
		wezterm.log_error("wezterm-session: cannot write " .. session_file .. ": " .. tostring(err))
		return
	end
	for ws, cwds in pairs(session_state) do
		for _, cwd in ipairs(cwds) do
			if cwd and cwd ~= "" then
				f:write(ws .. "\t" .. cwd .. "\n")
			end
		end
	end
	f:close()
end

local function load_entries()
	local f = io.open(session_file, "r")
	if not f then return {} end
	local entries = {}
	for line in f:lines() do
		local ws, cwd = line:match("^([^\t]+)\t(.+)$")
		if ws and cwd then
			table.insert(entries, { workspace = ws, cwd = cwd })
		end
	end
	f:close()
	return entries
end

local function restore_session()
	local entries = load_entries()
	if #entries == 0 then
		wezterm.mux.spawn_window({})
		return
	end
	local windows = {}
	local first_ws = nil
	for _, e in ipairs(entries) do
		if not first_ws then first_ws = e.workspace end
		if not windows[e.workspace] then
			local _, _, mux_win = wezterm.mux.spawn_window({
				workspace = e.workspace,
				cwd = e.cwd,
			})
			windows[e.workspace] = mux_win
		else
			windows[e.workspace]:spawn_tab({ cwd = e.cwd })
		end
	end
	wezterm.mux.set_active_workspace(first_ws)
end

wezterm.on("gui-startup", function()
	restore_session()
end)

wezterm.on("gui-attached", function()
	if #wezterm.mux.all_windows() == 0 then
		restore_session()
	end
end)

-- update-right-status passes pane directly — no mux_window() needed, works on all platforms
wezterm.on("update-right-status", function(window, pane)
	local ws = window:active_workspace()
	local cwd_url = pane:get_current_working_dir()
	local cwd = (cwd_url and cwd_url.file_path) or home
	-- track all tabs for this workspace via pcall; fall back to active pane only
	local cwds = {}
	local ok = pcall(function()
		for _, tab in ipairs(window:mux_window():tabs()) do
			local u = tab:active_pane():get_current_working_dir()
			table.insert(cwds, (u and u.file_path) or home)
		end
	end)
	session_state[ws] = (ok and #cwds > 0) and cwds or { cwd }

	local now = os.time()
	if now - last_save_time >= 60 then
		last_save_time = now
		write_session()
	end
end)

-- ALT+SHIFT+S
wezterm.on("save_session", function(window)
	local ws = window:active_workspace()
	local cwds = {}
	local ok = pcall(function()
		for _, tab in ipairs(window:mux_window():tabs()) do
			local u = tab:active_pane():get_current_working_dir()
			table.insert(cwds, (u and u.file_path) or home)
		end
	end)
	if ok and #cwds > 0 then session_state[ws] = cwds end
	write_session()
end)

-- ALT+SHIFT+R
wezterm.on("load_session", function(window, pane)
	local entries = load_entries()
	if #entries == 0 then
		window:toast_notification("WezTerm", "No saved session found", nil, 2000)
		return
	end
	local existing = {}
	for _, name in ipairs(wezterm.mux.get_workspace_names()) do
		existing[name] = true
	end
	local windows = {}
	local count = 0
	for _, e in ipairs(entries) do
		if not existing[e.workspace] then
			if not windows[e.workspace] then
				local _, _, mux_win = wezterm.mux.spawn_window({
					workspace = e.workspace,
					cwd = e.cwd,
				})
				windows[e.workspace] = mux_win
				count = count + 1
			else
				windows[e.workspace]:spawn_tab({ cwd = e.cwd })
			end
		end
	end
end)

wezterm.on("gui-shutdown", function()
	write_session()
end)

config.font = wezterm.font_with_fallback({
	{ family = "JetBrainsMono Nerd Font Mono", weight = "DemiBold" },
	{ family = "Fira Code" },
	"Monospace",
})

config.window_decorations = "RESIZE"
config.font_size = 12
config.color_scheme = "carbonfox"
config.window_background_opacity = 0.93
config.default_cursor_style = "SteadyBar"

config.tab_bar_at_bottom = true
config.colors = {
	background = "#0f1013",
	selection_fg = "none",
	selection_bg = "rgba(50% 50% 50% 50%)",
	tab_bar = {
		background = "#0f1013",
		active_tab = {
			bg_color = "#10B1FE",
			fg_color = "#0f1013",
			italic = false,
		},
		inactive_tab = {
			bg_color = "#334155",
			fg_color = "#94a3b8",
		},
		inactive_tab_hover = {
			bg_color = "#475569",
			fg_color = "#c7d2fe",
			italic = true,
		},
		new_tab = {
			bg_color = "#1e293b",
			fg_color = "#94a3b8",
		},
		new_tab_hover = {
			bg_color = "#475569",
			fg_color = "#c7d2fe",
		},
	},
}

config.hyperlink_rules = {
	{ regex = "\\((\\w+://\\S+)\\)", format = "$1", highlight = 1 },
	{ regex = "\\[(\\w+://\\S+)\\]", format = "$1", highlight = 1 },
	{ regex = "\\{(\\w+://\\S+)\\}", format = "$1", highlight = 1 },
	{ regex = "<(\\w+://\\S+)>", format = "$1", highlight = 1 },
	{ regex = "[^\\(]\\b(\\w+://\\S+[)/a-zA-Z0-9-]+)", format = "$1", highlight = 1 },
	{ regex = "\\b\\w+@[\\w-]+(\\.[\\w-]+)+\\b", format = "mailto:$0" },
}

config.keys = {
	{ key = "RightArrow", mods = "CTRL|SHIFT", action = wezterm.action.ActivateTabRelative(1) },
	{ key = "LeftArrow", mods = "CTRL|SHIFT", action = wezterm.action.ActivateTabRelative(-1) },
	{ key = "w", mods = "CTRL", action = wezterm.action.CloseCurrentPane({ confirm = false }) },
	{
		key = "w",
		mods = "ALT",
		action = wezterm.action.PromptInputLine({
			description = wezterm.format({
				{ Attribute = { Intensity = "Bold" } },
				{ Foreground = { AnsiColor = "Fuchsia" } },
				{ Text = "Enter name for workspace: " },
			}),
			action = wezterm.action_callback(function(window, pane, line)
				if line then
					window:perform_action(wezterm.action.SwitchToWorkspace({ name = line }), pane)
				end
			end),
		}),
	},
	{ key = "l", mods = "ALT", action = wezterm.action.ShowLauncherArgs({ flags = "WORKSPACES" }) },
	{ key = "s", mods = "ALT|SHIFT", action = wezterm.action.EmitEvent("save_session") },
	{ key = "r", mods = "ALT|SHIFT", action = wezterm.action.EmitEvent("load_session") },
}

if wezterm.target_triple:find("windows") then
	config.default_prog = { "powershell.exe" }
else
	config.default_prog = { "zsh" }
end

bar.apply_to_config(config, {
	modules = {
		tabs = {
			active_tab_fg = 1,
			active_tab_bg = "#10B1FE",
			inactive_tab_fg = "#94a3b8",
		},
		clock = { enabled = false },
	},
})

return config
