import sys
import os
import traceback

# Agregar raíz al sys.path para importaciones en entornos serverless
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_app = None
_init_error = None

try:
    from backend.app.main import app as _fastapi_app
    _app = _fastapi_app
except Exception:
    _init_error = traceback.format_exc()


async def app(scope, receive, send):
    """
    Entry point ASGI para Vercel Serverless Functions.
    Captura y formatea cualquier error no controlado para evitar el 500 FUNCTION_INVOCATION_FAILED genérico.
    """
    if _init_error:
        body = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AUREA • Error de Inicialización</title>
</head>
<body style="background:#000000;color:#FF453A;font-family:-apple-system,BlinkMacSystemFont,sans-serif;padding:24px;margin:0;">
    <h1 style="font-size:20px;margin-bottom:8px;">Error al Iniciar AUREA en Vercel</h1>
    <p style="color:#8E8E93;font-size:12px;margin-top:0;">Detalle técnico de la excepción:</p>
    <pre style="background:#1C1C1E;color:#FFFFFF;padding:16px;border-radius:12px;overflow:auto;font-size:12px;line-height:1.4;border:1px solid rgba(255,255,255,0.1);">{_init_error}</pre>
</body>
</html>""".encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 500,
            "headers": [
                (b"content-type", b"text/html; charset=utf-8"),
                (b"content-length", str(len(body)).encode("utf-8")),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })
        return

    # Si es evento de ciclo de vida (lifespan), delegar directamente a FastAPI
    if scope.get("type") == "lifespan":
        await _app(scope, receive, send)
        return

    try:
        await _app(scope, receive, send)
    except Exception:
        err = traceback.format_exc()
        body = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AUREA • Error de Ejecución</title>
</head>
<body style="background:#000000;color:#FF453A;font-family:-apple-system,BlinkMacSystemFont,sans-serif;padding:24px;margin:0;">
    <h1 style="font-size:20px;margin-bottom:8px;">Error en Tiempo de Ejecución</h1>
    <p style="color:#8E8E93;font-size:12px;margin-top:0;">Detalle técnico de la excepción:</p>
    <pre style="background:#1C1C1E;color:#FFFFFF;padding:16px;border-radius:12px;overflow:auto;font-size:12px;line-height:1.4;border:1px solid rgba(255,255,255,0.1);">{err}</pre>
</body>
</html>""".encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 500,
            "headers": [
                (b"content-type", b"text/html; charset=utf-8"),
                (b"content-length", str(len(body)).encode("utf-8")),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })
