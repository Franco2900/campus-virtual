import { useEffect, useRef, useState } from "react";

import {
  Button,
  Card,
  ConfirmDialog,
  DataTable,
  EmptyState,
  FormField,
  Modal,
  PageHeader,
  ROLE_META,
  RoleBadge,
  Spinner,
  StatusBadge,
  useToast,
} from "../../ui/index.js";
import { listUsers, setUserActive } from "./api.js";
import ResetPasswordForm from "./ResetPasswordForm.jsx";
import UserForm from "./UserForm.jsx";

const FILTER_DEBOUNCE_MS = 300;
const EMPTY_FILTERS = { q: "", role: "", active: "" };

export default function UsersPage() {
  const { notify } = useToast();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [queryInput, setQueryInput] = useState("");
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [formOpen, setFormOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [resetOpen, setResetOpen] = useState(false);
  const [resettingUser, setResettingUser] = useState(null);
  const [confirming, setConfirming] = useState(null);
  const [toggling, setToggling] = useState(false);
  const requestRef = useRef(0);

  async function loadUsers(criteria) {
    const requestId = ++requestRef.current;
    setLoading(true);
    setError("");
    try {
      const data = await listUsers(criteria);
      if (requestRef.current === requestId) {
        setUsers(data);
      }
    } catch (requestError) {
      if (requestRef.current === requestId) {
        setError(requestError.message);
      }
    } finally {
      if (requestRef.current === requestId) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    loadUsers(filters);
  }, [filters]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setFilters((previous) =>
        previous.q === queryInput.trim() ? previous : { ...previous, q: queryInput.trim() }
      );
    }, FILTER_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [queryInput]);

  function updateFilter(key, value) {
    setFilters((previous) => ({ ...previous, [key]: value }));
  }

  function clearFilters() {
    setQueryInput("");
    setFilters((previous) =>
      previous.q || previous.role || previous.active ? EMPTY_FILTERS : previous
    );
  }

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
    loadUsers(filters);
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

  const hasActiveFilters = Boolean(filters.q || filters.role || filters.active);

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
        <div
          className="alert alert-danger d-flex align-items-center gap-2"
          role="alert"
          data-testid="users-error"
        >
          <i className="bi bi-exclamation-triangle-fill" aria-hidden="true" />
          {error}
        </div>
      )}

      <Card className="p-3 mb-3">
        <div
          className="d-flex flex-wrap gap-3 align-items-end"
          role="group"
          aria-label="Filtros de usuarios"
          data-testid="users-filters"
        >
          <div className="flex-grow-1">
            <FormField id="users-filter-q" label="Buscar">
              <input
                id="users-filter-q"
                type="search"
                className="form-control"
                placeholder="Nombre, apellido o correo"
                value={queryInput}
                onChange={(event) => setQueryInput(event.target.value)}
                autoComplete="off"
                data-testid="users-filter-q"
              />
            </FormField>
          </div>
          <FormField id="users-filter-role" label="Rol">
            <select
              id="users-filter-role"
              className="form-select"
              value={filters.role}
              onChange={(event) => updateFilter("role", event.target.value)}
              data-testid="users-filter-role"
            >
              <option value="">Todos</option>
              {Object.entries(ROLE_META).map(([value, meta]) => (
                <option key={value} value={value}>
                  {meta.label}
                </option>
              ))}
            </select>
          </FormField>
          <FormField id="users-filter-active" label="Estado">
            <select
              id="users-filter-active"
              className="form-select"
              value={filters.active}
              onChange={(event) => updateFilter("active", event.target.value)}
              data-testid="users-filter-active"
            >
              <option value="">Todos</option>
              <option value="true">Activos</option>
              <option value="false">Inactivos</option>
            </select>
          </FormField>
          <Button
            variant="soft"
            icon="x-circle"
            className="mb-3"
            onClick={clearFilters}
            data-testid="users-filter-clear"
          >
            Limpiar filtros
          </Button>
        </div>
      </Card>

      <Card className="p-0 overflow-hidden">
        {loading ? (
          <div className="d-flex justify-content-center py-5">
            <Spinner label="Cargando usuarios..." />
          </div>
        ) : users.length === 0 && hasActiveFilters ? (
          <div data-testid="users-empty-filtered">
            <EmptyState icon="bi-search" title="No hay resultados para los criterios">
              <Button
                variant="soft"
                icon="x-circle"
                onClick={clearFilters}
                data-testid="users-filter-clear-empty"
              >
                Limpiar filtros
              </Button>
            </EmptyState>
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
