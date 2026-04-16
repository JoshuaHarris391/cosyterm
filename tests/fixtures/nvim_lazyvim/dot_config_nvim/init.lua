-- fixture: a minimal LazyVim-looking config the user has been tweaking.
-- The test treats the sha256 of this tree as the "precious" state that
-- must come back byte-for-byte after restore.
require("config.lazy")

-- a user tweak that matters to them
vim.opt.relativenumber = true
vim.keymap.set("n", "<leader>my", "<cmd>echo 'a line the user wrote themselves'<cr>")
