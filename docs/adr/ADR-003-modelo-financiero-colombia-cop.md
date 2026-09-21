# ADR-003: Modelo Financiero Adaptado al Ecosistema Colombiano (COP, Ciclo Mensual y Multi-Instrumento)

## Estado
Aceptado

## Contexto
Las aplicaciones de finanzas tradicionales suelen estar diseñadas para mercados anglosajones (ciclo de nómina quincenal o semanal, centavos de dólar/euro, solo cuentas corrientes y crédito). En Colombia, el usuario opera con:
* Moneda sin centavos prácticos (Pesos Colombianos - COP).
* Ciclo salarial estrictamente mensual.
* Múltiples instrumentos: Tarjetas de crédito (con fechas de corte y simulación de cuotas para evitar intereses de mora o usura), cuentas de débito operativas, cuentas de alto rendimiento líquido (Nu Colombia al 12-13% E.A., Lulo, Pibank) y billetera física en efectivo.
* Retiros frecuentes de cajero que no deben computarse como gastos, sino como transferencias internas.

## Decisión
1. **Representación de Moneda:** Valores enteros redondeados en COP, con separadores de miles estándar (`$ X.XXX.XXX COP`).
2. **Semáforo Dinámico Mensual:** Cálculo del presupuesto diario dividiendo el saldo libre de compromisos fijos entre los días calendario restantes del mes activo.
3. **Clasificación de Retiros de Cajero:** Todo SMS de retiro de cajero debita la cuenta de ahorros y acredita automáticamente la billetera física de "Efectivo", sin alterar negativamente el acumulado de gastos del mes.
4. **Devengo Diario de Rendimientos:** Módulo que proyecta y refleja los intereses diarios generados por el capital colocado en cuentas remuneradas con tasa E.A.

## Consecuencias
* **Positivas:** Ajuste perfecto a la realidad financiera real del usuario en Colombia, erradicación de duplicidad de gastos por retiro de efectivo y claridad en el gasto diario.
