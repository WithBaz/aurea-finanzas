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
        palabras_ingreso = [
            "ingreso", "ingresos", "me pagaron", "pagaron", "recibí", "recibi",
            "consignaron", "me consignaron", "consignación", "consignacion",
            "transfirieron", "me transfirieron", "transferencia recibida",
            "sueldo", "nómina", "nomina", "quincena", "abono", "honorarios",
            "gané", "gane", "ganancia", "me entró", "me entro", "cobré", "cobre",
            "depósito", "deposito", "depositaron", "me depositaron", "me giraron",
            "giraron", "reembolso", "devolución", "devolucion", "freelance"
        ]
        es_ingreso = any(palabra in t for palabra in palabras_ingreso)
        tipo = "INGRESO" if es_ingreso else "EGRESO"

        # En Colombia ningún ingreso (nómina, sueldo, transferencia, honorarios) es menor a $1.000 COP ($0.25 USD).
        # Si se detectó ingreso y el monto es menor a 1.000, auto-escalar a miles (ej. 500 -> 500.000 COP).
        if es_ingreso and 0 < monto < 1000:
            monto *= 1000.0

        # 4. Extraer Comercio / Concepto
        comercio = cls._extraer_concepto(t, es_ingreso=es_ingreso)

        # 5. Categoría
        categoria_nombre, categoria_id = CategorizadorComercios.sugerir_categoria(comercio, db)
        if es_ingreso and not categoria_id and db:
            from backend.app.models import Categoria
            cat_nom = db.query(Categoria).filter(Categoria.nombre.ilike("%nómina%")).first()
            if cat_nom:
                categoria_nombre = cat_nom.nombre
                categoria_id = cat_nom.id

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
        t = texto.lower().replace("\xa0", " ").replace("\u202f", " ")

        # 1. Limpieza inicial de puntuaciones intermedias de dictado Siri (ej. "500. mil", "1. millón", "2, millones" -> "500 mil", "1 millón")
        t = re.sub(r"(\d+)\s*[.,\-/]\s*(mil|k|lucas|barras|palos?|mill[oó]n(?:es)?)\b", r"\1 \2", t)

        # 2. Unir espacios de miles comunes en iOS (ej. "10 000" -> "10000", "500 000" -> "500000")
        t = re.sub(r"(\d+)\s+(\d{3})\b", r"\1\2", t)

        # 3. Palabras de números en español (ej. "diez mil", "quince mil")
        palabras_numeros = {
            "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
            "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11,
            "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16,
            "dieciséis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
            "veinte": 20, "veintiún": 21, "veintiun": 21, "veintidos": 22, "veintidós": 22,
            "veintitres": 23, "veintitrés": 23, "veinticuatro": 24, "veinticinco": 25,
            "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70,
            "ochenta": 80, "noventa": 90, "cien": 100, "ciento": 100, "doscientos": 200,
            "trescientos": 300, "cuatrocientos": 400, "quinientos": 500
        }

        # Millones + y medio (ej. "un millón y medio", "1 millon y medio", "dos millones y medio", "un palo y medio", "2 palos y medio")
        match_medio = re.search(r"\b(?:(un|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|\d+))\s+(?:mill[oó]n(?:es)?|palos?)\s+y\s+medio\b", t)
        if match_medio:
            cant_str = match_medio.group(1)
            val = float(palabras_numeros.get(cant_str, cant_str))
            return val * 1_000_000.0 + 500_000.0

        # Millones compuestos (ej. "1 millón 200", "1 millón 200 mil", "un millón 500 mil", "2 millones trescientos")
        match_compuesto = re.search(r"\b(?:(un|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|\d+))\s+(?:mill[oó]n(?:es)?|palos?)\s*(?:con\s+)?(?:(\d{1,3})|(" + "|".join(palabras_numeros.keys()) + r"))(?:\s*mil)?\b", t)
        if match_compuesto:
            cant_m = match_compuesto.group(1)
            val_m = float(palabras_numeros.get(cant_m, cant_m))
            cant_k_str = match_compuesto.group(2) or match_compuesto.group(3)
            val_k = float(palabras_numeros.get(cant_k_str, cant_k_str))
            return val_m * 1_000_000.0 + val_k * 1000.0

        # Millones en palabras (ej. "un millón", "un millon", "dos millones", "tres millones", "un palo", "dos palos")
        patron_palabras_millon = "un|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez"
        match_millon_palabra = re.search(rf"\b({patron_palabras_millon})\s+(?:mill[oó]n(?:es)?|palos?)\b", t)
        if match_millon_palabra:
            val = palabras_numeros.get(match_millon_palabra.group(1), 1)
            return float(val * 1_000_000)

        # Números en palabras + mil (ej. "diez mil", "quince mil", "diez lucas", "quinientos mil")
        patron_palabras = "|".join(palabras_numeros.keys())
        match_palabra_mil = re.search(rf"\b({patron_palabras})\s*(?:mil|k|lucas|barras)\b", t)
        if match_palabra_mil:
            palabra = match_palabra_mil.group(1)
            return float(palabras_numeros[palabra] * 1000)

        # 'mil' o 'mil pesos' solo (ej. 'mil pesos', 'mil de pan', 'un mil')
        match_mil_solo = re.search(r"\b(?:un\s+)?mil(?:\s+pesos|\s+cop)?\b", t)
        if match_mil_solo:
            idx = match_mil_solo.start()
            prev = t[:idx].rstrip(" .,-/:")
            if not re.search(r"(\d+|" + patron_palabras + r")$", prev):
                return 1000.0

        t_unido = t

        # 4. Millones con dígitos (ej. "1.5 millones", "2 millones", "1 millón", "1 millon", "2 palos")
        match_millon = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:mill[oó]n(?:es)?|palos?)\b", t_unido)
        if match_millon:
            num = float(match_millon.group(1).replace(",", "."))
            return num * 1_000_000.0

        # 5. Miles con dígitos y sufijo (ej. '15 mil', '15mil', '25 k', '25k', '10 lucas', '10 barras', '500 mil')
        match_mil = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:mil|k|lucas|barras)\b", t_unido)
        if match_mil:
            num = float(match_mil.group(1).replace(",", "."))
            return num * 1000.0

        # 6. Formatos numéricos con puntos o comas como separador de miles, o directos de 4 a 9 dígitos
        # Soporta: '10,000', '10.000', '20,000', '100,000', '100.000', '$45.000', '10000', '500000', '1,000,000'
        match_num = re.search(r"(?:\$|\b)\s*(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})?|\d{4,9}(?:[.,]\d{2})?)\b", t_unido)
        if match_num:
            raw = match_num.group(1)
            if re.search(r"[.,]\d{2}$", raw):
                raw = re.sub(r"[.,]\d{2}$", "", raw)
            clean = raw.replace(".", "").replace(",", "")
            return float(clean)

        # 7. Números de 1 a 3 dígitos en contexto colombiano (ej. "almuerzo 10" -> 10.000, "500" -> 500.000, "mercado 250" -> 250.000)
        # En la cotidianidad colombiana, montos de 1 a 999 sin la palabra explícita 'pesos'/'cop' corresponden a miles (k).
        match_chico = re.search(r"\b(\d{1,3})\b", t_unido)
        if match_chico:
            val = float(match_chico.group(1))
            if "pesos" not in t_unido and "cop" not in t_unido:
                if val >= 1:
                    return val * 1000.0
            return val

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
            # Si solo existe una cuenta activa configurada, asumirla por defecto
            if len(cuentas) == 1:
                return cuentas[0].id, cuentas[0].nombre

        return None, None

    @classmethod
    def _extraer_concepto(cls, texto: str, es_ingreso: bool = False) -> str:
        stop_words = (
            r"\b(pagué|pague|gasté|gaste|compré|compre|me|pagaron|recibí|recibi|consignaron|"
            r"transfirieron|giraron|depositaron|entró|entro|cobré|cobre|de|en|con|por|un|una|"
            r"unos|unas|la|el|los|las|mil|k|pesos|cop|efectivo|tarjeta|crédito|credito|debito|"
            r"débito|bancolombia|nu|nequi|daviplata)\b"
        )
        limpio = re.sub(stop_words, "", texto)
        limpio = re.sub(r"\$?\s*\d+(?:[.,]\d+)?", "", limpio)
        limpio = " ".join(limpio.split()).capitalize()
        if len(limpio) >= 2:
            return limpio
        return "Ingreso General" if es_ingreso else "Gasto General"
