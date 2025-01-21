return {
  "mfussenegger/nvim-dap",
  dependencies = {
    -- Install the vscode-js-debug adapter
    {
      "microsoft/vscode-js-debug",
      -- After install, build it and rename the dist directory to out
      build = "npm install --legacy-peer-deps --no-save && npx gulp vsDebugServerBundle && rm -rf out && mv dist out",
      version = "1.*",
    },
    {
      "Joakker/lua-json5",
      build = "./install.sh",
    },
  },
  opts = function()
    require("overseer").enable_dap()
  end,
  config = function()
    local dap = require("dap")

    dap.adapters["pwa-node"] = {
      type = "server",
      host = "localhost",
      port = "${port}",
      executable = {
        command = "js-debug-adapter",
        args = {
          "${port}",
        },
      },
    }

    dap.adapters.cppdbg = {
      id = "cppdbg",
      type = "executable",
      command = vim.fn.stdpath("data") .. "/mason/bin/OpenDebugAD7", -- if you use mason
    }

    dap.configurations.cpp = {
      {
        name = "Launch file",
        type = "cppdbg",
        request = "launch",
        program = function()
          return vim.fn.input("Path to executable: ", vim.fn.getcwd() .. "/", "file")
        end,
        cwd = "${workspaceFolder}",
        stopAtEntry = true,
      },
      {
        name = "Attach to gdbserver :1234",
        type = "cppdbg",
        request = "launch",
        MIMode = "gdb",
        miDebuggerServerAddress = "localhost:1234",
        miDebuggerPath = "/usr/bin/gdb",
        cwd = "${workspaceFolder}",
        program = function()
          return vim.fn.input("Path to executable: ", vim.fn.getcwd() .. "/", "file")
        end,
      },
    }
    -- If you also want to debug C programs, add this:
    dap.configurations.c = dap.configurations.cpp

    local keymap = vim.keymap.set
    local function focus_or_attach_dap(buffer_name, dap_ui_element)
      local found = false

      for _, win in ipairs(vim.api.nvim_list_wins()) do
        local buf = vim.api.nvim_win_get_buf(win)
        local buf_name = vim.api.nvim_buf_get_name(buf)
        if buf_name:match(buffer_name) then
          vim.api.nvim_set_current_win(win) -- Focus the window
          found = true
          break
        end
      end

      if not found then
        require("dapui").open({ dap_ui_element })
      end
    end

    keymap("n", "<leader>ds", function()
      focus_or_attach_dap("DAP Scopes", "scopes")
    end, { desc = "Focus or open DAP Scopes" })

    keymap("n", "<leader>dr", function()
      focus_or_attach_dap("dap%-repl%-", "repl") -- Focus or attach to DAP Repl
    end, { desc = "Focus or Open DAP Repl" })
    --
  end,
}
