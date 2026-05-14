import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    // Node.js 25+ emits a warning when worker threads access localStorage without --localstorage-file.
    // jsdom overrides globalThis.localStorage, but the warning fires before jsdom setup completes.
    // Passing /dev/null satisfies the flag so Node initialises the storage object without warning.
    execArgv: ['--localstorage-file=/dev/null'],
  },
})
