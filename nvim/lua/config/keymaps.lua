-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

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
  focus_or_attach_dap("dap%-repl%-", "repl")
end, { desc = "Focus or Open DAP Repl" })

keymap("n", "<leader>e", ":OilToggle<CR>", { noremap = true, silent = true, desc = "File Tree" })

keymap("n", "d", '"_d', { noremap = true, silent = true })
keymap("x", "d", '"_d', { noremap = true, silent = true })
keymap("x", "<leader>p", '"_dP', { noremap = true, silent = true })
keymap("n", "d", '"_d', { noremap = true, silent = true })
keymap("n", "<C-c>", '"+y', { noremap = true, silent = true })
keymap("v", "<C-c>", '"+y', { noremap = true, silent = true })
keymap("n", "<C-v>", '"+p', { noremap = true, silent = true })
keymap("v", "<C-v>", '"+p', { noremap = true, silent = true })
keymap("n", "<C-d>", "mciw*<Cmd>nohl<CR>", { remap = true })

keymap("n", "<leader>ft", ":ToggleTerm direction=float<CR>", { noremap = true, silent = true, desc = "Terminal" })
