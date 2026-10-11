import { motion, useReducedMotion } from "motion/react";
import { Outlet, useLocation } from "react-router-dom";

import Navbar from "./Navbar.jsx";
import Sidebar from "./Sidebar.jsx";

export default function AppLayout({ user, onLogout }) {
  const location = useLocation();
  const reduceMotion = useReducedMotion();

  return (
    <div className="app-shell">
      <Navbar user={user} onLogout={onLogout} />
      <div className="app-body">
        <Sidebar user={user} />
        <motion.main
          key={location.pathname}
          className="app-content"
          initial={reduceMotion ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, ease: "easeOut" }}
        >
          <Outlet />
        </motion.main>
      </div>
      <footer className="app-footer d-flex align-items-center justify-content-between flex-wrap gap-2">
        <span>Campus Virtual · UNLa · Grupo 12</span>
        <span className="d-inline-flex align-items-center gap-1">
          Hecho con <i className="bi bi-heart-fill" aria-hidden="true" /> y AI Engineering
        </span>
      </footer>
    </div>
  );
}
