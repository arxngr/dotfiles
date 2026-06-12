local wezterm = require("wezterm")
local bar = wezterm.plugin.require("https://github.com/adriankarlen/bar.wezterm")
local sessions = wezterm.plugin.require("https://github.com/abidibo/wezterm-sessions")

local config = wezterm.config_builder()

sessions.apply_to_config(config, {
	auto_save_interval_s = 60,
	git_branch_warn = true,
})

config.font = wezterm.font_with_fallback({
	"JetBrainsMono NFM",
	"Fira Code",
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
	{
		regex = "\\((\\w+://\\S+)\\)",
		format = "$1",
		highlight = 1,
	},
	{
		regex = "\\[(\\w+://\\S+)\\]",
		format = "$1",
		highlight = 1,
	},
	{
		regex = "\\{(\\w+://\\S+)\\}",
		format = "$1",
		highlight = 1,
	},
	{
		regex = "<(\\w+://\\S+)>",
		format = "$1",
		highlight = 1,
	},
	{
		regex = "[^\\(]\\b(\\w+://\\S+[)/a-zA-Z0-9-]+)",
		format = "$1",
		highlight = 1,
	},
	{
		regex = "\\b\\w+@[\\w-]+(\\.[\\w-]+)+\\b",
		format = "mailto:$0",
	},
}

config.keys = {
	{
		key = "RightArrow",
		mods = "CTRL|SHIFT",
		action = wezterm.action.ActivateTabRelative(1),
	},
	{
		key = "LeftArrow",
		mods = "CTRL|SHIFT",
		action = wezterm.action.ActivateTabRelative(-1),
	},
	{
		key = "w",
		mods = "CTRL",
		action = wezterm.action.CloseCurrentPane({ confirm = false }),
	},
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
	{
		key = "l",
		mods = "ALT",
		action = wezterm.action.ShowLauncherArgs({ flags = "WORKSPACES" }),
	},
	{
		key = "s",
		mods = "ALT|SHIFT",
		action = wezterm.action.EmitEvent("save_session"),
	},
	{
		key = "r",
		mods = "ALT|SHIFT",
		action = wezterm.action.EmitEvent("load_session"),
	},
}

if wezterm.target_triple:find("windows") then
	config.default_prog = { "powershell.exe" }
elseif wezterm.target_triple:find("darwin") or wezterm.target_triple:find("linux") then
	config.default_prog = { "zsh" }
end

bar.apply_to_config(config, {
	modules = {
		tabs = {
			active_tab_fg = 1,
			active_tab_bg = "#10B1FE",
			inactive_tab_fg = "#94a3b8",
		},
		clock = {
			enabled = false,
		},
	},
})

return config