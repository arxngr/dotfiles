return {
  "stevearc/oil.nvim",
  opts = {
    delete_to_trash = true,
    float = {
      max_height = 45,
      max_width = 120,
      border = "rounded",
      win_options = {
        winblend = 10,
      },
    },
    keymaps = {
      ["q"] = "actions.close",
    },
    view_options = {
      show_hidden = true,
    },
  },
  dependencies = { { "echasnovski/mini.icons", opts = {} } },
}
