# Guía Definitiva: Automatización de Apple Pay y Pruebas a $0 Costo

Configura la detección automática de pagos con Apple Pay en tu iPhone y prueba el funcionamiento **en 1 segundo sin gastar ni un solo peso**.

---

## 🚀 Método de Prueba Inmediata ($0 Costo / Sin Compras)

Para verificar que AUREA recibe tus peticiones sin tener que hacer pagos reales en datáfonos:

### Opción A: Prueba Directa en Safari / Navegador
Abre este enlace desde tu iPhone o computador:
```text
https://aurea-finanzas.vercel.app/api/v1/webhooks/test-apple-pay?monto=1000&comercio=Prueba+Datáfono
```
* **Respuesta esperada:** `{"status": "exitoso", "mensaje": "Pago Apple Pay de 1.000 pesos registrado en Prueba Datáfono...", ...}`
* Abre de inmediato AUREA y verás el movimiento reflejado en tu dashboard o historial.
* Si deseas probar la conexión sin alterar saldos ni crear registros en la base de datos, añade `&dry_run=true`:
  ```text
  https://aurea-finanzas.vercel.app/api/v1/webhooks/test-apple-pay?dry_run=true
  ```

### Opción B: Atajo de Prueba Rápida en iOS (1 Toque)
1. En la app **Atajos**, crea un atajo nuevo llamado `Probar Apple Pay`.
2. Agrega la acción **Obtener contenido de URL**:
   * **URL:** `https://aurea-finanzas.vercel.app/api/v1/webhooks/test-apple-pay`
   * **Método:** `GET`
3. Agrega la acción **Mostrar notificación** y selecciona el resultado del paso anterior.
4. Presiona el botón ▶️ (Play). Recibirás una notificación confirmando la sincronización en menos de 1 segundo.

---

## 💳 Configuración de la Automatización Automática de Apple Pay

Sigue estos pasos en la app **Atajos** de tu iPhone para que cada compra real se sincronice en segundo plano:

### 1. Crear el Disparador de Transacción
1. Abre la app **Atajos** y ve a la pestaña **Automatización** (en la barra inferior).
2. Toca el botón `+` (esquina superior derecha).
3. Busca y selecciona **Transacción** (*Transaction*).
4. Configura:
   * **Tarjeta:** Selecciona *Cualquier tarjeta* (o tu tarjeta específica, ej. Bancolombia, Nu, etc.).
   * **Categoría:** *Cualquiera*.
   * **Comercio:** *Cualquiera*.
   * **Momento:** Marca **Ejecutar de inmediato** (*Run Immediately*).
   * **Notificar al ejecutarse:** Opcional (déjalo activado las primeras veces si deseas ver un aviso cuando se ejecute).
5. Toca **Siguiente**.

### 2. Configurar la Acción HTTP
1. Selecciona **Nueva automatización en blanco** (o busca directamente en la barra de búsqueda inferior).
2. Agrega la acción **Obtener contenido de URL** (*Get Contents of URL*).
3. Despliega los detalles de la acción tocando la flechita azul y llena los campos:
   * **URL:** `https://aurea-finanzas.vercel.app/api/v1/webhooks/ios-shortcut`
   * **Método:** `POST`
   * **Encabezados (Headers):**
     * Toca *Agregar nuevo campo*
     * Clave: `Content-Type`
     * Texto: `application/json`
   * **Cuerpo de la petición (Request Body):** Cambia a `JSON`.
   * Añade los siguientes 4 campos usando la variable mágica **Entrada de atajo** (*Shortcut Input*):
     1. **`medio`**: Tipo *Texto* → escribe `APPLE_PAY`
     2. **`monto`**: Tipo *Texto* (o *Número*) → toca el valor, selecciona la variable mágica **Entrada de atajo** en la barra superior del teclado, pulsa sobre la pastilla azul recién insertada y cámbiala a **Monto** (*Amount*).
     3. **`comercio`**: Tipo *Texto* → selecciona **Entrada de atajo** → pulsa sobre ella → cámbiala a **Comercio** (*Merchant*).
     4. **`tarjeta`**: Tipo *Texto* → selecciona **Entrada de atajo** → pulsa sobre ella → cámbiala a **Tarjeta** (*Card*).
4. Toca **Listo**.

---

## 🛡️ ¿Por qué no te detectó las compras y qué se solucionó?
1. **Error silencioso de mayúsculas y anidamiento en iOS (Solucionado al 100%):** Al configurar Atajos en un iPhone en español, Apple asigna nombres con mayúscula inicial (`Monto`, `Comercio`, `Tarjeta`) o empaqueta las propiedades dentro de un objeto `Entrada de atajo`. Anteriormente, el backend requería estrictamente minúsculas y rechazaba estas peticiones con HTTP 400 silencioso. Ahora el receptor cuenta con un desanidador y normalizador universal que acepta mayúsculas, minúsculas, inglés, español y estructuras anidadas.
2. **Cero filtros contra Bancolombia:** En AUREA **no hay ningún bloqueo ni exclusión contra Bancolombia**. El sistema vincula automáticamente cualquier variación (`Bancolombia`, `Bancolombia Débito`, `Bancolombia Única`, `Mastercard Bancolombia`, `Visa Bancolombia`) a tu cuenta principal `Bancolombia Única`.
3. **Punto crítico en tu iPhone — Disparador de iOS:** En la app **Atajos** de tu iPhone, al crear o editar la automatización **Transacción**, asegúrate de que el campo **Tarjeta** esté configurado como **"Cualquier tarjeta"**. Si en el pasado seleccionaste una tarjeta específica (por ejemplo Nu) y no Bancolombia, el propio sistema operativo iOS **nunca dispara la automatización** cuando pagas con Bancolombia en el datáfono.
4. **Pruebas sin compras reales ($0 Costo):** Dispones del endpoint `/test-apple-pay` para comprobar la sincronización en 1 segundo desde Safari o directamente con el botón ▶️ Play en la app Atajos.
