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
   Uso de SQLite con SQLAlchemy 2.0 para garantizar portabilidad en entornos de desarrollo local, pruebas y despliegue rápido sin requerir servidores externos complejos de base de datos.
2. **Frontend Nativo:**  
   React Native con Expo para permitir pruebas directas en iPhone vía Expo Go con componentes nativos táctiles y respuesta háptica.
