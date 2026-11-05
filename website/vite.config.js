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
      // Copy root-level verification / meta files (e.g. Google Search Console, robots.txt, sitemap.xml, favicons)
      const rootFiles = fs.readdirSync(__dirname);
      for (const f of rootFiles) {
        if ((f.startsWith('google') && f.endsWith('.html')) || f === 'robots.txt' || f === 'sitemap.xml' || f.startsWith('favicon')) {
          fs.copyFileSync(resolve(__dirname, f), resolve(outDir, f));
        }
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
        main: resolve(__dirname, 'index.html')
      }
    }
  }
});
