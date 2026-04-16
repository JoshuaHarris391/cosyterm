-- fixture: LazyVim loader stub with a user-customised colorscheme line.
require("lazy").setup({
  spec = { { "LazyVim/LazyVim", import = "lazyvim.plugins" } },
  install = { colorscheme = { "tokyonight" } },
})
