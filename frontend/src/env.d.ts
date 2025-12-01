/// <reference types="vite/client" />

// Provide explicit typings for Vite env variables used in the app
interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
  // add other VITE_ env vars here if needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
