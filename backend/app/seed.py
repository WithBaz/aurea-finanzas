from datetime import datetime, timedelta, timezone
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
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Verificar si ya existen datos
        if db.query(Cuenta).count() > 0:
            print("La base de datos ya contiene datos. Saltando seed.")
            return

        print("Poblando base de datos inicial con ecosistema colombiano en COP...")

        # 1. Perfil Financiero
        perfil = PerfilFinanciero(
            dia_pago_mensual=30,
            ingreso_mensual_estimado=4500000.0,
            compromisos_fijos_mensual=1900000.0,
            porcentaje_ahorro_meta=15.0,
            umbral_gasto_hormiga=25000.0
        )
        db.add(perfil)

        # 2. Cuentas e Instrumentos Financieros
        c_debito = Cuenta(
            nombre="Bancolombia Ahorros",
            tipo=TipoCuenta.DEBITO,
            saldo_actual=2450000.0
        )
        c_nu = Cuenta(
            nombre="Nu Colombia (Cajita Remunerada)",
            tipo=TipoCuenta.ALTO_RENDIMIENTO,
            saldo_actual=5000000.0,
            tasa_ea=12.5
        )
        c_credito = Cuenta(
            nombre="Tarjeta Crédito Bancolombia Visa",
            tipo=TipoCuenta.CREDITO,
            saldo_actual=850000.0,  # Deuda acumulada
            cupo_total=6000000.0,
            dia_corte=15,
            dia_limite_pago=5
        )
        c_efectivo = Cuenta(
            nombre="Billetera Efectivo",
            tipo=TipoCuenta.EFECTIVO,
            saldo_actual=180000.0
        )
        db.add_all([c_debito, c_nu, c_credito, c_efectivo])
        db.flush()

        # 3. Categorías
        cat_alim = Categoria(
            nombre="Alimentación y Supermercado",
            icono="shopping-cart",
            color_hex="#10B981",
            palabras_clave="d1,tiendas d1,éxito,exito,carulla,jumbo,ara,tiendas ara,olimpica,crepes,panaderia,restaurante,rappi"
        )
        cat_trans = Categoria(
            nombre="Transporte y Movilidad",
            icono="navigation",
            color_hex="#3B82F6",
            palabras_clave="uber,didi,cabify,terpel,texaco,primax,gasolina,peaje,transmilenio,sitp"
        )
        cat_serv = Categoria(
            nombre="Servicios y Hogar",
            icono="home",
            color_hex="#F59E0B",
            palabras_clave="enel,codensa,epm,acueducto,vanti,claro,movistar,tigo,arriendo,administracion"
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
            palabras_clave="farmatodo,cruz verde,drogueria,la rebaja,eps,sanitas,sura"
        )
        cat_nomina = Categoria(
            nombre="Nómina y Salario",
            icono="dollar-sign",
            color_hex="#059669",
            palabras_clave="nomina,salario,sueldo,honorarios"
        )
        db.add_all([cat_alim, cat_trans, cat_serv, cat_ocio, cat_salud, cat_nomina])
        db.flush()

        # 4. Metas de Ahorro
        meta_fondo = MetaAhorro(
            nombre="Fondo de Emergencia (6 Meses)",
            monto_objetivo=8000000.0,
            monto_actual=3500000.0,
            icono="shield"
        )
        meta_viaje = MetaAhorro(
            nombre="Viaje Fin de Año",
            monto_objetivo=3000000.0,
            monto_actual=1200000.0,
            icono="compass"
        )
        db.add_all([meta_fondo, meta_viaje])
        db.commit()
        print("Seed completado exitosamente: cuentas base listas sin transacciones ficticias.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
