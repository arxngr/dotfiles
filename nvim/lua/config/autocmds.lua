-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
--
-- Add any additional autocmds here
-- with `vim.api.nvim_create_autocmd`
--
-- Or remove existing autocmds by their group name (which is prefixed with `lazyvim_` for the defaults)
-- e.g. vim.api.nvim_del_augroup_by_name("lazyvim_wrap_spell")
--
--

local oil_available, _ = pcall(require, "oil")
if oil_available then
  local oil = require("oil")

  vim.api.nvim_create_autocmd("FileType", {
    pattern = "dap-float",
    callback = function()
      vim.api.nvim_buf_set_keymap(0, "n", "q", "<cmd>close!<CR>", { noremap = true, silent = true })
    end,
  })

  vim.api.nvim_create_user_command("OilToggle", function()
    if vim.bo.filetype == "oil" then
      vim.cmd("bd") -- Close the Oil buffer
    else
      oil.toggle_float() -- Open Oil in floating mode
    end
  end, { nargs = 0 })
end

require("neo-tree").setup({
  filesystem = {
    hijack_netrw_behavior = "open_current",
    window = {
      position = "float",
    },
  },
})
