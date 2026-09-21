import re
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.models import Cuenta, TipoCuenta
from backend.app.services.categorizer import CategorizadorComercios


class NLPSmartExpenseParser:
    """
    Parser de lenguaje natural para registrar gastos por voz o texto rápido
    (Compatible con Apple Intelligence, Siri Dictation y atajos de voz).
    Ejemplos:
    - 'Pagué 15 mil de taxi en efectivo'
    - 'Almuerzo 25000 con Bancolombia'
    - 'Compré 42.000 en el D1 con tarjeta de crédito'
    - 'Café 8500'
    """

    @classmethod
    def interpretar_texto_gasto(cls, texto: str, db: Optional[Session] = None) -> Dict[str, Any]:
        t = texto.strip().lower()

        # 1. Extraer Monto
        monto = cls._extraer_monto(t)

        # 2. Detectar Cuenta
        cuenta_id, cuenta_nombre = cls._detectar_cuenta(t, db)

        # 3. Detectar Tipo (Ingreso vs Egreso)
        es_ingreso = any(palabra in t for palabra in ["ingreso", "me pagaron", "recibí", "consignaron", "sueldo", "abono"])
        tipo = "INGRESO" if es_ingreso else "EGRESO"

        # 4. Extraer Comercio / Concepto
        comercio = cls._extraer_concepto(t)

        # 5. Categoría
        categoria_nombre, categoria_id = CategorizadorComercios.sugerir_categoria(comercio, db)

        return {
            "monto": monto,
            "tipo": tipo,
            "comercio": comercio,
            "cuenta_id": cuenta_id,
            "cuenta_nombre": cuenta_nombre,
            "categoria_nombre": categoria_nombre,
            "categoria_id": categoria_id,
            "requiere_confirmar_cuenta": cuenta_id is None,
            "texto_original": texto
        }

    @classmethod
    def _extraer_monto(cls, texto: str) -> float:
        # Casos como '15 mil', '15mil', '25 k', '25k'
        match_mil = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:mil|k)\b", texto)
        if match_mil:
            num = float(match_mil.group(1).replace(",", "."))
            return num * 1000.0

        # Casos como '$45.000', '$ 45000', '45.000', '45000'
        match_num = re.search(r"(?:\$|\b)\s*(\d{1,3}(?:\.\d{3})+|\d{4,9})\b", texto)
        if match_num:
            raw = match_num.group(1).replace(".", "").replace(",", "")
            return float(raw)

        # Números de 3 dígitos con contexto de dinero (ej. 500)
        match_chico = re.search(r"\b(\d{2,3})\b", texto)
        if match_chico:
            return float(match_chico.group(1))

        return 0.0

    @classmethod
    def _detectar_cuenta(cls, texto: str, db: Optional[Session] = None) -> Tuple[Optional[int], Optional[str]]:
        palabras_efectivo = ["efectivo", "en cash", "plata en mano", "billetes"]
        palabras_bancolombia = ["bancolombia", "banco", "débito", "debito"]
        palabras_nu = ["nu", "nubank", "cajita", "cuenta nu"]
        palabras_credito = ["crédito", "credito", "tarjeta de crédito", "tarjeta credito", "visa", "mastercard"]

        cuenta_detectada_tipo = None
        if any(p in texto for p in palabras_efectivo):
            cuenta_detectada_tipo = TipoCuenta.EFECTIVO
        elif any(p in texto for p in palabras_credito):
            cuenta_detectada_tipo = TipoCuenta.CREDITO
        elif any(p in texto for p in palabras_nu):
            cuenta_detectada_tipo = TipoCuenta.ALTO_RENDIMIENTO
        elif any(p in texto for p in palabras_bancolombia):
            cuenta_detectada_tipo = TipoCuenta.DEBITO

        if db and cuenta_detectada_tipo:
            cuenta = db.query(Cuenta).filter(Cuenta.tipo == cuenta_detectada_tipo, Cuenta.activa == True).first()
            if cuenta:
                return cuenta.id, cuenta.nombre

        # Si no se detectó tipo específico, buscar por nombre exacto de la cuenta en la DB
        if db:
            cuentas = db.query(Cuenta).filter(Cuenta.activa == True).all()
            for c in cuentas:
                if c.nombre.lower() in texto:
                    return c.id, c.nombre

        return None, None

    @classmethod
    def _extraer_concepto(cls, texto: str) -> str:
        # Quitar palabras de enlace comunes para quedarnos con el comercio/concepto
        limpio = re.sub(r"\b(pagué|pague|gasté|gaste|compré|compre|de|en|con|por|un|una|unos|unas|la|el|los|las|mil|k|pesos|cop|efectivo|tarjeta|crédito|debito|bancolombia|nu)\b", "", texto)
        # Quitar dígitos
        limpio = re.sub(r"\$?\s*\d+(?:[.,]\d+)?", "", limpio)
        limpio = " ".join(limpio.split()).capitalize()
        return limpio if len(limpio) >= 2 else "Gasto General"
