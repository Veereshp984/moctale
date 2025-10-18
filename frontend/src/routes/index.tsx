import { lazy } from "react";
import { useRoutes } from "react-router-dom";

const HomePage = lazy(() => import("@/pages/Home"));
const NotFoundPage = lazy(() => import("@/pages/NotFound"));

export function AppRoutes(): JSX.Element | null {
  return useRoutes([
    {
      path: "/",
      element: <HomePage />,
    },
    {
      path: "*",
      element: <NotFoundPage />,
    },
  ]);
}
