# AUREA - Administración Unificada de Recursos, Egresos y Ahorro

Plataforma inteligente de finanzas personales diseñada para iPhone y ecosistemas móviles modernos, impulsada por un backend en FastAPI y una aplicación móvil nativa en React Native (Expo). Integra conciliación desatendida en tiempo real para **Apple Pay** y **SMS bancarios colombianos** (Bancolombia, Nequi, Daviplata) mediante Atajos de iOS, con soporte para ciclo de nómina mensual en Pesos Colombianos (COP), gestión multi-instrumento (débito, crédito, cuentas de alto rendimiento y efectivo) y semáforo dinámico de gasto diario.

---

## 📌 Problemática que Resuelve

Llevar el control de las finanzas personales suele fracasar por tres grandes fricciones cotidianas:
1. **La Fricción del Registro Manual:** El 90% de las personas deja de usar apps financieras porque abrir la app y escribir cada compra de \$10.000 o \$50.000 COP resulta tedioso y fácil de olvidar.
2. **Desconexión con el Ecosistema Colombiano:** Las apps internacionales asumen quincenas o semanas, dólares o euros con centavos, e ignoran la realidad de las cuentas de alto rendimiento remuneradas (Nu Colombia, Lulo, Pibank), las tarjetas de crédito con fechas de corte específicas y los retiros de cajero.
3. **El Error de Duplicar Retiros en Efectivo:** La mayoría de herramientas computan un retiro en cajero como un "gasto", y luego vuelven a computar el gasto cuando pagas en efectivo, duplicando artificialmente las salidas de dinero.

**AUREA** resuelve esto automatizando la ingesta de transacciones en segundo plano desde el iPhone (vía Apple Pay y lectura de SMS de bancos colombianos), conciliando retiros como transferencias internas y guiando tus decisiones de gasto con un **Semáforo Diario de Presupuesto Mensual**.

---

## 🎯 Capacidades Principales y Reglas de Negocio

* **Conciliación Desatendida con Atajos de iOS:**
  * **Apple Pay:** Registra el pago en milisegundos con comercio, monto exacto en COP y tarjeta utilizada.
  * **SMS Bancarios (Colombia):** Parser con expresiones regulares para Bancolombia, Nequi, Daviplata y Davivienda.
* **Inteligencia de Retiros de Cajero:**  
  Un retiro en cajero automático debita la cuenta de ahorros y acredita automáticamente la billetera física de *Efectivo*, sin computarlo como gasto mensual.
* **Ciclo Salarial Mensual & Semáforo de Gasto Diario:**  
  Calcula dinámicamente tu disponible diario dividiendo el saldo libre de compromisos fijos entre los días restantes del mes activo.
  * 🟢 **Verde:** Gasto dentro del rango seguro diario.
  * 🟡 **Amarillo:** Gasto cercano al umbral diario.
  * 🔴 **Rojo:** Exceso de gasto diario; redistribución automática para los días venideros.
* **Monitoreo de 4 Instrumentos Financieros:**
  * **Débito:** Cuentas corrientes y de ahorros operativas.
  * **Crédito:** Monitoreo de cupo disponible, fecha de corte y fecha límite de pago.
  * **Cuentas de Alto Rendimiento:** Devengo y proyección de intereses diarios (tasa E.A. de cuentas Nu, Lulo, Pibank).
  * **Efectivo Físico:** Control del dinero de bolsillo con registro ágil.
* **Auto-Categorización Inteligente por Comercio:**  
  Catálogo precargado de comercios colombianos (D1, Éxito, Ara, Terpel, Oxxo, Rappi, Uber, etc.) con aprendizaje adaptativo para nuevos establecimientos.

---

## 🧱 Modelo de Dominio

1. **Cuenta:** Instrumento financiero con balance en COP (Débito, Crédito, Alto Rendimiento, Efectivo).
2. **Categoria:** Clasificación del movimiento (Alimentación, Transporte, Ocio, Servicios, Ahorro, etc.) con palabras clave para matching de comercios.
3. **Transaccion:** Registro del movimiento (monto, tipo: ingreso/egreso/transferencia interna, fecha, comercio, medio: Apple Pay/SMS/Manual).
4. **MetaAhorro:** Objetivos financieros con meta monetaria, saldo ahorrado acumulado y fecha objetivo.
5. **ConfiguracionPresupuesto:** Parámetros del usuario (día de cobro de nómina mensual, compromisos fijos, meta de ahorro).

---

## 🛠️ Stack Tecnológico

* **Backend:** Python 3.12+ con **FastAPI** (asíncrono, OpenAPI Swagger interactivo)
* **Persistencia:** **SQLAlchemy 2.0** con SQLite y claves foráneas activadas
* **Validación y Modelado:** **Pydantic V2**
* **Frontend Móvil (iOS):** **React Native** con **Expo** (experiencia nativa táctil en iPhone vía Expo Go)
* **Suite de Pruebas:** **Pytest** con TestClient (validación exhaustiva del parser de SMS y cálculos en COP)

---

## 🚀 Instalación y Puesta en Marcha (Desde Cero)

### Método 1: Inicio Rápido en 1 Clic (Recomendado para Windows)
El proyecto incluye el ejecutable [`iniciar_sistema.bat`](iniciar_sistema.bat) en la raíz:
1. Haz **doble clic** sobre `iniciar_sistema.bat`.
2. El script detectará el entorno virtual Python (lo creará si no existe), instalará dependencias, sembrará datos de prueba colombianos (`seed.py`) y levantará el backend y la vista interactiva:
   * **Dashboard & Simulador Móvil:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
   * **Documentación Swagger:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### Método 2: Instalación Manual por Terminal

```bash
# 1. Configurar entorno virtual Python
python -m venv .venv
.venv\Scripts\activate  # En Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

# 2. Poblar base de datos inicial con datos colombianos en COP
python -m backend.app.seed

# 3. Iniciar el servidor backend
uvicorn backend.app.main:app --reload --port 8000
```

---

### Método 3: Despliegue en la Nube (Vercel / Render) & Uso Standalone en iPhone (Sin PC)

El proyecto incluye preconfiguración oficial para **Vercel** ([`vercel.json`](vercel.json), [`api/index.py`](api/index.py)) y **Render** ([`render.yaml`](render.yaml)):

1. Inicia sesión en [Vercel](https://vercel.com) con tu cuenta de GitHub.
2. Haz clic en **Add New...** $\rightarrow$ **Project**.
3. Selecciona tu repositorio `WithBaz/aurea-finanzas` y haz clic en **Import**.
4. Haz clic en **Deploy**. En menos de 1 minuto tendrás tu URL HTTPS pública y activa (ej. `https://aurea-finanzas.vercel.app`).
5. **En tu iPhone:** Abre esa URL en Safari o Chrome, toca **"Compartir"** $\rightarrow$ **"Agregar a pantalla de inicio"**.
6. ¡Listo! AUREA se abrirá a pantalla completa como una app independiente en tu teléfono, sin depender de tu PC ni de Expo Go, con tus atajos de Apple Pay y SMS recibiendo pagos las 24 horas del día.

---

### Método 4: Ejecutar en tu iPhone en Desarrollo con Expo Go

1. Descarga la aplicación gratuita **Expo Go** desde la App Store en tu iPhone.
2. En una terminal dentro de la carpeta `mobile/`:
   ```bash
   cd mobile
   npx expo start --tunnel
   ```
3. Escanea el código QR con la cámara de tu iPhone para abrir el entorno de desarrollo nativo.

---

## 🧪 Pruebas Automatizadas

El sistema cuenta con una suite completa de pruebas unitarias y de integración que validan el parseo de SMS de bancos colombianos, retiros en cajero, cálculos del semáforo diario y rendimientos de cuentas:
```bash
pytest -v
```

---

## 📡 Resumen de Endpoints de la API REST

| Módulo | Método | Endpoint | Descripción |
|---|---|---|---|
| **Webhooks iOS** | `POST` | `/api/v1/webhooks/ios-shortcut` | Ingesta desatendida para pagos Apple Pay y SMS bancarios |
| **Métricas** | `GET` | `/api/v1/metricas/semaforo` | Semáforo diario, disponible real y ritmo del mes (30 días) |
| **Métricas** | `GET` | `/api/v1/metricas/rendimientos` | Rendimientos diarios devengados en cuentas remuneradas (Nu/Lulo) |
| **Cuentas** | `GET` / `POST` | `/api/v1/cuentas` | Listar y crear cuentas (Débito, Crédito, Rendimiento, Efectivo) |
| **Transacciones** | `GET` / `POST` | `/api/v1/transacciones` | Listar con filtros y registrar transacciones manuales |
| **Metas** | `GET` / `POST` | `/api/v1/metas` | Consultar y crear metas de ahorro gamificadas |
| **Seed** | `POST` | `/api/v1/seed` | Cargar catálogo de comercios y datos de prueba en COP |

---

## 📁 Documentación de Arquitectura y Gobernanza

* [AGENTS.md](AGENTS.md): Directrices operativas y estándares de ingeniería para IA.
* [ASSUMPTIONS.md](ASSUMPTIONS.md): Supuestos técnicos y reglas de negocio del ecosistema financiero colombiano.
* [BITACORA-IA.md](BITACORA-IA.md): Bitácora histórica auditable de trabajo con IA.
* [ADR-001: Selección del Stack Tecnológico](docs/adr/ADR-001-seleccion-stack-react-native-fastapi.md)
* [ADR-002: Ingesta Desatendida vía Atajos de iOS](docs/adr/ADR-002-conciliacion-desatendida-atajos-ios.md)
* [ADR-003: Modelo Financiero en COP](docs/adr/ADR-003-modelo-financiero-colombia-cop.md)
* [Guía: Atajo de Apple Pay para iPhone](docs/shortcuts/atajo-apple-pay.md)
* [Guía: Atajo de SMS Bancarios para iPhone](docs/shortcuts/atajo-sms-bancarios.md)
