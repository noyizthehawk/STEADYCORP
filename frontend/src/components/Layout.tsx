import { Link, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../lib/auth";

// Shared frame around every page: a slim header + the current page in <Outlet/>.
export default function Layout() {
  const { user, signOut } = useAuth();
  const location = useLocation();

  return (
    <div className="flex min-h-screen flex-col bg-white text-black">
      <header className="flex items-center justify-between px-4 py-3">
        <Link to="/" className="lnk text-red-500">
          STEADYCORP
        </Link>
        {user ? (
          <span className="flex items-center gap-2">
            <span className="px-2 py-1">{user.email}</span>
            <button onClick={signOut} className="lnk">
              LOG OUT
            </button>
          </span>
        ) : (
          <Link to="/signin" state={{ from: location.pathname }} className="lnk">
            SIGN IN
          </Link>
        )}
      </header>

      <main className="flex flex-1 items-center justify-center px-6 pb-20">
        <Outlet />
      </main>
    </div>
  );
}
