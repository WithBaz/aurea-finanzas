# Configuración de Atajo de Voz / Apple Intelligence para AUREA

Esta guía explica cómo registrar gastos por voz con **Siri y Apple Intelligence** en tu iPhone **sin necesidad de abrir la aplicación**, incluso con la pantalla bloqueada o usando el **Botón de Acción** del iPhone.

---

## 🎯 ¿Cómo Funciona la Experiencia?

1. Dices: **"Oye Siri, registrar gasto"** (o mantienes presionado el botón lateral / Botón de Acción del iPhone).
2. Siri o Apple Intelligence te pregunta: **"¿Qué gastaste?"**
3. Dices de forma natural:
   * *"Pagué 15 mil en Nequi"* (descuenta de Nequi)
   * *"Pagué 15 mil de taxi en efectivo"* (descuenta de Billetera Efectivo)
   * *"Almuerzo 28000 con Bancolombia"* (descuenta de Bancolombia)
   * *"Mandé plata por Nequi 25 mil"* (descuenta de Nequi)
   * *"Mercado 65 mil con Nu"* (descuenta de Nu)
4. El atajo procesa tu voz en segundo plano y envía la frase directamente a tu backend de AUREA.
5. Siri te responde confirmando la cuenta exacta: **"¡Listo! Registrado egreso de 15.000 pesos en 'Almuerzo' con Nequi."**
6. Tu saldo y tu semáforo diario quedan actualizados automáticamente.

---

## 🛠️ Paso a Paso para Crear el Atajo en la App "Atajos" de iOS

Abre la app nativa **Atajos** (Shortcuts) en tu iPhone y pulsa el botón **+** (arriba a la derecha) para crear un nuevo atajo.

### 1. Renombrar el Atajo
* Toca el título arriba y renómbralo exactamente como:  
  **`Registrar Gasto`**  
  *(Este es el comando de voz con el que Siri lo activará cuando digas "Oye Siri, registrar gasto")*.

### 2. Acción 1: Solicitar Entrada de Voz / Texto
* Busca la acción: **Solicitar entrada** (*Ask for Input*).
* Configuración:
  * **Tipo:** Texto
  * **Pregunta:** `¿Qué gastaste?`

### 3. Acción 2: Enviar al Backend de AUREA
* Busca la acción: **Obtener contenido de URL** (*Get Contents of URL*).
* Configuración:
  * **URL:** Copia la URL directa desde tu app AUREA en **Ajustes** -> **Automatizaciones de iOS** -> **Atajo de Voz / Siri** (que ya viene con tu token personal):  
    `https://<TU-DOMINIO-VERCEL>/api/v1/transacciones/ia-rapida?token=<TU-TOKEN>`  
    *(O si usas ngrok local: `https://xxxx.ngrok-free.app/api/v1/transacciones/ia-rapida?token=<TU-TOKEN>`)*.
  * Toca en **Mostrar más / Avanzado**:
    * **Método:** `POST`
    * **Encabezados (Headers):**
      * Clave: `Content-Type`
      * Texto: `application/json`
    * **Cuerpo de la petición (Request Body):** Selecciona `JSON`
      * Toca **Agregar nuevo campo** -> `Texto`
      * Clave: `texto`
      * Valor: Toca la variable **Entrada provista** (el texto de la Acción 1).

### 4. Acción 3: Extraer la Respuesta
* Busca la acción: **Obtener valor de diccionario** (*Get Dictionary Value*).
  * Clave: `mensaje`
  * De: Selecciona **Contenido de URL**.

### 5. Acción 4: Confirmación por Voz o Notificación
* Busca la acción: **Mostrar notificación** (*Show Notification*).
  * Texto: Selecciona la variable **Valor de diccionario** generada en el paso anterior.
* *(Opcional)* Si quieres que Siri te lo hable por los auriculares o el altavoz:
  * Busca la acción: **Leer texto con Siri** (*Speak Text*) y pásale el **Valor de diccionario**.

---

## ⚡ 4 Formas de Usarlo Sin Abrir la App

1. **Por Voz (Manos Libres):**  
   Dile a tu iPhone o AirPods: *"Oye Siri, registrar gasto"*.
2. **Con el Botón de Acción (iPhone 15 Pro / 16 Pro):**  
   Ve a *Ajustes* -> *Botón de Acción* -> Selecciona *Atajo* -> Elige **Registrar Gasto**. Con presionar el botón lateral un segundo, hablas y se registra tu gasto.
3. **En la Pantalla de Bloqueo (iOS 18):**  
   Mantén presionada tu pantalla de bloqueo -> *Personalizar* -> Reemplaza la linterna o la cámara por el atajo **Registrar Gasto**.
4. **Doble Toque Trasero (Back Tap):**  
   Ve a *Ajustes* -> *Accesibilidad* -> *Tocar* -> *Tocar atrás* -> *Doble toque* -> Selecciona **Registrar Gasto**. Dos toques con el dedo detrás del teléfono y listo.
