import { defineConfig } from 'vite';
import { resolve } from 'path';
import fs from 'fs';

function copyStaticAssets() {
  return {
    name: 'copy-static-assets',
    closeBundle() {
      const outDir = resolve(__dirname, 'dist');
      if (fs.existsSync(resolve(__dirname, 'script.js'))) {
        fs.copyFileSync(resolve(__dirname, 'script.js'), resolve(outDir, 'script.js'));
      }
      if (fs.existsSync(resolve(__dirname, 'styles.css'))) {
        fs.copyFileSync(resolve(__dirname, 'styles.css'), resolve(outDir, 'styles.css'));
      }
      const srcAssets = resolve(__dirname, 'assets');
      const dstAssets = resolve(outDir, 'assets');
      if (fs.existsSync(srcAssets)) {
        fs.cpSync(srcAssets, dstAssets, { recursive: true });
      }
    }
  };
}

export default defineConfig({
  base: './',
  plugins: [copyStaticAssets()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        voices: resolve(__dirname, 'voices.html'),
        motion: resolve(__dirname, 'motion.html')
      }
    }
  }
});
