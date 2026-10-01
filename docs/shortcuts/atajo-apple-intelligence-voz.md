# Configuración de Atajo de Voz / Apple Intelligence para AUREA (Gastos e Ingresos)

Esta guía explica cómo registrar **gastos e ingresos** por voz con **Siri y Apple Intelligence** en tu iPhone **sin necesidad de abrir la aplicación**, incluso con la pantalla bloqueada o usando el **Botón de Acción** del iPhone.

---

## 🎯 ¿Cómo Funciona la Experiencia?

1. Dices: **"Oye Siri, registrar movimiento"** o **"Oye Siri, registrar gasto e ingreso"**.
2. Siri o Apple Intelligence te pregunta: **"¿Qué movimiento hiciste?"**
3. Dices de forma natural lo que pasó:
   * **Gastos:**
     * *"Pagué 15 mil en Nequi"* (descuenta de Nequi)
     * *"Pagué 12 mil de taxi en efectivo"* (descuenta de Billetera Efectivo)
     * *"Almuerzo 28000 con Bancolombia"* (descuenta de Bancolombia)
     * *"Mercado 65 mil con Nu"* (descuenta de Nu)
   * **Ingresos:**
     * *"Me pagaron 500 mil en Bancolombia"* (suma a Bancolombia)
     * *"Me consignaron 80 mil a Nequi"* (suma a Nequi)
     * *"Entraron 200 mil a Bancolombia"* (suma a Bancolombia)
     * *"Sueldo 2 millones en Bancolombia"* (suma a Bancolombia)
     * *"Venta de 80 mil en efectivo"* (suma a Efectivo)
     * *"Me devolvieron 30 mil en Nequi"* (suma a Nequi)
4. El atajo procesa tu frase y el backend de AUREA detecta automáticamente si fue **gasto** o **ingreso**, la cuenta y el monto.
5. Siri te responde:
   * *"¡Listo! Registrado gasto de 15.000 pesos en 'Almuerzo' con Nequi."*
   * *"¡Listo! Registrado ingreso de 500.000 pesos en 'Nómina' con Bancolombia."*

---

## 🛠️ Cómo Configurar o Validar tu Atajo en iOS

Tienes dos formas de tener tu atajo en la app **Atajos**:

### 🌟 Opción 1: Atajo Inteligente Libre (Detecta si es Gasto o Ingreso automáticamente)
1. **Nombre del Atajo:** `Registrar Movimiento` (o `Registrar Gasto e Ingreso`).
2. **Acción 1:** **Solicitar entrada** (*Ask for Input*):
   * Pregunta: `¿Qué movimiento hiciste?` (Tipo: Texto)
3. **Acción 2:** **Obtener contenido de URL** (*Get Contents of URL*):
   * URL: `https://<TU-DOMINIO>/api/v1/transacciones/ia-rapida?texto=` y tocas la variable **Entrada provista**.
   * Método: `GET`.
4. **Acción 3:** **Mostrar resultado** o **Leer texto con Siri** con la variable **Contenido de URL**.

### 📋 Opción 2: Atajo con Menú ("Gasto" / "Ingreso")
Si prefieres que el atajo te pregunte primero si es Gasto o Ingreso con una lista:
1. **Acción 1:** **Elegir del menú**:
   * Opción 1: `Gasto`
   * Opción 2: `Ingreso`
2. **Dentro de "Gasto":**
   * **Solicitar entrada:** Texto con pregunta *"¿Qué gastaste?"*
   * **Obtener contenido de URL:** `https://<TU-DOMINIO>/api/v1/transacciones/ia-rapida?texto=[Entrada]&tipo=gasto`
3. **Dentro de "Ingreso":**
   * **Solicitar entrada:** Texto con pregunta *"¿Qué dinero ingresó?"*
   * **Obtener contenido de URL:** `https://<TU-DOMINIO>/api/v1/transacciones/ia-rapida?texto=[Entrada]&tipo=ingreso`
4. **Acción final:** **Mostrar resultado** de la respuesta del servidor.
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
