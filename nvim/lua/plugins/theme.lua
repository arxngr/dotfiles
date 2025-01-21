return {
  {
    "navarasu/onedark.nvim",
    opts = {
      style = "darker",
      colors = {},
      highlights = {},
    },
  },

  {
    "uloco/bluloco.nvim",
    lazy = true,
    priority = 1000,
    dependencies = { "rktjmp/lush.nvim" },
    config = function()
      transparent = true
    end,
  },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "onedark",
    },
  },
}
