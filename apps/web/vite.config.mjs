import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));

/** @type {import('vite').UserConfig} */
export default {
  optimizeDeps: {
    include: ["qrcode"],
  },
  build: {
    rollupOptions: {
      input: {
        main: resolve(root, "index.html"),
        doar: resolve(root, "doar.html"),
      },
    },
  },
};
