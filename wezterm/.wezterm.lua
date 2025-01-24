local wezterm = require("wezterm")
local config = {}
config.keys = {}

-- **Basic Configuration**
config.font = wezterm.font_with_fallback({
	"JetBrains Mono",
	"Fira Code",
	"Monospace",
})
config.font_size = 12.0
config.color_scheme = "Dark+"
config.enable_tab_bar = true
config.colors = {
	selection_fg = "none",
	selection_bg = "rgba(50% 50% 50% 50%)",
}

config.window_decorations = "TITLE"

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
