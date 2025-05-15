return {
  "nvim-neo-tree/neo-tree.nvim",
  config = function()
    require("neo-tree").setup({
      filesystem = {
        filtered_items = {
          visible = true, -- Show hidden files
          show_hidden_count = true,
          hide_dotfiles = false,
          hide_gitignored = false,
        },
      },
      window = {
        position = "float",
        popup = {
          size = {
            height = "80%",
            width = "50%",
          },
        },
      },
      event_handlers = {
        {
          event = "neo_tree_buffer_enter",
          handler = function()
            vim.cmd("setlocal relativenumber")
          end,
        },
      },
    })
  end,
}
