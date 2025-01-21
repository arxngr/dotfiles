return {
  "axkirillov/hbac.nvim",
  config = function(_, opts)
    require("hbac").setup({
      autoclose = true, -- Automatically close buffers when they exceed the threshold
      threshold = 5, -- Maximum number of buffers to keep open
      close_command = function(bufnr)
        vim.api.nvim_buf_delete(bufnr, {}) -- Command to delete buffers
      end,
      close_buffers_with_windows = false, -- Do not close buffers with open windows
    })
  end,
}
