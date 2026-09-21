# Bitácora de Desarrollo con IA - Proyecto AUREA

Registro cronológico y auditable de las interacciones, decisiones técnicas, prompts y evolución del desarrollo conjunto entre el usuario y el asistente de Inteligencia Artificial (Antigravity).

---

## Sesión 1: 21 de Septiembre de 2026 - Ideación, Arquitectura y Gobernanza

### 1. Contexto Inicial y Solicitud del Usuario
* **Requerimiento:** Creación de una aplicación de finanzas personales diseñada para iPhone, con publicación y trazabilidad en GitHub bajo el mismo estándar de calidad y gobernanza del proyecto de veterinaria (`proud-pascal`).
* **Necesidades Específicas Planteadas:**
  * Uso de la app en iPhone (el usuario navega en Google Chrome y busca sensación 100% nativa de App Store).
  * Moneda principal en Pesos Colombianos (COP).
  * Ingesta automática de transacciones vía **Apple Pay** y **SMS bancarios**.
  * Ciclo de nómina mensual (30 días).
  * Instrumentos financieros: Tarjetas de crédito, débito, cuentas remuneradas de alto rendimiento (Nu/Lulo) y efectivo físico.
  * Nombre corto en siglas con significado profundo.

### 2. Respuestas y Decisiones de Diseño de la IA
* **Selección del Nombre:** El usuario seleccionó **AUREA** (**A**dministración **U**nificada de **R**ecursos, **E**gresos y **A**horro), con inspiración en la Proporción Áurea de equilibrio perfecto.
* **Resolución de la Plataforma Móvil:**
  * Se analizó PWA vs. React Native. Dado que el usuario usa Chrome en iOS y desea experiencia nativa idéntica a la App Store con respuesta táctil fluida, se adoptó **React Native (Expo)** y se complementó con endpoints Swagger y vista web interactiva para pruebas inmediatas en Windows.
* **Solución de Integración iOS para Apple Pay y SMS:**
  * Ante las restricciones del sandbox de iOS, se diseñó la solución mediante **Automatizaciones de Atajos de iOS (Apple Shortcuts)** que invocan un Webhook REST en el backend de FastAPI.
* **Regla de Negocio de Retiros de Cajero:**
  * El parser clasifica los retiros en cajero como transferencias internas hacia la billetera de efectivo, evitando computarlos erróneamente como gastos.

### 3. Artefactos y Código Producido
* Creación de `implementation_plan.md` y aprobación explícita por el usuario.
* Configuración de gobernanza: `.gitignore`, `.github/workflows/ci.yml`, `AGENTS.md`, `ASSUMPTIONS.md`, `BITACORA-IA.md`.
* Documentación de Decisiones de Arquitectura: `ADR-001`, `ADR-002`, `ADR-003`.
* Guías de configuración de Atajos de iOS: `docs/shortcuts/`.
