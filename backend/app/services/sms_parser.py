import re
from typing import Dict, Any, Optional
from datetime import datetime


def limpiar_monto(monto_str: str) -> float:
    """
    Convierte cadenas como '$45.000', '45.000,00', '$ 1.250.000' a float limpio.
    """
    if not monto_str:
        return 0.0
    # Eliminar símbolo de pesos y espacios
    limpio = monto_str.replace("$", "").replace("COP", "").strip()
    # Si tiene puntos como separadores de miles (estilo colombiano: 150.000)
    # y comas para decimales si los hubiera
    if "." in limpio and "," in limpio:
        limpio = limpio.replace(".", "").replace(",", ".")
    elif "." in limpio and not "," in limpio:
        # En Colombia 50.000 suele ser cincuenta mil, no cincuenta con cero decimales
        # Si hay un solo punto y tiene exactamente 3 digitos después, es separador de miles
        partes = limpio.split(".")
        if len(partes) == 2 and len(partes[1]) == 3:
            limpio = partes[0] + partes[1]
        elif len(partes) > 2:
            limpio = "".join(partes)
    return float(limpio)


class SMSParser:
    """
    Motor de análisis sintáctico con expresiones regulares para SMS bancarios colombianos y Apple Pay.
    """

    @classmethod
    def parse_sms(cls, texto: str, remitente: Optional[str] = None) -> Dict[str, Any]:
        t = texto.strip()
        
        # 1. Retiro en Cajero (Bancolombia / Otros) -> Transferencia Interna a Efectivo
        match_retiro = re.search(
            r"(?:retiro por|retiro exitoso de|retiro en cajero por)\s*\$?([\d\.,]+)\s*(?:en\s+([^.]+?))?(?:\s+a las|\.|\s*$)",
            t,
            re.IGNORECASE
        )
        if match_retiro or ("retiro" in t.lower() and "cajero" in t.lower()):
            monto_raw = match_retiro.group(1) if match_retiro else cls._extraer_monto_generico(t)
            comercio = match_retiro.group(2).strip() if (match_retiro and match_retiro.group(2)) else "Cajero Automático"
            return {
                "es_valido": True,
                "tipo": "TRANSFERENCIA_INTERNA",
                "monto": limpiar_monto(monto_raw),
                "comercio": f"Retiro {comercio}",
                "es_retiro_cajero": True,
                "medio": "SMS",
                "descripcion": f"Retiro de efectivo conciliado: {t[:60]}"
            }

        # 2. Bancolombia - Compra con Débito o Crédito
        match_bcol_compra = re.search(
            r"Bancolombia le informa compra por\s*\$?([\d\.,]+)\s*(?:con\s+([^,]+?))?\s*en\s+([^.]+?)(?:\s+a las|\.|$)",
            t,
            re.IGNORECASE
        )
        if match_bcol_compra:
            monto_raw = match_bcol_compra.group(1)
            instrumento_raw = match_bcol_compra.group(2) or ""
            comercio = match_bcol_compra.group(3).strip()
            es_credito = "cred" in instrumento_raw.lower() or "t.cred" in t.lower()
            return {
                "es_valido": True,
                "tipo": "EGRESO",
                "monto": limpiar_monto(monto_raw),
                "comercio": comercio,
                "es_credito": es_credito,
                "es_retiro_cajero": False,
                "medio": "SMS",
                "descripcion": f"Compra {comercio} via SMS Bancolombia"
            }

        # 3. Bancolombia - Transferencia Recibida (Ingreso)
        match_bcol_recibida = re.search(
            r"Bancolombia le informa transferencia recibida(?: de ([^p]+?))?\s*por\s*\$?([\d\.,]+)",
            t,
            re.IGNORECASE
        )
        if match_bcol_recibida:
            origen = (match_bcol_recibida.group(1) or "Tercero").strip()
            monto_raw = match_bcol_recibida.group(2)
            return {
                "es_valido": True,
                "tipo": "INGRESO",
                "monto": limpiar_monto(monto_raw),
                "comercio": f"Transferencia de {origen}",
                "es_retiro_cajero": False,
                "medio": "SMS",
                "descripcion": f"Ingreso recibido de {origen}"
            }

        # 4. Nequi - Pago o Envío
        match_nequi_pago = re.search(
            r"(?:Pagaste|Enviaste)\s*\$?([\d\.,]+)\s*(?:a\s+([^.]+?))?(?:\s+con Nequi|\.|$)",
            t,
            re.IGNORECASE
        )
        if match_nequi_pago:
            monto_raw = match_nequi_pago.group(1)
            destino = (match_nequi_pago.group(2) or "Nequi").strip()
            return {
                "es_valido": True,
                "tipo": "EGRESO",
                "monto": limpiar_monto(monto_raw),
                "comercio": destino,
                "es_retiro_cajero": False,
                "medio": "SMS",
                "descripcion": f"Pago Nequi a {destino}"
            }

        # 5. Nequi - Recepción
        match_nequi_recibido = re.search(
            r"Te enviaron\s*\$?([\d\.,]+)(?:\s+de parte de\s+([^.]+?))?(?:\.|$)",
            t,
            re.IGNORECASE
        )
        if match_nequi_recibido:
            monto_raw = match_nequi_recibido.group(1)
            origen = (match_nequi_recibido.group(2) or "Nequi").strip()
            return {
                "es_valido": True,
                "tipo": "INGRESO",
                "monto": limpiar_monto(monto_raw),
                "comercio": f"Nequi de {origen}",
                "es_retiro_cajero": False,
                "medio": "SMS",
                "descripcion": f"Transferencia Nequi recibida de {origen}"
            }

        # 6. Daviplata - Pago / Envío
        match_daviplata_pago = re.search(
            r"DaviPlata le informa que paso plata por\s*\$?([\d\.,]+)\s*(?:a\s+([^.]+?))?(?:\.|$)",
            t,
            re.IGNORECASE
        )
        if match_daviplata_pago:
            monto_raw = match_daviplata_pago.group(1)
            destino = (match_daviplata_pago.group(2) or "DaviPlata").strip()
            return {
                "es_valido": True,
                "tipo": "EGRESO",
                "monto": limpiar_monto(monto_raw),
                "comercio": destino,
                "es_retiro_cajero": False,
                "medio": "SMS",
                "descripcion": f"Paso plata DaviPlata a {destino}"
            }

        # 7. Regla Genérica de Detección de Pagos por Expresión Regular
        monto_gen = cls._extraer_monto_generico(t)
        if monto_gen:
            tipo = "EGRESO"
            if any(k in t.lower() for k in ["recibiste", "abono", "consignacion", "te enviaron", "transferencia recibida"]):
                tipo = "INGRESO"
            return {
                "es_valido": True,
                "tipo": tipo,
                "monto": limpiar_monto(monto_gen),
                "comercio": "Movimiento Bancario Detectado",
                "es_retiro_cajero": False,
                "medio": "SMS",
                "descripcion": t[:100]
            }

        return {
            "es_valido": False,
            "mensaje": "No se pudo extraer una transacción válida del mensaje SMS",
            "raw": t
        }

    @classmethod
    def _extraer_monto_generico(cls, texto: str) -> Optional[str]:
        match = re.search(r"\$\s*([\d\.,]+)", texto)
        if match:
            return match.group(1)
        match_num = re.search(r"(?:por|valor de|de)\s+([\d\.,]{4,})", texto, re.IGNORECASE)
        if match_num:
            return match_num.group(1)
        return None
