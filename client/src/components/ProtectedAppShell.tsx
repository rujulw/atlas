import { type ReactElement } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

type ProtectedAppShellProps = {
  isAuthenticated?: boolean;
};

export default function ProtectedAppShell({
  isAuthenticated = false
}: ProtectedAppShellProps): ReactElement {
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
