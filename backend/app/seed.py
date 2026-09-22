from datetime import datetime, timezone
from backend.app.database import engine, Base, SessionLocal
from backend.app.models import (
    Cuenta,
    Categoria,
    Transaccion,
    MetaAhorro,
    PerfilFinanciero,
    TipoCuenta,
    TipoTransaccion,
    MedioCaptura,
)


def seed_data():
    """
    Inicializa las categorías base del comercio colombiano y el perfil financiero inicial en limpio (0.0).
    NO crea cuentas ficticias ni transacciones de prueba para permitir que el usuario empiece 100% desde cero.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Perfil Financiero Inicial en Limpio
        perfil = db.query(PerfilFinanciero).first()
        if not perfil:
            perfil = PerfilFinanciero(
                dia_pago_mensual=30,
                ingreso_mensual_estimado=0.0,
                compromisos_fijos_mensual=0.0,
                porcentaje_ahorro_meta=10.0,
                umbral_gasto_hormiga=25000.0
            )
            db.add(perfil)

        # 2. Categorías del Ecosistema Colombiano (necesarias para el categorizador automático de compras)
        if db.query(Categoria).count() == 0:
            cat_alim = Categoria(
                nombre="Alimentación y Supermercado",
                icono="shopping-cart",
                color_hex="#10B981",
                palabras_clave="d1,tiendas d1,éxito,exito,carulla,jumbo,ara,tiendas ara,olimpica,crepes,panaderia,restaurante,rappi,comida,almuerzo,desayuno,cena,cafe,café,snack"
            )
            cat_trans = Categoria(
                nombre="Transporte y Movilidad",
                icono="navigation",
                color_hex="#3B82F6",
                palabras_clave="uber,didi,cabify,terpel,texaco,primax,gasolina,peaje,transmilenio,sitp,taxi"
            )
            cat_serv = Categoria(
                nombre="Servicios y Hogar",
                icono="home",
                color_hex="#F59E0B",
                palabras_clave="enel,codensa,epm,acueducto,vanti,claro,movistar,tigo,arriendo,administracion,servicios"
            )
            cat_ocio = Categoria(
                nombre="Ocio y Suscripciones",
                icono="film",
                color_hex="#8B5CF6",
                palabras_clave="netflix,spotify,apple.com/bill,prime,hbo,cine colombia,cine,gym,smart fit"
            )
            cat_salud = Categoria(
                nombre="Salud y Farmacia",
                icono="heart",
                color_hex="#EF4444",
                palabras_clave="farmatodo,cruz verde,drogueria,la rebaja,eps,sanitas,sura,drogas"
            )
            cat_nomina = Categoria(
                nombre="Nómina y Salario",
                icono="dollar-sign",
                color_hex="#059669",
                palabras_clave="nomina,salario,sueldo,honorarios,ingreso"
            )
            db.add_all([cat_alim, cat_trans, cat_serv, cat_ocio, cat_salud, cat_nomina])

        db.commit()
        print("Seed completado: Categorías base inicializadas. Base de datos lista para configuración desde cero.")
    finally:
        db.close()


def reset_database_to_zero():
    """
    Función de utilidad para vaciar todas las cuentas, transacciones y metas,
    permitiendo al usuario iniciar completamente desde cero.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(Transaccion).delete()
        db.query(MetaAhorro).delete()
        db.query(Cuenta).delete()
        perfil = db.query(PerfilFinanciero).first()
        if perfil:
            perfil.ingreso_mensual_estimado = 0.0
            perfil.compromisos_fijos_mensual = 0.0
        db.commit()
        print("Base de datos reiniciada a cero con éxito.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
