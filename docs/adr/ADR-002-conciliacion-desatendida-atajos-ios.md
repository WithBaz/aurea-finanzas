# ADR-002: Ingesta y Conciliación Desatendida de Pagos mediante Atajos de iOS (Apple Shortcuts)

## Estado
Aceptado

## Contexto
El usuario necesita registrar automáticamente pagos realizados mediante **Apple Pay** y transacciones notificadas por **SMS** de bancos colombianos (Bancolombia, Nequi, Daviplata). En el sistema operativo iOS, las políticas de seguridad y sandboxing prohíben estrictamente que cualquier app externa lea los mensajes SMS de la bandeja de entrada o intercepte transacciones del sistema sin intervención expresa del usuario.

## Decisión
Aprovechar la plataforma nativa de **Automatizaciones de Atajos de iOS (Apple Shortcuts)** presente de forma gratuita en todos los iPhone modernos. Se configuran dos disparadores personales:
1. **Trigger de Transacción Apple Pay:** Dispara una acción HTTP POST cada vez que el usuario paga con su tarjeta en Apple Pay, enviando monto, comercio y tarjeta.
2. **Trigger de Recepción de SMS:** Dispara una acción HTTP POST cuando entra un SMS cuyo remitente contenga palabras clave bancarias ("Bancolombia", "Nequi", "DaviPlata").

En el backend de AUREA, se implementa un endpoint `/api/v1/webhooks/ios-shortcut` con un motor de expresiones regulares (*Regex Parser*) que descompone el mensaje, extrae monto, comercio, fecha, e identifica si se trata de un egreso, ingreso o retiro en cajero automático.

## Consecuencias
* **Positivas:** Registro 100% automático sin fricción, compatible con las directivas de seguridad de Apple, sin necesidad de librerías privadas ni jailbreak.
* **Negativas:** Requiere una configuración inicial de 2 minutos por parte del usuario en la app *Atajos* de su iPhone (documentada paso a paso en `docs/shortcuts/`).
