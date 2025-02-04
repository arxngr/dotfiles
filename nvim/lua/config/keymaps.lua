-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
local keymap = vim.keymap.set
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

keymap("n", "<leader>tt", ":ToggleTerm direction=float<CR>", { noremap = true, silent = true, desc = "Terminal" })
keymap("t", "<ESC>", [[<C-\><C-n>]], { desc = "Escape Terminal Mode" })
