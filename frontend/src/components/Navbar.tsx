import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Scale,
  FilePlus,
  BookOpen,
  LayoutDashboard,
  Settings,
  LogOut,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const navLinkClass = (path: string) =>
    `inline-flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition ${
      location.pathname === path
        ? "bg-indigo-50 text-indigo-700"
        : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
    }`;

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 no-print">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link
            to={user ? "/dashboard" : "/"}
            className="flex items-center gap-2 font-bold text-lg text-slate-900"
          >
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
              <Scale className="w-5 h-5" />
            </div>
            <span>TenantGuard</span>
          </Link>

          {user && (
            <nav className="hidden md:flex items-center gap-1">
              <Link to="/dashboard" className={navLinkClass("/dashboard")}>
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
              <Link
                to="/complaints/new"
                className={navLinkClass("/complaints/new")}
              >
                <FilePlus className="w-4 h-4" />
                New Complaint
              </Link>
              <Link to="/sources" className={navLinkClass("/sources")}>
                <BookOpen className="w-4 h-4" />
                Legal Library
              </Link>
              <Link to="/settings" className={navLinkClass("/settings")}>
                <Settings className="w-4 h-4" />
                Settings
              </Link>
            </nav>
          )}
        </div>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <span className="hidden sm:inline-block text-xs font-medium px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">
                {user.default_jurisdiction}
              </span>
              <span className="text-sm text-slate-700 font-medium hidden sm:inline">
                {user.full_name}
              </span>
              <button
                onClick={handleLogout}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium text-slate-600 hover:text-red-600 hover:bg-red-50 transition"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Sign Out</span>
              </button>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/auth"
                className="px-4 py-2 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-100"
              >
                Sign In
              </Link>
              <Link
                to="/auth?mode=register"
                className="px-4 py-2 rounded-md text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
