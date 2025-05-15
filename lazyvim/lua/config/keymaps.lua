-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

local keymap = vim.keymap.set
local opts = { noremap = true, silent = true }

keymap("n", "d", '"_d', opts)
keymap("x", "d", '"_d', opts)
keymap("x", "<leader>p", '"_dP', opts)
keymap("n", "<C-c>", '"+y', opts)
keymap("v", "<C-c>", '"+y', opts)
keymap("n", "<C-v>", '"+p', opts)
keymap("v", "<C-v>", '"+p', opts)
