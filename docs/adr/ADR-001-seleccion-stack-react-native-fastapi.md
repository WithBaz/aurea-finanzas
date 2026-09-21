# ADR-001: Selección del Stack Tecnológico (React Native + Expo y FastAPI)

## Estado
Aceptado

## Contexto
El usuario requiere una aplicación de finanzas personales para utilizar en su iPhone con la sensación táctil y fluida de una aplicación descargada directamente de la App Store. Además, el usuario utiliza Google Chrome como navegador en iOS (donde la instalación de PWAs es limitada por restricciones de Apple) y necesita un backend ágil para procesar webhooks de automatizaciones de iOS y persistir datos financieros con alto rendimiento.

## Decisión
1. **Frontend Móvil:** **React Native con Expo**.
   * Permite ejecutar la aplicación directamente en el iPhone del usuario a través de la app oficial **Expo Go** sin requerir licencia anual de desarrollador Apple (\$99/año) ni una computadora Mac con Xcode.
   * Proporciona componentes nativos puros (Cocoa Touch / UIKit), gestos fluidos, retroalimentación háptica y navegación nativa por pestañas.
2. **Backend & API:** **Python 3.12+ con FastAPI y SQLAlchemy 2.0**.
   * FastAPI provee alto rendimiento asíncrono, documentación automática OpenAPI/Swagger y esquemas estrictos con Pydantic V2.
   * SQLite como motor relacional portable con claves foráneas activas para un despliegue y desarrollo local inmediato.

## Consecuencias
* **Positivas:** Experiencia nativa real en el iPhone del usuario, pruebas interactivas en vivo vía código QR, tipado estricto en backend y bajo costo de infraestructura.
* **Negativas:** Requiere mantener dos entornos (Node.js/TypeScript para la app móvil y Python para el backend API).
