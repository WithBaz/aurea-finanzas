# Guía de Configuración: Atajo de SMS Bancarios Colombianos para iPhone

Aprende a configurar la automatización nativa de iOS para que cuando recibas un mensaje de texto de tu banco (Bancolombia, Nequi, Daviplata, etc.), tu iPhone extraiga el texto y lo envíe automáticamente a **AUREA**.

---

## Requisitos
* iPhone con iOS 14 o superior.
* Servidor de AUREA activo (en tu red local o desplegado en la nube con URL HTTPS).

---

## Paso a Paso en tu iPhone

1. Abre la aplicación **Atajos** (*Shortcuts*) en tu iPhone.
2. Ve a la pestaña **Automatización**.
3. Toca **Nueva automatización** (o el botón `+`).
4. Selecciona el disparador **Mensaje** (*Message*).
5. Configura los filtros del mensaje:
   * **El mensaje contiene:** Escribe palabras clave comunes separadas (ej. `compra`, `transferencia`, `retiro`, `Bancolombia`, `Nequi`).
   * **Momento:** Selecciona **Ejecutar de inmediato** (*Run Immediately*) y desactiva *Notificar al ejecutar*.
6. Toca **Siguiente**.
7. Agrega la acción **Obtener contenido de URL** (*Get Contents of URL*):
   * **URL:** `https://tu-servidor-aurea.com/api/v1/webhooks/ios-shortcut`
   * **Método:** `POST`
   * **Headers:**
     * `Content-Type`: `application/json`
   * **Request Body:** Selecciona `JSON` y añade:
     * `medio`: Texto `SMS`
     * `texto_sms`: Variable `Contenido del atajo` (o `Texto del mensaje`).
8. Toca **Listo**.

El backend de AUREA se encargará de procesar el texto con su motor de expresiones regulares, identificando si fue un retiro en cajero, una compra o una transferencia recibida.
