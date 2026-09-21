# Guía de Configuración: Atajo de Apple Pay para iPhone

Aprende a configurar en menos de 2 minutos la automatización nativa de iOS para que cada vez que pagues con tu tarjeta en Apple Pay, se envíe el registro automático a **AUREA**.

---

## Requisitos
* iPhone con iOS 14 o superior.
* Al menos una tarjeta configurada en la app **Wallet (Cartera)** de Apple.
* Servidor de AUREA activo (en tu red local o desplegado en la nube con URL HTTPS).

---

## Paso a Paso en tu iPhone

1. Abre la aplicación **Atajos** (*Shortcuts*) en tu iPhone.
2. Toca la pestaña inferior **Automatización**.
3. Toca el botón **Nueva automatización** (o el botón `+` en la esquina superior derecha).
4. Desplázate hacia abajo y selecciona la opción **Transacción** (*Transaction*).
5. Configura los parámetros:
   * **Tarjeta:** Selecciona *Cualquier tarjeta* (o tu tarjeta principal).
   * **Categoría:** *Cualquier categoría*.
   * **Comercio:** *Cualquier comercio*.
   * **Momento:** Selecciona **Ejecutar de inmediato** (*Run Immediately*) y desactiva *Preguntar antes de ejecutar*.
6. Toca **Siguiente**.
7. En la pantalla de acciones, busca y agrega la acción **Obtener contenido de URL** (*Get Contents of URL*):
   * **URL:** `https://tu-servidor-aurea.com/api/v1/webhooks/ios-shortcut`
   * **Método:** `POST`
   * **Encabezados (Headers):**
     * `Content-Type`: `application/json`
   * **Cuerpo de la petición (Request Body):** Selecciona `JSON` y añade los siguientes campos con las variables de la transacción provistas por iOS:
     * `medio`: Texto `APPLE_PAY`
     * `monto`: Variable `Monto` de la transacción
     * `comercio`: Variable `Comercio` de la transacción
     * `tarjeta`: Variable `Nombre de la tarjeta`
8. Toca **Listo** en la esquina superior.

¡Listo! Cada vez que apoyes tu iPhone en un datáfono con Apple Pay, el cobro viajará en milisegundos a AUREA sin que tengas que abrir la aplicación.
