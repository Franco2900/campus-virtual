# frontend-design-system Specification

## Purpose
Establecer una base visual única y reutilizable para el frontend del Campus Virtual: tokens de diseño con soporte de tema claro y oscuro, un sistema de componentes sobre Bootstrap, un shell de aplicación con navegación por rol y animaciones consistentes, de modo que los casos de uso CU-04 a CU-10 construyan sus pantallas sobre esa base sin reinventar estilos.

## Requirements

### Requirement: Tokenización del diseño y temas

El sistema SHALL definir los valores visuales (colores de marca, colores por rol, colores semánticos, neutros, tipografía y espaciado) como tokens centralizados, y SHALL soportar un tema claro y un tema oscuro derivados de los mismos tokens. Ningún color SHALL codificarse directamente en los componentes; todos MUST consumirse a través de los tokens o de clases semánticas.

#### Scenario: Tema claro y oscuro disponibles

- **GIVEN** que la aplicación está cargada
- **WHEN** el usuario cambia el tema entre claro y oscuro
- **THEN** el sistema aplica los valores del tema elegido en toda la interfaz sin recargar la página

#### Scenario: Tokenización de colores

- **GIVEN** que un componente necesita un color de marca, de rol o semántico
- **WHEN** se implementa o modifica ese componente
- **THEN** el color proviene de un token o clase semántica y no de un valor literal embebido en el componente

### Requirement: Persistencia y detección del tema

El sistema SHALL recordar la preferencia de tema del usuario entre sesiones y SHALL respetar la preferencia del sistema operativo cuando el usuario no haya elegido una explícitamente. La carga inicial MUST NOT mostrar un tema incorrecto antes de aplicar la preferencia.

#### Scenario: Preferencia recordada

- **GIVEN** que el usuario seleccionó un tema distinto al del sistema
- **WHEN** vuelve a cargar la aplicación
- **THEN** el sistema arranca en el tema previamente seleccionado

#### Scenario: Default por preferencia del sistema

- **GIVEN** que el usuario nunca eligió un tema
- **WHEN** carga la aplicación
- **THEN** el tema inicial coincide con `prefers-color-scheme` del sistema

### Requirement: Sistema de componentes reutilizable

El sistema SHALL proveer un conjunto de componentes de interfaz reutilizables (al menos: botón, tarjeta, badge, badge de rol, tabla de datos, campo de formulario, modal/diálogo de confirmación, notificación efímera, indicador de carga y estado vacío) construidos sobre Bootstrap y consumibles desde las features. Las features MUST usar estos componentes en lugar de HTML y estilos ad hoc para las piezas que el sistema ya cubre.

#### Scenario: Reutilización de componentes

- **GIVEN** que una pantalla necesita una acción, un badge o una tabla
- **WHEN** se implementa esa pantalla
- **THEN** usa los componentes del sistema en lugar de reimplementar el marcado y los estilos

#### Scenario: Confirmación de acción destructiva

- **GIVEN** que una acción requiere confirmación del usuario
- **WHEN** la acción se dispara
- **THEN** el sistema muestra un diálogo de confirmación reutilizable y solo ejecuta la acción si el usuario confirma

### Requirement: Shell de aplicación y navegación por rol

El sistema SHALL proveer un contenedor de aplicación común (encabezado, navegación lateral y área de contenido) para las vistas autenticadas, de modo que las pantallas se integren sin repetir la estructura. La navegación lateral SHALL mostrar únicamente las secciones correspondientes al rol del usuario autenticado.

#### Scenario: Vista autenticada dentro del shell

- **GIVEN** que un usuario tiene sesión activa
- **WHEN** accede a una sección de la aplicación
- **THEN** la sección se muestra dentro del shell común (encabezado, navegación y contenido) sin duplicar esa estructura en la pantalla

#### Scenario: Navegación acorde al rol

- **GIVEN** que un usuario tiene un rol determinado
- **WHEN** se renderiza la navegación lateral
- **THEN** se listan solo las secciones habilitadas para ese rol

#### Scenario: Protección de secciones por rol

- **GIVEN** que un usuario autenticado con un rol no autorizado intenta acceder a una sección restringida
- **WHEN** navega a esa sección
- **THEN** el sistema no muestra la sección y responde con un mensaje de permisos

#### Scenario: Acceso sin sesión

- **GIVEN** que no hay sesión activa
- **WHEN** se intenta acceder a una sección protegida
- **THEN** el sistema redirige al inicio de sesión

### Requirement: Semántica de color por rol

El sistema SHALL asociar un color distintivo a cada rol (Estudiante, Profesor, Administrador) y SHALL aplicarlo de forma consistente donde se identifique el rol (badge de rol, identificación del usuario). El color de rol MUST ser distinguible entre roles.

#### Scenario: Identificación visual del rol

- **GIVEN** que un usuario con rol Profesor está autenticado
- **WHEN** el sistema muestra la identificación de ese usuario o su badge de rol
- **THEN** se usa el color asignado al rol Profesor, distinguible del de Estudiante y Administrador

### Requirement: Animaciones consistentes y accesibles

El sistema SHALL proveer animaciones consistentes para transiciones estructurales (cambio de vista, aparición/desaparición de modales y notificaciones) y micro-interacciones. Todas las animaciones MUST respetar la preferencia de movimiento reducido del usuario; cuando `prefers-reduced-motion` esté activo, el sistema MUST NOT animar.

#### Scenario: Respeto por movimiento reducido

- **GIVEN** que el usuario tiene activada la preferencia de movimiento reducido
- **WHEN** se produce una transición o micro-interacción animada
- **THEN** el sistema no reproduce la animación y presenta el estado final de forma inmediata

### Requirement: Portabilidad de las dependencias de interfaz

El sistema SHALL integrar todas sus dependencias visuales (framework de estilos, iconos, tipografía y librería de animación) empaquetadas en el build, sin descargar recursos desde la red en tiempo de ejecución ni depender de una plataforma particular. La aplicación MUST construirse y ejecutarse en Windows, Linux y macOS con los pasos documentados.

#### Scenario: Sin dependencia de red en runtime

- **GIVEN** que la aplicación fue construida
- **WHEN** se ejecuta sin acceso a Internet
- **THEN** los estilos, iconos y tipografía se muestran correctamente porque están empaquetados en el build

#### Scenario: Build multiplataforma

- **GIVEN** que se ejecutan los pasos documentados de instalación y build
- **WHEN** se construye el frontend
- **THEN** el build finaliza correctamente en el sistema operativo soportado sin pasos exclusivos de otra plataforma
