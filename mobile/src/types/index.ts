export type TipoCuenta = 'DEBITO' | 'CREDITO' | 'ALTO_RENDIMIENTO' | 'EFECTIVO';
export type TipoTransaccion = 'INGRESO' | 'EGRESO' | 'TRANSFERENCIA_INTERNA';
export type MedioCaptura = 'APPLE_PAY' | 'SMS' | 'MANUAL' | 'WEBHOOK';

export interface Cuenta {
  id: number;
  nombre: string;
  tipo: TipoCuenta;
  saldo_actual: number;
  cupo_total?: number;
  tasa_ea?: number;
  dia_corte?: number;
  dia_limite_pago?: number;
  activa: boolean;
}

export interface Transaccion {
  id: number;
  monto: number;
  tipo: TipoTransaccion;
  medio: MedioCaptura;
  fecha: string;
  comercio: string;
  descripcion?: string;
  es_gasto_hormiga: boolean;
}

export interface SemaforoData {
  color: 'VERDE' | 'AMARILLO' | 'ROJO';
  dia_actual_ciclo: number;
  dias_totales_mes: number;
  dias_restantes: number;
  presupuesto_disponible_total: number;
  limite_gasto_diario_sugerido: number;
  gasto_hoy: number;
  disponible_hoy_restante: number;
  gasto_acumulado_mes: number;
  gastos_hormiga_acumulados: number;
  mensaje_guia: string;
}

export interface RendimientoData {
  cuenta_id: number;
  cuenta_nombre: string;
  saldo_actual: number;
  tasa_ea: number;
  rendimiento_diario_estimado: number;
  rendimiento_mensual_proyectado: number;
}
