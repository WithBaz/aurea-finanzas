# Registro de Asunciones Técnicas y de Negocio - AUREA

Este documento recoge de manera transparente los supuestos, restricciones y decisiones asumidas para el diseño del sistema **AUREA**.

---

## 1. Asunciones de Dominio Financiero (Colombia - COP)

1. **Moneda y Decimales:**  
   La divisa oficial del sistema es el Peso Colombiano (COP). Dado que en Colombia no circulan monedas fraccionarias de centavos en el uso cotidiano, las operaciones monetarias se redondean a números enteros, con formato visual de separador de miles por punto (ej. `$ 1.500.000 COP`).
2. **Ciclo Salarial Mensual:**  
   El usuario percibe sus ingresos bajo un esquema de nómina mensual (generalmente los días 30 o último día de cada mes calendario). El semáforo de gasto divide el presupuesto disponible real entre los días restantes del ciclo mensual activo.
3. **Manejo de Instrumentos Financieros:**  
   * **Débito / Ahorros:** Descuentan inmediatamente el saldo disponible.
   * **Crédito:** Incrementan la deuda acumulada de la tarjeta y reducen el cupo disponible. Registran fecha de corte y de pago.
   * **Cuentas de Rendimiento Remuneradas:** Cuentas líquidas (ej. Nu Colombia al ~12-13% E.A.) que devengan intereses diarios acreditados al balance.
   * **Efectivo:** Considerado una billetera física. Los retiros en cajero se concilian como transferencias entre cuenta bancaria y efectivo, no como gastos.

---

## 2. Asunciones de Plataforma e Integración Móvil (iOS)

1. **Privacidad del Sandbox de iOS:**  
   Las aplicaciones de terceros en iOS no pueden acceder de forma arbitraria a la base de datos de mensajes SMS ni monitorear silenciosamente Apple Pay en segundo plano sin consentimiento del usuario.
2. **Arquitectura de Ingesta vía Atajos de Apple (Shortcuts):**  
   Se asume el uso de la funcionalidad nativa de automatizaciones personales en la app *Atajos* de iOS. Estas automatizaciones se disparan al detectar transacciones de Apple Pay o la llegada de SMS de remitentes bancarios autorizados, enviando una petición HTTP POST al backend de AUREA.
3. **Idempotencia de Transacciones:**  
   Se utiliza un hash de firma basado en (fecha, monto, comercio, cuenta) o un identificador de transacción para evitar registros duplicados en caso de reintentos de red del atajo.

---

## 3. Asunciones Tecnológicas

1. **Persistencia Portable:**  
   Uso de SQLite con SQLAlchemy 2.0 para garantizar portabilidad en entornos de desarrollo local, pruebas y despliegue rápido sin requerir servidores externos complejos de base de datos, con plena compatibilidad para PostgreSQL en entornos de producción persistente.
2. **Frontend Nativo y PWA Autónomo:**  
   Arquitectura dual: aplicación en React Native con Expo para pruebas en Expo Go, combinada con Progressive Web App (PWA) optimizada para Safari en iPhone (`apple-mobile-web-app-capable`, *safe areas*, temas Dark/Light nativos) que elimina la dependencia de compilaciones o cuentas de desarrollador de Apple.

---

## 4. Asunciones de Seguridad, Control de Acceso y Multi-Tenant

1. **Aislamiento Estricto de Datos:**  
   Cada usuario registrado (titular o amigos) posee un espacio de datos estrictamente aislado. Ningún usuario puede consultar, editar, eliminar ni transferir saldos de cuentas pertenecientes a otro usuario (prevención total de IDOR).
2. **Autenticación Criptográfica:**  
   El acceso a los recursos protegidos exige la presentación de un token Bearer criptográfico válido (`secrets.token_hex(24)`). No se confía en encabezados descriptivos como `X-Usuario-Id` sin validación del token de sesión.
3. **Protección contra Peticiones Anónimas:**  
   Una vez que existen usuarios registrados en la base de datos, todos los endpoints de consulta y manipulación financiera exigen autenticación obligatoria (`401 Unauthorized`).
4. **Validación Biométrica Segura:**  
   El flujo de Face ID / Touch ID valida credenciales de forma criptográfica y respeta el estado de activación configurado por el usuario en su perfil.

---

## 5. Asunciones de Despliegue en Producción

1. **Ejecución Continua en la Nube:**  
   El backend se ejecuta en una plataforma serverless / contenedor en la nube (ej. Vercel o Render) con soporte HTTPS, permitiendo que las automatizaciones de Atajos de iOS envíen pagos en tiempo real sin requerir una máquina local encendida.
2. **Rehidratación y Resiliencia en Contenedores Efímeros:**  
   Para entornos de ejecución serverless efímeros, la PWA implementa mecanismos de sincronización protegida desde caché local (`/api/v1/cuentas/sincronizar`), garantizando la preservación del estado financiero.
