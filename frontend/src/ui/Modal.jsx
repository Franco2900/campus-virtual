import { useEffect, useRef } from "react";
import BootstrapModal from "bootstrap/js/dist/modal";

export default function Modal({
  open,
  title,
  size,
  footer,
  onClose,
  scrollable = false,
  testId,
  children,
}) {
  const elementRef = useRef(null);
  const instanceRef = useRef(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    const element = elementRef.current;
    if (!element) {
      return undefined;
    }
    const instance = new BootstrapModal(element, { backdrop: "static", keyboard: true });
    instanceRef.current = instance;
    const handleHidden = () => onCloseRef.current?.();
    element.addEventListener("hidden.bs.modal", handleHidden);
    return () => {
      element.removeEventListener("hidden.bs.modal", handleHidden);
      instance.dispose();
      instanceRef.current = null;
    };
  }, []);

  useEffect(() => {
    const instance = instanceRef.current;
    if (!instance) {
      return;
    }
    if (open) {
      instance.show();
    } else {
      instance.hide();
    }
  }, [open]);

  const dialogClass = [
    "modal-dialog",
    "modal-dialog-centered",
    size ? `modal-${size}` : "",
    scrollable ? "modal-dialog-scrollable" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className="modal fade"
      ref={elementRef}
      tabIndex={-1}
      aria-hidden="true"
      data-testid={testId}
    >
      <div className={dialogClass}>
        <div className="modal-content">
          {title && (
            <div className="modal-header">
              <h5 className="modal-title">{title}</h5>
              <button
                type="button"
                className="btn-close"
                aria-label="Cerrar"
                onClick={() => instanceRef.current?.hide()}
              />
            </div>
          )}
          <div className="modal-body">{children}</div>
          {footer && <div className="modal-footer">{footer}</div>}
        </div>
      </div>
    </div>
  );
}
