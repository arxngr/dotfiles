return {
  {
    "folke/edgy.nvim",
    event = "VeryLazy",
    keys = {
      {
        "<leader>ue",
        function()
          require("edgy").toggle()
        end,
        desc = "Edgy Toggle",
      },
      {
        "<leader>uE",
        function()
          require("edgy").select()
        end,
        desc = "Edgy Select Window",
      },
    },
    opts = function()
      local opts = {
        bottom = {
          { title = "DAP Repl", ft = "dap-repl", size = { height = 15 } },
        },
        left = {
          { title = "DAP Scope", ft = "dapui_scopes", size = { width = 50 } },
          { title = "Neotest Summary", ft = "neotest-summary" },
          { title = "DAP Breakpoint", ft = "dapui_breakpoints", size = { width = 50 } },
          { title = "DAP Stack", ft = "dapui_stacks", size = { width = 50 } },
        },
        right = {
          {
            ft = "help",
            size = { height = 14, width = 100 },
            filter = function(buf)
              return vim.bo[buf].buftype == "help"
            end,
          },
        },
        keys = {
          -- Resize bindings
          ["<c-Right>"] = function(win)
            win:resize("width", 2)
          end,
          ["<c-Left>"] = function(win)
            win:resize("width", -2)
          end,
          ["<c-Up>"] = function(win)
            win:resize("height", 2)
          end,
          ["<c-Down>"] = function(win)
            win:resize("height", -2)
          end,
        },
      }
      return opts
    end,
  },
}
