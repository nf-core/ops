import { defineConfig } from 'vite';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export default defineConfig({
  root: 'src',
  base: './',
  build: {
    outDir: resolve(__dirname, 'dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        script: resolve(__dirname, 'src/index.html')
      },
      output: {
        entryFileNames: 'main.js',
        assetFileNames: '[name].[ext]'
      }
    },
    minify: false,
    sourcemap: true
  }
});
