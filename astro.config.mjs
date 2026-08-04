// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  // The public address the finished site will live at. Astro uses this to build
  // the sitemap and canonical URLs later. It is the DEMO address for now and gets
  // changed to https://www.la-casa-weybridge.com only at launch.
  site: 'https://la-casa-demo.netlify.app',
});
