import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from backend.app.database import engine, Base
from backend.app.api.v1.api import api_router
from backend.app.seed import seed_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_data()
    yield


app = FastAPI(
    title="AUREA - API Financiera Personal",
    description="Backend para la app móvil AUREA con ingesta desatendida de Apple Pay y SMS bancarios en Colombia (COP).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Habilitar CORS para conexión con la app móvil Expo en iPhone
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectar routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse)
def mobile_dashboard_preview():
    """
    Interfaz Web Nativa para iPhone (PWA Standalone) en COP.
    Diseño fluido de borde a borde sin marcos de celular simulados, con personalización de cuentas reales,
    modo privacidad, edición de saldos y configuración del ciclo de nómina.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="AUREA">
        <title>AUREA • Finanzas Personales</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {
                --sat: env(safe-area-inset-top, 16px);
                --sab: env(safe-area-inset-bottom, 24px);
            }
            body {
                background: #090D16;
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
                -webkit-tap-highlight-color: transparent;
                padding-top: var(--sat);
                padding-bottom: calc(var(--sab) + 70px);
            }
            .ios-card {
                background: rgba(19, 25, 42, 0.85);
                backdrop-filter: blur(25px);
                -webkit-backdrop-filter: blur(25px);
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            .glow-primary {
                box-shadow: 0 4px 20px -2px rgba(245, 158, 11, 0.15);
            }
            /* Ocultar barra de scroll para estética iOS */
            ::-webkit-scrollbar { display: none; }
        </style>
    </head>
    <body class="text-slate-100 min-h-screen selection:bg-amber-500 selection:text-black">
        
        <div class="w-full max-w-lg mx-auto px-4 sm:px-6 pt-2">

            <!-- Top Header Nativo iOS -->
            <div class="flex justify-between items-center py-3 mb-2">
                <div>
                    <div class="flex items-center gap-1.5">
                        <span class="w-2 h-2 rounded-full bg-amber-400"></span>
                        <span class="text-[11px] font-bold tracking-widest text-amber-400 uppercase">AUREA • COP</span>
                    </div>
                    <h1 class="text-2xl font-extrabold text-white tracking-tight">Mi Billetera</h1>
                </div>
                <div class="flex items-center gap-2">
                    <!-- Botón Modo Privacidad 👁️ -->
                    <button onclick="toggleModoPrivacidad()" id="btn-privacidad" class="w-10 h-10 rounded-2xl ios-card flex items-center justify-center text-slate-300 hover:text-white active:scale-95 transition" title="Ocultar saldos">
                        <i class="fa-solid fa-eye text-sm" id="icono-ojo"></i>
                    </button>
                    <!-- Botón Configuración de Nómina Real ⚙️ -->
                    <button onclick="abrirModalPerfil()" class="w-10 h-10 rounded-2xl ios-card flex items-center justify-center text-slate-300 hover:text-white active:scale-95 transition" title="Configurar nómina real">
                        <i class="fa-solid fa-gear text-sm"></i>
                    </button>
                </div>
            </div>

            <!-- Card 1: Balance Neto Disponible -->
            <div class="ios-card rounded-3xl p-5 mb-4 glow-primary">
                <div class="flex justify-between items-start">
                    <div>
                        <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Patrimonio Líquido Disponible</span>
                        <div class="text-3xl font-black text-white mt-1 tracking-tight" id="balance-neto-total">$ 0 COP</div>
                    </div>
                    <span class="text-[10px] font-extrabold uppercase px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                        Nómina Mensual
                    </span>
                </div>
                <div class="flex items-center gap-4 mt-4 pt-3 border-t border-slate-800 text-xs">
                    <div>
                        <span class="text-slate-400 block text-[10px] uppercase font-semibold">Total en Cuentas</span>
                        <span id="subtotal-cuentas" class="font-bold text-emerald-400 text-sm">$ 0</span>
                    </div>
                    <div class="w-px h-6 bg-slate-800"></div>
                    <div>
                        <span class="text-slate-400 block text-[10px] uppercase font-semibold">Deuda en Tarjetas</span>
                        <span id="subtotal-deuda" class="font-bold text-amber-400 text-sm">$ 0</span>
                    </div>
                </div>
            </div>

            <!-- Card 2: Semáforo Dinámico Mensual -->
            <div id="semaforo-card" class="ios-card rounded-3xl p-5 mb-4 relative overflow-hidden transition-all border-emerald-500/30">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Disponible para gastar hoy</span>
                        <div class="text-2xl font-black text-emerald-400 mt-0.5" id="disponible-hoy">$ 0 COP</div>
                    </div>
                    <span id="badge-color" class="px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                        VERDE
                    </span>
                </div>
                <p id="mensaje-guia" class="text-xs text-slate-300 leading-relaxed mt-1">Calculando presupuesto diario según tu nómina...</p>
                
                <div class="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-slate-800 text-xs">
                    <div>
                        <span class="text-slate-400 block text-[10px] uppercase font-semibold">Días restantes del mes</span>
                        <span id="dias-restantes" class="font-bold text-white text-sm">-</span>
                    </div>
                    <div>
                        <span class="text-slate-400 block text-[10px] uppercase font-semibold">Límite diario sugerido</span>
                        <span id="limite-diario" class="font-bold text-amber-300 text-sm">-</span>
                    </div>
                </div>
            </div>

            <!-- Card 3: Rendimientos Nu Colombia (12.5% E.A.) -->
            <div class="ios-card rounded-2xl p-4 mb-4 border border-violet-500/30 bg-violet-950/20 flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-violet-600/30 flex items-center justify-center text-violet-400 text-base">
                        <i class="fa-solid fa-arrow-trend-up"></i>
                    </div>
                    <div>
                        <span class="text-[10px] font-bold uppercase tracking-wider text-violet-300">Rendimientos Nu (12.5% E.A.)</span>
                        <div class="text-sm font-black text-white" id="rendimiento-diario">+ $ 0 COP hoy</div>
                    </div>
                </div>
                <span class="text-[10px] text-violet-300 font-bold bg-violet-900/60 px-2.5 py-1 rounded-lg">Automático</span>
            </div>

            <!-- Card 4: Cuentas e Instrumentos con Edición Rápida -->
            <div class="mb-5">
                <div class="flex justify-between items-center mb-3 px-1">
                    <div>
                        <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Mis Instrumentos</span>
                        <span class="text-[11px] text-slate-500 block">Toca el lápiz para poner tus saldos reales</span>
                    </div>
                    <button onclick="abrirModalNuevaCuenta()" class="px-2.5 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-300 text-xs font-bold border border-amber-500/30 flex items-center gap-1">
                        <i class="fa-solid fa-plus"></i> Cuenta
                    </button>
                </div>
                <div id="cuentas-list" class="space-y-2.5">
                    <!-- Dinámico -->
                </div>
            </div>

            <!-- Accesos Rápidos de Simulación & Limpieza -->
            <div class="ios-card rounded-2xl p-3 mb-6">
                <div class="flex justify-between items-center mb-2 px-1">
                    <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        <i class="fa-brands fa-apple mr-1"></i> Probar Atajos o Limpiar
                    </span>
                    <button onclick="limpiarDatosDemo()" class="text-[10px] text-rose-400 hover:text-rose-300 font-bold underline">
                        Borrar transacciones demo
                    </button>
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <button onclick="simularApplePay()" class="bg-gradient-to-r from-amber-500 to-amber-600 active:scale-95 text-slate-950 font-bold text-xs py-2.5 px-3 rounded-xl transition flex items-center justify-center gap-1.5">
                        <i class="fa-brands fa-apple"></i> Probar Apple Pay
                    </button>
                    <button onclick="simularRetiroSMS()" class="bg-gradient-to-r from-blue-600 to-indigo-600 active:scale-95 text-white font-bold text-xs py-2.5 px-3 rounded-xl transition flex items-center justify-center gap-1.5">
                        <i class="fa-solid fa-money-bill-transfer"></i> Probar Retiro SMS
                    </button>
                </div>
            </div>

            <!-- Movimientos Recientes -->
            <div class="mb-6">
                <div class="flex justify-between items-center mb-3 px-1">
                    <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Últimos Movimientos</span>
                    <span class="text-[11px] text-slate-500" id="conteo-tx">0 movimientos</span>
                </div>
                <div id="transacciones-list" class="space-y-2">
                    <!-- Dinámico -->
                </div>
            </div>

        </div>

        <!-- Barra de Navegación Inferior Flotante Estilo iOS con Botón Central (+) -->
        <div class="fixed bottom-0 left-0 right-0 z-40 bg-slate-900/90 backdrop-blur-xl border-t border-slate-800/80 px-6 py-2.5 flex justify-between items-center max-w-lg mx-auto">
            <button onclick="window.scrollTo({top: 0, behavior: 'smooth'})" class="flex flex-col items-center text-amber-400">
                <i class="fa-solid fa-wallet text-lg"></i>
                <span class="text-[10px] font-bold mt-1">Billetera</span>
            </button>

            <!-- Botón Central Destacado (+) para Registrar Gasto -->
            <button onclick="abrirModalGasto()" class="w-12 h-12 rounded-full bg-gradient-to-tr from-amber-500 to-amber-400 -mt-6 shadow-lg shadow-amber-500/30 flex items-center justify-center text-slate-950 text-xl font-black active:scale-90 transition border-4 border-[#090D16]">
                <i class="fa-solid fa-plus"></i>
            </button>

            <button onclick="recargarDatos()" class="flex flex-col items-center text-slate-400 hover:text-white">
                <i class="fa-solid fa-arrows-rotate text-lg"></i>
                <span class="text-[10px] font-bold mt-1">Refrescar</span>
            </button>
        </div>

        <!-- Modal 1: Registrar Gasto / Ingreso Manual -->
        <div id="modal-gasto" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-slate-900 border border-slate-700">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-extrabold text-white">Registrar Movimiento</h3>
                    <button onclick="cerrarModalGasto()" class="text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="space-y-3">
                    <div>
                        <label class="text-[10px] font-bold uppercase text-slate-400 block mb-1">Tipo</label>
                        <div class="grid grid-cols-2 gap-2">
                            <button type="button" id="btn-tipo-egreso" onclick="setTipoMovimiento('EGRESO')" class="py-2 rounded-xl text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/50">Egreso (Gasto)</button>
                            <button type="button" id="btn-tipo-ingreso" onclick="setTipoMovimiento('INGRESO')" class="py-2 rounded-xl text-xs font-bold bg-slate-800 text-slate-400 border border-slate-700">Ingreso</button>
                        </div>
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-slate-400 block mb-1">Monto en COP</label>
                        <input type="number" id="input-monto" placeholder="Ej: 35000" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-white font-bold text-base focus:border-amber-400 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-slate-400 block mb-1">Comercio / Detalle</label>
                        <input type="text" id="input-comercio" placeholder="Ej: Supermercado D1, Taxi, Almuerzo" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-white text-sm focus:border-amber-400 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-slate-400 block mb-1">Cuenta</label>
                        <select id="select-cuenta" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-white text-sm focus:border-amber-400 outline-none">
                            <!-- Dinámico -->
                        </select>
                    </div>
                    <div class="pt-2 flex gap-2">
                        <button onclick="cerrarModalGasto()" class="w-1/2 py-2.5 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold">Cancelar</button>
                        <button onclick="guardarMovimientoManual()" class="w-1/2 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-black">Guardar</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal 2: Editar Saldo Real de una Cuenta -->
        <div id="modal-editar-cuenta" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-slate-900 border border-slate-700">
                <div class="flex justify-between items-center mb-3">
                    <div>
                        <h3 class="text-base font-extrabold text-white" id="edit-nombre-cuenta">Editar Saldo Real</h3>
                        <span class="text-[11px] text-slate-400" id="edit-tipo-cuenta">Cuenta</span>
                    </div>
                    <button onclick="cerrarModalEditarCuenta()" class="text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <input type="hidden" id="edit-cuenta-id">
                <div class="space-y-3">
                    <div>
                        <label class="text-[10px] font-bold uppercase text-slate-400 block mb-1">Saldo Actual Real en COP</label>
                        <input type="number" id="edit-saldo" placeholder="0" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-white font-bold text-lg focus:border-amber-400 outline-none">
                    </div>
                    <div class="pt-2 flex gap-2">
                        <button onclick="cerrarModalEditarCuenta()" class="w-1/2 py-2.5 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold">Cancelar</button>
                        <button onclick="guardarEdicionSaldo()" class="w-1/2 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-black">Actualizar Saldo</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal 3: Configuración de Nómina Real ⚙️ -->
        <div id="modal-perfil" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-slate-900 border border-slate-700 max-h-[90vh] overflow-y-auto">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-extrabold text-white">Mi Nómina y Finanzas Reales</h3>
                    <button onclick="cerrarModalPerfil()" class="text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="space-y-3">
                    <div>
                        <label class="text-[10px] font-bold uppercase text-slate-400 block mb-1">Ingreso Mensual Estimado (Sueldo COP)</label>
                        <input type="number" id="perfil-ingreso" placeholder="Ej: 4500000" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-amber-400 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-slate-400 block mb-1">Compromisos Fijos Mensuales (Arriendo, Servicios)</label>
                        <input type="number" id="perfil-fijos" placeholder="Ej: 1800000" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-amber-400 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-slate-400 block mb-1">Día de Cobro Mensual (Día de nómina)</label>
                        <input type="number" id="perfil-dia" min="1" max="31" placeholder="Ej: 30" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-amber-400 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-slate-400 block mb-1">Meta de Ahorro Mensual (%)</label>
                        <input type="number" id="perfil-ahorro" min="0" max="100" placeholder="15" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-amber-400 outline-none">
                    </div>
                    <div class="pt-3 flex gap-2">
                        <button onclick="cerrarModalPerfil()" class="w-1/2 py-2.5 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold">Cancelar</button>
                        <button onclick="guardarPerfilReal()" class="w-1/2 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-black">Guardar Ajustes</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let cuentasData = [];
            let modoPrivacidad = false;
            let tipoMovimientoActual = 'EGRESO';

            function toggleModoPrivacidad() {
                modoPrivacidad = !modoPrivacidad;
                const icono = document.getElementById('icono-ojo');
                if(modoPrivacidad) {
                    icono.className = 'fa-solid fa-eye-slash text-amber-400';
                } else {
                    icono.className = 'fa-solid fa-eye text-slate-300';
                }
                recargarDatos();
            }

            function formatearCOP(monto) {
                if(modoPrivacidad) return '$ •••••• COP';
                return '$ ' + Math.round(monto).toLocaleString('es-CO') + ' COP';
            }

            async function cargarSemaforo() {
                try {
                    const res = await fetch('/api/v1/metricas/semaforo');
                    const data = await res.json();
                    document.getElementById('disponible-hoy').innerText = formatearCOP(data.disponible_hoy_restante);
                    document.getElementById('mensaje-guia').innerText = data.mensaje_guia;
                    document.getElementById('dias-restantes').innerText = data.dias_restantes + ' días';
                    document.getElementById('limite-diario').innerText = formatearCOP(data.limite_gasto_diario_sugerido);
                    
                    const badge = document.getElementById('badge-color');
                    badge.innerText = data.color;
                    const card = document.getElementById('semaforo-card');
                    if(data.color === 'VERDE') {
                        badge.className = 'px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/40';
                        card.className = 'ios-card rounded-3xl p-5 mb-4 relative overflow-hidden transition-all border-emerald-500/30';
                    } else if(data.color === 'AMARILLO') {
                        badge.className = 'px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider bg-amber-500/20 text-amber-300 border border-amber-500/40';
                        card.className = 'ios-card rounded-3xl p-5 mb-4 relative overflow-hidden transition-all border-amber-500/30';
                    } else {
                        badge.className = 'px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider bg-rose-500/20 text-rose-300 border border-rose-500/40';
                        card.className = 'ios-card rounded-3xl p-5 mb-4 relative overflow-hidden transition-all border-rose-500/30';
                    }
                } catch (e) {
                    console.error("Error semáforo", e);
                }
            }

            async function cargarRendimientos() {
                try {
                    const res = await fetch('/api/v1/metricas/rendimientos');
                    const data = await res.json();
                    if(data.length > 0) {
                        const total = data.reduce((acc, curr) => acc + curr.rendimiento_diario_estimado, 0);
                        document.getElementById('rendimiento-diario').innerText = '+ ' + formatearCOP(total) + ' hoy';
                    }
                } catch(e) {
                    console.error("Error rendimientos", e);
                }
            }

            async function cargarCuentas() {
                try {
                    const res = await fetch('/api/v1/cuentas');
                    cuentasData = await res.json();
                    
                    let totalCuentas = 0;
                    let totalDeuda = 0;

                    const container = document.getElementById('cuentas-list');
                    const select = document.getElementById('select-cuenta');
                    container.innerHTML = '';
                    select.innerHTML = '';

                    cuentasData.forEach(c => {
                        if(c.tipo === 'CREDITO') {
                            totalDeuda += c.saldo_actual;
                        } else {
                            totalCuentas += c.saldo_actual;
                        }

                        let icon = 'fa-credit-card';
                        let iconColor = 'text-blue-400';
                        if(c.tipo === 'ALTO_RENDIMIENTO') { icon = 'fa-piggy-bank'; iconColor = 'text-purple-400'; }
                        if(c.tipo === 'EFECTIVO') { icon = 'fa-money-bill-wave'; iconColor = 'text-emerald-400'; }
                        if(c.tipo === 'CREDITO') { icon = 'fa-regular fa-credit-card'; iconColor = 'text-amber-400'; }

                        const item = document.createElement('div');
                        item.className = 'ios-card p-3.5 rounded-2xl flex items-center justify-between';
                        item.innerHTML = `
                            <div class="flex items-center gap-3">
                                <div class="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center ${iconColor} text-sm">
                                    <i class="fa-solid ${icon}"></i>
                                </div>
                                <div>
                                    <span class="text-sm font-bold text-white block leading-tight">${c.nombre}</span>
                                    <span class="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">${c.tipo}</span>
                                </div>
                            </div>
                            <div class="flex items-center gap-2.5">
                                <span class="text-sm font-black ${c.tipo === 'CREDITO' ? 'text-amber-400' : 'text-emerald-400'}">
                                    ${formatearCOP(c.saldo_actual)}
                                </span>
                                <button onclick="abrirModalEditarCuenta(${c.id}, '${c.nombre}', '${c.tipo}', ${c.saldo_actual})" class="w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center text-xs transition" title="Editar Saldo Real">
                                    <i class="fa-solid fa-pen"></i>
                                </button>
                            </div>
                        `;
                        container.appendChild(item);

                        // Llenar select modal
                        const opt = document.createElement('option');
                        opt.value = c.id;
                        opt.innerText = c.nombre;
                        select.appendChild(opt);
                    });

                    // Totales
                    document.getElementById('subtotal-cuentas').innerText = formatearCOP(totalCuentas);
                    document.getElementById('subtotal-deuda').innerText = formatearCOP(totalDeuda);
                    const balanceNeto = totalCuentas - totalDeuda;
                    document.getElementById('balance-neto-total').innerText = formatearCOP(balanceNeto);

                } catch(e) {
                    console.error("Error cuentas", e);
                }
            }

            async function cargarTransacciones() {
                try {
                    const res = await fetch('/api/v1/transacciones?limit=15');
                    const txs = await res.json();
                    const container = document.getElementById('transacciones-list');
                    document.getElementById('conteo-tx').innerText = txs.length + ' movimientos';
                    container.innerHTML = '';

                    if(txs.length === 0) {
                        container.innerHTML = '<div class="text-center py-6 text-slate-500 text-xs font-semibold">No hay movimientos registrados. ¡Toca (+) para registrar tu primer gasto!</div>';
                        return;
                    }

                    txs.forEach(t => {
                        const item = document.createElement('div');
                        item.className = 'ios-card p-3 rounded-2xl flex items-center justify-between';
                        item.innerHTML = `
                            <div>
                                <span class="text-xs font-bold text-white block">${t.comercio}</span>
                                <div class="flex items-center gap-1.5 mt-0.5">
                                    <span class="text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">${t.medio}</span>
                                    ${t.es_gasto_hormiga ? '<span class="text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-amber-950 text-amber-300">Hormiga</span>' : ''}
                                </div>
                            </div>
                            <span class="text-xs font-black ${t.tipo === 'INGRESO' ? 'text-emerald-400' : t.tipo === 'EGRESO' ? 'text-rose-400' : 'text-blue-400'}">
                                ${t.tipo === 'INGRESO' ? '+' : '-'} ${formatearCOP(t.monto)}
                            </span>
                        `;
                        container.appendChild(item);
                    });
                } catch(e) {
                    console.error("Error txs", e);
                }
            }

            // Modales y Acciones
            function abrirModalGasto() {
                document.getElementById('modal-gasto').classList.remove('hidden');
                document.getElementById('input-monto').focus();
            }
            function cerrarModalGasto() {
                document.getElementById('modal-gasto').classList.add('hidden');
            }

            function setTipoMovimiento(tipo) {
                tipoMovimientoActual = tipo;
                const btnEgreso = document.getElementById('btn-tipo-egreso');
                const btnIngreso = document.getElementById('btn-tipo-ingreso');
                if(tipo === 'EGRESO') {
                    btnEgreso.className = 'py-2 rounded-xl text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/50';
                    btnIngreso.className = 'py-2 rounded-xl text-xs font-bold bg-slate-800 text-slate-400 border border-slate-700';
                } else {
                    btnIngreso.className = 'py-2 rounded-xl text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/50';
                    btnEgreso.className = 'py-2 rounded-xl text-xs font-bold bg-slate-800 text-slate-400 border border-slate-700';
                }
            }

            async function guardarMovimientoManual() {
                const monto = parseFloat(document.getElementById('input-monto').value);
                const comercio = document.getElementById('input-comercio').value.trim();
                const cuentaId = parseInt(document.getElementById('select-cuenta').value);

                if(!monto || !comercio || !cuentaId) {
                    alert('Por favor ingresa monto, comercio y cuenta.');
                    return;
                }

                await fetch('/api/v1/transacciones', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        monto: monto,
                        comercio: comercio,
                        cuenta_origen_id: cuentaId,
                        tipo: tipoMovimientoActual,
                        medio: 'MANUAL'
                    })
                });

                cerrarModalGasto();
                document.getElementById('input-monto').value = '';
                document.getElementById('input-comercio').value = '';
                recargarDatos();
            }

            function abrirModalEditarCuenta(id, nombre, tipo, saldo) {
                document.getElementById('edit-cuenta-id').value = id;
                document.getElementById('edit-nombre-cuenta').innerText = nombre;
                document.getElementById('edit-tipo-cuenta').innerText = tipo;
                document.getElementById('edit-saldo').value = Math.round(saldo);
                document.getElementById('modal-editar-cuenta').classList.remove('hidden');
            }
            function cerrarModalEditarCuenta() {
                document.getElementById('modal-editar-cuenta').classList.add('hidden');
            }

            async function guardarEdicionSaldo() {
                const id = document.getElementById('edit-cuenta-id').value;
                const nuevoSaldo = parseFloat(document.getElementById('edit-saldo').value);
                if(isNaN(nuevoSaldo)) return;

                await fetch('/api/v1/cuentas/' + id, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ saldo_actual: nuevoSaldo })
                });
                cerrarModalEditarCuenta();
                recargarDatos();
            }

            async function abrirModalPerfil() {
                const res = await fetch('/api/v1/metricas/perfil');
                const perfil = await res.json();
                document.getElementById('perfil-ingreso').value = perfil.ingreso_mensual_estimado;
                document.getElementById('perfil-fijos').value = perfil.compromisos_fijos_mensual;
                document.getElementById('perfil-dia').value = perfil.dia_pago_mensual;
                document.getElementById('perfil-ahorro').value = perfil.porcentaje_ahorro_meta;
                document.getElementById('modal-perfil').classList.remove('hidden');
            }
            function cerrarModalPerfil() {
                document.getElementById('modal-perfil').classList.add('hidden');
            }

            async function guardarPerfilReal() {
                const ingreso = parseFloat(document.getElementById('perfil-ingreso').value);
                const fijos = parseFloat(document.getElementById('perfil-fijos').value);
                const dia = parseInt(document.getElementById('perfil-dia').value);
                const ahorro = parseFloat(document.getElementById('perfil-ahorro').value);

                await fetch('/api/v1/metricas/perfil', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ingreso_mensual_estimado: ingreso,
                        compromisos_fijos_mensual: fijos,
                        dia_pago_mensual: dia,
                        porcentaje_ahorro_meta: ahorro
                    })
                });
                cerrarModalPerfil();
                recargarDatos();
            }

            async function limpiarDatosDemo() {
                if(!confirm('¿Deseas eliminar todas las transacciones de prueba para empezar limpio con tus datos reales?')) return;
                await fetch('/api/v1/metricas/limpiar-demo', { method: 'POST' });
                alert('¡Datos de prueba eliminados! Tu historial ha quedado limpio.');
                recargarDatos();
            }

            async function simularApplePay() {
                const monto = 35000;
                await fetch('/api/v1/webhooks/ios-shortcut', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        medio: 'APPLE_PAY',
                        monto: monto,
                        comercio: 'Tiendas D1 Calle 53',
                        tarjeta: 'Bancolombia'
                    })
                });
                recargarDatos();
            }

            async function simularRetiroSMS() {
                const sms = "Bancolombia le informa retiro por $100.000 en CAJERO EXITO a las 11:00. 21/09/2026";
                await fetch('/api/v1/webhooks/ios-shortcut', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        medio: 'SMS',
                        texto_sms: sms
                    })
                });
                recargarDatos();
            }

            function recargarDatos() {
                cargarSemaforo();
                cargarRendimientos();
                cargarCuentas();
                cargarTransacciones();
            }

            recargarDatos();
        </script>
    </body>
    </html>
    """
    return html_content
