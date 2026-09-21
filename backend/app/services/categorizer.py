from typing import Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.models import Categoria


CATALOGO_COMERCIOS_COLOMBIA = {
    "Alimentación y Supermercado": [
        "d1", "tiendas d1", "éxito", "exito", "carulla", "jumbo", "metro", "ara",
        "tiendas ara", "olimpica", "surtimax", "colsubsidio", "makro", "costco",
        "mercadolibre", "restaurante", "panaderia", "cafeteria", "starbucks",
        "juan valdez", "tostao", "crepes", "waffles", "mcdonalds", "kfc", "frisby",
        "el corral", "subway", "dominos", "rappi"
    ],
    "Transporte y Movilidad": [
        "uber", "didi", "cabify", "indrive", "terpel", "texaco", "primax",
        "esso", "mobil", "biomax", "gasolina", "peaje", "transmilenio",
        "sitp", "metro medellin", "tullave", "parqueadero", "estacionamiento"
    ],
    "Servicios y Hogar": [
        "enel", "codensa", "epm", "acueducto", "gas natural", "vanti",
        "claro", "movistar", "tigo", "etb", "wom", "arriendo", "administracion",
        "homecenter", "sodimac", "easy"
    ],
    "Ocio y Suscripciones": [
        "netflix", "spotify", "apple.com/bill", "apple", "prime video", "amazon",
        "hbo", "max", "disney", "cine colombia", "cinemark", "procinal", "steam",
        "playstation", "xbox", "gym", "smart fit", "bodytech"
    ],
    "Salud y Cuidado Personal": [
        "farmatodo", "cruz verde", "drogueria", "la rebaja", "pasteur",
        "dermatologia", "odontologia", "eps", "sanitas", "colsanitas", "sura"
    ],
    "Educación y Desarrollo": [
        "platzi", "udemy", "coursera", "universidad", "colegio", "libreria",
        "panamericana", "kindle"
    ],
    "Transferencias y Retiros": [
        "retiro cajero", "cajero automatico", "atm", "servibanca", "redeban"
    ]
}


class CategorizadorComercios:
    @classmethod
    def sugerir_categoria(cls, comercio: str, db: Optional[Session] = None) -> Tuple[Optional[str], Optional[int]]:
        """
        Devuelve (nombre_categoria, categoria_id) basado en las palabras clave del comercio.
        """
        c_lower = (comercio or "").lower().strip()
        
        # 1. Búsqueda en catálogo preconfigurado de Colombia
        for cat_nombre, keywords in CATALOGO_COMERCIOS_COLOMBIA.items():
            for kw in keywords:
                if kw in c_lower:
                    cat_id = None
                    if db:
                        categoria = db.query(Categoria).filter(Categoria.nombre.ilike(f"%{cat_nombre}%")).first()
                        if categoria:
                            cat_id = categoria.id
                    return cat_nombre, cat_id

        # 2. Si no se encuentra en el catálogo fijo, buscar en palabras clave de la base de datos
        if db:
            categorias = db.query(Categoria).all()
            for cat in categorias:
                if cat.palabras_clave:
                    kws = [k.strip().lower() for k in cat.palabras_clave.split(",") if k.strip()]
                    for kw in kws:
                        if kw in c_lower:
                            return cat.nombre, cat.id

        return "Otros Gastos", None

    @classmethod
    def es_gasto_hormiga(cls, monto: float, umbral: float = 25000.0) -> bool:
        """
        Determina si una transacción califica como gasto hormiga (por debajo del umbral en COP, típicamente $25.000).
        """
        return 0 < monto <= umbral
