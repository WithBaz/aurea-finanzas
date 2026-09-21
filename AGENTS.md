# Directrices Operativas para Agentes de IA - Proyecto AUREA

Este documento define el contexto operativo, estándares de ingeniería, convenciones de código y restricciones técnicas para cualquier agente de Inteligencia Artificial que colabore en el desarrollo del sistema **AUREA** (**A**dministración **U**nificada de **R**ecursos, **E**gresos y **A**horro).

---

## 1. Misión del Sistema
Construir una plataforma financiera personal integral con experiencia móvil nativa para iPhone (React Native / Expo), impulsada por un backend en FastAPI que realiza conciliación desatendida mediante **Atajos de iOS (Apple Shortcuts)** para pagos de **Apple Pay** y **SMS bancarios colombianos** (Bancolombia, Nequi, Daviplata), adaptada a un ciclo de nómina mensual en Pesos Colombianos (COP).

---

## 2. Convenciones de Ingeniería y Estándares de Código

### A. Backend (Python 3.12+ / FastAPI)
* **Tipado Estricto:** Uso obligatorio de anotaciones de tipo (`typing`, `Union`, `Optional`, `list[T]`) en todas las funciones y métodos.
* **Validación de Datos:** Esquemas de entrada y salida desacoplados utilizando **Pydantic V2**.
* **Persistencia:** SQLAlchemy 2.0 con sintaxis moderna (`select`, `session.scalars()`). Claves foráneas activas (`PRAGMA foreign_keys=ON;` en SQLite).
* **Manejo Monetario:** Todos los montos se manejan como enteros o flotantes redondeados en COP (sin centavos fraccionarios en display, formato colombiano `$ 1.250.000 COP`).

### B. Ingesta y Webhooks de Atajos iOS
* Todo endpoint receptor de webhooks debe ser **idempotente** (evitar duplicar cobros si un atajo se dispara dos veces).
* Las transferencias internas (como retiros en cajero) deben acreditar a la billetera de efectivo y debitar de la cuenta bancaria sin computar doble gasto en el semáforo mensual.

### C. Control de Versiones (Git)
* Commits semánticos con la especificación *Conventional Commits*:
  * `feat:` Nueva funcionalidad o regla de negocio.
  * `fix:` Corrección de errores.
  * `test:` Adición o modificación de pruebas unitarias/integración.
  * `docs:` Cambios o adiciones a documentación y ADRs.
  * `refactor:` Mejoras en código sin alterar comportamiento externo.

---

## 3. Filosofía de Pruebas Automatizadas
* Cada nueva regla de negocio (ej. fórmula del semáforo diario, parser de nuevos bancos, cálculo de cuotas de tarjeta de crédito) debe contar con pruebas unitarias en `pytest`.
* Cobertura prioritaria en:
  1. Regex y extractores de texto de SMS y Apple Pay.
  2. Rebalanceo de cuentas en transferencias internas y retiros.
  3. Proyección de rendimientos diarios (cuentas de alto rendimiento).
