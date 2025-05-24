local wezterm = require("wezterm")
local bar = wezterm.plugin.require("https://github.com/adriankarlen/bar.wezterm")

local config = {}

bar.apply_to_config(config)
-- **Basic Configuration**
config.font = wezterm.font_with_fallback({
	"JetBrainsMono NF Medium",
	"Fira Code",
	"Monospace",
})

config.window_decorations = "RESIZE"
config.font_size = 12
config.color_scheme = "PencilDark"
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

-- Hyperlink rules
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

-- Keybindings
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
}

-- Conditional Default Program
if wezterm.target_triple:find("windows") then
	config.default_prog = { "powershell.exe" }
elseif wezterm.target_triple:find("darwin") or wezterm.target_triple:find("linux") then
	config.default_prog = { "zsh" }
end

return config
