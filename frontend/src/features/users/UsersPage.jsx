import { useEffect, useState } from "react";

import {
  Button,
  Card,
  ConfirmDialog,
  DataTable,
  Modal,
  PageHeader,
  RoleBadge,
  Spinner,
  StatusBadge,
  useToast,
} from "../../ui/index.js";
import { listUsers, setUserActive } from "./api.js";
import ResetPasswordForm from "./ResetPasswordForm.jsx";
import UserForm from "./UserForm.jsx";

export default function UsersPage() {
  const { notify } = useToast();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [resetOpen, setResetOpen] = useState(false);
  const [resettingUser, setResettingUser] = useState(null);
  const [confirming, setConfirming] = useState(null);
  const [toggling, setToggling] = useState(false);

  async function loadUsers() {
    setLoading(true);
    setError("");
    try {
      const data = await listUsers();
      setUsers(data);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers();
  }, []);

  function openEdit(user) {
    setEditingUser(user);
    setFormOpen(true);
  }

  function openReset(user) {
    setResettingUser(user);
    setResetOpen(true);
  }

  function handleSaved(saved) {
    setFormOpen(false);
    loadUsers();
    notify({
      tone: "success",
      title: "Usuario actualizado",
      message: `Se guardaron los cambios de ${saved.first_name} ${saved.last_name}.`,
    });
  }

  function handlePasswordReset() {
    const user = resettingUser;
    setResetOpen(false);
    notify({
      tone: "success",
      title: "Contraseña actualizada",
      message: `Se reseteó la contraseña de ${user.first_name} ${user.last_name}.`,
    });
  }

  async function confirmToggle() {
    const user = confirming;
    if (!user) {
      return;
    }
    setToggling(true);
    try {
      const updated = await setUserActive(user.id, !user.active);
      setUsers((previous) => previous.map((item) => (item.id === updated.id ? updated : item)));
      notify({
        tone: "success",
        title: updated.active ? "Usuario activado" : "Usuario desactivado",
        message: `${updated.first_name} ${updated.last_name} cambió de estado.`,
      });
    } catch (requestError) {
      notify({
        tone: "danger",
        title: "No se pudo cambiar el estado",
        message: requestError.message,
      });
    } finally {
      setToggling(false);
      setConfirming(null);
    }
  }

  const columns = [
    {
      key: "name",
      header: "Usuario",
      render: (user) => (
        <span
          className={user.active ? "fw-semibold" : "fw-semibold text-secondary"}
          data-testid={`user-name-${user.id}`}
        >
          {user.first_name} {user.last_name}
        </span>
      ),
    },
    { key: "email", header: "Correo" },
    { key: "role", header: "Rol", render: (user) => <RoleBadge role={user.role} /> },
    {
      key: "active",
      header: "Estado",
      render: (user) => <StatusBadge active={user.active} />,
    },
    {
      key: "actions",
      header: "",
      className: "text-end",
      render: (user) => (
        <div className="d-flex justify-content-end gap-2">
          <Button
            variant="soft"
            className="btn-sm"
            icon="pencil"
            onClick={() => openEdit(user)}
            data-testid={`user-edit-${user.id}`}
          >
            Editar
          </Button>
          <Button
            variant="soft"
            className="btn-sm"
            icon="key"
            onClick={() => openReset(user)}
            data-testid={`user-reset-${user.id}`}
          >
            Contraseña
          </Button>
          <Button
            variant="soft"
            className="btn-sm"
            icon={user.active ? "toggle-off" : "toggle-on"}
            onClick={() => setConfirming(user)}
            data-testid={`user-toggle-${user.id}`}
          >
            {user.active ? "Desactivar" : "Activar"}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div data-testid="users-page">
      <PageHeader
        title="Usuarios"
        subtitle="Datos, rol y estado de las cuentas del campus"
        icon="bi-people-fill"
      />

      {error && (
        <div className="alert alert-danger d-flex align-items-center gap-2" role="alert">
          <i className="bi bi-exclamation-triangle-fill" aria-hidden="true" />
          {error}
        </div>
      )}

      <Card className="p-0 overflow-hidden">
        {loading ? (
          <div className="d-flex justify-content-center py-5">
            <Spinner label="Cargando usuarios..." />
          </div>
        ) : (
          <DataTable
            columns={columns}
            rows={users}
            empty="Todavía no hay usuarios registrados."
            emptyIcon="bi-person-x"
          />
        )}
      </Card>

      <Modal
        open={formOpen}
        title={editingUser ? "Editar usuario" : "Usuario"}
        onClose={() => setFormOpen(false)}
      >
        {formOpen && editingUser && (
          <UserForm
            key={editingUser.id}
            user={editingUser}
            onSaved={handleSaved}
            onCancel={() => setFormOpen(false)}
          />
        )}
      </Modal>

      <Modal open={resetOpen} title="Resetear contraseña" onClose={() => setResetOpen(false)}>
        {resetOpen && resettingUser && (
          <ResetPasswordForm
            key={resettingUser.id}
            user={resettingUser}
            onSaved={handlePasswordReset}
            onCancel={() => setResetOpen(false)}
          />
        )}
      </Modal>

      <ConfirmDialog
        open={Boolean(confirming)}
        title={confirming?.active ? "Desactivar usuario" : "Activar usuario"}
        tone={confirming?.active ? "danger" : "brand"}
        icon={confirming?.active ? "toggle-off" : "toggle-on"}
        confirmVariant={confirming?.active ? "danger" : "brand"}
        confirmLabel={confirming?.active ? "Desactivar" : "Activar"}
        loading={toggling}
        message={
          confirming
            ? `¿Confirmás ${confirming.active ? "desactivar" : "activar"} a ${confirming.first_name} ${confirming.last_name}?`
            : ""
        }
        onConfirm={confirmToggle}
        onCancel={() => setConfirming(null)}
      />
    </div>
  );
}
