import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";

const ToastContext = createContext(null);

const TONES = {
  success: {
    color: "var(--campus-success)",
    background: "var(--campus-success-soft)",
    icon: "bi-check-circle-fill",
  },
  danger: {
    color: "var(--campus-danger)",
    background: "var(--campus-danger-soft)",
    icon: "bi-x-circle-fill",
  },
  warning: {
    color: "var(--campus-warning)",
    background: "var(--campus-warning-soft)",
    icon: "bi-exclamation-triangle-fill",
  },
  info: {
    color: "var(--campus-brand)",
    background: "var(--campus-brand-soft)",
    icon: "bi-info-circle-fill",
  },
};

function ToastItem({ toast, onDismiss, reduceMotion }) {
  const tone = TONES[toast.tone] ?? TONES.info;
  const initial = reduceMotion ? { opacity: 0 } : { opacity: 0, y: 16, scale: 0.96 };
  const animate = reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0, scale: 1 };
  const exit = reduceMotion ? { opacity: 0 } : { opacity: 0, x: 32 };

  return (
    <motion.div
      layout
      initial={initial}
      animate={animate}
      exit={exit}
      transition={{ duration: 0.22, ease: "easeOut" }}
      className="campus-card d-flex align-items-start gap-3 p-3"
      style={{ width: "22rem", maxWidth: "calc(100vw - 2rem)" }}
      role="status"
      data-testid="toast"
    >
      <span
        className="auth-brand__icon"
        style={{ ...tone, width: "2.25rem", height: "2.25rem", fontSize: "1.1rem" }}
        aria-hidden="true"
      >
        <i className={`bi ${tone.icon}`} />
      </span>
      <div className="flex-grow-1">
        {toast.title && <div className="fw-semibold">{toast.title}</div>}
        <div className="small text-secondary">{toast.message}</div>
      </div>
      <button
        type="button"
        className="btn-close"
        aria-label="Cerrar notificación"
        onClick={() => onDismiss(toast.id)}
      />
    </motion.div>
  );
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const timers = useRef(new Map());
  const reduceMotion = useReducedMotion();

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const notify = useCallback(
    (toast) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const item = { id, tone: "info", duration: 4000, ...toast };
      setToasts((current) => [...current, item]);
      if (item.duration > 0) {
        timers.current.set(
          id,
          setTimeout(() => dismiss(id), item.duration)
        );
      }
      return id;
    },
    [dismiss]
  );

  useEffect(() => {
    const pending = timers.current;
    return () => {
      pending.forEach((timer) => clearTimeout(timer));
      pending.clear();
    };
  }, []);

  const value = useMemo(() => ({ notify, dismiss }), [notify, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="position-fixed bottom-0 end-0 p-3 d-flex flex-column gap-2"
        style={{ zIndex: 1090 }}
      >
        <AnimatePresence initial={false}>
          {toasts.map((toast) => (
            <ToastItem
              key={toast.id}
              toast={toast}
              onDismiss={dismiss}
              reduceMotion={reduceMotion}
            />
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast debe usarse dentro de ToastProvider");
  }
  return context;
}
