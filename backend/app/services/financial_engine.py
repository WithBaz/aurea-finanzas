import calendar
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models import (
    Cuenta,
    Transaccion,
    TipoCuenta,
    TipoTransaccion,
    PerfilFinanciero,
)


class FinancialEngine:
    """
    Motor de cálculo financiero para ciclo salarial mensual colombiano en COP.
    """

    @classmethod
    def calcular_semaforo_mensual(cls, db: Session, fecha_referencia: Optional[datetime] = None) -> Dict[str, Any]:
        ahora = fecha_referencia or datetime.now(timezone.utc)
        hoy_inicio = datetime(ahora.year, ahora.month, ahora.day, 0, 0, 0)
        hoy_fin = datetime(ahora.year, ahora.month, ahora.day, 23, 59, 59)

        # 1. Obtener perfil financiero
        perfil = db.query(PerfilFinanciero).first()
        if not perfil:
            perfil = PerfilFinanciero(
                dia_pago_mensual=30,
                ingreso_mensual_estimado=4000000.0,
                compromisos_fijos_mensual=1800000.0,
                porcentaje_ahorro_meta=15.0,
                umbral_gasto_hormiga=25000.0,
            )
            db.add(perfil)
            db.commit()
            db.refresh(perfil)

        # 2. Días del mes y días restantes
        _, total_dias_mes = calendar.monthrange(ahora.year, ahora.month)
        dia_actual = ahora.day
        # Días restantes incluyendo hoy
        dias_restantes = max(1, total_dias_mes - dia_actual + 1)

        # 3. Calcular ingresos y egresos del mes actual
        inicio_mes = datetime(ahora.year, ahora.month, 1, 0, 0, 0)
        fin_mes = datetime(ahora.year, ahora.month, total_dias_mes, 23, 59, 59)

        # Suma de egresos del mes (excluyendo transferencias internas)
        egresos_mes_query = db.query(func.sum(Transaccion.monto)).filter(
            Transaccion.tipo == TipoTransaccion.EGRESO,
            Transaccion.fecha >= inicio_mes,
            Transaccion.fecha <= fin_mes
        ).scalar()
        gasto_acumulado_mes = float(egresos_mes_query or 0.0)

        # Gasto de hoy
        gasto_hoy_query = db.query(func.sum(Transaccion.monto)).filter(
            Transaccion.tipo == TipoTransaccion.EGRESO,
            Transaccion.fecha >= hoy_inicio,
            Transaccion.fecha <= hoy_fin
        ).scalar()
        gasto_hoy = float(gasto_hoy_query or 0.0)

        # Gastos hormiga del mes
        gastos_hormiga_query = db.query(func.sum(Transaccion.monto)).filter(
            Transaccion.tipo == TipoTransaccion.EGRESO,
            Transaccion.es_gasto_hormiga == True,
            Transaccion.fecha >= inicio_mes,
            Transaccion.fecha <= fin_mes
        ).scalar()
        gastos_hormiga_acumulados = float(gastos_hormiga_query or 0.0)

        # 4. Cálculo de presupuesto disponible
        # Presupuesto libre = Ingreso estimado - Compromisos Fijos - Meta Ahorro
        ahorro_planeado = perfil.ingreso_mensual_estimado * (perfil.porcentaje_ahorro_meta / 100.0)
        presupuesto_operativo_total = max(0.0, perfil.ingreso_mensual_estimado - perfil.compromisos_fijos_mensual - ahorro_planeado)
        
        # Presupuesto disponible para lo que resta del mes
        presupuesto_disponible_restante = max(0.0, presupuesto_operativo_total - gasto_acumulado_mes)

        # Límite diario sugerido
        limite_diario_sugerido = round(presupuesto_disponible_restante / dias_restantes, 2)
        disponible_hoy_restante = max(0.0, limite_diario_sugerido - gasto_hoy)

        # 5. Determinación del Semáforo
        if limite_diario_sugerido <= 0:
            color = "ROJO"
            mensaje = "Presupuesto mensual agotado. Limita todos los gastos al mínimo esencial."
        elif gasto_hoy <= (limite_diario_sugerido * 0.85):
            color = "VERDE"
            mensaje = f"Excelente ritmo financiero. Tienes ${disponible_hoy_restante:,.0f} COP disponibles para hoy."
        elif gasto_hoy <= limite_diario_sugerido:
            color = "AMARILLO"
            mensaje = f"Atención: te quedan ${disponible_hoy_restante:,.0f} COP de tu presupuesto diario sugerido."
        else:
            color = "ROJO"
            exceso = gasto_hoy - limite_diario_sugerido
            mensaje = f"Superaste tu meta diaria por ${exceso:,.0f} COP. El límite de los días restantes se recalculará automáticamente."

        return {
            "color": color,
            "dia_actual_ciclo": dia_actual,
            "dias_totales_mes": total_dias_mes,
            "dias_restantes": dias_restantes,
            "presupuesto_disponible_total": round(presupuesto_disponible_restante, 2),
            "limite_gasto_diario_sugerido": limite_diario_sugerido,
            "gasto_hoy": gasto_hoy,
            "disponible_hoy_restante": round(disponible_hoy_restante, 2),
            "gasto_acumulado_mes": gasto_acumulado_mes,
            "gastos_hormiga_acumulados": gastos_hormiga_acumulados,
            "mensaje_guia": mensaje,
        }

    @classmethod
    def calcular_rendimientos_diarios(cls, db: Session) -> List[Dict[str, Any]]:
        """
        Calcula el rendimiento diario y mensual devengado por cuentas de alto rendimiento
        según la fórmula de interés compuesto con tasa E.A.
        Rendimiento diario = Saldo * ((1 + Tasa_EA)^(1/365) - 1)
        """
        cuentas_rendimiento = db.query(Cuenta).filter(
            Cuenta.tipo == TipoCuenta.ALTO_RENDIMIENTO,
            Cuenta.activa == True,
            Cuenta.saldo_actual > 0,
            Cuenta.tasa_ea > 0
        ).all()

        resultados = []
        for cuenta in cuentas_rendimiento:
            tasa_decimal = cuenta.tasa_ea / 100.0
            tasa_diaria = ((1.0 + tasa_decimal) ** (1.0 / 365.0)) - 1.0
            rendimiento_diario = round(cuenta.saldo_actual * tasa_diaria, 2)
            
            # Proyección mensual aproximada (30 días)
            tasa_mensual = ((1.0 + tasa_decimal) ** (30.0 / 365.0)) - 1.0
            rendimiento_mensual = round(cuenta.saldo_actual * tasa_mensual, 2)

            resultados.append({
                "cuenta_id": cuenta.id,
                "cuenta_nombre": cuenta.nombre,
                "saldo_actual": cuenta.saldo_actual,
                "tasa_ea": cuenta.tasa_ea,
                "rendimiento_diario_estimado": rendimiento_diario,
                "rendimiento_mensual_proyectado": rendimiento_mensual,
            })
        return resultados
