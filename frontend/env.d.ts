/// <reference types="vite/client" />

declare module "*.svg" {
  import type { FC, SVGProps } from "react";
  const component: FC<SVGProps<SVGSVGElement>>;
  export default component;
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
