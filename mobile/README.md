# AUREA Mobile (React Native + Expo)

Aplicación móvil nativa para iPhone diseñada para dar una experiencia idéntica a una app instalada de la App Store, con retroalimentación háptica, tarjetas dinámicas y modo oscuro.

---

## 📲 Cómo ejecutarla en tu iPhone en 1 minuto

1. Descarga la aplicación gratuita **Expo Go** desde la App Store en tu iPhone.
2. Abre una terminal en tu computador dentro de la carpeta `mobile/`:
   ```bash
   cd mobile
   npm install
   npx expo start
   ```
3. En la terminal aparecerá un **código QR**.
4. Abre la cámara de tu iPhone y enfoca el código QR.
5. Toca la notificación que dice *"Abrir en Expo Go"*.
6. ¡Listo! AUREA se abrirá directamente en tu iPhone.

> [!TIP]
> Para que el iPhone se comunique con el backend en tu computador, asegúrate de que ambos dispositivos estén conectados a la misma red Wi-Fi y coloca la IP local de tu computador en `src/services/api.ts` (o utiliza la URL de despliegue HTTPS si desplegaste el backend en Vercel/Railway).
