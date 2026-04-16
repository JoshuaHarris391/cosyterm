-- fixture: a NON-LazyVim custom config. Notable: no lazy-lock.json beside it.
-- The pre-flight should detect this and route away from 'replace'.
print("custom init.lua — user's own thing, NOT LazyVim")

vim.opt.number = true
require("my.own.config")
