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
* Publicación progresiva de 15 commits semánticos en el repositorio GitHub `WithBaz/aurea-finanzas`.

---

## Sesión 2: 21 de Septiembre de 2026 - Puesta en Marcha en iPhone, Migración a SDK 57 y Refinamiento de UX

### 1. Diagnósticos y Soluciones en Entorno Móvil iOS
* **Incidencia 1: Error de Conectividad Inicial en Red Local**
  * *Síntoma:* Expo Go no lograba conectarse con el servidor en la IP local del PC (`could not connect to the server`).
  * *Solución:* Instalación de `@expo/ngrok` y activación del modo túnel seguro (`npx expo start --tunnel`), permitiendo la conexión a través de cualquier red Wi-Fi o datos celulares sin bloqueos de firewall.
* **Incidencia 2: Incompatibilidad de Versión de Expo Go en iPhone**
  * *Síntoma:* La app Expo Go en el iPhone requería **SDK 57.0.0**, mientras el proyecto base estaba en SDK 51.
  * *Solución:* Migración integral del proyecto React Native a **Expo SDK 57**, actualizando dependencias alineadas: `expo@~57.0.24`, `react@19.2.3`, `react-native@0.86.3`, `expo-haptics@~57.0.3` y `expo-linear-gradient@~57.0.2`.
* **Incidencia 3: Paridad de Sesión de Cuenta Expo**
  * *Síntoma:* Expo Go solicitó paridad de autenticación (`You're signed in to Expo Go as 'withbaz', but not signed in to Expo CLI`).
  * *Solución:* Orientación al usuario para vinculación directa o lectura anónima.

### 2. Refinamiento de Interfaz de Usuario (UX)
* **Reubicación del Botón de Registro de Gastos (`+ Gasto`):**
  * El botón original en la esquina superior derecha colisionaba con el botón flotante nativo de herramientas de Expo Go.
  * Se rediseñó la experiencia incorporando un **Botón de Acción Flotante (FAB - Floating Action Button)** prominente y centrado en la barra de navegación inferior (al estilo de apps financieras como Nequi y Nu), garantizando ergonomía táctil con el pulgar y cero interferencias con controles del sistema operativo.
