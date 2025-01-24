local wezterm = require("wezterm")
local config = {}
config.keys = {}

-- **Basic Configuration**
config.font = wezterm.font_with_fallback({
	"JetBrains Mono",
	"Fira Code",
	"Monospace",
})
config.font_size = 12.5
config.color_scheme = "PencilDark"
config.window_background_opacity = 0.85
config.enable_tab_bar = true
config.colors = {
	selection_fg = "none",
	selection_bg = "rgba(50% 50% 50% 50%)",
}

config.hyperlink_rules = {
	{
		regex = "\\((\\w+://\\S+)\\)",
		format = "$1",
		highlight = 1,
	},
	-- Matches: a URL in brackets: [URL]
	{
		regex = "\\[(\\w+://\\S+)\\]",
		format = "$1",
		highlight = 1,
	},
	-- Matches: a URL in curly braces: {URL}
	{
		regex = "\\{(\\w+://\\S+)\\}",
		format = "$1",
		highlight = 1,
	},
	-- Matches: a URL in angle brackets: <URL>
	{
		regex = "<(\\w+://\\S+)>",
		format = "$1",
		highlight = 1,
	},
	-- Then handle URLs not wrapped in brackets
	{
		-- Before
		--regex = '\\b\\w+://\\S+[)/a-zA-Z0-9-]+',
		--format = '$0',
		-- After
		regex = "[^(]\\b(\\w+://\\S+[)/a-zA-Z0-9-]+)",
		format = "$1",
		highlight = 1,
	},
	-- implicit mailto link
	{
		regex = "\\b\\w+@[\\w-]+(\\.[\\w-]+)+\\b",
		format = "mailto:$0",
	},
}

config.colors = {
	tab_bar = {
		background = "#1e293b",

		active_tab = {
			bg_color = "#0f172a",
			fg_color = "#a5b4fc",
			italic = false,
		},

		-- Inactive tabs styling
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

config.enable_tab_bar = true
config.hide_tab_bar_if_only_one_tab = false
config.use_fancy_tab_bar = true
config.window_decorations = "RESIZE"

table.insert(config.keys, {
	key = "RightArrow",
	mods = "CTRL|SHIFT",
	action = wezterm.action.ActivateTabRelative(1),
})

table.insert(config.keys, {
	key = "LeftArrow",
	mods = "CTRL|SHIFT",
	action = wezterm.action.ActivateTabRelative(-1),
})

config.keys = {
	{
		key = "w",
		mods = "CTRL",
		action = wezterm.action.CloseCurrentPane({ confirm = false }),
	},
}
return config
