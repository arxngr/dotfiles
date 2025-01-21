return {
  "rcarriga/nvim-dap-ui",
  dependencies = {
    "nvim-neotest/nvim-nio",
  },
  opts = {
    layouts = {
      {
        elements = {
          { id = "repl", size = 0.05 },
        },
        size = 55,
        position = "bottom",
      },
      {
        elements = {
          { id = "scopes", size = 0.25 },
          { id = "breakpoints", size = 0.25 },
          { id = "stacks", size = 0.25 },
        },
        size = 40, -- Width of the layout (for `right` or `left`)
        position = "left", -- Can be "left" or "right"
      },
    },
  },
  config = function(_, opts)
    local dap = require("dap")
    local dapui = require("dapui")

    dapui.setup(opts)
    dap.listeners.before.attach.dapui_config = function()
      dapui.open({})
    end
    dap.listeners.before.launch.dapui_config = function()
      dapui.open({})
    end
  end,
}
