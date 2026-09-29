# AUREA — Administración Unificada de Recursos, Egresos y Ahorro

[![Python 3.12](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PWA Ready](https://img.shields.io/badge/PWA-iOS%20Standalone-000000?style=flat&logo=apple&logoColor=white)](https://apple.com)
[![Tests Passing](https://img.shields.io/badge/Tests-59%2F59%20Passing-success?style=flat&logo=pytest&logoColor=white)](tests/)
[![Security Audited](https://img.shields.io/badge/Security-OWASP%20Hardened-blueviolet?style=flat&logo=shield)](tests/test_security_audit.py)

Plataforma financiera personal integral y de alta seguridad, adaptada al contexto bancario colombiano en Pesos Colombianos (COP) y diseñada para una experiencia nativa en **iPhone** (PWA autónoma con soporte Face ID y cliente móvil en React Native / Expo). 

AUREA automatiza la conciliación desatendida en tiempo real para **Apple Pay** y **SMS bancarios** (Bancolombia, Nequi, Daviplata, Davivienda) mediante Atajos de iOS, administra tarjetas de crédito con fechas de corte y pagos inteligentes, aparta compromisos fijos del ciclo de nómina mensual, proyecta rendimientos diarios de cuentas remuneradas y guía las decisiones financieras mediante un **Semáforo Dinámico de Gasto Diario**.

---

## 🌐 Estado del Sistema: Desplegado y Listo para Producción

El sistema se encuentra **completamente desplegado y operativo en la nube**, permitiendo su uso continuo las 24 horas del día desde el iPhone sin depender de mantener encendida una computadora personal:

* **URL de Producción (Web / PWA):** Desplegado en Vercel (`https://aurea-finanzas.vercel.app` o tu dominio personalizado).
* **Endpoints de API / Webhooks:** Activos bajo protocolo HTTPS seguro con cabeceras de blindaje OWASP.
* **Integración con Atajos de iOS:** Webhooks listos para recibir eventos de Apple Pay, SMS y comandos por voz de Siri / Apple Intelligence.

---

## 📱 Cómo Usar la Aplicación en tu iPhone (PWA Standalone)

Para disfrutar de AUREA con experiencia de aplicación nativa sin barra de navegación:

1. **Abrir en Safari:** Ingresa a la URL de producción desde tu iPhone.
2. **Agregar a la Pantalla de Inicio:**
   * Toca el botón **Compartir** (icono central con flecha hacia arriba en Safari).
   * Desplázate hacia abajo y selecciona **"Agregar a pantalla de inicio"** (icono `+`).
   * Toca **"Agregar"** en la esquina superior derecha.
3. **Acceso Standalone:**
   * Abre el icono de **AUREA** creado en tu pantalla de inicio.
   * Se iniciará a pantalla completa (*edge-to-edge*), respetando el Dynamic Island y las áreas seguras (*safe areas*) de iOS.
   * Disfruta de autenticación biométrica Face ID, cambio de Modo Claro/Oscuro y registro ágil.

---

## 💻 Cómo Probar o Desarrollar en tu Máquina Local

Cualquier persona puede clonar, levantar y probar AUREA localmente en pocos minutos.

### Prerrequisitos
* **Python 3.12+** instalado.
* **Git** instalado.
* *(Opcional)* **Node.js 18+** si deseas ejecutar la aplicación móvil nativa alternativa en `mobile/`.

---

### Opción 1: Inicio Rápido en 1 Clic (Windows)
El proyecto incluye un script automatizado en la raíz:
1. Haz doble clic en el archivo [`iniciar_sistema.bat`](iniciar_sistema.bat).
2. El script creará el entorno virtual `.venv`, instalará dependencias, sembrará los datos base e iniciará el servidor:
   * **App Web / Dashboard:** [http://localhost:8000](http://localhost:8000)
   * **Documentación Interactiva Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Opción 2: Instalación Manual por Terminal (Windows / macOS / Linux)

```bash
# 1. Clonar el repositorio
git clone https://github.com/WithBaz/aurea-finanzas.git
cd aurea-finanzas

# 2. Crear y activar el entorno virtual de Python
# En Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# En macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias del backend
pip install -r requirements.txt

# 4. (Opcional) Cargar catálogo de comercios y datos colombianos de prueba
python -m backend.app.seed

# 5. Iniciar el servidor local
uvicorn backend.app.main:app --reload --port 8000
```

Accede a:
* **Aplicación en vivo:** [http://localhost:8000](http://localhost:8000)
* **Documentación Swagger / OpenAPI:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Opción 3: Ejecutar la Suite de Pruebas Automatizadas

AUREA cuenta con **59 pruebas automatizadas** que cubren reglas de negocio en COP, parsers bancarios, cálculos financieros y auditoría estricta de seguridad:

```bash
# Ejecutar todas las pruebas con reporte detallado
pytest -v
```

---

### Opción 4: Ejecutar la App Móvil Alternativa con Expo (React Native)

Si deseas probar la variante nativa en React Native con Expo Go en tu celular:

```bash
cd mobile
npm install
npx expo start --tunnel
```

Escanea el código QR resultante con la cámara de tu iPhone para abrir el proyecto en **Expo Go**.

---

## 🎯 Capacidades Principales y Reglas de Negocio

### 1. Conciliación Desatendida con Atajos de iOS (Apple Shortcuts)
* **Apple Pay:** Detecta transacciones al instante extrayendo comercio, monto exacto en COP y tarjeta empleada.
* **SMS Bancarios (Colombia):** Motor de expresiones regulares optimizado para SMS de **Bancolombia, Nequi, Daviplata y Davivienda**.
* **Inteligencia de Retiros en Cajero:** Un retiro en cajero debita la cuenta bancaria y acredita automáticamente la *Billetera de Efectivo*, evitando computar una doble salida de dinero en el presupuesto mensual.

### 2. Gestión Integral de Tarjetas de Crédito
* **Control de Cupo y Deuda:** Monitoreo en tiempo real de cupo total, cupo disponible y saldo adeudado.
* **Corte de Tarjeta (`/corte`):** Fija el saldo facturado del periodo y actualiza el estado a `PENDIENTE_PAGO`.
* **Pago Inteligente (`/pagar`):** Al abonar o pagar la tarjeta desde una cuenta de débito/ahorros, se descuenta de la cuenta origen y se restaura el cupo disponible sin registrar doble gasto en el semáforo.

### 3. Ciclo Salarial Mensual & Semáforo Dinámico
* **Ciclo en Pesos Colombianos (COP):** Diseñado para nómina mensual (generalmente día 30).
* **Apartado Automático de Compromisos Fijos:** Arriendos, servicios, suscripciones y metas de ahorro se descuentan inmediatamente del presupuesto operativo.
* **Semáforo Diario de Gasto:**
  * 🟢 **Verde:** Gasto dentro del presupuesto diario seguro.
  * 🟡 **Amarillo:** Gasto cercano al límite diario sugerido.
  * 🔴 **Rojo:** Exceso de gasto; redistribución automática para los días restantes del mes.

### 4. Cuentas Remuneradas de Alto Rendimiento
* Cálculo y proyección diaria de intereses devengados para cuentas colombianas de alto rendimiento (ej: **Nu Colombia**, **Lulo Bank**, **Pibank**) aplicando la fórmula de tasa Efectiva Anual (E.A.) convertida a tasa diaria.

### 5. Asistente por Dictado de Voz / Siri (NLP Smart Parser)
* Registro rápido de transacciones mediante lenguaje natural (ej. *"Pagué 15 mil de taxi en efectivo"*, *"Almuerzo 22k con Bancolombia"*, *"Recibí 100 mil de nómina"*).
* Endpoint `/api/v1/transacciones/ia-rapida` con detección inteligente de montos en miles, comercios y cuentas asociadas.

### 6. Experiencia Visual Apple (Modo Claro / Modo Oscuro)
* Interfaz con diseño nativo de Apple: soporte completo para **Modo Oscuro OLED** (`#000000`) y **Modo Claro** (`#F2F2F7`), con selector persistente y tipografía SF Pro.

---

## 🛡️ Seguridad, Auditoría y Aislamiento de Datos

El backend de AUREA cuenta con blindaje de ciberseguridad validado por pruebas unitarias de penetración:

* **Protección contra Peticiones Anónimas:** Ningún usuario no autenticado puede consultar cuentas, transacciones ni métricas financieras una vez registrados los usuarios del sistema (`401 Unauthorized`).
* **Autenticación Criptográfica:** Uso de tokens Bearer (`secrets.token_hex(24)`) y PIN/Contraseña con salt y comparación de tiempo constante (`secrets.compare_digest`).
* **Neutralización de Header Spoofing:** El encabezado `X-Usuario-Id` no se acepta como mecanismo de autenticación en solitario. Discrepancias entre token y usuario se rechazan con `403 Forbidden`.
* **Anti-IDOR Estricto:** Se previene manipulación cruzada en `/transacciones`, `/cuentas`, `/ia-rapida`, `/sincronizar` y webhooks.
* **Aislamiento Multi-Usuario en Webhooks:** Los eventos de Apple Pay y SMS solo afectan las cuentas del titular autenticado mediante el token de su atajo.
* **Cabeceras de Seguridad HTTP (OWASP):**
  * `X-Frame-Options: DENY` (anti-clickjacking)
  * `X-Content-Type-Options: nosniff` (anti-MIME-sniffing)
  * `X-XSS-Protection: 1; mode=block`
  * `Referrer-Policy: strict-origin-when-cross-origin`

---

## 📡 Resumen de Endpoints Principales (API REST)

| Módulo | Método | Endpoint | Descripción |
|---|---|---|---|
| **Autenticación** | `POST` | `/api/v1/auth/registro` | Registro de usuario independiente (titular o amigo) |
| **Autenticación** | `POST` | `/api/v1/auth/login` | Inicio de sesión con PIN o contraseña alfanumérica |
| **Autenticación** | `POST` | `/api/v1/auth/face-id-login` | Validación biométrica con Face ID / Touch ID |
| **Autenticación** | `POST` | `/api/v1/auth/cambiar-pin` | Cambio seguro de contraseña con validación de credencial actual |
| **Cuentas** | `GET` / `POST` | `/api/v1/cuentas` | Listar y registrar instrumentos financieros |
| **Cuentas** | `POST` | `/api/v1/cuentas/sincronizar` | Rehidratar cuentas desde caché local (aislado por usuario) |
| **Tarjetas** | `POST` | `/api/v1/cuentas/{id}/corte` | Registrar fecha de corte y facturar saldo adeudado |
| **Tarjetas** | `POST` | `/api/v1/cuentas/{id}/pagar` | Abonar o pagar tarjeta debitando de cuenta de ahorros |
| **Transacciones** | `GET` / `POST` | `/api/v1/transacciones` | Listar con filtros y crear transacciones manuales |
| **Transacciones** | `GET` / `POST` | `/api/v1/transacciones/ia-rapida` | Registro ultra-rápido por voz / NLP para Atajos de Siri |
| **Gastos Fijos** | `GET` / `POST` | `/api/v1/gastos-fijos` | Gestionar compromisos mensuales y apartado de nómina |
| **Métricas** | `GET` | `/api/v1/metricas/dashboard` | Estado consolidado ultrarrápido para el dashboard |
| **Métricas** | `GET` | `/api/v1/metricas/semaforo` | Semáforo diario y cálculo de presupuesto en COP |
| **Métricas** | `GET` | `/api/v1/metricas/rendimientos` | Rendimientos diarios devengados en cuentas Nu/Lulo |
| **Webhooks** | `POST` | `/api/v1/webhooks/ios-shortcut` | Receptor desatendido para Apple Pay y SMS bancarios |

---

## 📚 Documentación Adicional del Repositorio

* [AGENTS.md](AGENTS.md): Convenciones de ingeniería, estándares de tipado Python y reglas de desarrollo.
* [ASSUMPTIONS.md](ASSUMPTIONS.md): Registro técnico de asunciones del modelo financiero colombiano y seguridad.
* [BITACORA-IA.md](BITACORA-IA.md): Bitácora cronológica auditable del desarrollo colaborativo con IA.
* [Guía: Atajo de Apple Pay para iPhone](docs/shortcuts/atajo-apple-pay.md)
* [Guía: Atajo de SMS Bancarios para iPhone](docs/shortcuts/atajo-sms-bancarios.md)
* [Guía: Atajo de Apple Intelligence / Voz para iPhone](docs/shortcuts/atajo-apple-intelligence-voz.md)
* [ADR-001: Selección del Stack Tecnológico](docs/adr/ADR-001-seleccion-stack-react-native-fastapi.md)
* [ADR-002: Ingesta Desatendida vía Atajos de iOS](docs/adr/ADR-002-conciliacion-desatendida-atajos-ios.md)
* [ADR-003: Modelo Financiero en COP](docs/adr/ADR-003-modelo-financiero-colombia-cop.md)
