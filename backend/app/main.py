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
                background: #090D16;
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
                -webkit-tap-highlight-color: transparent;
                padding-top: var(--sat);
                padding-bottom: calc(var(--sab) + 70px);
            }
            .ios-card {
                background: rgba(19, 25, 42, 0.90);
                backdrop-filter: blur(25px);
                -webkit-backdrop-filter: blur(25px);
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            .glow-primary {
                box-shadow: 0 4px 20px -2px rgba(245, 158, 11, 0.15);
            }
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
                        <span id="badge-db" class="text-[9px] font-bold px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">...</span>
                    </div>
                    <h1 class="text-2xl font-black text-white tracking-tight">Mi Billetera</h1>
                </div>
            </div>

            <!-- Apple Intelligence: Entrada Inteligente por Voz o Texto Rápido -->
            <div class="ios-card rounded-2xl p-2 mb-4 flex items-center gap-2 border border-amber-500/40 bg-gradient-to-r from-slate-900 to-amber-950/20">
                <div class="w-8 h-8 rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-400 text-sm">
                    <i class="fa-solid fa-wand-magic-sparkles"></i>
                </div>
                <input type="text" id="input-ia" placeholder="Dicta o escribe: '15 mil de taxi en efectivo'..." class="bg-transparent flex-1 text-xs text-white placeholder-slate-500 outline-none" onkeydown="if(event.key==='Enter') enviarAppleIntelligence()">
                <button onclick="enviarAppleIntelligence()" class="px-3 py-1.5 rounded-xl bg-amber-500 active:scale-90 text-slate-950 font-extrabold text-xs flex items-center gap-1 transition">
                    <span>Registrar</span>
                    <i class="fa-solid fa-arrow-up text-[10px]"></i>
                </button>
            </div>

            <!-- Card 1: Patrimonio Líquido / Balance Neto Real -->
            <div class="ios-card rounded-3xl p-5 mb-4 glow-primary">
                <div class="flex justify-between items-start">
                    <div>
                        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Patrimonio Líquido Real</span>
                        <div class="flex items-center gap-2.5 mt-1">
                            <div class="text-3xl font-black text-white tracking-tight" id="balance-neto-total">$ 0 COP</div>
                            <!-- Modo Privacidad 👁️ al lado del saldo -->
                            <button onclick="toggleModoPrivacidad()" id="btn-privacidad" class="w-7 h-7 rounded-lg bg-slate-800/80 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white active:scale-90 transition border border-slate-700/50" title="Ocultar o ver saldo">
                                <i class="fa-solid fa-eye text-xs" id="icono-ojo"></i>
                            </button>
                        </div>
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
                        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Disponible para gastar hoy</span>
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

            <!-- Card 3: Rendimientos Cuentas de Alto Rendimiento (Nu / Lulo) -->
            <div id="card-rendimientos" class="ios-card rounded-2xl p-4 mb-4 border border-violet-500/30 bg-violet-950/20 flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-violet-600/30 flex items-center justify-center text-violet-400 text-base">
                        <i class="fa-solid fa-arrow-trend-up"></i>
                    </div>
                    <div>
                        <span class="text-[10px] font-bold uppercase tracking-wider text-violet-300">Rendimientos Diarios Nu</span>
                        <div class="text-sm font-black text-white" id="rendimiento-diario">+ $ 0 COP hoy</div>
                    </div>
                </div>
                <span class="text-[10px] text-violet-300 font-bold bg-violet-900/60 px-2.5 py-1 rounded-lg">Automático</span>
            </div>

            <!-- Card 4: Todas Mis Cuentas (Con saldo editable y botón de agregar) -->
            <div class="mb-5">
                <div class="flex justify-between items-center mb-3 px-1">
                    <div>
                        <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Mis Cuentas e Instrumentos</span>
                        <span class="text-[10px] text-slate-500 block">Toca el lápiz para registrar tu saldo actual</span>
                    </div>
                    <button onclick="abrirModalNuevaCuenta()" class="px-3 py-1.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 text-xs font-bold border border-amber-500/40 flex items-center gap-1.5 active:scale-95 transition">
                        <i class="fa-solid fa-plus text-[10px]"></i>
                        <span>Agregar Cuenta</span>
                    </button>
                </div>
                <div id="cuentas-list" class="space-y-2.5">
                    <!-- Dinámico -->
                </div>
            </div>

            <!-- Card 5: Movimientos Recientes -->
            <div class="mb-6">
                <div class="flex justify-between items-center mb-3 px-1">
                    <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Movimientos Registrados</span>
                    <span class="text-[11px] text-slate-500" id="conteo-tx">0 movimientos</span>
                </div>
                <div id="transacciones-list" class="space-y-2">
                    <!-- Dinámico -->
                </div>
            </div>

        </div>

        <!-- Barra de Navegación Inferior Flotante con Botón Central (+) -->
        <div class="fixed bottom-0 left-0 right-0 z-40 bg-slate-900/90 backdrop-blur-xl border-t border-slate-800/80 px-8 py-2.5 flex justify-between items-center max-w-lg mx-auto">
            <button onclick="window.scrollTo({top: 0, behavior: 'smooth'})" class="flex flex-col items-center text-amber-400">
                <i class="fa-solid fa-wallet text-lg"></i>
                <span class="text-[10px] font-bold mt-1">Billetera</span>
            </button>

            <!-- Botón Central Destacado (+) para Registrar Gasto Rápido -->
            <button onclick="abrirModalGasto()" class="w-12 h-12 rounded-full bg-gradient-to-tr from-amber-500 to-amber-400 -mt-6 shadow-lg shadow-amber-500/30 flex items-center justify-center text-slate-950 text-xl font-black active:scale-90 transition border-4 border-[#090D16]">
                <i class="fa-solid fa-plus"></i>
            </button>

            <button onclick="abrirModalPerfil()" class="flex flex-col items-center text-slate-400 hover:text-white">
                <i class="fa-solid fa-gear text-lg"></i>
                <span class="text-[10px] font-bold mt-1">Ajustes</span>
            </button>
        </div>

        <!-- Modal 1: ¿De qué cuenta fue la compra? (Detección y Confirmación Inteligente) -->
        <div id="modal-preguntar-cuenta" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-slate-900 border border-slate-700">
                <div class="text-center mb-4">
                    <div class="w-12 h-12 rounded-2xl bg-amber-500/20 text-amber-400 text-xl flex items-center justify-center mx-auto mb-2">
                        <i class="fa-solid fa-question"></i>
                    </div>
                    <h3 class="text-lg font-black text-white" id="pregunta-titulo">¿De qué cuenta fue el pago?</h3>
                    <p class="text-xs text-slate-300 mt-1" id="pregunta-subtitulo">Selecciona la cuenta para descontar el saldo:</p>
                </div>
                <div id="opciones-cuentas-pregunta" class="space-y-2 mb-4">
                    <!-- Dinámico -->
                </div>
                <button onclick="cerrarModalPreguntaCuenta()" class="w-full py-2.5 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold">Cancelar</button>
            </div>
        </div>

        <!-- Modal 2: Registrar Gasto / Ingreso Manual -->
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

        <!-- Modal 3: Editar Saldo Real de una Cuenta -->
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
                        <label class="text-[10px] font-bold uppercase text-slate-400 block mb-1">Nombre de la Cuenta</label>
                        <input type="text" id="edit-nombre-input" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-amber-400 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-slate-400 block mb-1">Saldo Actual Real en COP</label>
                        <input type="number" id="edit-saldo" placeholder="0" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-white font-bold text-lg focus:border-amber-400 outline-none">
                    </div>
                    <div class="pt-2 flex gap-2">
                        <button onclick="eliminarCuentaActual()" class="py-2.5 px-3 rounded-xl bg-rose-500/20 text-rose-300 text-xs font-bold border border-rose-500/30">Eliminar</button>
                        <button onclick="guardarEdicionSaldo()" class="flex-1 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-black">Actualizar Saldo</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal 4: Agregar Nueva Cuenta Personalizada -->
        <div id="modal-nueva-cuenta" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-slate-900 border border-slate-700">
                <div class="flex justify-between items-center mb-3">
                    <h3 class="text-base font-extrabold text-white">Agregar Nueva Cuenta</h3>
                    <button onclick="cerrarModalNuevaCuenta()" class="text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="space-y-3">
                    <div>
                        <label class="text-[10px] font-bold uppercase text-slate-400 block mb-1">Nombre de la Cuenta</label>
                        <input type="text" id="nueva-cuenta-nombre" placeholder="Ej: Nequi, Daviplata, Bancolombia, Billetera" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white text-sm focus:border-amber-400 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-slate-400 block mb-1">Tipo de Instrumento</label>
                        <select id="nueva-cuenta-tipo" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white text-sm focus:border-amber-400 outline-none">
                            <option value="DEBITO">Cuenta Débito / Ahorros (Bancolombia, Nequi)</option>
                            <option value="EFECTIVO">Efectivo Físico (Billetera)</option>
                            <option value="CREDITO">Tarjeta de Crédito (Visa, Mastercard)</option>
                            <option value="ALTO_RENDIMIENTO">Cuenta Alto Rendimiento (Nu, Lulo, Pibank)</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-slate-400 block mb-1">Saldo Inicial en COP</label>
                        <input type="number" id="nueva-cuenta-saldo" placeholder="0" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-amber-400 outline-none">
                    </div>
                    <div class="pt-2 flex gap-2">
                        <button onclick="cerrarModalNuevaCuenta()" class="w-1/2 py-2.5 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold">Cancelar</button>
                        <button onclick="guardarNuevaCuenta()" class="w-1/2 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-black">Crear Cuenta</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal 5: Configuración de Nómina Real ⚙️ -->
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

                    <div class="pt-4 mt-2 border-t border-slate-800 text-center">
                        <button onclick="reiniciarTodoDesdeCero()" class="w-full py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-bold transition flex items-center justify-center gap-2">
                            <i class="fa-solid fa-trash-can"></i>
                            <span>Borrar todo y empezar desde cero</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal 6: Guía y Configuración de Atajos de iOS (Siri & Apple Intelligence) ⚡ -->
        <div id="modal-atajos" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-slate-900 border border-slate-700 max-h-[90vh] overflow-y-auto">
                <div class="flex justify-between items-center mb-4">
                    <div class="flex items-center gap-2">
                        <div class="w-8 h-8 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center text-sm">
                            <i class="fa-solid fa-bolt"></i>
                        </div>
                        <h3 class="text-base font-extrabold text-white">Atajos de iOS & Siri</h3>
                    </div>
                    <button onclick="cerrarModalAtajos()" class="text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
                </div>

                <div class="space-y-4 text-xs">
                    <!-- Guía 1: Siri Registrar Gasto -->
                    <div class="p-3.5 rounded-2xl bg-slate-950 border border-amber-500/30">
                        <div class="flex items-center gap-2 text-amber-400 font-black text-xs mb-1">
                            <i class="fa-solid fa-arrow-trend-down"></i>
                            <span>1. Atajo: "Registrar Gasto" (Voz o Siri)</span>
                        </div>
                        <p class="text-slate-300 leading-relaxed text-[11px] mb-2">
                            Di: <em>"Oye Siri, registrar gasto"</em>. Ejemplo: <em>"15 mil de taxi en efectivo"</em> o <em>"almuerzo 20 mil"</em>.
                        </p>
                        <div class="bg-slate-900 p-2.5 rounded-xl border border-slate-800 space-y-1 text-[11px] text-slate-300 mb-2">
                            <div>• Acción 1: <strong>Solicitar [Texto]</strong> con <em>"¿Qué gastaste?"</em></div>
                            <div>• Acción 2: <strong>Obtener contenido de URL</strong> (POST JSON con campo <code>texto</code>)</div>
                            <div>• Acción 3: <strong>Mostrar notificación</strong> con la respuesta</div>
                        </div>
                        <div class="flex items-center gap-2">
                            <input type="text" id="url-ia-endpoint" readonly class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-[10px] text-amber-300 font-mono select-all">
                            <button onclick="copiarUrlIA()" class="px-3 py-1.5 rounded-lg bg-amber-500 text-slate-950 font-black text-[10px] shrink-0 active:scale-95 transition">
                                Copiar
                            </button>
                        </div>
                    </div>

                    <!-- Guía 2: Siri Registrar Ingreso -->
                    <div class="p-3.5 rounded-2xl bg-slate-950 border border-emerald-500/30">
                        <div class="flex items-center gap-2 text-emerald-400 font-black text-xs mb-1">
                            <i class="fa-solid fa-arrow-trend-up"></i>
                            <span>2. Atajo: "Registrar Ingreso" (Voz o Siri)</span>
                        </div>
                        <p class="text-slate-300 leading-relaxed text-[11px] mb-2">
                            Di: <em>"Oye Siri, registrar ingreso"</em>. Ejemplo: <em>"500 mil en Bancolombia"</em> o <em>"500"</em>.
                        </p>
                        <div class="bg-slate-900 p-2.5 rounded-xl border border-slate-800 space-y-1 text-[11px] text-slate-300 mb-2">
                            <div>• Acción 1: <strong>Solicitar [Texto]</strong> con <em>"¿Cuánto ingresó?"</em></div>
                            <div>• Acción 2: <strong>Obtener contenido de URL</strong> con la URL de ingreso</div>
                            <div>• Acción 3: <strong>Mostrar notificación</strong> con la respuesta</div>
                        </div>
                        <div class="flex items-center gap-2">
                            <input type="text" id="url-ia-ingreso-endpoint" readonly class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-[10px] text-emerald-300 font-mono select-all">
                            <button onclick="copiarUrlIAIngreso()" class="px-3 py-1.5 rounded-lg bg-emerald-500 text-slate-950 font-black text-[10px] shrink-0 active:scale-95 transition">
                                Copiar
                            </button>
                        </div>
                    </div>

                    <!-- Guía 3: Apple Pay Automático -->
                    <div class="p-3.5 rounded-2xl bg-slate-950 border border-slate-800">
                        <div class="flex items-center gap-2 text-blue-400 font-black text-xs mb-1">
                            <i class="fa-brands fa-apple"></i>
                            <span>3. Apple Pay Automático</span>
                        </div>
                        <p class="text-slate-300 leading-relaxed text-[11px] mb-2">
                            En la app <strong>Atajos</strong> -> <strong>Automatización</strong> -> <strong>"Transacción de Wallet"</strong>. Envía el webhook al pagar.
                        </p>
                        <div class="flex items-center gap-2">
                            <input type="text" id="url-webhook-endpoint" readonly class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-[10px] text-blue-300 font-mono select-all">
                            <button onclick="copiarUrlWebhook()" class="px-3 py-1.5 rounded-lg bg-blue-500 text-white font-bold text-[10px] shrink-0 active:scale-95 transition">
                                Copiar
                            </button>
                        </div>
                    </div>
                </div>

                <div class="mt-4 pt-3 border-t border-slate-800 text-center">
                    <button onclick="cerrarModalAtajos()" class="w-full py-2.5 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold">Entendido</button>
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
                        badgeDb.className = 'text-[9px] font-bold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30';
                        badgeDb.innerText = '📱 LOCAL';
                        badgeDb.title = 'Guardado local en tu iPhone con auto-rehidratación';
                    }
                }

                // 1. Semáforo
                if(data.semaforo) {
                    const s = data.semaforo;
                    document.getElementById('disponible-hoy').innerText = formatearCOP(s.disponible_hoy_restante);
                    document.getElementById('mensaje-guia').innerText = s.mensaje_guia || '';
                    document.getElementById('dias-restantes').innerText = (s.dias_restantes || 0) + ' días';
                    document.getElementById('limite-diario').innerText = formatearCOP(s.limite_gasto_diario_sugerido || 0);

                    const badge = document.getElementById('badge-color');
                    badge.innerText = s.color || 'VERDE';
                    const card = document.getElementById('semaforo-card');
                    if(s.color === 'VERDE') {
                        badge.className = 'px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/40';
                        card.className = 'ios-card rounded-3xl p-5 mb-4 relative overflow-hidden transition-all border-emerald-500/30';
                    } else if(s.color === 'AMARILLO') {
                        badge.className = 'px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider bg-amber-500/20 text-amber-300 border border-amber-500/40';
                        card.className = 'ios-card rounded-3xl p-5 mb-4 relative overflow-hidden transition-all border-amber-500/30';
                    } else {
                        badge.className = 'px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider bg-rose-500/20 text-rose-300 border border-rose-500/40';
                        card.className = 'ios-card rounded-3xl p-5 mb-4 relative overflow-hidden transition-all border-rose-500/30';
                    }
                }

                // 2. Rendimientos
                const cardRend = document.getElementById('card-rendimientos');
                if(data.rendimientos && data.rendimientos.length > 0) {
                    cardRend.style.display = 'flex';
                    const total = data.rendimientos.reduce((acc, curr) => acc + (curr.rendimiento_diario_estimado || 0), 0);
                    document.getElementById('rendimiento-diario').innerText = '+ ' + formatearCOP(total) + ' hoy';
                } else {
                    cardRend.style.display = 'none';
                }

                // 3. Cuentas
                cuentasData = data.cuentas || [];
                let totalCuentas = 0;
                let totalDeuda = 0;
                const containerCuentas = document.getElementById('cuentas-list');
                const selectCuenta = document.getElementById('select-cuenta');
                containerCuentas.innerHTML = '';
                selectCuenta.innerHTML = '';

                if(cuentasData.length === 0) {
                    containerCuentas.innerHTML = `
                        <div class="ios-card p-6 rounded-3xl text-center border border-amber-500/20 bg-gradient-to-b from-slate-900 to-amber-950/10">
                            <div class="w-12 h-12 rounded-2xl bg-amber-500/20 text-amber-400 flex items-center justify-center mx-auto mb-3 text-lg">
                                <i class="fa-solid fa-wallet"></i>
                            </div>
                            <h4 class="text-sm font-black text-white mb-1">¡Todo listo para empezar de cero!</h4>
                            <p class="text-xs text-slate-400 mb-4 leading-relaxed">No tienes cuentas configuradas aún. Registra tu cuenta bancaria, billetera o efectivo con tu saldo real.</p>
                            <button onclick="abrirModalNuevaCuenta()" class="w-full py-3 px-4 rounded-xl bg-amber-500 active:scale-95 text-slate-950 font-black text-xs flex items-center justify-center gap-2 transition shadow-lg shadow-amber-500/20">
                                <i class="fa-solid fa-plus text-sm"></i>
                                <span>Agregar Mi Primera Cuenta</span>
                            </button>
                        </div>
                    `;
                    const opt = document.createElement('option');
                    opt.value = "";
                    opt.innerText = "Primero crea una cuenta";
                    selectCuenta.appendChild(opt);
                } else {
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
                        containerCuentas.appendChild(item);

                        const opt = document.createElement('option');
                        opt.value = c.id;
                        opt.innerText = c.nombre;
                        selectCuenta.appendChild(opt);
                    });
                }

                document.getElementById('subtotal-cuentas').innerText = formatearCOP(totalCuentas);
                document.getElementById('subtotal-deuda').innerText = formatearCOP(totalDeuda);
                const balanceNeto = totalCuentas - totalDeuda;
                document.getElementById('balance-neto-total').innerText = formatearCOP(balanceNeto);

                // 4. Transacciones
                const containerTx = document.getElementById('transacciones-list');
                const txs = data.transacciones || [];
                document.getElementById('conteo-tx').innerText = txs.length + ' movimientos';
                containerTx.innerHTML = '';

                if(txs.length === 0) {
                    containerTx.innerHTML = '<div class="text-center py-6 text-slate-500 text-xs font-semibold">No hay movimientos registrados. ¡Toca (+) o usa Apple Intelligence para registrar tu primer gasto!</div>';
                } else {
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
                        containerTx.appendChild(item);
                    });
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
                            btn.className = 'w-full py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs flex justify-between items-center transition border border-slate-700';
                            btn.innerHTML = `
                                <span>${c.nombre}</span>
                                <span class="text-emerald-400">${formatearCOP(c.saldo_actual)}</span>
                            `;
                            btn.onclick = () => confirmarCuentaGasto(c.id);
                            container.appendChild(btn);
                        });
                        document.getElementById('modal-preguntar-cuenta').classList.remove('hidden');
                    } else if(data.status === 'registrado') {
                        input.value = '';
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
                document.getElementById('input-ia').value = '';
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

            // Ajustes Perfil
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

            async function reiniciarTodoDesdeCero() {
                if(!confirm('¿Estás seguro de que deseas eliminar todas las cuentas, movimientos y empezar completamente desde cero? Esta acción no se puede deshacer.')) return;
                try {
                    localStorage.removeItem('aurea_dashboard_cache');
                    const res = await fetch('/api/v1/metricas/reiniciar-todo', { method: 'POST' });
                    const data = await res.json();
                    alert(data.mensaje || 'Base de datos reiniciada a cero.');
                    cerrarModalPerfil();
                    fetchDashboard();
                } catch(e) {
                    alert('Error al reiniciar datos');
                }
            }

            // Modal Atajos de iOS
            function abrirModalAtajos() {
                const origin = window.location.origin;
                document.getElementById('url-ia-endpoint').value = origin + '/api/v1/transacciones/ia-rapida';
                document.getElementById('url-ia-ingreso-endpoint').value = origin + '/api/v1/transacciones/ia-rapida?tipo=INGRESO';
                document.getElementById('url-webhook-endpoint').value = origin + '/api/v1/webhooks/ios-shortcut';
                document.getElementById('modal-atajos').classList.remove('hidden');
            }
            function cerrarModalAtajos() {
                document.getElementById('modal-atajos').classList.add('hidden');
            }

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
