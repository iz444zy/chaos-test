import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['batchbook-icon.svg'],
      manifest: {
        name: 'BatchBook',
        short_name: 'BatchBook',
        description: 'A kitchen notebook for developing and preserving recipes.',
        theme_color: '#8e422d',
        background_color: '#f7f3ec',
        display: 'standalone',
        start_url: '/',
        icons: [
          {
            src: 'batchbook-icon.svg',
            sizes: 'any',
            type: 'image/svg+xml',
            purpose: 'any',
          },
        ],
      },
    }),
  ],
})
