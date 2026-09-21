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


---

## Sesión 3: 21 de Septiembre de 2026 - PWA Autónoma iOS, Apple Intelligence NLP y Gestión de Cuentas Reales

### 1. Requerimientos del Usuario
* **Autonomía Móvil Total:** Usar la aplicación en el iPhone como una app nativa en la Pantalla de Inicio, sin depender de tener el PC encendido 24/7 ni pagar los $99 USD/año del Apple Developer Program.
* **Eliminación de Marcos Simulados:** Ajustar el diseño visual para que no se muestre como "un celular dentro de otro", aprovechando la pantalla completa de borde a borde (*edge-to-edge*) con *safe areas* de iOS.
* **Eliminación Definitiva de Datos Demo:** Retirar botones de "borrar datos demo" y transacciones simuladas; la aplicación queda limpia y lista para uso real.
* **Gestión Total de Cuentas y Saldos:** Permitir registrar saldos en todas las cuentas bancarias (Bancolombia, Nequi, Nu, Daviplata, Efectivo) y agregar nuevas cuentas.
* **Entrada Rápida con Apple Intelligence / Siri:** Registrar gastos por dictado de voz o texto libre (ej: *"Pagué 15 mil de taxi en efectivo"*).
* **Detección Automática y Pregunta Inteligente de Cuenta:** Detectar la cuenta usada o presentar un selector de 1 toque si el gasto no especifica la fuente de dinero.

### 2. Implementaciones Realizadas
* **Arquitectura de Despliegue en la Nube (Opción B):**
  * Configuración Serverless con FastAPI en Vercel (`api/index.py`, `vercel.json`) y Render (`render.yaml`).
  * PWA nativa con `apple-mobile-web-app-capable`, `status-bar-style: black-translucent` y viewport viewport-fit=cover.
* **Servicio NLP Apple Intelligence (`backend/app/services/nlp_expense_parser.py`):**
  * Extracción inteligente de montos colombianos ("15 mil", "25k", "$45.000", "8500").
  * Detección contextual de cuenta (Efectivo, Débito, Crédito, Nu/Rendimiento) y concepto.
  * Endpoint `POST /api/v1/transacciones/ia-rapida` con retorno `status: "requiere_cuenta"` si la cuenta es ambigua.
* **Asignación y Rebalanceo Dinámico (`PATCH /transacciones/{id}/asignar-cuenta`):**
  * Rebalanceo automático de saldos entre cuentas de origen si el usuario cambia la cuenta asignada.
* **Refactorización de Interfaz Nativa (`backend/app/main.py`):**
  * Eliminación de bordes simulados y dynamic islands ficticias; diseño puro Tailwind CSS oscuro para OLED de iPhone.
  * Barra de Apple Intelligence con gradiente Siri y botón de dictado/voz.
  * Modal interactivo de creación de cuentas y edición rápida de saldos en 1 toque.
  * Modal emergente cuando un gasto requiere confirmar la cuenta de pago.
* **Pruebas Automatizadas:**
  * Configuración centralizada `tests/conftest.py`.
  * Cobertura de 23 tests unitarios en `pytest` pasando al 100% en < 0.4s.
