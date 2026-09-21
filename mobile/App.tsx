import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  RefreshControl,
  Alert,
  Modal,
  TextInput,
} from 'react-native';
import { ApiService } from './src/services/api';
import { Cuenta, Transaccion, SemaforoData, RendimientoData } from './src/types';

export default function App() {
  const [tab, setTab] = useState<'billetera' | 'transacciones' | 'atajos'>('billetera');
  const [semaforo, setSemaforo] = useState<SemaforoData | null>(null);
  const [rendimientos, setRendimientos] = useState<RendimientoData[]>([]);
  const [cuentas, setCuentas] = useState<Cuenta[]>([]);
  const [transacciones, setTransacciones] = useState<Transaccion[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  // Modal para registro de gasto rápido en efectivo
  const [modalVisible, setModalVisible] = useState(false);
  const [nuevoMonto, setNuevoMonto] = useState('');
  const [nuevoComercio, setNuevoComercio] = useState('');

  const cargarDatos = async () => {
    try {
      setRefreshing(true);
      const [sem, ren, cue, tra] = await Promise.all([
        ApiService.getSemaforo().catch(() => null),
        ApiService.getRendimientos().catch(() => []),
        ApiService.getCuentas().catch(() => []),
        ApiService.getTransacciones().catch(() => []),
      ]);
      if (sem) setSemaforo(sem);
      setRendimientos(ren);
      setCuentas(cue);
      setTransacciones(tra);
    } catch (e) {
      console.log('Error cargando datos:', e);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    cargarDatos();
  }, []);

  const formatearCOP = (monto: number) => {
    return '$ ' + Math.round(monto).toLocaleString('es-CO') + ' COP';
  };

  const guardarGastoRapido = async () => {
    const montoNum = parseFloat(nuevoMonto.replace(/[^0-9]/g, ''));
    if (!montoNum || !nuevoComercio) {
      Alert.alert('Atención', 'Por favor ingresa monto y comercio.');
      return;
    }
    const cEfectivo = cuentas.find((c) => c.tipo === 'EFECTIVO') || cuentas[0];
    if (!cEfectivo) return;

    try {
      await ApiService.registrarGastoManual(montoNum, nuevoComercio, cEfectivo.id);
      Alert.alert('¡Registrado!', `Gasto de ${formatearCOP(montoNum)} guardado.`);
      setModalVisible(false);
      setNuevoMonto('');
      setNuevoComercio('');
      cargarDatos();
    } catch (e) {
      Alert.alert('Error', 'No se pudo conectar con el servidor AUREA.');
    }
  };

  const colorSemaforo = semaforo?.color === 'VERDE' ? '#10B981' : semaforo?.color === 'AMARILLO' ? '#F59E0B' : '#EF4444';

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Header Estilo iOS */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerSub}>AUREA • COP</Text>
          <Text style={styles.headerTitle}>Mi Billetera</Text>
        </View>
        <TouchableOpacity style={styles.addBtn} onPress={() => setModalVisible(true)}>
          <Text style={styles.addBtnText}>+ Gasto</Text>
        </TouchableOpacity>
      </View>

      {/* Contenido Principal con RefreshControl */}
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={cargarDatos} tintColor="#F59E0B" />}
      >
        {tab === 'billetera' && (
          <>
            {/* Tarjeta del Semáforo Mensual */}
            <View style={[styles.card, { borderColor: colorSemaforo }]}>
              <View style={styles.rowBetween}>
                <Text style={styles.cardLabel}>DISPONIBLE PARA HOY</Text>
                <View style={[styles.badge, { backgroundColor: colorSemaforo + '25', borderColor: colorSemaforo }]}>
                  <Text style={[styles.badgeText, { color: colorSemaforo }]}>{semaforo?.color || 'VERDE'}</Text>
                </View>
              </View>
              <Text style={[styles.amountBig, { color: colorSemaforo }]}>
                {formatearCOP(semaforo?.disponible_hoy_restante || 0)}
              </Text>
              <Text style={styles.cardAdvice}>{semaforo?.mensaje_guia || 'Calculando presupuesto...'}</Text>

              <View style={styles.divider} />
              <View style={styles.rowBetween}>
                <View>
                  <Text style={styles.statLabel}>Días restantes</Text>
                  <Text style={styles.statVal}>{semaforo?.dias_restantes || 30} días</Text>
                </View>
                <View style={{ alignItems: 'flex-end' }}>
                  <Text style={styles.statLabel}>Límite diario sugerido</Text>
                  <Text style={[styles.statVal, { color: '#FBBF24' }]}>
                    {formatearCOP(semaforo?.limite_gasto_diario_sugerido || 0)}
                  </Text>
                </View>
              </View>
            </View>

            {/* Rendimientos Diarios Nu Colombia */}
            {rendimientos.length > 0 && (
              <View style={styles.yieldCard}>
                <View>
                  <Text style={styles.yieldSub}>RENDIMIENTOS NU (12.5% E.A.)</Text>
                  <Text style={styles.yieldAmount}>
                    + {formatearCOP(rendimientos[0].rendimiento_diario_estimado)} hoy
                  </Text>
                </View>
                <Text style={styles.yieldPill}>Automático</Text>
              </View>
            )}

            {/* Mis Cuentas e Instrumentos */}
            <Text style={styles.sectionTitle}>MIS INSTRUMENTOS</Text>
            {cuentas.map((c) => (
              <View key={c.id} style={styles.accountCard}>
                <View>
                  <Text style={styles.accountName}>{c.nombre}</Text>
                  <Text style={styles.accountType}>{c.tipo}</Text>
                </View>
                <Text style={[styles.accountBalance, c.tipo === 'CREDITO' ? { color: '#F59E0B' } : { color: '#10B981' }]}>
                  {formatearCOP(c.saldo_actual)}
                </Text>
              </View>
            ))}
          </>
        )}

        {tab === 'transacciones' && (
          <>
            <Text style={styles.sectionTitle}>ÚLTIMOS MOVIMIENTOS</Text>
            {transacciones.length === 0 ? (
              <Text style={styles.emptyText}>No hay transacciones registradas aún.</Text>
            ) : (
              transacciones.map((t) => (
                <View key={t.id} style={styles.txCard}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.txMerchant}>{t.comercio}</Text>
                    <View style={styles.tagRow}>
                      <Text style={styles.txTag}>{t.medio}</Text>
                      {t.es_gasto_hormiga && <Text style={[styles.txTag, { color: '#F59E0B' }]}>Hormiga</Text>}
                    </View>
                  </View>
                  <Text
                    style={[
                      styles.txAmount,
                      t.tipo === 'INGRESO' ? { color: '#10B981' } : t.tipo === 'EGRESO' ? { color: '#EF4444' } : { color: '#60A5FA' },
                    ]}
                  >
                    {t.tipo === 'INGRESO' ? '+' : '-'} {formatearCOP(t.monto)}
                  </Text>
                </View>
              ))
            )}
          </>
        )}

        {tab === 'atajos' && (
          <View style={styles.card}>
            <Text style={styles.cardLabel}>INTEGRACIÓN AUTOMÁTICA DE IPHONE</Text>
            <Text style={styles.shortcutsTitle}>Apple Pay & SMS Bancarios</Text>
            <Text style={styles.shortcutsBody}>
              1. Abre la app <Text style={{ color: '#F59E0B', fontWeight: 'bold' }}>Atajos</Text> en tu iPhone.{'\n'}
              2. Ve a <Text style={{ color: '#F59E0B' }}>Automatización</Text> y pulsa (+).{'\n'}
              3. Selecciona <Text style={{ color: '#F59E0B' }}>Transacción</Text> para Apple Pay o <Text style={{ color: '#F59E0B' }}>Mensaje</Text> para SMS.{'\n'}
              4. Configura acción HTTP POST a:{'\n'}
              <Text style={{ color: '#60A5FA', fontSize: 11 }}>http://tu-servidor-aurea.com/api/v1/webhooks/ios-shortcut</Text>
            </Text>
          </View>
        )}
      </ScrollView>

      {/* Barra Inferior Nativa (Tab Bar) */}
      <View style={styles.tabBar}>
        <TouchableOpacity style={styles.tabItem} onPress={() => setTab('billetera')}>
          <Text style={[styles.tabText, tab === 'billetera' && styles.tabActive]}>Billetera</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.tabItem} onPress={() => setTab('transacciones')}>
          <Text style={[styles.tabText, tab === 'transacciones' && styles.tabActive]}>Movimientos</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.tabItem} onPress={() => setTab('atajos')}>
          <Text style={[styles.tabText, tab === 'atajos' && styles.tabActive]}>Atajos iOS</Text>
        </TouchableOpacity>
      </View>

      {/* Modal Registro de Gasto Rápido */}
      <Modal visible={modalVisible} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Registrar Gasto Rápido</Text>
            <TextInput
              style={styles.input}
              placeholder="Monto en COP (ej: 15000)"
              placeholderTextColor="#64748B"
              keyboardType="numeric"
              value={nuevoMonto}
              onChangeText={setNuevoMonto}
            />
            <TextInput
              style={styles.input}
              placeholder="Comercio (ej: Panadería, Taxi)"
              placeholderTextColor="#64748B"
              value={nuevoComercio}
              onChangeText={setNuevoComercio}
            />
            <View style={styles.modalBtns}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setModalVisible(false)}>
                <Text style={styles.cancelBtnText}>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.saveBtn} onPress={guardarGastoRapido}>
                <Text style={styles.saveBtnText}>Guardar</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0B0F19' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingTop: 10, paddingBottom: 15 },
  headerSub: { fontSize: 11, fontWeight: '700', color: '#F59E0B', letterSpacing: 1.5, textTransform: 'uppercase' },
  headerTitle: { fontSize: 26, fontWeight: '900', color: '#FFFFFF' },
  addBtn: { backgroundColor: '#F59E0B', paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20 },
  addBtnText: { color: '#0F172A', fontWeight: '800', fontSize: 12 },
  scrollContent: { paddingHorizontal: 20, paddingBottom: 40 },
  card: { backgroundColor: '#131B2E', borderRadius: 24, padding: 18, borderWidth: 1, marginBottom: 16 },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardLabel: { fontSize: 10, fontWeight: '700', color: '#94A3B8', letterSpacing: 1 },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12, borderWidth: 1 },
  badgeText: { fontSize: 10, fontWeight: '800' },
  amountBig: { fontSize: 28, fontWeight: '900', marginTop: 4 },
  cardAdvice: { fontSize: 12, color: '#CBD5E1', marginTop: 4, lineHeight: 18 },
  divider: { height: 1, backgroundColor: '#1E293B', marginVertical: 12 },
  statLabel: { fontSize: 11, color: '#94A3B8' },
  statVal: { fontSize: 14, fontWeight: '800', color: '#FFFFFF', marginTop: 2 },
  yieldCard: { backgroundColor: '#2E1065', borderRadius: 20, padding: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, borderWidth: 1, borderColor: '#8B5CF6' },
  yieldSub: { fontSize: 10, fontWeight: '800', color: '#C4B5FD', letterSpacing: 1 },
  yieldAmount: { fontSize: 18, fontWeight: '900', color: '#FFFFFF', marginTop: 2 },
  yieldPill: { backgroundColor: '#4C1D95', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 10, color: '#DDD6FE', fontSize: 10, fontWeight: '700' },
  sectionTitle: { fontSize: 11, fontWeight: '800', color: '#64748B', letterSpacing: 1.5, marginBottom: 10, marginTop: 4 },
  accountCard: { backgroundColor: '#131B2E', borderRadius: 16, padding: 14, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, borderWidth: 1, borderColor: '#1E293B' },
  accountName: { fontSize: 14, fontWeight: '700', color: '#FFFFFF' },
  accountType: { fontSize: 10, color: '#94A3B8', marginTop: 2 },
  accountBalance: { fontSize: 14, fontWeight: '800' },
  txCard: { backgroundColor: '#131B2E', borderRadius: 16, padding: 14, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  txMerchant: { fontSize: 14, fontWeight: '700', color: '#FFFFFF' },
  tagRow: { flexDirection: 'row', gap: 6, marginTop: 4 },
  txTag: { fontSize: 9, fontWeight: '800', color: '#94A3B8', backgroundColor: '#1E293B', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 6 },
  txAmount: { fontSize: 14, fontWeight: '800' },
  emptyText: { color: '#64748B', textAlign: 'center', marginVertical: 30 },
  shortcutsTitle: { fontSize: 18, fontWeight: '800', color: '#FFFFFF', marginTop: 4 },
  shortcutsBody: { fontSize: 13, color: '#CBD5E1', lineHeight: 22, marginTop: 8 },
  tabBar: { flexDirection: 'row', backgroundColor: '#0F172A', borderTopWidth: 1, borderColor: '#1E293B', paddingVertical: 12, justifyContent: 'space-around' },
  tabItem: { alignItems: 'center' },
  tabText: { fontSize: 12, fontWeight: '700', color: '#64748B' },
  tabActive: { color: '#F59E0B' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.7)', justifyContent: 'center', padding: 20 },
  modalCard: { backgroundColor: '#1E293B', borderRadius: 24, padding: 20 },
  modalTitle: { fontSize: 18, fontWeight: '800', color: '#FFFFFF', marginBottom: 16 },
  input: { backgroundColor: '#0F172A', borderRadius: 12, padding: 12, color: '#FFFFFF', fontSize: 14, marginBottom: 12, borderWidth: 1, borderColor: '#334155' },
  modalBtns: { flexDirection: 'row', justifyContent: 'flex-end', gap: 10, marginTop: 8 },
  cancelBtn: { paddingHorizontal: 16, paddingVertical: 10 },
  cancelBtnText: { color: '#94A3B8', fontWeight: '700' },
  saveBtn: { backgroundColor: '#F59E0B', paddingHorizontal: 20, paddingVertical: 10, borderRadius: 12 },
  saveBtnText: { color: '#0F172A', fontWeight: '800' },
});
