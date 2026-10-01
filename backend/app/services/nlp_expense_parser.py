import re
import unicodedata
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.models import Cuenta, TipoCuenta
from backend.app.services.categorizer import CategorizadorComercios


def normalizar_texto(texto: str) -> str:
    """
    Normaliza el texto eliminando tildes/acentos y caracteres combinados
    para comparación insensible a diacríticos (ej. 'Nequí' -> 'nequi', 'crédito' -> 'credito').
    """
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    sin_tildes = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return sin_tildes.strip()


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
    def interpretar_texto_gasto(cls, texto: str, db: Optional[Session] = None, usuario_id: Optional[int] = None) -> Dict[str, Any]:
        t = texto.strip().lower()

        # 1. Extraer Monto
        monto = cls._extraer_monto(t)

        # 2. Detectar Cuenta
        cuenta_id, cuenta_nombre = cls._detectar_cuenta(t, db, usuario_id=usuario_id)

        # 3. Detectar Tipo (Ingreso vs Egreso)
        palabras_egreso_fuertes = [
            "pagué", "pague", "gasté", "gaste", "compré", "compre",
            "gasto", "gastos", "egreso", "egresos", "salida", "salidas",
            "mandé", "mande", "envié", "envie", "pasé", "pase",
            "le pasé", "le pase", "le mandé", "le mande", "le transferí", "le transferi",
            "transferí", "transferi",
            "retiré", "retire", "saqué", "saque"
        ]

        palabras_ingreso = [
            "ingreso", "ingresos", "ingresaron", "ingresó", "ingreso", "ingresé", "ingrese", "ingresar",
            "me pagaron", "pagaron", "me pagó", "me pago", "pago recibido", "recibí", "recibi", "recibido", "recibida",
            "consignaron", "me consignaron", "consignación", "consignacion", "consigne", "consigné", "consigno", "consignó",
            "transfirieron", "me transfirieron", "transferencia recibida", "transfirio", "transfirió",
            "me pasaron", "pasaron", "me enviaron", "enviaron", "me mandaron", "mandaron",
            "me llegaron", "llegaron", "me llegó", "me llego", "llegó", "llego",
            "recargué", "recargue", "metí", "meti",
            "sueldo", "nómina", "nomina", "salario", "salarios", "quincena", "abono", "abonaron", "me abonaron", "honorarios",
            "gané", "gane", "ganancia", "ganancias",
            "me entró", "me entro", "entraron", "entró", "entro", "entrada", "entradas",
            "cobré", "cobre", "cobro", "cobros",
            "depósito", "deposito", "depositaron", "me depositaron", "me giraron",
            "giraron", "reembolso", "reembolsos", "devolución", "devolucion", "devolvieron", "me devolvieron",
            "me debían", "me debian", "deuda que me pagaron", "plata que me debían", "plata que me debian",
            "venta", "ventas", "freelance", "propina", "propinas",
            "rendimiento", "rendimientos", "intereses", "dividendos"
        ]

        t_norm = normalizar_texto(t)
        palabras_egreso_norm = [normalizar_texto(p) for p in palabras_egreso_fuertes]
        palabras_ingreso_norm = [normalizar_texto(p) for p in palabras_ingreso]

        primeras_palabras = " ".join(t_norm.split()[:3])
        inicio_ingreso = any(primeras_palabras.startswith(p) or f" {p} " in f" {primeras_palabras} " for p in ["ingreso", "ingresos", "ingresaron", "entrada", "recibi", "me pagaron", "me entro", "nomina", "sueldo", "salario", "consignacion", "abono", "gane", "venta"])
        inicio_egreso = any(primeras_palabras.startswith(p) or f" {p} " in f" {primeras_palabras} " for p in ["gasto", "gastos", "pague", "compre", "mande", "envie", "pase", "retire", "saque"])

        tipo_explicito = False
        if inicio_ingreso and not inicio_egreso:
            tipo = "INGRESO"
            tipo_explicito = True
        elif inicio_egreso and not inicio_ingreso:
            tipo = "EGRESO"
            tipo_explicito = True
        else:
            es_egreso_explicito = any(p in t_norm for p in palabras_egreso_norm)
            es_ingreso = any(palabra in t_norm for palabra in palabras_ingreso_norm)
            if es_ingreso and not es_egreso_explicito:
                tipo = "INGRESO"
                tipo_explicito = True
            elif es_egreso_explicito and not es_ingreso:
                tipo = "EGRESO"
                tipo_explicito = True
            elif es_ingreso and es_egreso_explicito:
                idx_egreso = min([t_norm.find(p) for p in palabras_egreso_norm if p in t_norm])
                idx_ingreso = min([t_norm.find(p) for p in palabras_ingreso_norm if p in t_norm])
                tipo = "INGRESO" if idx_ingreso < idx_egreso else "EGRESO"
                tipo_explicito = True
            else:
                tipo = "EGRESO"
                tipo_explicito = False

        # En Colombia ningún ingreso (nómina, sueldo, transferencia, honorarios) es menor a $1.000 COP ($0.25 USD).
        # Si se detectó ingreso y el monto es menor a 1.000, auto-escalar a miles (ej. 500 -> 500.000 COP).
        if tipo == "INGRESO" and 0 < monto < 1000:
            monto *= 1000.0

        # 4. Extraer Comercio / Concepto
        comercio = cls._extraer_concepto(t, es_ingreso=(tipo == "INGRESO"))

        # Si el concepto detectado es una categoría clara de gasto cotidiano (almuerzo, taxi, etc.), marcar tipo_explicito
        conceptos_egreso = ["almuerzo", "desayuno", "cena", "comida", "taxi", "uber", "didi", "gasolina", "mercado", "supermercado", "arriendo", "servicios", "peaje", "parqueadero"]
        if not tipo_explicito and any(c in t_norm for c in conceptos_egreso):
            tipo_explicito = True

        # 5. Categoría
        categoria_nombre, categoria_id = CategorizadorComercios.sugerir_categoria(comercio, db)
        if tipo == "INGRESO" and not categoria_id and db:
            from backend.app.models import Categoria
            cat_nom = db.query(Categoria).filter(Categoria.nombre.ilike("%nómina%")).first()
            if cat_nom:
                categoria_nombre = cat_nom.nombre
                categoria_id = cat_nom.id

        return {
            "monto": monto,
            "tipo": tipo,
            "tipo_explicito": tipo_explicito,
            "comercio": comercio,
            "cuenta_id": cuenta_id,
            "cuenta_nombre": cuenta_nombre,
            "categoria_nombre": categoria_nombre,
            "categoria_id": categoria_id,
            "requiere_confirmar_cuenta": cuenta_id is None,
            "requiere_confirmar_tipo": not tipo_explicito,
            "texto_original": texto
        }

    @classmethod
    def _detectar_cuenta(cls, texto: str, db: Optional[Session] = None, usuario_id: Optional[int] = None) -> Tuple[Optional[int], Optional[str]]:
        if not db:
            return None, None

        t = normalizar_texto(texto)
        query = db.query(Cuenta).filter(Cuenta.activa == True)
        if usuario_id:
            from sqlalchemy import or_
            query = query.filter(or_(Cuenta.usuario_id == usuario_id, Cuenta.usuario_id.is_(None)))
        cuentas = query.all()
        if not cuentas:
            cuentas = db.query(Cuenta).filter(Cuenta.activa == True).all()

        # 1. Mapeo de entidades financieras / instrumentos colombianos (sin tildes para búsqueda precisa)
        keywords_map = {
            "nequi": ["nequi", "neki", "neky", "nekki", "nequie"],
            "daviplata": ["daviplata", "davi", "davyplata", "davi plata"],
            "bancolombia": ["bancolombia", "banco colombia", "bancolombia a la mano", "a la mano"],
            "davivienda": ["davivienda"],
            "nu": ["nu", "nubank", "cajita", "cajitas", "cuenta nu"],
            "lulo": ["lulo", "lulobank", "lulo bank"],
            "rappi": ["rappi", "rappipay", "rappi pay"],
            "falabella": ["falabella", "banco falabella"],
            "bbva": ["bbva"],
            "scotia": ["colpatria", "scotiabank"],
            "bogota": ["banco de bogota", "banco bogota", "bogota"],
            "efectivo": ["efectivo", "en cash", "cash", "billetes", "plata en mano", "en fisico", "plata de efectivo", "billetera efectivo"],
            "credito": ["tarjeta de credito", "credito", "tarjeta", "tc", "visa", "mastercard", "amex", "american express"]
        }

        entidad_detectada = None
        for key, tokens in keywords_map.items():
            if any(token in t for token in tokens):
                entidad_detectada = key

                # A. Buscar cuenta de la base de datos cuyo nombre contenga la entidad
                for c in cuentas:
                    nom_c = normalizar_texto(c.nombre)
                    if any(token in nom_c for token in tokens):
                        return c.id, c.nombre

                # B. Mapeo por tipo o coincidencia especializada
                if key == "nequi":
                    # Si el usuario ya tiene una cuenta con 'nequi' en su nombre
                    c_neq = next((c for c in cuentas if "nequi" in normalizar_texto(c.nombre)), None)
                    if c_neq:
                        return c_neq.id, c_neq.nombre
                    # Si el usuario dijo explícitamente Nequi pero no la tiene creada, auto-aprovisionarla
                    nueva_c = Cuenta(
                        nombre="Nequi",
                        tipo=TipoCuenta.DEBITO,
                        saldo_actual=0.0,
                        usuario_id=usuario_id,
                        activa=True
                    )
                    db.add(nueva_c)
                    db.commit()
                    db.refresh(nueva_c)
                    return nueva_c.id, nueva_c.nombre

                elif key == "daviplata":
                    c_davi = next((c for c in cuentas if "daviplata" in normalizar_texto(c.nombre)), None)
                    if c_davi:
                        return c_davi.id, c_davi.nombre
                    nueva_c = Cuenta(
                        nombre="Daviplata",
                        tipo=TipoCuenta.DEBITO,
                        saldo_actual=0.0,
                        usuario_id=usuario_id,
                        activa=True
                    )
                    db.add(nueva_c)
                    db.commit()
                    db.refresh(nueva_c)
                    return nueva_c.id, nueva_c.nombre

                elif key == "efectivo":
                    c_ef = next((c for c in cuentas if c.tipo == TipoCuenta.EFECTIVO or "efectivo" in normalizar_texto(c.nombre)), None)
                    if c_ef:
                        return c_ef.id, c_ef.nombre
                    nueva_c = Cuenta(
                        nombre="Billetera Efectivo",
                        tipo=TipoCuenta.EFECTIVO,
                        saldo_actual=0.0,
                        usuario_id=usuario_id,
                        activa=True
                    )
                    db.add(nueva_c)
                    db.commit()
                    db.refresh(nueva_c)
                    return nueva_c.id, nueva_c.nombre

                elif key == "credito":
                    c_cr = next((c for c in cuentas if c.tipo == TipoCuenta.CREDITO), None)
                    if c_cr:
                        return c_cr.id, c_cr.nombre
                    nueva_c = Cuenta(
                        nombre="Tarjeta de Crédito",
                        tipo=TipoCuenta.CREDITO,
                        saldo_actual=0.0,
                        cupo_total=5000000.0,
                        usuario_id=usuario_id,
                        activa=True
                    )
                    db.add(nueva_c)
                    db.commit()
                    db.refresh(nueva_c)
                    return nueva_c.id, nueva_c.nombre

                elif key == "nu":
                    c_nu = next((c for c in cuentas if c.tipo == TipoCuenta.ALTO_RENDIMIENTO or "nu" in normalizar_texto(c.nombre)), None)
                    if c_nu:
                        return c_nu.id, c_nu.nombre
                    nueva_c = Cuenta(
                        nombre="Nu Colombia (Cajita)",
                        tipo=TipoCuenta.ALTO_RENDIMIENTO,
                        saldo_actual=0.0,
                        tasa_ea=13.0,
                        usuario_id=usuario_id,
                        activa=True
                    )
                    db.add(nueva_c)
                    db.commit()
                    db.refresh(nueva_c)
                    return nueva_c.id, nueva_c.nombre

                elif key in ["bancolombia", "davivienda"]:
                    c_deb = next((c for c in cuentas if c.tipo == TipoCuenta.DEBITO and "nequi" not in normalizar_texto(c.nombre) and key in normalizar_texto(c.nombre)), None)
                    if c_deb:
                        return c_deb.id, c_deb.nombre
                    nom_banco = "Bancolombia Principal" if key == "bancolombia" else "Davivienda"
                    nueva_c = Cuenta(
                        nombre=nom_banco,
                        tipo=TipoCuenta.DEBITO,
                        saldo_actual=0.0,
                        usuario_id=usuario_id,
                        activa=True
                    )
                    db.add(nueva_c)
                    db.commit()
                    db.refresh(nueva_c)
                    return nueva_c.id, nueva_c.nombre

        # 2. Búsqueda directa por el nombre de las cuentas del usuario
        for c in cuentas:
            nom_c = normalizar_texto(c.nombre)
            if nom_c in t:
                return c.id, c.nombre
            # Excluir palabras genéricas como 'plata', 'dinero', 'cuenta', etc.
            palabras_c = [w for w in re.findall(r"\w+", nom_c) if len(w) >= 4 and w not in ["cuenta", "tarjeta", "billetera", "banco", "plata", "dinero", "saldo"]]
            if palabras_c and any(w in t for w in palabras_c):
                return c.id, c.nombre

        # 3. Si el usuario sólo tiene 1 cuenta activa y NO se especificó otra entidad en el texto, asignarla
        if len(cuentas) == 1 and not entidad_detectada:
            return cuentas[0].id, cuentas[0].nombre

        return None, None

    @classmethod
    def _extraer_concepto(cls, texto: str, es_ingreso: bool = False) -> str:
        stop_words = (
            r"\b(pagué|pague|gasté|gaste|compré|compre|gasto|gastos|egreso|egresos|"
            r"me|pagaron|pagó|pago|recibí|recibi|consignaron|consigné|consigne|consignación|consignacion|"
            r"transfirieron|giraron|depositaron|entró|entro|entraron|cobré|cobre|cobro|cobros|mandé|mande|envié|envie|"
            r"pasé|pase|enviaron|mandaron|pasaron|llegó|llego|llegaron|recargué|recargue|metí|meti|"
            r"de|en|con|por|un|una|unos|unas|la|el|los|las|"
            r"mil|k|pesos|cop|efectivo|tarjeta|crédito|credito|debito|débito|bancolombia|nu|nequi|"
            r"nequí|neki|neky|daviplata|davi|davivienda|bbva|rappi|lulo|cajita|cajero|cuenta|"
            r"plata|dinero|fisico|físico|saldo)\b"
        )
        limpio = re.sub(stop_words, "", texto, flags=re.IGNORECASE)
        limpio = re.sub(r"\$?\s*\d+(?:[.,]\d+)?", "", limpio)
        limpio = " ".join(limpio.split()).capitalize()
        if len(limpio) >= 2:
            return limpio
        return "Ingreso General" if es_ingreso else "Gasto General"
