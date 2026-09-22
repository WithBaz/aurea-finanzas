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
    description="Backend para la app móvil AUREA con ingesta desatendida de Apple Pay, SMS bancarios y Apple Intelligence en Colombia (COP).",
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
    Diseño minimalista y limpio de borde a borde, con entrada por lenguaje natural (Apple Intelligence),
    gestión completa de cuentas reales, asignación inteligente de compras y cero datos ficticios.
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
                background: #0B0813;
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
                -webkit-tap-highlight-color: transparent;
                padding-top: var(--sat);
                padding-bottom: calc(var(--sab) + 70px);
            }
            .ios-card {
                background: rgba(20, 14, 34, 0.88);
                backdrop-filter: blur(25px);
                -webkit-backdrop-filter: blur(25px);
                border: 1px solid rgba(168, 85, 247, 0.16);
            }
            .glow-primary {
                box-shadow: 0 8px 32px -4px rgba(168, 85, 247, 0.22);
            }
            .tab-view {
                animation: fadeIn 0.15s ease-in-out;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(4px); }
                to { opacity: 1; transform: translateY(0); }
            }
            ::-webkit-scrollbar { display: none; }
        </style>
    </head>
    <body class="text-slate-100 min-h-screen selection:bg-purple-600 selection:text-white">
        
        <div class="w-full max-w-lg mx-auto px-4 sm:px-6 pt-2">

            <!-- Top Header Nativo iOS con Título Dinámico -->
            <div class="flex justify-between items-center py-3 mb-2">
                <div>
                    <div class="flex items-center gap-1.5">
                        <span class="w-2 h-2 rounded-full bg-purple-400"></span>
                        <span class="text-[11px] font-bold tracking-widest text-purple-300 uppercase">AUREA</span>
                        <span id="badge-db" class="text-[9px] font-bold px-2 py-0.5 rounded-full bg-purple-950/60 text-purple-300 border border-purple-800/50">...</span>
                    </div>
                    <h1 class="text-2xl font-black text-white tracking-tight" id="header-titulo">Mi Billetera</h1>
                </div>
            </div>

            <!-- VISTA 1: BILLETERA (Panel Principal) -->
            <div id="view-billetera" class="tab-view pb-24">
                <!-- Apartado 1: Saldo Disponible para Gastar con Saldo Total Integrado -->
                <div class="ios-card rounded-3xl p-5 mb-4 glow-primary border border-purple-500/25 bg-gradient-to-b from-[#160F2E] to-[#0E0A1A]">
                    <!-- Saldo disponible para gastar -->
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Saldo disponible para gastar</span>
                            <div class="flex items-center gap-2.5 mt-1">
                                <div class="text-3xl font-black text-emerald-400 tracking-tight" id="disponible-hoy">$ 0</div>
                                <!-- Modo Privacidad 👁️ al lado del saldo principal -->
                                <button onclick="toggleModoPrivacidad()" id="btn-privacidad" class="w-7 h-7 rounded-lg bg-purple-950/40 hover:bg-purple-900/50 flex items-center justify-center text-purple-300 hover:text-white active:scale-90 transition border border-purple-500/25" title="Ocultar o ver saldo">
                                    <i class="fa-solid fa-eye text-xs" id="icono-ojo"></i>
                                </button>
                            </div>
                        </div>
                        <span id="badge-disponible" class="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                            LIBRE PARA GASTAR
                        </span>
                    </div>

                    <!-- Apartado integrado: Saldo Total y Gastos Fijos -->
                    <div class="mt-4 pt-3.5 border-t border-purple-900/40 grid grid-cols-2 gap-3">
                        <div class="p-3 rounded-2xl bg-[#0B0816]/80 border border-purple-900/30 flex flex-col justify-between">
                            <div>
                                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Saldo Total</span>
                                <div class="text-lg font-black text-white mt-0.5" id="balance-neto-total">$ 0</div>
                            </div>
                            <button onclick="cambiarTab('cuentas')" class="text-[10px] text-purple-300 font-bold hover:text-white flex items-center gap-1 mt-2 transition">
                                <span>Ver Cuentas</span>
                                <i class="fa-solid fa-chevron-right text-[8px]"></i>
                            </button>
                        </div>
                        <div class="p-3 rounded-2xl bg-[#0B0816]/80 border border-purple-900/30 flex flex-col justify-between">
                            <div>
                                <span class="text-[10px] font-bold text-purple-300 uppercase tracking-wider block">Gastos Fijos</span>
                                <div class="text-lg font-black text-purple-200 mt-0.5" id="subtotal-apartado-fijos">$ 0</div>
                            </div>
                            <span class="text-[9px] text-purple-400/80 font-semibold block mt-2" id="estado-fijos-apartados">
                                Apartado de nómina
                            </span>
                        </div>
                    </div>
                </div>

                <!-- Apartado 2: Gastos Fijos del Mes -->
                <div class="ios-card rounded-3xl p-5 mb-4 border border-purple-500/25 bg-gradient-to-b from-[#140E24] to-[#0E0A1A]">
                    <div class="flex justify-between items-start mb-2">
                        <div>
                            <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Gastos Fijos del Mes</span>
                            <div class="text-2xl font-black text-purple-200 mt-0.5" id="total-gastos-fijos">$ 0</div>
                        </div>
                        <span id="badge-estado-gastos-fijos" class="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-purple-950/80 text-purple-300 border border-purple-600/40">
                            🔒 APARTADOS DE NÓMINA
                        </span>
                    </div>
                    <p class="text-[11px] text-purple-300/70 leading-relaxed mb-3">
                        Descontados automáticamente de tu saldo disponible para proteger tus pagos fijos.
                    </p>

                    <div class="flex justify-between items-center mb-2.5 pt-2 border-t border-purple-900/30">
                        <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Compromisos Fijos</span>
                        <button onclick="abrirModalNuevoGastoFijo()" class="px-2.5 py-1 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 text-[11px] font-bold border border-purple-500/35 flex items-center gap-1 active:scale-95 transition">
                            <i class="fa-solid fa-plus text-[9px]"></i>
                            <span>Agregar Gasto Fijo</span>
                        </button>
                    </div>

                    <div id="gastos-fijos-list" class="space-y-2">
                        <!-- Dinámico -->
                    </div>
                </div>
            </div>

            <!-- VISTA 2: MOVIMIENTOS (Panel Independiente) -->
            <div id="view-movimientos" class="tab-view hidden pb-24">
                <div class="flex justify-between items-center mb-4">
                    <div>
                        <span class="text-[11px] font-bold text-purple-400 uppercase tracking-wider">Historial Financiero</span>
                        <div class="text-xs text-purple-300/70" id="conteo-tx">0 movimientos</div>
                    </div>
                    <button onclick="abrirModalGasto()" class="px-3 py-1.5 rounded-xl bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 text-xs font-bold border border-purple-500/35 flex items-center gap-1.5 active:scale-95 transition">
                        <i class="fa-solid fa-plus text-[10px]"></i>
                        <span>Registrar</span>
                    </button>
                </div>

                <div id="transacciones-list" class="space-y-2.5">
                    <!-- Dinámico -->
                </div>
            </div>

            <!-- VISTA 3: CUENTAS E INSTRUMENTOS (Panel Independiente) -->
            <div id="view-cuentas" class="tab-view hidden pb-24">
                <div class="flex justify-between items-center mb-3">
                    <div>
                        <span class="text-[11px] font-bold text-purple-400 uppercase tracking-wider">Tus Instrumentos</span>
                        <p class="text-[11px] text-purple-300/70">Toca el lápiz para actualizar tu saldo real</p>
                    </div>
                    <button onclick="abrirModalNuevaCuenta()" class="px-3 py-1.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-black shadow-md shadow-purple-900/30 flex items-center gap-1.5 active:scale-95 transition">
                        <i class="fa-solid fa-plus text-[10px]"></i>
                        <span>Nueva Cuenta</span>
                    </button>
                </div>

                <!-- Resumen de Saldos -->
                <div class="ios-card p-4 rounded-3xl mb-4 border border-purple-500/20 bg-gradient-to-r from-purple-950/40 via-[#130E26] to-[#0E0A1A]">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <span class="text-slate-400 block text-[10px] uppercase font-bold tracking-wider">Total en Cuentas</span>
                            <span id="subtotal-cuentas" class="font-black text-emerald-400 text-lg">$ 0</span>
                        </div>
                        <div>
                            <span class="text-slate-400 block text-[10px] uppercase font-bold tracking-wider">Deuda en Tarjetas</span>
                            <span id="subtotal-deuda" class="font-black text-rose-400 text-lg">$ 0</span>
                        </div>
                    </div>
                </div>

                <!-- Rendimientos Nu (Cuenta de Alto Rendimiento) -->
                <div id="card-rendimientos" class="ios-card p-3.5 rounded-2xl mb-4 flex items-center justify-between border border-fuchsia-500/25 bg-fuchsia-950/20" style="display: none;">
                    <div class="flex items-center gap-2.5">
                        <div class="w-8 h-8 rounded-xl bg-fuchsia-500/20 text-fuchsia-300 flex items-center justify-center text-xs">
                            <i class="fa-solid fa-piggy-bank"></i>
                        </div>
                        <div>
                            <span class="text-xs font-bold text-white block">Rendimientos Nu (Cajita)</span>
                            <span class="text-[10px] text-fuchsia-300/80">12.5% E.A. estimado</span>
                        </div>
                    </div>
                    <span id="rendimiento-diario" class="text-xs font-black text-fuchsia-300">+ $ 0 hoy</span>
                </div>

                <!-- Lista de Cuentas -->
                <div id="cuentas-list" class="space-y-2.5 mb-4">
                    <!-- Dinámico -->
                </div>
            </div>

            <!-- VISTA 4: AJUSTES Y NÓMINA (Panel Independiente) -->
            <div id="view-ajustes" class="tab-view hidden pb-24">
                <div class="mb-4">
                    <span class="text-[11px] font-bold text-purple-400 uppercase tracking-wider">Configuración Personal</span>
                    <p class="text-[11px] text-purple-300/70">Personaliza tu ciclo de nómina mensual y atajos de Siri</p>
                </div>

                <!-- Card: Mi Nómina -->
                <div class="ios-card rounded-3xl p-5 mb-4 border border-purple-500/25 bg-gradient-to-b from-[#140E24] to-[#0E0A1A]">
                    <div class="flex items-center gap-2 mb-3">
                        <div class="w-7 h-7 rounded-lg bg-purple-900/50 text-purple-300 flex items-center justify-center text-xs">
                            <i class="fa-solid fa-money-check-dollar"></i>
                        </div>
                        <h3 class="text-sm font-extrabold text-white">Mi Nómina y Finanzas</h3>
                    </div>
                    <div class="space-y-3">
                        <div>
                            <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Ingreso Mensual Estimado (Sueldo $)</label>
                            <input type="number" id="perfil-ingreso" placeholder="Ej: 4500000" class="w-full bg-[#0B0816] border border-purple-900/40 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-purple-400 outline-none">
                        </div>
                        <div>
                            <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Día de Cobro Mensual (Día de nómina 1-31)</label>
                            <input type="number" id="perfil-dia" min="1" max="31" placeholder="Ej: 1" class="w-full bg-[#0B0816] border border-purple-900/40 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-purple-400 outline-none">
                        </div>
                        <div>
                            <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Meta de Ahorro Mensual (%)</label>
                            <input type="number" id="perfil-ahorro" min="0" max="100" placeholder="15" class="w-full bg-[#0B0816] border border-purple-900/40 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-purple-400 outline-none">
                        </div>
                        <button onclick="guardarPerfilReal()" class="w-full py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-black shadow-md shadow-purple-900/30 active:scale-95 transition">
                            Guardar Ajustes de Nómina
                        </button>
                    </div>
                </div>

                <!-- Card: Atajos de iOS & Siri -->
                <div class="ios-card rounded-3xl p-5 mb-4 border border-purple-500/25 bg-gradient-to-b from-[#140E24] to-[#0E0A1A]">
                    <div class="flex items-center gap-2 mb-3">
                        <div class="w-7 h-7 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center text-xs">
                            <i class="fa-solid fa-bolt"></i>
                        </div>
                        <h3 class="text-sm font-extrabold text-white">Atajos de iOS & Siri</h3>
                    </div>
                    
                    <div class="space-y-3 text-xs">
                        <!-- Guía 1: Siri Registrar Gasto -->
                        <div class="p-3 rounded-2xl bg-[#0B0816] border border-amber-500/25">
                            <span class="text-amber-400 font-bold text-xs block mb-1">1. Atajo Siri: "Registrar Gasto"</span>
                            <p class="text-[11px] text-slate-300 mb-2">Di <em>"Oye Siri, registrar gasto"</em> y dicta (ej. <em>"15 mil de taxi"</em>).</p>
                            <div class="flex items-center gap-2">
                                <input type="text" id="url-ia-endpoint" readonly class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-[10px] text-amber-300 font-mono select-all">
                                <button onclick="copiarUrlIA()" class="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-black text-[10px] shrink-0 active:scale-95 transition">
                                    Copiar
                                </button>
                            </div>
                        </div>

                        <!-- Guía 2: Siri Registrar Ingreso -->
                        <div class="p-3 rounded-2xl bg-[#0B0816] border border-emerald-500/25">
                            <span class="text-emerald-400 font-bold text-xs block mb-1">2. Atajo Siri: "Registrar Ingreso"</span>
                            <p class="text-[11px] text-slate-300 mb-2">Di <em>"Oye Siri, registrar ingreso"</em> y dicta (ej. <em>"500 mil sueldo"</em>).</p>
                            <div class="flex items-center gap-2">
                                <input type="text" id="url-ia-ingreso-endpoint" readonly class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-[10px] text-emerald-300 font-mono select-all">
                                <button onclick="copiarUrlIAIngreso()" class="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-[10px] shrink-0 active:scale-95 transition">
                                    Copiar
                                </button>
                            </div>
                        </div>

                        <!-- Guía 3: Apple Pay Automático -->
                        <div class="p-3 rounded-2xl bg-[#0B0816] border border-blue-500/25">
                            <span class="text-blue-400 font-bold text-xs block mb-1">3. Apple Pay Automático (Wallet)</span>
                            <p class="text-[11px] text-slate-300 mb-2">En Atajos -> Automatización -> "Transacción de Wallet".</p>
                            <div class="flex items-center gap-2">
                                <input type="text" id="url-webhook-endpoint" readonly class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-[10px] text-blue-300 font-mono select-all">
                                <button onclick="copiarUrlWebhook()" class="px-3 py-1.5 rounded-lg bg-blue-500 hover:bg-blue-400 text-white font-bold text-[10px] shrink-0 active:scale-95 transition">
                                    Copiar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Card: Zona de Peligro -->
                <div class="ios-card rounded-3xl p-5 mb-6 border border-rose-500/20 bg-rose-950/10 text-center">
                    <span class="text-[10px] font-bold text-rose-400 uppercase tracking-wider block mb-2">Reinicio Completo</span>
                    <button onclick="reiniciarTodoDesdeCero()" class="w-full py-2.5 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs font-bold transition flex items-center justify-center gap-2 active:scale-95">
                        <i class="fa-solid fa-trash-can"></i>
                        <span>Borrar todo y empezar desde cero</span>
                    </button>
                </div>
            </div>

        </div>

        <!-- Barra de Navegación Inferior Flotante con Pestañas Independientes -->
        <nav class="fixed bottom-0 left-0 right-0 z-40 bg-[#0E0A1D]/95 backdrop-blur-xl border-t border-purple-500/20 px-5 py-2 flex justify-between items-center max-w-lg mx-auto">
            <button onclick="cambiarTab('billetera')" id="tab-btn-billetera" class="flex flex-col items-center text-purple-400 py-1 transition-colors">
                <i class="fa-solid fa-wallet text-base"></i>
                <span class="text-[10px] font-bold mt-1">Billetera</span>
            </button>

            <button onclick="cambiarTab('movimientos')" id="tab-btn-movimientos" class="flex flex-col items-center text-slate-400 hover:text-purple-300 py-1 transition-colors">
                <i class="fa-solid fa-clock-rotate-left text-base"></i>
                <span class="text-[10px] font-bold mt-1">Movimientos</span>
            </button>

            <!-- Botón Central Destacado (+) para Registrar Gasto / Ingreso Rápido -->
            <button onclick="abrirModalGasto()" class="w-12 h-12 rounded-full bg-gradient-to-tr from-purple-600 via-purple-500 to-fuchsia-500 -mt-6 shadow-lg shadow-purple-600/40 flex items-center justify-center text-white text-xl font-black active:scale-90 transition border-4 border-[#0B0813]" title="Registrar Movimiento">
                <i class="fa-solid fa-plus"></i>
            </button>

            <button onclick="cambiarTab('cuentas')" id="tab-btn-cuentas" class="flex flex-col items-center text-slate-400 hover:text-purple-300 py-1 transition-colors">
                <i class="fa-solid fa-credit-card text-base"></i>
                <span class="text-[10px] font-bold mt-1">Cuentas</span>
            </button>

            <button onclick="cambiarTab('ajustes')" id="tab-btn-ajustes" class="flex flex-col items-center text-slate-400 hover:text-purple-300 py-1 transition-colors">
                <i class="fa-solid fa-gear text-base"></i>
                <span class="text-[10px] font-bold mt-1">Ajustes</span>
            </button>
        </nav>

        <!-- Modal 1: ¿De qué cuenta fue la compra? (Detección y Confirmación Inteligente) -->
        <div id="modal-preguntar-cuenta" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-[#130E26] border border-purple-500/25">
                <div class="text-center mb-4">
                    <div class="w-12 h-12 rounded-2xl bg-purple-500/20 text-purple-400 text-xl flex items-center justify-center mx-auto mb-2">
                        <i class="fa-solid fa-question"></i>
                    </div>
                    <h3 class="text-lg font-black text-white" id="pregunta-titulo">¿De qué cuenta fue el pago?</h3>
                    <p class="text-xs text-slate-300 mt-1" id="pregunta-subtitulo">Selecciona la cuenta para descontar el saldo:</p>
                </div>
                <div id="opciones-cuentas-pregunta" class="space-y-2 mb-4">
                    <!-- Dinámico -->
                </div>
                <button onclick="cerrarModalPreguntaCuenta()" class="w-full py-2.5 rounded-xl bg-purple-950/40 hover:bg-purple-900/50 text-purple-200 border border-purple-900/30 text-xs font-bold">Cancelar</button>
            </div>
        </div>

        <!-- Modal 2: Registrar Gasto / Ingreso Manual -->
        <div id="modal-gasto" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-[#130E26] border border-purple-500/25">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-extrabold text-white">Registrar Movimiento</h3>
                    <button onclick="cerrarModalGasto()" class="text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="space-y-3">
                    <div>
                        <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Tipo</label>
                        <div class="grid grid-cols-2 gap-2">
                            <button type="button" id="btn-tipo-egreso" onclick="setTipoMovimiento('EGRESO')" class="py-2 rounded-xl text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/50">Egreso (Gasto)</button>
                            <button type="button" id="btn-tipo-ingreso" onclick="setTipoMovimiento('INGRESO')" class="py-2 rounded-xl text-xs font-bold bg-purple-950/40 text-slate-400 border border-purple-900/30">Ingreso</button>
                        </div>
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Monto ($)</label>
                        <input type="number" id="input-monto" placeholder="Ej: 35000" class="w-full bg-[#0B0816] border border-purple-900/40 rounded-xl px-3 py-2.5 text-white font-bold text-base focus:border-purple-400 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Comercio / Detalle</label>
                        <input type="text" id="input-comercio" placeholder="Ej: Supermercado D1, Taxi, Almuerzo" class="w-full bg-[#0B0816] border border-purple-900/40 rounded-xl px-3 py-2.5 text-white text-sm focus:border-purple-400 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Cuenta</label>
                        <select id="select-cuenta" class="w-full bg-[#0B0816] border border-purple-900/40 rounded-xl px-3 py-2.5 text-white text-sm focus:border-purple-400 outline-none">
                            <!-- Dinámico -->
                        </select>
                    </div>
                    <div class="pt-2 flex gap-2">
                        <button onclick="cerrarModalGasto()" class="w-1/2 py-2.5 rounded-xl bg-purple-950/40 hover:bg-purple-900/50 text-purple-200 border border-purple-900/30 text-xs font-bold">Cancelar</button>
                        <button onclick="guardarMovimientoManual()" class="w-1/2 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-black shadow-md shadow-purple-900/30">Guardar</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal 3: Editar Saldo Real de una Cuenta -->
        <div id="modal-editar-cuenta" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-[#130E26] border border-purple-500/25">
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
                        <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Nombre de la Cuenta</label>
                        <input type="text" id="edit-nombre-input" class="w-full bg-[#0B0816] border border-purple-900/40 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-purple-400 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Saldo Actual Real ($)</label>
                        <input type="number" id="edit-saldo" placeholder="0" class="w-full bg-[#0B0816] border border-purple-900/40 rounded-xl px-3 py-2.5 text-white font-bold text-lg focus:border-purple-400 outline-none">
                    </div>
                    <div class="pt-2 flex gap-2">
                        <button onclick="eliminarCuentaActual()" class="py-2.5 px-3 rounded-xl bg-rose-500/20 text-rose-300 text-xs font-bold border border-rose-500/30">Eliminar</button>
                        <button onclick="guardarEdicionSaldo()" class="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-black shadow-md shadow-purple-900/30">Actualizar Saldo</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal 4: Agregar Nueva Cuenta Personalizada -->
        <div id="modal-nueva-cuenta" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-[#130E26] border border-purple-500/25">
                <div class="flex justify-between items-center mb-3">
                    <h3 class="text-base font-extrabold text-white">Agregar Nueva Cuenta</h3>
                    <button onclick="cerrarModalNuevaCuenta()" class="text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="space-y-3">
                    <div>
                        <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Nombre de la Cuenta</label>
                        <input type="text" id="nueva-cuenta-nombre" placeholder="Ej: Nequi, Daviplata, Bancolombia, Billetera" class="w-full bg-[#0B0816] border border-purple-900/40 rounded-xl px-3 py-2 text-white text-sm focus:border-purple-400 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Tipo de Instrumento</label>
                        <select id="nueva-cuenta-tipo" class="w-full bg-[#0B0816] border border-purple-900/40 rounded-xl px-3 py-2 text-white text-sm focus:border-purple-400 outline-none">
                            <option value="DEBITO">Cuenta Débito / Ahorros (Bancolombia, Nequi)</option>
                            <option value="EFECTIVO">Efectivo Físico (Billetera)</option>
                            <option value="CREDITO">Tarjeta de Crédito (Visa, Mastercard)</option>
                            <option value="ALTO_RENDIMIENTO">Cuenta Alto Rendimiento (Nu, Lulo, Pibank)</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Saldo Inicial ($)</label>
                        <input type="number" id="nueva-cuenta-saldo" placeholder="0" class="w-full bg-[#0B0816] border border-purple-900/40 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-purple-400 outline-none">
                    </div>
                    <div class="pt-2 flex gap-2">
                        <button onclick="cerrarModalNuevaCuenta()" class="w-1/2 py-2.5 rounded-xl bg-purple-950/40 hover:bg-purple-900/50 text-purple-200 border border-purple-900/30 text-xs font-bold">Cancelar</button>
                        <button onclick="guardarNuevaCuenta()" class="w-1/2 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-black shadow-md shadow-purple-900/30">Crear Cuenta</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal: Agregar Nuevo Gasto Fijo 📌 -->
        <div id="modal-nuevo-gasto-fijo" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-[#130E26] border border-purple-500/25">
                <div class="flex justify-between items-center mb-3">
                    <h3 class="text-base font-extrabold text-white">Agregar Gasto Fijo Mensual</h3>
                    <button onclick="cerrarModalNuevoGastoFijo()" class="text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="space-y-3">
                    <div>
                        <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Concepto / Nombre</label>
                        <input type="text" id="nuevo-fijo-nombre" placeholder="Ej: Arriendo, Internet, Servicios Públicos, Seguro" class="w-full bg-[#0B0816] border border-purple-900/40 rounded-xl px-3 py-2 text-white text-sm focus:border-purple-400 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Monto Mensual ($)</label>
                        <input type="number" id="nuevo-fijo-monto" placeholder="Ej: 1200000" class="w-full bg-[#0B0816] border border-purple-900/40 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-purple-400 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-purple-300 block mb-1">Día Habitual de Pago (1 - 31)</label>
                        <input type="number" id="nuevo-fijo-dia" min="1" max="31" placeholder="Ej: 5" value="5" class="w-full bg-[#0B0816] border border-purple-900/40 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-purple-400 outline-none">
                    </div>
                    <div class="pt-2 flex gap-2">
                        <button onclick="cerrarModalNuevoGastoFijo()" class="w-1/2 py-2.5 rounded-xl bg-purple-950/40 hover:bg-purple-900/50 text-purple-200 border border-purple-900/30 text-xs font-bold">Cancelar</button>
                        <button onclick="guardarNuevoGastoFijo()" class="w-1/2 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-black shadow-md shadow-purple-900/30">Crear Gasto Fijo</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let cuentasData = [];
            let modoPrivacidad = false;
            let tipoMovimientoActual = 'EGRESO';
            let transaccionPendienteAsignar = null;

            function toggleModoPrivacidad() {
                modoPrivacidad = !modoPrivacidad;
                const icono = document.getElementById('icono-ojo');
                if(modoPrivacidad) {
                    icono.className = 'fa-solid fa-eye-slash text-fuchsia-400';
                } else {
                    icono.className = 'fa-solid fa-eye text-purple-300';
                }
                recargarDatos();
            }

            function formatearCOP(monto) {
                if(modoPrivacidad) return '$ ••••••';
                return '$ ' + Math.round(monto).toLocaleString('es-CO');
            }

            // Renderizado unificado y ultra-rápido del Dashboard
            function aplicarDatosDashboard(data) {
                if(!data) return;

                // Estado de la Base de Datos
                const badgeDb = document.getElementById('badge-db');
                if(badgeDb) {
                    if(data.es_postgresql) {
                        badgeDb.className = 'text-[9px] font-black px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40';
                        badgeDb.innerText = '☁️ NUBE';
                        badgeDb.title = 'Conectado a PostgreSQL en la nube (persistente)';
                    } else {
                        badgeDb.className = 'text-[9px] font-bold px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-300 border border-purple-500/30';
                        badgeDb.innerText = '📱 LOCAL';
                        badgeDb.title = 'Guardado local en tu iPhone con auto-rehidratación';
                    }
                }

                // 1. Cuentas e Instrumentos
                cuentasData = data.cuentas || [];
                let totalCuentas = 0;
                let totalDeuda = 0;
                const containerCuentas = document.getElementById('cuentas-list');
                const selectCuenta = document.getElementById('select-cuenta');
                if(containerCuentas) containerCuentas.innerHTML = '';
                if(selectCuenta) selectCuenta.innerHTML = '';

                if(cuentasData.length === 0) {
                    if(containerCuentas) {
                        containerCuentas.innerHTML = `
                            <div class="ios-card p-6 rounded-3xl text-center border border-purple-500/25 bg-gradient-to-b from-[#130E26] to-purple-950/20">
                                <div class="w-12 h-12 rounded-2xl bg-purple-500/20 text-purple-400 flex items-center justify-center mx-auto mb-3 text-lg">
                                    <i class="fa-solid fa-wallet"></i>
                                </div>
                                <h4 class="text-sm font-black text-white mb-1">¡Todo listo para empezar!</h4>
                                <p class="text-xs text-slate-400 mb-4 leading-relaxed">No tienes cuentas configuradas aún. Registra tu cuenta bancaria o efectivo con tu saldo real.</p>
                                <button onclick="abrirModalNuevaCuenta()" class="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 active:scale-95 text-white font-black text-xs flex items-center justify-center gap-2 transition shadow-lg shadow-purple-900/40">
                                    <i class="fa-solid fa-plus text-sm"></i>
                                    <span>Agregar Mi Primera Cuenta</span>
                                </button>
                            </div>
                        `;
                    }
                    if(selectCuenta) {
                        const opt = document.createElement('option');
                        opt.value = "";
                        opt.innerText = "Primero crea una cuenta";
                        selectCuenta.appendChild(opt);
                    }
                } else {
                    cuentasData.forEach(c => {
                        if(c.tipo === 'CREDITO') {
                            totalDeuda += c.saldo_actual;
                        } else {
                            totalCuentas += c.saldo_actual;
                        }

                        let icon = 'fa-credit-card';
                        let iconColor = 'text-indigo-400';
                        if(c.tipo === 'ALTO_RENDIMIENTO') { icon = 'fa-piggy-bank'; iconColor = 'text-fuchsia-400'; }
                        if(c.tipo === 'EFECTIVO') { icon = 'fa-money-bill-wave'; iconColor = 'text-emerald-400'; }
                        if(c.tipo === 'CREDITO') { icon = 'fa-regular fa-credit-card'; iconColor = 'text-rose-400'; }

                        if(containerCuentas) {
                            const item = document.createElement('div');
                            item.className = 'ios-card p-3.5 rounded-2xl flex items-center justify-between border border-purple-500/15';
                            item.innerHTML = `
                                <div class="flex items-center gap-3">
                                    <div class="w-9 h-9 rounded-xl bg-purple-950/50 flex items-center justify-center ${iconColor} text-sm">
                                        <i class="fa-solid ${icon}"></i>
                                    </div>
                                    <div>
                                        <span class="text-sm font-bold text-white block leading-tight">${c.nombre}</span>
                                        <span class="text-[10px] text-purple-300/70 uppercase tracking-wider font-semibold">${c.tipo}</span>
                                    </div>
                                </div>
                                <div class="flex items-center gap-2.5">
                                    <span class="text-sm font-black ${c.tipo === 'CREDITO' ? 'text-rose-400' : 'text-emerald-400'}">
                                        ${formatearCOP(c.saldo_actual)}
                                    </span>
                                    <button onclick="abrirModalEditarCuenta(${c.id}, '${c.nombre}', '${c.tipo}', ${c.saldo_actual})" class="w-7 h-7 rounded-lg bg-purple-950/40 hover:bg-purple-900/50 text-purple-300 hover:text-white flex items-center justify-center text-xs transition border border-purple-500/20" title="Editar Saldo Real">
                                        <i class="fa-solid fa-pen"></i>
                                    </button>
                                </div>
                            `;
                            containerCuentas.appendChild(item);
                        }

                        if(selectCuenta) {
                            const opt = document.createElement('option');
                            opt.value = c.id;
                            opt.innerText = c.nombre;
                            selectCuenta.appendChild(opt);
                        }
                    });
                }

                const elSubCuentas = document.getElementById('subtotal-cuentas');
                if(elSubCuentas) elSubCuentas.innerText = formatearCOP(totalCuentas);

                const elSubDeuda = document.getElementById('subtotal-deuda');
                if(elSubDeuda) elSubDeuda.innerText = formatearCOP(totalDeuda);

                const balanceNeto = totalCuentas - totalDeuda;
                const elBalTotal = document.getElementById('balance-neto-total');
                if(elBalTotal) elBalTotal.innerText = formatearCOP(balanceNeto);

                // 2. Gastos Fijos (Apartados de Nómina)
                const gfData = data.gastos_fijos;
                let totalFijos = 0;
                let nominaRecibida = false;
                if(gfData) {
                    totalFijos = gfData.total_fijos || 0;
                    nominaRecibida = !!gfData.nomina_recibida;
                    const totalGfEl = document.getElementById('total-gastos-fijos');
                    if(totalGfEl) totalGfEl.innerText = formatearCOP(totalFijos);

                    const badgeGf = document.getElementById('badge-estado-gastos-fijos');
                    if(badgeGf) {
                        if(nominaRecibida) {
                            badgeGf.className = 'px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-purple-950/80 text-purple-300 border border-purple-600/40';
                            badgeGf.innerText = '🔒 APARTADOS DE NÓMINA';
                        } else {
                            badgeGf.className = 'px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-amber-500/20 text-amber-300 border border-amber-500/40';
                            badgeGf.innerText = '⏳ PENDIENTE POR APARTAR';
                        }
                    }

                    const containerGf = document.getElementById('gastos-fijos-list');
                    if(containerGf) {
                        containerGf.innerHTML = '';
                        const items = gfData.items || [];
                        if(items.length === 0) {
                            containerGf.innerHTML = `
                                <div class="text-center py-4 px-3 rounded-2xl bg-purple-950/30 border border-purple-900/40">
                                    <p class="text-xs text-purple-300/80 font-bold mb-1">Sin compromisos fijos aún</p>
                                    <p class="text-[11px] text-slate-400 mb-2">Registra arriendo, servicios o cuotas para apartarlos de tu saldo disponible.</p>
                                    <button onclick="abrirModalNuevoGastoFijo()" class="text-xs text-purple-300 font-extrabold underline hover:text-white">Agregar Mi Primer Gasto Fijo</button>
                                </div>
                            `;
                        } else {
                            items.forEach(item => {
                                let icon = 'fa-house';
                                const nom = (item.nombre || '').toLowerCase();
                                if(nom.includes('servicio') || nom.includes('luz') || nom.includes('agua') || nom.includes('gas') || nom.includes('enel') || nom.includes('epm')) icon = 'fa-bolt';
                                else if(nom.includes('internet') || nom.includes('wifi') || nom.includes('celular') || nom.includes('plan') || nom.includes('claro') || nom.includes('tigo') || nom.includes('movistar')) icon = 'fa-wifi';
                                else if(nom.includes('gym') || nom.includes('gimnasio') || nom.includes('smart fit')) icon = 'fa-dumbbell';
                                else if(nom.includes('netflix') || nom.includes('spotify') || nom.includes('sub') || nom.includes('youtube') || nom.includes('apple')) icon = 'fa-star';

                                const el = document.createElement('div');
                                el.className = 'p-3 rounded-2xl bg-purple-950/40 border border-purple-500/15 flex items-center justify-between';
                                el.innerHTML = `
                                    <div class="flex items-center gap-3">
                                        <div class="w-8 h-8 rounded-xl bg-purple-900/50 flex items-center justify-center text-purple-300 text-xs">
                                            <i class="fa-solid ${icon}"></i>
                                        </div>
                                        <div>
                                            <span class="text-xs font-bold text-white block leading-tight">${item.nombre}</span>
                                            <span class="text-[10px] text-purple-300/70">Día habitual: ${item.dia_pago}</span>
                                        </div>
                                    </div>
                                    <div class="flex items-center gap-2">
                                        <span class="text-xs font-black text-purple-200">${formatearCOP(item.monto)}</span>
                                        <button onclick="togglePagadoGastoFijo(${item.id})" class="px-2 py-1 rounded-lg text-[10px] font-bold transition ${item.pagado_este_mes ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-purple-900/40 text-purple-300 border border-purple-700/40'}" title="Marcar como pagado o pendiente">
                                            ${item.pagado_este_mes ? '✓ Cubierto' : 'Apartado'}
                                        </button>
                                        <button onclick="eliminarGastoFijo(${item.id})" class="w-6 h-6 rounded-lg bg-rose-500/15 hover:bg-rose-500/30 text-rose-300 flex items-center justify-center text-[10px] transition" title="Eliminar compromiso">
                                            <i class="fa-solid fa-trash"></i>
                                        </button>
                                    </div>
                                `;
                                containerGf.appendChild(el);
                            });
                        }
                    }
                }

                // Actualizar subtotal apartado de gastos fijos en la Card 1
                const elSubApartadoFijos = document.getElementById('subtotal-apartado-fijos');
                if(elSubApartadoFijos) elSubApartadoFijos.innerText = formatearCOP(totalFijos);

                // 3. Saldo Disponible para Gastar (Card 1 Principal)
                // Se descuentan los gastos fijos del mes del saldo total disponible
                const fijosADescontar = (nominaRecibida || totalFijos > 0) ? totalFijos : 0;
                const saldoDisponibleReal = Math.max(0, balanceNeto - fijosADescontar);
                const elDispHoy = document.getElementById('disponible-hoy');
                if(elDispHoy) {
                    elDispHoy.innerText = formatearCOP(totalFijos > 0 ? saldoDisponibleReal : balanceNeto);
                }

                const badgeDisp = document.getElementById('badge-disponible');
                if(badgeDisp) {
                    if(balanceNeto <= 0) {
                        badgeDisp.className = 'px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-rose-500/20 text-rose-300 border border-rose-500/30';
                        badgeDisp.innerText = 'SIN SALDO';
                    } else if(totalFijos > 0) {
                        badgeDisp.className = 'px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-500/15 text-emerald-300 border border-emerald-500/30';
                        badgeDisp.innerText = 'LIBRE PARA GASTAR';
                    } else {
                        badgeDisp.className = 'px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-purple-500/20 text-purple-300 border border-purple-500/30';
                        badgeDisp.innerText = 'TOTAL DISPONIBLE';
                    }
                }

                // 4. Rendimientos Nu
                const cardRend = document.getElementById('card-rendimientos');
                if(cardRend) {
                    if(data.rendimientos && data.rendimientos.length > 0) {
                        cardRend.style.display = 'flex';
                        const total = data.rendimientos.reduce((acc, curr) => acc + (curr.rendimiento_diario_estimado || 0), 0);
                        const elRend = document.getElementById('rendimiento-diario');
                        if(elRend) elRend.innerText = '+ ' + formatearCOP(total) + ' hoy';
                    } else {
                        cardRend.style.display = 'none';
                    }
                }

                // 5. Transacciones
                const containerTx = document.getElementById('transacciones-list');
                const txs = data.transacciones || [];
                const elConteoTx = document.getElementById('conteo-tx');
                if(elConteoTx) elConteoTx.innerText = txs.length + ' movimientos registrados';
                if(containerTx) {
                    containerTx.innerHTML = '';
                    if(txs.length === 0) {
                        containerTx.innerHTML = '<div class="text-center py-8 text-slate-500 text-xs font-semibold">No hay movimientos registrados aún. ¡Toca (+) para registrar tu primer movimiento!</div>';
                    } else {
                        txs.forEach(t => {
                            const item = document.createElement('div');
                            item.className = 'ios-card p-3 rounded-2xl flex items-center justify-between border border-purple-500/15';
                            item.innerHTML = `
                                <div>
                                    <span class="text-xs font-bold text-white block">${t.comercio}</span>
                                    <div class="flex items-center gap-1.5 mt-0.5">
                                        <span class="text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-900/40">${t.medio}</span>
                                        ${t.es_gasto_hormiga ? '<span class="text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-700/40">Hormiga</span>' : ''}
                                    </div>
                                </div>
                                <span class="text-xs font-black ${t.tipo === 'INGRESO' ? 'text-emerald-400' : t.tipo === 'EGRESO' ? 'text-rose-400' : 'text-blue-400'}">
                                    ${t.tipo === 'INGRESO' ? '+' : '-'} ${formatearCOP(t.monto)}
                                </span>
                            `;
                            containerTx.appendChild(item);
                        });
                    }
                }
            }

            // Sincronización automática cliente-servidor (rehidratación de contenedores efímeros)
            async function sincronizarCuentasConServidor(cuentasGuardadas) {
                try {
                    const payload = cuentasGuardadas.map(c => ({
                        nombre: c.nombre,
                        tipo: c.tipo,
                        saldo_actual: c.saldo_actual,
                        cupo_total: c.cupo_total || 0,
                        tasa_ea: c.tasa_ea || 0
                    }));
                    await fetch('/api/v1/cuentas/sincronizar', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    await fetchDashboard(false);
                } catch(e) {
                    console.error("Error al rehidratar cuentas", e);
                }
            }

            async function fetchDashboard(intentarRehidratar = true) {
                try {
                    const res = await fetch('/api/v1/metricas/dashboard');
                    if(!res.ok) return;
                    const data = await res.json();

                    // Si el servidor reinició y tiene 0 cuentas pero el cliente tiene cuentas guardadas:
                    const cacheRaw = localStorage.getItem('aurea_dashboard_cache');
                    if(intentarRehidratar && data.cuentas.length === 0 && cacheRaw) {
                        try {
                            const cached = JSON.parse(cacheRaw);
                            if(cached.cuentas && cached.cuentas.length > 0) {
                                console.log("Servidor reiniciado. Rehidratando cuentas desde la memoria local...");
                                await sincronizarCuentasConServidor(cached.cuentas);
                                return;
                            }
                        } catch(e) {}
                    }

                    aplicarDatosDashboard(data);
                    localStorage.setItem('aurea_dashboard_cache', JSON.stringify(data));
                } catch(e) {
                    console.warn("Conexión con servidor lenta o en espera, conservando caché local", e);
                }
            }

            function recargarDatos() {
                fetchDashboard();
            }

            // Apple Intelligence por Voz / Texto
            async function enviarAppleIntelligence() {
                const input = document.getElementById('input-ia');
                if(!input) return;
                const texto = input.value.trim();
                if(!texto) return;

                try {
                    const res = await fetch('/api/v1/transacciones/ia-rapida', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ texto: texto })
                    });
                    const data = await res.json();

                    if(data.status === 'requiere_cuenta') {
                        // Preguntar de qué cuenta fue
                        transaccionPendienteAsignar = data;
                        document.getElementById('pregunta-titulo').innerText = '¿De qué cuenta pagaste?';
                        document.getElementById('pregunta-subtitulo').innerText = 'Detectado: $' + Math.round(data.monto).toLocaleString('es-CO') + ' en ' + data.comercio;
                        
                        const container = document.getElementById('opciones-cuentas-pregunta');
                        container.innerHTML = '';
                        cuentasData.forEach(c => {
                            const btn = document.createElement('button');
                            btn.className = 'w-full py-3 px-4 rounded-xl bg-purple-950/60 hover:bg-purple-900/70 text-white font-bold text-xs flex justify-between items-center transition border border-purple-800/40';
                            btn.innerHTML = `
                                <span>${c.nombre}</span>
                                <span class="text-emerald-400">${formatearCOP(c.saldo_actual)}</span>
                            `;
                            btn.onclick = () => confirmarCuentaGasto(c.id);
                            container.appendChild(btn);
                        });
                        document.getElementById('modal-preguntar-cuenta').classList.remove('hidden');
                    } else if(data.status === 'registrado') {
                        if(input) input.value = '';
                        recargarDatos();
                    } else {
                        alert(data.detail || 'No se pudo interpretar el gasto');
                    }
                } catch(e) {
                    alert('Error al conectar con Apple Intelligence');
                }
            }

            async function confirmarCuentaGasto(cuentaId) {
                if(!transaccionPendienteAsignar) return;
                await fetch('/api/v1/transacciones/ia-rapida', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        texto: transaccionPendienteAsignar.comercio + ' ' + transaccionPendienteAsignar.monto,
                        cuenta_id: cuentaId
                    })
                });
                cerrarModalPreguntaCuenta();
                const elIa = document.getElementById('input-ia');
                if(elIa) elIa.value = '';
                recargarDatos();
            }

            function cerrarModalPreguntaCuenta() {
                document.getElementById('modal-preguntar-cuenta').classList.add('hidden');
                transaccionPendienteAsignar = null;
            }

            // Modales de Gasto Manual
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

            // Edición de Cuenta
            function abrirModalEditarCuenta(id, nombre, tipo, saldo) {
                document.getElementById('edit-cuenta-id').value = id;
                document.getElementById('edit-nombre-input').value = nombre;
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
                const nuevoNombre = document.getElementById('edit-nombre-input').value.trim();
                if(isNaN(nuevoSaldo)) return;

                // Actualizar optimísticamente en memoria local
                const c = cuentasData.find(x => x.id == id);
                if(c) {
                    c.saldo_actual = nuevoSaldo;
                    if(nuevoNombre) c.nombre = nuevoNombre;
                    const cacheRaw = localStorage.getItem('aurea_dashboard_cache');
                    if(cacheRaw) {
                        let cache = JSON.parse(cacheRaw);
                        cache.cuentas = cuentasData;
                        localStorage.setItem('aurea_dashboard_cache', JSON.stringify(cache));
                    }
                    aplicarDatosDashboard({ cuentas: cuentasData });
                }

                await fetch('/api/v1/cuentas/' + id, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        saldo_actual: nuevoSaldo,
                        nombre: nuevoNombre || undefined
                    })
                });
                cerrarModalEditarCuenta();
                fetchDashboard();
            }

            async function eliminarCuentaActual() {
                const id = document.getElementById('edit-cuenta-id').value;
                if(!confirm('¿Seguro que deseas eliminar esta cuenta?')) return;
                try {
                    const res = await fetch('/api/v1/cuentas/' + id, { method: 'DELETE' });
                    if(!res.ok) {
                        alert('No se pudo eliminar la cuenta en el servidor.');
                        return;
                    }
                    cuentasData = cuentasData.filter(x => x.id != id);
                    const cacheRaw = localStorage.getItem('aurea_dashboard_cache');
                    if(cacheRaw) {
                        let cache = JSON.parse(cacheRaw);
                        cache.cuentas = cuentasData;
                        localStorage.setItem('aurea_dashboard_cache', JSON.stringify(cache));
                    }
                    cerrarModalEditarCuenta();
                    await fetchDashboard(false);
                } catch(e) {
                    console.error('Error al eliminar cuenta:', e);
                    alert('Error de conexión al eliminar la cuenta');
                }
            }

            // Crear Nueva Cuenta
            function abrirModalNuevaCuenta() {
                document.getElementById('modal-nueva-cuenta').classList.remove('hidden');
                document.getElementById('nueva-cuenta-nombre').focus();
            }
            function cerrarModalNuevaCuenta() {
                document.getElementById('modal-nueva-cuenta').classList.add('hidden');
            }

            async function guardarNuevaCuenta() {
                const nombre = document.getElementById('nueva-cuenta-nombre').value.trim();
                const tipo = document.getElementById('nueva-cuenta-tipo').value;
                const saldo = parseFloat(document.getElementById('nueva-cuenta-saldo').value) || 0;

                if(!nombre) {
                    alert('Ingresa el nombre de la cuenta');
                    return;
                }

                try {
                    const res = await fetch('/api/v1/cuentas', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            nombre: nombre,
                            tipo: tipo,
                            saldo_actual: saldo,
                            tasa_ea: tipo === 'ALTO_RENDIMIENTO' ? 12.5 : 0
                        })
                    });
                    const nueva = await res.json();
                    
                    // Guardar de inmediato en la memoria local del dispositivo
                    cuentasData.push(nueva);
                    const cacheRaw = localStorage.getItem('aurea_dashboard_cache');
                    let cache = cacheRaw ? JSON.parse(cacheRaw) : { cuentas: [] };
                    cache.cuentas = cuentasData;
                    localStorage.setItem('aurea_dashboard_cache', JSON.stringify(cache));
                    aplicarDatosDashboard(cache);
                } catch(e) {
                    console.error("Error al guardar cuenta", e);
                }

                cerrarModalNuevaCuenta();
                document.getElementById('nueva-cuenta-nombre').value = '';
                document.getElementById('nueva-cuenta-saldo').value = '';
                fetchDashboard();
            }

            // Navegación entre vistas independientes (Tabs)
            let tabActual = 'billetera';

            function cambiarTab(tab) {
                tabActual = tab;
                const tabs = ['billetera', 'movimientos', 'cuentas', 'ajustes'];
                const titulos = {
                    'billetera': 'Mi Billetera',
                    'movimientos': 'Movimientos',
                    'cuentas': 'Mis Cuentas',
                    'ajustes': 'Ajustes y Nómina'
                };
                const elTitulo = document.getElementById('header-titulo');
                if (elTitulo && titulos[tab]) {
                    elTitulo.innerText = titulos[tab];
                }

                tabs.forEach(t => {
                    const viewEl = document.getElementById('view-' + t);
                    const btnEl = document.getElementById('tab-btn-' + t);
                    if (t === tab) {
                        if (viewEl) viewEl.classList.remove('hidden');
                        if (btnEl) {
                            btnEl.className = 'flex flex-col items-center text-purple-400 py-1 transition-colors';
                        }
                    } else {
                        if (viewEl) viewEl.classList.add('hidden');
                        if (btnEl) {
                            btnEl.className = 'flex flex-col items-center text-slate-400 hover:text-purple-300 py-1 transition-colors';
                        }
                    }
                });

                window.scrollTo({ top: 0, behavior: 'smooth' });

                if (tab === 'ajustes') {
                    cargarDatosPerfilAjustes();
                }
            }

            // Cargar y configurar datos del perfil y atajos en Ajustes
            async function cargarDatosPerfilAjustes() {
                try {
                    const res = await fetch('/api/v1/metricas/perfil');
                    if (res.ok) {
                        const perfil = await res.json();
                        const elIngreso = document.getElementById('perfil-ingreso');
                        const elDia = document.getElementById('perfil-dia');
                        const elAhorro = document.getElementById('perfil-ahorro');
                        if(elIngreso && perfil.ingreso_mensual_estimado) elIngreso.value = perfil.ingreso_mensual_estimado;
                        if(elDia && perfil.dia_pago_mensual) elDia.value = perfil.dia_pago_mensual;
                        if(elAhorro && perfil.porcentaje_ahorro_meta) elAhorro.value = perfil.porcentaje_ahorro_meta;
                    }
                    const origin = window.location.origin;
                    const elIa = document.getElementById('url-ia-endpoint');
                    const elIaIngreso = document.getElementById('url-ia-ingreso-endpoint');
                    const elWebhook = document.getElementById('url-webhook-endpoint');
                    if(elIa) elIa.value = origin + '/api/v1/transacciones/ia-rapida';
                    if(elIaIngreso) elIaIngreso.value = origin + '/api/v1/transacciones/ia-rapida?tipo=INGRESO';
                    if(elWebhook) elWebhook.value = origin + '/api/v1/webhooks/ios-shortcut';
                } catch(e) {
                    console.error("Error al cargar ajustes de perfil:", e);
                }
            }

            async function guardarPerfilReal() {
                const ingreso = parseFloat(document.getElementById('perfil-ingreso').value);
                const dia = parseInt(document.getElementById('perfil-dia').value);
                const ahorro = parseFloat(document.getElementById('perfil-ahorro').value);

                try {
                    const res = await fetch('/api/v1/metricas/perfil', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            ingreso_mensual_estimado: isNaN(ingreso) ? undefined : ingreso,
                            dia_pago_mensual: isNaN(dia) ? undefined : dia,
                            porcentaje_ahorro_meta: isNaN(ahorro) ? undefined : ahorro
                        })
                    });
                    if (res.ok) {
                        alert('¡Ajustes de nómina guardados correctamente!');
                        recargarDatos();
                    } else {
                        alert('No se pudieron guardar los ajustes.');
                    }
                } catch(e) {
                    alert('Error de conexión al guardar ajustes.');
                }
            }

            async function reiniciarTodoDesdeCero() {
                if(!confirm('¿Estás seguro de que deseas eliminar todas las cuentas, movimientos y compromisos para empezar completamente desde cero? Esta acción no se puede deshacer.')) return;
                try {
                    localStorage.removeItem('aurea_dashboard_cache');
                    const res = await fetch('/api/v1/metricas/reiniciar-todo', { method: 'POST' });
                    const data = await res.json();
                    alert(data.mensaje || 'Base de datos reiniciada a cero.');
                    cambiarTab('billetera');
                    fetchDashboard();
                } catch(e) {
                    alert('Error al reiniciar datos');
                }
            }

            // Gestión de Gastos Fijos
            function abrirModalNuevoGastoFijo() {
                document.getElementById('modal-nuevo-gasto-fijo').classList.remove('hidden');
                document.getElementById('nuevo-fijo-nombre').focus();
            }
            function cerrarModalNuevoGastoFijo() {
                document.getElementById('modal-nuevo-gasto-fijo').classList.add('hidden');
                document.getElementById('nuevo-fijo-nombre').value = '';
                document.getElementById('nuevo-fijo-monto').value = '';
            }
            async function guardarNuevoGastoFijo() {
                const nombre = document.getElementById('nuevo-fijo-nombre').value.trim();
                const monto = parseFloat(document.getElementById('nuevo-fijo-monto').value);
                const diaPago = parseInt(document.getElementById('nuevo-fijo-dia').value) || 5;

                if(!nombre || !monto || isNaN(monto)) {
                    alert('Por favor ingresa un concepto y un monto válido.');
                    return;
                }

                try {
                    const res = await fetch('/api/v1/gastos-fijos', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ nombre: nombre, monto: monto, dia_pago: diaPago })
                    });
                    if(res.ok) {
                        cerrarModalNuevoGastoFijo();
                        fetchDashboard();
                    } else {
                        const err = await res.json();
                        alert(err.detail || 'Error al guardar gasto fijo');
                    }
                } catch(e) {
                    alert('Error de conexión al guardar gasto fijo');
                }
            }
            async function togglePagadoGastoFijo(id) {
                try {
                    await fetch('/api/v1/gastos-fijos/' + id + '/toggle-pagado', { method: 'PATCH' });
                    fetchDashboard();
                } catch(e) {
                    console.error(e);
                }
            }
            async function eliminarGastoFijo(id) {
                if(!confirm('¿Deseas eliminar este gasto fijo?')) return;
                try {
                    await fetch('/api/v1/gastos-fijos/' + id, { method: 'DELETE' });
                    fetchDashboard();
                } catch(e) {
                    console.error(e);
                }
            }

            // Redirecciones de compatibilidad hacia las nuevas vistas
            function abrirModalCuentas() { cambiarTab('cuentas'); }
            function cerrarModalCuentas() {}
            function abrirModalMovimientos() { cambiarTab('movimientos'); }
            function cerrarModalMovimientos() {}
            function abrirModalPerfil() { cambiarTab('ajustes'); }
            function cerrarModalPerfil() {}
            function abrirModalAtajos() { cambiarTab('ajustes'); }
            function cerrarModalAtajos() {}

            function copiarUrlIA() {
                const input = document.getElementById('url-ia-endpoint');
                navigator.clipboard.writeText(input.value).then(() => {
                    alert('¡URL del Atajo de Gasto copiada al portapapeles!');
                }).catch(() => {
                    input.select();
                    document.execCommand('copy');
                    alert('¡URL de Gasto copiada!');
                });
            }

            function copiarUrlIAIngreso() {
                const input = document.getElementById('url-ia-ingreso-endpoint');
                navigator.clipboard.writeText(input.value).then(() => {
                    alert('¡URL del Atajo de Ingreso copiada al portapapeles!');
                }).catch(() => {
                    input.select();
                    document.execCommand('copy');
                    alert('¡URL de Ingreso copiada!');
                });
            }

            function copiarUrlWebhook() {
                const input = document.getElementById('url-webhook-endpoint');
                navigator.clipboard.writeText(input.value).then(() => {
                    alert('¡URL de Apple Pay / SMS copiada al portapapeles!');
                }).catch(() => {
                    input.select();
                    document.execCommand('copy');
                    alert('¡URL copiada!');
                });
            }

            // 1. Carga instantánea a 0 milisegundos desde la memoria del dispositivo
            const cacheInicial = localStorage.getItem('aurea_dashboard_cache');
            if(cacheInicial) {
                try {
                    aplicarDatosDashboard(JSON.parse(cacheInicial));
                } catch(e) {}
            }

            // 2. Carga y verificación en segundo plano con el servidor
            fetchDashboard();
            cargarDatosPerfilAjustes();

            // 3. Auto-recarga desatendida cada 8 segundos con 1 sola petición consolidada ultra-liviana
            setInterval(fetchDashboard, 8000);

            // 4. Auto-recarga automática instantánea cuando el usuario regresa a la app desde Siri o desbloqueo
            document.addEventListener('visibilitychange', () => {
                if (!document.hidden) fetchDashboard();
            });
            window.addEventListener('focus', fetchDashboard);
        </script>
    </body>
    </html>
    """
    return html_content
