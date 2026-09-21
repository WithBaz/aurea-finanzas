import { Cuenta, Transaccion, SemaforoData, RendimientoData } from '../types';

// En desarrollo local en iPhone vía Expo Go, reemplaza '127.0.0.1' por la IP local de tu PC (ej: 192.168.1.XX)
// o por tu URL de despliegue HTTPS en producción
const BASE_URL = 'http://127.0.0.1:8000/api/v1';

export const ApiService = {
  async getSemaforo(): Promise<SemaforoData> {
    const res = await fetch(`${BASE_URL}/metricas/semaforo`);
    if (!res.ok) throw new Error('Error al obtener semáforo');
    return res.json();
  },

  async getRendimientos(): Promise<RendimientoData[]> {
    const res = await fetch(`${BASE_URL}/metricas/rendimientos`);
    if (!res.ok) throw new Error('Error al obtener rendimientos');
    return res.json();
  },

  async getCuentas(): Promise<Cuenta[]> {
    const res = await fetch(`${BASE_URL}/cuentas`);
    if (!res.ok) throw new Error('Error al obtener cuentas');
    return res.json();
  },

  async getTransacciones(): Promise<Transaccion[]> {
    const res = await fetch(`${BASE_URL}/transacciones?limit=25`);
    if (!res.ok) throw new Error('Error al obtener transacciones');
    return res.json();
  },

  async registrarGastoManual(monto: number, comercio: string, cuentaId: number): Promise<Transaccion> {
    const res = await fetch(`${BASE_URL}/transacciones`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        monto,
        comercio,
        cuenta_origen_id: cuentaId,
        tipo: 'EGRESO',
        medio: 'MANUAL',
      }),
    });
    if (!res.ok) throw new Error('Error al registrar gasto');
    return res.json();
  },
};
