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
    try:
        import backend.app.models
        Base.metadata.create_all(bind=engine)
        seed_data()
    except Exception as e:
        import logging
        logging.error(f"Advertencia: no se pudo inicializar la base de datos en lifespan: {e}")
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
    Interfaz Web Nativa para iPhone (PWA Standalone) en Pesos Colombianos ($).
    Diseño Apple Human Interface Guidelines (HIG) con modo oscuro puro (Obsidian / System Dark),
    autenticación con PIN de 4 dígitos y Face ID estilo Bancolombia, múltiples tarjetas de crédito
    estilo Apple Wallet con cupo total y disponible, detalle y edición de movimientos, y Apple Pay.
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
        <meta name="theme-color" content="#000000">
        <title>AUREA • Finanzas Personales</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {
                --sat: env(safe-area-inset-top, 20px);
                --sab: env(safe-area-inset-bottom, 24px);
                --system-bg: #000000;
                --card-bg: #1C1C1E;
                --card-secondary: #2C2C2E;
                --separator: rgba(255, 255, 255, 0.08);
                --apple-green: #30D158;
                --apple-blue: #0A84FF;
                --apple-red: #FF453A;
                --apple-orange: #FF9F0A;
                --apple-gray: #8E8E93;
            }
            body {
                background: #000000;
                color: #FFFFFF;
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", system-ui, sans-serif;
                -webkit-font-smoothing: antialiased;
                -webkit-tap-highlight-color: transparent;
                padding-top: var(--sat);
                padding-bottom: calc(var(--sab) + 72px);
                user-select: none;
            }
            .ios-card {
                background: #1C1C1E;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            .ios-card-glass {
                background: rgba(28, 28, 30, 0.85);
                backdrop-filter: blur(25px);
                -webkit-backdrop-filter: blur(25px);
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            .apple-wallet-card {
                background: linear-gradient(135deg, #1C1C1E 0%, #2A2A2E 50%, #171719 100%);
                border: 1px solid rgba(255, 255, 255, 0.12);
                box-shadow: 0 12px 30px -8px rgba(0, 0, 0, 0.65);
            }
            .tab-view {
                animation: fadeIn 0.18s cubic-bezier(0.16, 1, 0.3, 1);
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(6px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .keypad-btn {
                transition: transform 0.1s ease, background-color 0.1s ease;
            }
            .keypad-btn:active {
                transform: scale(0.92);
                background-color: rgba(255, 255, 255, 0.22);
            }
            ::-webkit-scrollbar { display: none; }
        </style>
    </head>
    <body class="selection:bg-blue-600 selection:text-white">

        <!-- ========================================== -->
        <!-- PANTALLA DE SEGURIDAD / LOGIN (Bancolombia + Face ID) -->
        <!-- ========================================== -->
        <div id="pantalla-auth" class="fixed inset-0 z-50 bg-black flex flex-col justify-between items-center px-6 py-12 transition-opacity duration-300">
            <!-- Header de Seguridad -->
            <div class="text-center pt-8">
                <div class="w-16 h-16 rounded-3xl bg-[#1C1C1E] border border-white/10 flex items-center justify-center mx-auto mb-4 shadow-xl">
                    <i class="fa-solid fa-face-smile text-3xl text-blue-400" id="auth-icono-biometria"></i>
                </div>
                <h2 class="text-2xl font-black tracking-tight text-white" id="auth-saludo">AUREA</h2>
                <p class="text-xs text-[#8E8E93] mt-1" id="auth-instruccion">Ingresa tu clave de 4 dígitos</p>
            </div>

            <!-- Formulario de Registro Inicial (si no hay usuario aún) -->
            <div id="form-registro-inicial" class="w-full max-w-xs space-y-3 hidden">
                <div>
                    <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Tu Nombre o Alias</label>
                    <input type="text" id="reg-nombre" placeholder="Ej: Jorge" class="w-full bg-[#1C1C1E] border border-white/10 rounded-2xl px-4 py-3 text-white font-bold text-sm outline-none focus:border-blue-500">
                </div>
                <div>
                    <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Crea tu PIN de 4 dígitos</label>
                    <input type="password" id="reg-pin" maxlength="4" placeholder="••••" class="w-full bg-[#1C1C1E] border border-white/10 rounded-2xl px-4 py-3 text-white font-black text-center text-lg tracking-widest outline-none focus:border-blue-500">
                </div>
                <button onclick="guardarRegistroInicial()" class="w-full py-3.5 rounded-2xl bg-[#0A84FF] text-white font-black text-sm active:scale-95 transition shadow-lg shadow-blue-500/20">
                    Crear PIN y Continuar
                </button>
            </div>

            <!-- Teclado Numérico y Puntos PIN Estilo Bancolombia / iOS -->
            <div id="contenedor-teclado-pin" class="w-full max-w-xs flex flex-col items-center">
                <!-- 4 Puntos Indicadores de PIN -->
                <div class="flex items-center gap-5 mb-8">
                    <div id="pin-dot-1" class="w-3.5 h-3.5 rounded-full border border-white/30 transition-all duration-150"></div>
                    <div id="pin-dot-2" class="w-3.5 h-3.5 rounded-full border border-white/30 transition-all duration-150"></div>
                    <div id="pin-dot-3" class="w-3.5 h-3.5 rounded-full border border-white/30 transition-all duration-150"></div>
                    <div id="pin-dot-4" class="w-3.5 h-3.5 rounded-full border border-white/30 transition-all duration-150"></div>
                </div>

                <!-- Teclado 3x4 iOS -->
                <div class="grid grid-cols-3 gap-5 w-full">
                    <button onclick="teclearPin('1')" class="keypad-btn h-16 rounded-full bg-[#1C1C1E] text-2xl font-normal text-white flex items-center justify-center border border-white/5">1</button>
                    <button onclick="teclearPin('2')" class="keypad-btn h-16 rounded-full bg-[#1C1C1E] text-2xl font-normal text-white flex items-center justify-center border border-white/5">2</button>
                    <button onclick="teclearPin('3')" class="keypad-btn h-16 rounded-full bg-[#1C1C1E] text-2xl font-normal text-white flex items-center justify-center border border-white/5">3</button>

                    <button onclick="teclearPin('4')" class="keypad-btn h-16 rounded-full bg-[#1C1C1E] text-2xl font-normal text-white flex items-center justify-center border border-white/5">4</button>
                    <button onclick="teclearPin('5')" class="keypad-btn h-16 rounded-full bg-[#1C1C1E] text-2xl font-normal text-white flex items-center justify-center border border-white/5">5</button>
                    <button onclick="teclearPin('6')" class="keypad-btn h-16 rounded-full bg-[#1C1C1E] text-2xl font-normal text-white flex items-center justify-center border border-white/5">6</button>

                    <button onclick="teclearPin('7')" class="keypad-btn h-16 rounded-full bg-[#1C1C1E] text-2xl font-normal text-white flex items-center justify-center border border-white/5">7</button>
                    <button onclick="teclearPin('8')" class="keypad-btn h-16 rounded-full bg-[#1C1C1E] text-2xl font-normal text-white flex items-center justify-center border border-white/5">8</button>
                    <button onclick="teclearPin('9')" class="keypad-btn h-16 rounded-full bg-[#1C1C1E] text-2xl font-normal text-white flex items-center justify-center border border-white/5">9</button>

                    <button onclick="activarFaceId()" id="btn-teclado-faceid" class="keypad-btn h-16 rounded-full text-blue-400 flex items-center justify-center text-xl" title="Ingresar con Face ID">
                        <i class="fa-solid fa-face-smile"></i>
                    </button>
                    <button onclick="teclearPin('0')" class="keypad-btn h-16 rounded-full bg-[#1C1C1E] text-2xl font-normal text-white flex items-center justify-center border border-white/5">0</button>
                    <button onclick="borrarDigitoPin()" class="keypad-btn h-16 rounded-full text-white/80 flex items-center justify-center text-lg" title="Borrar">
                        <i class="fa-solid fa-delete-left"></i>
                    </button>
                </div>
            </div>

            <!-- Footer Seguro -->
            <div class="text-[11px] text-[#8E8E93] flex items-center gap-1.5 pb-4">
                <i class="fa-solid fa-shield-halved text-blue-400 text-xs"></i>
                <span>Protección privada en tu iPhone</span>
            </div>
        </div>

        <!-- ========================================== -->
        <!-- APP PRINCIPAL NATIVA iOS -->
        <!-- ========================================== -->
        <div class="w-full max-w-lg mx-auto px-4 sm:px-6 pt-2">

            <!-- Top Header Estilo Apple HIG -->
            <div class="flex justify-between items-center py-2 mb-3">
                <div class="flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-[#0A84FF]"></span>
                    <span class="text-xs font-bold tracking-widest text-[#8E8E93] uppercase">AUREA</span>
                    <span id="badge-db" class="text-[9px] font-bold px-2 py-0.5 rounded-full bg-[#1C1C1E] text-slate-300 border border-white/10">...</span>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="bloquearApp()" class="w-8 h-8 rounded-full bg-[#1C1C1E] border border-white/10 flex items-center justify-center text-white/80 hover:text-white active:scale-90 transition text-xs" title="Bloquear App">
                        <i class="fa-solid fa-lock"></i>
                    </button>
                </div>
            </div>

            <h1 class="text-3xl font-extrabold text-white tracking-tight mb-4" id="header-titulo">Billetera</h1>

            <!-- ========================================== -->
            <!-- VISTA 1: BILLETERA (Panel Principal) -->
            <!-- ========================================== -->
            <div id="view-billetera" class="tab-view pb-24">

                <!-- Apartado 1: Saldo Disponible para Gastar con Saldo Total Integrado -->
                <div class="ios-card rounded-3xl p-5 mb-4 border border-white/10 bg-[#1C1C1E]">
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="text-[11px] font-bold text-[#8E8E93] uppercase tracking-wider block">Saldo disponible para gastar</span>
                            <div class="flex items-center gap-2.5 mt-1.5">
                                <div class="text-4xl font-extrabold text-white tracking-tight" id="disponible-hoy">$ 0</div>
                                <button onclick="toggleModoPrivacidad()" id="btn-privacidad" class="w-8 h-8 rounded-xl bg-[#2C2C2E] hover:bg-[#3A3A3C] flex items-center justify-center text-slate-300 hover:text-white active:scale-90 transition" title="Ocultar o ver saldo">
                                    <i class="fa-solid fa-eye text-xs" id="icono-ojo"></i>
                                </button>
                            </div>
                        </div>
                        <span id="badge-disponible" class="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#30D158]/15 text-[#30D158] border border-[#30D158]/30">
                            LIBRE PARA GASTAR
                        </span>
                    </div>

                    <!-- Apartado integrado: Saldo Total y Gastos Fijos Pendientes -->
                    <div class="mt-5 pt-4 border-t border-white/10 grid grid-cols-2 gap-3">
                        <div class="p-3.5 rounded-2xl bg-[#000000]/60 border border-white/5 flex flex-col justify-between">
                            <div>
                                <span class="text-[10px] font-bold text-[#8E8E93] uppercase tracking-wider block">Saldo Total en Cuentas</span>
                                <div class="text-lg font-bold text-white mt-0.5" id="balance-neto-total">$ 0</div>
                            </div>
                            <button onclick="cambiarTab('cuentas')" class="text-[10px] text-blue-400 font-semibold hover:text-white flex items-center gap-1 mt-2.5 transition">
                                <span>Ver Cuentas</span>
                                <i class="fa-solid fa-chevron-right text-[8px]"></i>
                            </button>
                        </div>
                        <div class="p-3.5 rounded-2xl bg-[#000000]/60 border border-white/5 flex flex-col justify-between">
                            <div>
                                <span class="text-[10px] font-bold text-[#8E8E93] uppercase tracking-wider block">Gastos Fijos</span>
                                <div class="text-lg font-bold text-slate-200 mt-0.5" id="subtotal-apartado-fijos">$ 0</div>
                            </div>
                            <span class="text-[9px] text-[#8E8E93] font-medium block mt-2.5" id="estado-fijos-apartados">
                                Apartados de nómina
                            </span>
                        </div>
                    </div>
                </div>

                <!-- Apartado 2: Gastos Fijos del Mes -->
                <div class="ios-card rounded-3xl p-5 mb-4 border border-white/10 bg-[#1C1C1E]">
                    <div class="flex justify-between items-start mb-2">
                        <div>
                            <span class="text-[11px] font-bold text-[#8E8E93] uppercase tracking-wider">Gastos Fijos del Mes</span>
                            <div class="text-2xl font-extrabold text-white mt-0.5" id="total-gastos-fijos">$ 0</div>
                        </div>
                        <span id="badge-estado-gastos-fijos" class="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-white/10 text-white border border-white/15">
                            🔒 COMPROMISOS
                        </span>
                    </div>
                    <p class="text-[11px] text-[#8E8E93] leading-relaxed mb-3.5">
                        Los gastos ya cubiertos no restan de tu disponible. Solo los pendientes se apartan.
                    </p>

                    <div class="flex justify-between items-center mb-3 pt-2.5 border-t border-white/10">
                        <span class="text-[11px] font-bold uppercase tracking-wider text-[#8E8E93]">Tus Compromisos</span>
                        <button onclick="abrirModalNuevoGastoFijo()" class="px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/15 text-white text-[11px] font-bold border border-white/10 flex items-center gap-1.5 active:scale-95 transition">
                            <i class="fa-solid fa-plus text-[9px]"></i>
                            <span>Agregar Fijo</span>
                        </button>
                    </div>

                    <div id="gastos-fijos-list" class="space-y-2">
                        <!-- Dinámico -->
                    </div>
                </div>

                <!-- Apartado 3: Múltiples Tarjetas de Crédito (Estilo Apple Wallet) -->
                <div class="ios-card rounded-3xl p-5 mb-4 border border-white/10 bg-[#1C1C1E]">
                    <div class="flex justify-between items-start mb-2">
                        <div>
                            <span class="text-[11px] font-bold text-[#8E8E93] uppercase tracking-wider">Tarjetas de Crédito</span>
                            <div class="flex items-baseline gap-2 mt-0.5">
                                <div class="text-2xl font-extrabold text-rose-400" id="total-deuda-tc">$ 0</div>
                                <span class="text-xs text-[#8E8E93] font-semibold">deuda</span>
                            </div>
                        </div>
                        <div class="text-right">
                            <span class="text-[10px] font-bold text-[#8E8E93] uppercase tracking-wider block">Cupo Disponible Total</span>
                            <div class="text-base font-extrabold text-emerald-400" id="total-cupo-disponible-tc">$ 0</div>
                        </div>
                    </div>

                    <p class="text-[11px] text-[#8E8E93] leading-relaxed mb-3.5">
                        Tus compras a crédito utilizan el cupo de tus tarjetas y no se descuentan de tu saldo líquido diario.
                    </p>

                    <div class="flex justify-between items-center mb-3 pt-2.5 border-t border-white/10">
                        <span class="text-[11px] font-bold uppercase tracking-wider text-[#8E8E93]">Mis Tarjetas</span>
                        <div class="flex items-center gap-2">
                            <button onclick="abrirModalNuevaTarjeta()" class="px-2.5 py-1.5 rounded-xl bg-white/10 hover:bg-white/15 text-white text-[11px] font-bold border border-white/10 flex items-center gap-1 active:scale-95 transition">
                                <i class="fa-solid fa-plus text-[9px]"></i>
                                <span>Nueva TC</span>
                            </button>
                            <button onclick="abrirModalGastoTC()" class="px-2.5 py-1.5 rounded-xl bg-[#0A84FF]/20 hover:bg-[#0A84FF]/30 text-[#0A84FF] text-[11px] font-bold border border-[#0A84FF]/30 flex items-center gap-1 active:scale-95 transition">
                                <i class="fa-solid fa-credit-card text-[9px]"></i>
                                <span>+ Gasto con TC</span>
                            </button>
                        </div>
                    </div>

                    <!-- Contenedor de Tarjetas estilo Apple Wallet -->
                    <div id="tarjetas-credito-cards" class="space-y-3 mb-3">
                        <!-- Dinámico con cards estilo Apple Wallet -->
                    </div>

                    <!-- Historial Reciente de Compras con Tarjeta -->
                    <div class="pt-2 border-t border-white/5">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-[#8E8E93] block mb-2">Últimas Compras a Crédito</span>
                        <div id="transacciones-tc-list" class="space-y-2">
                            <!-- Dinámico -->
                        </div>
                    </div>
                </div>

            </div>

            <!-- ========================================== -->
            <!-- VISTA 2: MOVIMIENTOS (Historial Interactivo con Detalle) -->
            <!-- ========================================== -->
            <div id="view-movimientos" class="tab-view hidden pb-24">
                <div class="flex justify-between items-center mb-4">
                    <div>
                        <span class="text-[11px] font-bold text-[#8E8E93] uppercase tracking-wider">Historial Financiero</span>
                        <div class="text-xs text-[#8E8E93]" id="conteo-tx">0 movimientos</div>
                    </div>
                    <button onclick="abrirModalGasto()" class="px-3.5 py-2 rounded-2xl bg-[#0A84FF] hover:bg-blue-600 text-white text-xs font-bold flex items-center gap-1.5 active:scale-95 transition shadow-md shadow-blue-500/20">
                        <i class="fa-solid fa-plus text-[10px]"></i>
                        <span>Registrar</span>
                    </button>
                </div>

                <div id="transacciones-list" class="space-y-2.5">
                    <!-- Dinámico: cada fila abre modal de detalle al tocarse -->
                </div>
            </div>

            <!-- ========================================== -->
            <!-- VISTA 3: CUENTAS E INSTRUMENTOS -->
            <!-- ========================================== -->
            <div id="view-cuentas" class="tab-view hidden pb-24">
                <div class="flex justify-between items-center mb-3">
                    <div>
                        <span class="text-[11px] font-bold text-[#8E8E93] uppercase tracking-wider">Tus Instrumentos</span>
                        <p class="text-[11px] text-[#8E8E93]">Toca el lápiz para actualizar tu saldo o cupo</p>
                    </div>
                    <button onclick="abrirModalNuevaCuenta()" class="px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/15 text-white text-xs font-bold border border-white/10 flex items-center gap-1.5 active:scale-95 transition">
                        <i class="fa-solid fa-plus text-[10px]"></i>
                        <span>Nueva Cuenta</span>
                    </button>
                </div>

                <!-- Resumen de Saldos -->
                <div class="ios-card p-4 rounded-3xl mb-4 border border-white/10 bg-[#1C1C1E]">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <span class="text-[#8E8E93] block text-[10px] uppercase font-bold tracking-wider">Total en Cuentas</span>
                            <span id="subtotal-cuentas" class="font-extrabold text-[#30D158] text-lg">$ 0</span>
                        </div>
                        <div>
                            <span class="text-[#8E8E93] block text-[10px] uppercase font-bold tracking-wider">Deuda en Tarjetas</span>
                            <span id="subtotal-deuda" class="font-extrabold text-[#FF453A] text-lg">$ 0</span>
                        </div>
                    </div>
                </div>

                <!-- Rendimientos Nu (Cuenta de Alto Rendimiento) -->
                <div id="card-rendimientos" class="ios-card p-3.5 rounded-2xl mb-4 flex items-center justify-between border border-fuchsia-500/20 bg-fuchsia-950/20" style="display: none;">
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

            <!-- ========================================== -->
            <!-- VISTA 4: AJUSTES, NÓMINA Y SEGURIDAD -->
            <!-- ========================================== -->
            <div id="view-ajustes" class="tab-view hidden pb-24">
                <div class="mb-4">
                    <span class="text-[11px] font-bold text-[#8E8E93] uppercase tracking-wider">Configuración Personal</span>
                    <p class="text-[11px] text-[#8E8E93]">Seguridad, ciclo de nómina y automatización de Apple Pay</p>
                </div>

                <!-- Card 1: Seguridad & Face ID -->
                <div class="ios-card rounded-3xl p-5 mb-4 border border-white/10 bg-[#1C1C1E]">
                    <div class="flex items-center gap-2 mb-3">
                        <div class="w-7 h-7 rounded-lg bg-blue-500/20 text-[#0A84FF] flex items-center justify-center text-xs">
                            <i class="fa-solid fa-shield-halved"></i>
                        </div>
                        <h3 class="text-sm font-bold text-white">Seguridad y Face ID</h3>
                    </div>
                    <div class="space-y-3 text-xs">
                        <div class="flex justify-between items-center py-2 border-b border-white/5">
                            <div>
                                <span class="font-bold text-white block">Desbloqueo con Face ID</span>
                                <span class="text-[11px] text-[#8E8E93]">Accede instantáneamente sin teclear tu PIN</span>
                            </div>
                            <label class="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" id="switch-faceid" onchange="toggleFaceIdSwitch()" class="sr-only peer">
                                <div class="w-11 h-6 bg-[#2C2C2E] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#30D158]"></div>
                            </label>
                        </div>
                        <div class="pt-1 flex gap-2">
                            <button onclick="abrirModalCambiarPin()" class="w-1/2 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-white font-bold text-xs transition">
                                Cambiar PIN
                            </button>
                            <button onclick="bloquearApp()" class="w-1/2 py-2.5 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 font-bold text-xs transition">
                                Bloquear App
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Card 2: Mi Nómina -->
                <div class="ios-card rounded-3xl p-5 mb-4 border border-white/10 bg-[#1C1C1E]">
                    <div class="flex items-center gap-2 mb-3">
                        <div class="w-7 h-7 rounded-lg bg-emerald-500/20 text-[#30D158] flex items-center justify-center text-xs">
                            <i class="fa-solid fa-money-check-dollar"></i>
                        </div>
                        <h3 class="text-sm font-bold text-white">Mi Nómina y Finanzas</h3>
                    </div>
                    <div class="space-y-3">
                        <div>
                            <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Ingreso Mensual Estimado ($)</label>
                            <input type="number" id="perfil-ingreso" placeholder="Ej: 4500000" class="w-full bg-[#000000] border border-white/10 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-blue-500 outline-none">
                        </div>
                        <div>
                            <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Día de Cobro Mensual (1-31)</label>
                            <input type="number" id="perfil-dia" min="1" max="31" placeholder="Ej: 1" class="w-full bg-[#000000] border border-white/10 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-blue-500 outline-none">
                        </div>
                        <div>
                            <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Meta de Ahorro Mensual (%)</label>
                            <input type="number" id="perfil-ahorro" min="0" max="100" placeholder="15" class="w-full bg-[#000000] border border-white/10 rounded-xl px-3 py-2 text-white font-bold text-sm focus:border-blue-500 outline-none">
                        </div>
                        <button onclick="guardarPerfilReal()" class="w-full py-2.5 rounded-xl bg-[#0A84FF] hover:bg-blue-600 text-white text-xs font-black shadow-md shadow-blue-500/20 active:scale-95 transition">
                            Guardar Ajustes de Nómina
                        </button>
                    </div>
                </div>

                <!-- Card 3: Apple Pay & Atajos de iOS (Guía Paso a Paso) -->
                <div class="ios-card rounded-3xl p-5 mb-4 border border-white/10 bg-[#1C1C1E]">
                    <div class="flex items-center gap-2 mb-3">
                        <div class="w-7 h-7 rounded-lg bg-white/10 text-white flex items-center justify-center text-xs">
                            <i class="fa-brands fa-apple"></i>
                        </div>
                        <h3 class="text-sm font-bold text-white">Apple Pay Automático (Wallet)</h3>
                    </div>
                    
                    <div class="space-y-3 text-xs">
                        <p class="text-[11px] text-[#8E8E93] leading-relaxed">
                            Configura esta automatización en tu iPhone para que cada pago con Apple Pay se registre solo:
                        </p>
                        <div class="p-3 rounded-2xl bg-[#000000] border border-white/5 space-y-2">
                            <div class="flex items-center gap-2">
                                <span class="w-4 h-4 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px] font-bold">1</span>
                                <span class="text-[11px] text-white font-semibold">Abre la app <strong>Atajos</strong> en tu iPhone</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="w-4 h-4 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px] font-bold">2</span>
                                <span class="text-[11px] text-white font-semibold">Toca <strong>Automatización</strong> -> (+) -> <strong>Transacción de Wallet</strong></span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="w-4 h-4 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px] font-bold">3</span>
                                <span class="text-[11px] text-white font-semibold">Elige "Cualquier tarjeta" y marca "Ejecutar inmediatamente"</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="w-4 h-4 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px] font-bold">4</span>
                                <span class="text-[11px] text-white font-semibold">Agrega acción: <strong>Obtener contenido de URL</strong> (POST a esta URL):</span>
                            </div>
                            <div class="flex items-center gap-2 pt-1">
                                <input type="text" id="url-webhook-endpoint" readonly class="w-full bg-[#1C1C1E] border border-white/10 rounded-xl px-2.5 py-1.5 text-[10px] text-blue-400 font-mono select-all">
                                <button onclick="copiarUrlWebhook()" class="px-3 py-1.5 rounded-xl bg-[#0A84FF] text-white font-bold text-[10px] shrink-0 active:scale-95 transition">
                                    Copiar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Card 4: Zona de Peligro -->
                <div class="ios-card rounded-3xl p-5 mb-6 border border-rose-500/20 bg-rose-950/10 text-center">
                    <span class="text-[10px] font-bold text-rose-400 uppercase tracking-wider block mb-2">Reinicio Completo</span>
                    <button onclick="reiniciarTodoDesdeCero()" class="w-full py-2.5 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs font-bold transition flex items-center justify-center gap-2 active:scale-95">
                        <i class="fa-solid fa-trash-can"></i>
                        <span>Borrar todo y empezar desde cero</span>
                    </button>
                </div>
            </div>

        </div>

        <!-- ========================================== -->
        <!-- BARRA DE NAVEGACIÓN INFERIOR (Apple iOS Tab Bar) -->
        <!-- ========================================== -->
        <nav class="fixed bottom-0 left-0 right-0 z-40 bg-[#1C1C1E]/90 backdrop-blur-2xl border-t border-white/10 px-6 py-2 flex justify-between items-center max-w-lg mx-auto">
            <button onclick="cambiarTab('billetera')" id="tab-btn-billetera" class="flex flex-col items-center text-[#0A84FF] py-1 transition-colors">
                <i class="fa-solid fa-wallet text-lg"></i>
                <span class="text-[10px] font-bold mt-1">Billetera</span>
            </button>

            <button onclick="cambiarTab('movimientos')" id="tab-btn-movimientos" class="flex flex-col items-center text-[#8E8E93] hover:text-white py-1 transition-colors">
                <i class="fa-solid fa-clock-rotate-left text-lg"></i>
                <span class="text-[10px] font-bold mt-1">Movimientos</span>
            </button>

            <!-- Botón Central Destacado (+) -->
            <button onclick="abrirModalGasto()" class="w-12 h-12 rounded-full bg-[#0A84FF] hover:bg-blue-600 -mt-6 shadow-lg shadow-blue-500/30 flex items-center justify-center text-white text-xl font-black active:scale-90 transition border-4 border-[#000000]" title="Registrar Movimiento">
                <i class="fa-solid fa-plus"></i>
            </button>

            <button onclick="cambiarTab('cuentas')" id="tab-btn-cuentas" class="flex flex-col items-center text-[#8E8E93] hover:text-white py-1 transition-colors">
                <i class="fa-solid fa-credit-card text-lg"></i>
                <span class="text-[10px] font-bold mt-1">Cuentas</span>
            </button>

            <button onclick="cambiarTab('ajustes')" id="tab-btn-ajustes" class="flex flex-col items-center text-[#8E8E93] hover:text-white py-1 transition-colors">
                <i class="fa-solid fa-gear text-lg"></i>
                <span class="text-[10px] font-bold mt-1">Ajustes</span>
            </button>
        </nav>

        <!-- ========================================== -->
        <!-- MODALES DE ACCIÓN (iOS Bottom Sheet Style) -->
        <!-- ========================================== -->

        <!-- Modal: Detalle y Edición de Movimiento 📝 -->
        <div id="modal-detalle-tx" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-[#1C1C1E] border border-white/10 max-h-[90vh] overflow-y-auto">
                <div class="w-10 h-1 rounded-full bg-white/20 mx-auto mb-4"></div>
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <span class="text-[10px] font-bold uppercase text-[#8E8E93] tracking-wider block">Detalle de Movimiento</span>
                        <h3 class="text-xl font-extrabold text-white mt-0.5" id="dtx-comercio-titulo">Movimiento</h3>
                        <span class="text-xs text-[#8E8E93]" id="dtx-fecha-hora">Fecha</span>
                    </div>
                    <button onclick="cerrarDetalleTransaccion()" class="text-[#8E8E93] hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <input type="hidden" id="dtx-id">
                <div class="space-y-3 text-xs">
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Monto ($)</label>
                        <input type="number" id="dtx-monto" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2.5 text-white font-extrabold text-lg focus:border-blue-500 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Comercio / Detalle</label>
                        <input type="text" id="dtx-comercio" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2 text-white font-bold text-sm focus:border-blue-500 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Tipo de Movimiento</label>
                        <div class="grid grid-cols-2 gap-2">
                            <button type="button" id="dtx-btn-egreso" onclick="setDetalleTipo('EGRESO')" class="py-2.5 rounded-xl font-bold transition text-xs">Egreso (Gasto)</button>
                            <button type="button" id="dtx-btn-ingreso" onclick="setDetalleTipo('INGRESO')" class="py-2.5 rounded-xl font-bold transition text-xs">Ingreso</button>
                        </div>
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Cuenta / Tarjeta Origen</label>
                        <select id="dtx-cuenta" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2.5 text-white text-xs focus:border-blue-500 outline-none">
                            <!-- Dinámico -->
                        </select>
                    </div>
                    <div id="dtx-cuotas-container" class="hidden">
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Número de Cuotas</label>
                        <input type="number" id="dtx-cuotas" min="1" max="48" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2 text-white font-bold text-xs focus:border-blue-500 outline-none">
                    </div>
                    <div class="pt-3 flex gap-2">
                        <button onclick="eliminarMovimientoActual()" class="w-1/3 py-3 rounded-2xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 font-bold border border-rose-500/30 text-xs active:scale-95 transition">
                            Eliminar
                        </button>
                        <button onclick="guardarCambiosDetalleMovimiento()" class="w-2/3 py-3 rounded-2xl bg-[#0A84FF] hover:bg-blue-600 text-white font-black text-xs active:scale-95 transition shadow-lg shadow-blue-500/20">
                            Guardar Cambios
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal: Registrar Gasto / Ingreso Manual -->
        <div id="modal-gasto" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-[#1C1C1E] border border-white/10">
                <div class="w-10 h-1 rounded-full bg-white/20 mx-auto mb-4"></div>
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-extrabold text-white">Registrar Movimiento</h3>
                    <button onclick="cerrarModalGasto()" class="text-[#8E8E93] hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="space-y-3">
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Tipo</label>
                        <div class="grid grid-cols-2 gap-2">
                            <button type="button" id="btn-tipo-egreso" onclick="setTipoMovimiento('EGRESO')" class="py-2.5 rounded-xl text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/50">Egreso (Gasto)</button>
                            <button type="button" id="btn-tipo-ingreso" onclick="setTipoMovimiento('INGRESO')" class="py-2.5 rounded-xl text-xs font-bold bg-[#2C2C2E] text-[#8E8E93] border border-white/5">Ingreso</button>
                        </div>
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Monto ($)</label>
                        <input type="number" id="input-monto" placeholder="Ej: 35000" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2.5 text-white font-extrabold text-lg focus:border-blue-500 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Comercio / Detalle</label>
                        <input type="text" id="input-comercio" placeholder="Ej: Supermercado D1, Taxi, Almuerzo" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2.5 text-white text-sm focus:border-blue-500 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Cuenta o Tarjeta</label>
                        <select id="select-cuenta" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2.5 text-white text-sm focus:border-blue-500 outline-none">
                            <!-- Dinámico -->
                        </select>
                    </div>
                    <div class="pt-2 flex gap-2">
                        <button onclick="cerrarModalGasto()" class="w-1/2 py-3 rounded-2xl bg-[#2C2C2E] hover:bg-[#3A3A3C] text-white text-xs font-bold transition">Cancelar</button>
                        <button onclick="guardarMovimientoManual()" class="w-1/2 py-3 rounded-2xl bg-[#0A84FF] hover:bg-blue-600 text-white text-xs font-black shadow-lg shadow-blue-500/20 transition">Guardar</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal: Agregar Nueva Tarjeta / Cuenta (Con soporte de Cupo Total y Cupo Disponible) -->
        <div id="modal-nueva-cuenta" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-[#1C1C1E] border border-white/10">
                <div class="w-10 h-1 rounded-full bg-white/20 mx-auto mb-4"></div>
                <div class="flex justify-between items-center mb-3">
                    <h3 class="text-base font-extrabold text-white" id="modal-cuenta-titulo">Agregar Instrumento</h3>
                    <button onclick="cerrarModalNuevaCuenta()" class="text-[#8E8E93] hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="space-y-3">
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Tipo de Instrumento</label>
                        <select id="nueva-cuenta-tipo" onchange="adaptarFormularioCuenta()" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2 text-white text-sm focus:border-blue-500 outline-none">
                            <option value="CREDITO">💳 Tarjeta de Crédito (Visa, Mastercard, Nu, Bancolombia)</option>
                            <option value="DEBITO">🏦 Cuenta Débito / Ahorros (Bancolombia, Nequi)</option>
                            <option value="EFECTIVO">💵 Efectivo Físico (Billetera)</option>
                            <option value="ALTO_RENDIMIENTO">📈 Cuenta Alto Rendimiento (Nu Cajita, Lulo, Pibank)</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Nombre</label>
                        <input type="text" id="nueva-cuenta-nombre" placeholder="Ej: Nu Mastercard, Bancolombia Visa" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2 text-white text-sm focus:border-blue-500 outline-none">
                    </div>

                    <!-- Campos exclusivos para Tarjeta de Crédito -->
                    <div id="campos-tc" class="space-y-3">
                        <div>
                            <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Cupo Total Otorgado ($)</label>
                            <input type="number" id="nueva-cuenta-cupo-total" oninput="actualizarPrevisualizacionDeuda()" placeholder="Ej: 5000000" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2 text-white font-bold text-sm focus:border-blue-500 outline-none">
                        </div>
                        <div>
                            <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Cupo Disponible en este momento ($)</label>
                            <input type="number" id="nueva-cuenta-cupo-disponible" oninput="actualizarPrevisualizacionDeuda()" placeholder="Ej: 3500000" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2 text-white font-bold text-sm focus:border-blue-500 outline-none">
                        </div>
                        <div class="p-2.5 rounded-xl bg-[#000000] border border-white/5 text-[11px] text-[#8E8E93]" id="tc-deuda-preview">
                            Deuda actual calculada: <strong class="text-rose-400">$ 0</strong>
                        </div>
                    </div>

                    <!-- Campo estándar de Saldo para Cuentas Líquidas -->
                    <div id="campos-saldo-estandar" class="hidden">
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Saldo Actual Real ($)</label>
                        <input type="number" id="nueva-cuenta-saldo" placeholder="Ej: 1500000" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2 text-white font-bold text-sm focus:border-blue-500 outline-none">
                    </div>

                    <div class="pt-2 flex gap-2">
                        <button onclick="cerrarModalNuevaCuenta()" class="w-1/2 py-3 rounded-2xl bg-[#2C2C2E] hover:bg-[#3A3A3C] text-white text-xs font-bold transition">Cancelar</button>
                        <button onclick="guardarNuevaCuenta()" class="w-1/2 py-3 rounded-2xl bg-[#0A84FF] hover:bg-blue-600 text-white text-xs font-black shadow-lg shadow-blue-500/20 transition">Crear</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal: Editar Saldo / Cupo de Cuenta -->
        <div id="modal-editar-cuenta" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-[#1C1C1E] border border-white/10">
                <div class="w-10 h-1 rounded-full bg-white/20 mx-auto mb-4"></div>
                <div class="flex justify-between items-center mb-3">
                    <div>
                        <h3 class="text-base font-extrabold text-white" id="edit-nombre-cuenta">Editar Cuenta</h3>
                        <span class="text-[11px] text-[#8E8E93]" id="edit-tipo-cuenta">Cuenta</span>
                    </div>
                    <button onclick="cerrarModalEditarCuenta()" class="text-[#8E8E93] hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <input type="hidden" id="edit-cuenta-id">
                <div class="space-y-3">
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Nombre</label>
                        <input type="text" id="edit-nombre-input" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2 text-white font-bold text-sm focus:border-blue-500 outline-none">
                    </div>
                    <div id="edit-container-saldo">
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1" id="edit-saldo-label">Saldo Actual Real ($)</label>
                        <input type="number" id="edit-saldo" placeholder="0" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2.5 text-white font-bold text-lg focus:border-blue-500 outline-none">
                    </div>
                    <div id="edit-container-cupo" class="space-y-3 hidden">
                        <div>
                            <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Cupo Total ($)</label>
                            <input type="number" id="edit-cupo-total" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2 text-white font-bold text-sm focus:border-blue-500 outline-none">
                        </div>
                        <div>
                            <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Cupo Disponible Actual ($)</label>
                            <input type="number" id="edit-cupo-disponible" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2 text-white font-bold text-sm focus:border-blue-500 outline-none">
                        </div>
                    </div>
                    <div class="pt-2 flex gap-2">
                        <button onclick="eliminarCuentaActual()" class="py-3 px-4 rounded-2xl bg-rose-500/20 text-rose-300 text-xs font-bold border border-rose-500/30">Eliminar</button>
                        <button onclick="guardarEdicionSaldo()" class="flex-1 py-3 rounded-2xl bg-[#0A84FF] hover:bg-blue-600 text-white text-xs font-black shadow-lg shadow-blue-500/20">Actualizar</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal: Agregar Nuevo Gasto Fijo 📌 -->
        <div id="modal-nuevo-gasto-fijo" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-[#1C1C1E] border border-white/10">
                <div class="w-10 h-1 rounded-full bg-white/20 mx-auto mb-4"></div>
                <div class="flex justify-between items-center mb-3">
                    <h3 class="text-base font-extrabold text-white">Agregar Gasto Fijo Mensual</h3>
                    <button onclick="cerrarModalNuevoGastoFijo()" class="text-[#8E8E93] hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="space-y-3">
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Concepto / Nombre</label>
                        <input type="text" id="nuevo-fijo-nombre" placeholder="Ej: Arriendo, Internet, Servicios Públicos, Seguro" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2 text-white text-sm focus:border-blue-500 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Monto Mensual ($)</label>
                        <input type="number" id="nuevo-fijo-monto" placeholder="Ej: 1200000" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2 text-white font-bold text-sm focus:border-blue-500 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Día Habitual de Pago (1 - 31)</label>
                        <input type="number" id="nuevo-fijo-dia" min="1" max="31" placeholder="Ej: 5" value="5" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-3 py-2 text-white font-bold text-sm focus:border-blue-500 outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">¿Ya cubriste este pago este mes?</label>
                        <div class="grid grid-cols-2 gap-2">
                            <button type="button" id="btn-fijo-cubierto" onclick="setEstadoNuevoFijo(true)" class="py-2.5 px-2 rounded-xl text-[11px] font-bold bg-[#30D158]/20 text-[#30D158] border border-[#30D158]/40 transition">
                                ✓ Ya cubierto este mes
                            </button>
                            <button type="button" id="btn-fijo-pendiente" onclick="setEstadoNuevoFijo(false)" class="py-2.5 px-2 rounded-xl text-[11px] font-bold bg-[#000000] text-[#8E8E93] border border-white/10 transition">
                                ⏳ Por pagar este mes
                            </button>
                        </div>
                        <p class="text-[10px] text-[#8E8E93] mt-1" id="ayuda-estado-fijo">
                            ✓ No se descontará de tu saldo disponible actual porque ya fue cubierto.
                        </p>
                    </div>
                    <div class="pt-2 flex gap-2">
                        <button onclick="cerrarModalNuevoGastoFijo()" class="w-1/2 py-3 rounded-2xl bg-[#2C2C2E] hover:bg-[#3A3A3C] text-white text-xs font-bold transition">Cancelar</button>
                        <button onclick="guardarNuevoGastoFijo()" class="w-1/2 py-3 rounded-2xl bg-[#0A84FF] hover:bg-blue-600 text-white text-xs font-black shadow-lg shadow-blue-500/20 transition">Crear Gasto Fijo</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal: Cambiar PIN de 4 Dígitos -->
        <div id="modal-cambiar-pin" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-end sm:items-center justify-center p-0 sm:p-4 hidden">
            <div class="ios-card w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 bg-[#1C1C1E] border border-white/10">
                <div class="w-10 h-1 rounded-full bg-white/20 mx-auto mb-4"></div>
                <div class="flex justify-between items-center mb-3">
                    <h3 class="text-base font-extrabold text-white">Cambiar PIN de Acceso</h3>
                    <button onclick="cerrarModalCambiarPin()" class="text-[#8E8E93] hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="space-y-3">
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">PIN Actual (4 dígitos)</label>
                        <input type="password" id="chg-pin-actual" maxlength="4" placeholder="••••" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-4 py-2.5 text-center text-white font-black text-base tracking-widest outline-none">
                    </div>
                    <div>
                        <label class="text-[10px] font-bold uppercase text-[#8E8E93] block mb-1">Nuevo PIN (4 dígitos)</label>
                        <input type="password" id="chg-pin-nuevo" maxlength="4" placeholder="••••" class="w-full bg-[#000000] border border-white/10 rounded-2xl px-4 py-2.5 text-center text-white font-black text-base tracking-widest outline-none">
                    </div>
                    <div class="pt-2 flex gap-2">
                        <button onclick="cerrarModalCambiarPin()" class="w-1/2 py-3 rounded-2xl bg-[#2C2C2E] text-white text-xs font-bold">Cancelar</button>
                        <button onclick="ejecutarCambioPin()" class="w-1/2 py-3 rounded-2xl bg-[#0A84FF] text-white text-xs font-black">Actualizar PIN</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // ==========================================
            // ESTADO GLOBAL & SEGURIDAD (Bancolombia + Face ID)
            // ==========================================
            let cuentasData = [];
            let transaccionesData = [];
            let modoPrivacidad = false;
            let tipoMovimientoActual = 'EGRESO';
            let nuevoFijoPagado = true;
            let pinIngresado = "";
            let sesionAutenticada = false;
            let usuarioActual = null;
            let faceIdHabilitado = false;

            // Verificar Estado de Seguridad al cargar
            async function inicializarSeguridad() {
                // 1. Si la sesión ya fue desbloqueada en esta navegación, mantener abierta
                if (sessionStorage.getItem('aurea_sesion_activa') === 'true') {
                    desbloquearApp(false);
                    return;
                }

                try {
                    const res = await fetch('/api/v1/auth/estado');
                    if(!res.ok) return;
                    const estado = await res.json();

                    const authScreen = document.getElementById('pantalla-auth');
                    const formReg = document.getElementById('form-registro-inicial');
                    const tecladoPin = document.getElementById('contenedor-teclado-pin');
                    const saludo = document.getElementById('auth-saludo');
                    const instruccion = document.getElementById('auth-instruccion');
                    const btnFaceId = document.getElementById('btn-teclado-faceid');
                    const switchFaceId = document.getElementById('switch-faceid');

                    if(!estado.registrado) {
                        // Modo Primer Registro
                        saludo.innerText = "Bienvenido a AUREA";
                        instruccion.innerText = "Crea tu acceso personal privado";
                        formReg.classList.remove('hidden');
                        tecladoPin.classList.add('hidden');
                    } else {
                        // Modo Login Habitual
                        usuarioActual = estado.username;
                        faceIdHabilitado = estado.face_id_enabled;
                        saludo.innerText = "Hola, " + (usuarioActual || "Usuario");
                        instruccion.innerText = "Ingresa tu PIN de 4 dígitos";
                        formReg.classList.add('hidden');
                        tecladoPin.classList.remove('hidden');
                        if(switchFaceId) switchFaceId.checked = faceIdHabilitado;

                        if(!faceIdHabilitado && btnFaceId) {
                            btnFaceId.style.opacity = '0.5';
                        }
                    }
                } catch(e) {
                    console.error("Error al inicializar autenticación:", e);
                }
            }

            function teclearPin(digito) {
                if(pinIngresado.length < 4) {
                    pinIngresado += digito;
                    actualizarDotsPin();
                    if(pinIngresado.length === 4) {
                        verificarPinIngresado();
                    }
                }
            }

            function borrarDigitoPin() {
                if(pinIngresado.length > 0) {
                    pinIngresado = pinIngresado.slice(0, -1);
                    actualizarDotsPin();
                }
            }

            function actualizarDotsPin() {
                for(let i = 1; i <= 4; i++) {
                    const dot = document.getElementById('pin-dot-' + i);
                    if(dot) {
                        if(i <= pinIngresado.length) {
                            dot.className = 'w-3.5 h-3.5 rounded-full bg-white scale-110 transition-all duration-150 shadow-md shadow-white/40';
                        } else {
                            dot.className = 'w-3.5 h-3.5 rounded-full border border-white/30 transition-all duration-150';
                        }
                    }
                }
            }

            async function verificarPinIngresado() {
                try {
                    const res = await fetch('/api/v1/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ pin: pinIngresado })
                    });
                    if(res.ok) {
                        desbloquearApp();
                    } else {
                        // Error de PIN con vibración visual
                        const teclado = document.getElementById('contenedor-teclado-pin');
                        if(teclado) {
                            teclado.style.transform = 'translateX(6px)';
                            setTimeout(() => teclado.style.transform = 'translateX(-6px)', 80);
                            setTimeout(() => teclado.style.transform = 'translateX(0)', 160);
                        }
                        pinIngresado = "";
                        actualizarDotsPin();
                        alert("PIN incorrecto. Intenta nuevamente.");
                    }
                } catch(e) {
                    alert("Error al verificar credenciales.");
                    pinIngresado = "";
                    actualizarDotsPin();
                }
            }

            async function registrarPasskeyDispositivo() {
                if (!window.PublicKeyCredential) {
                    alert("Este navegador no soporta Face ID. Ingresa normalmente con tu PIN de 4 dígitos.");
                    return false;
                }
                try {
                    const challenge = new Uint8Array(32);
                    window.crypto.getRandomValues(challenge);
                    const userId = new Uint8Array(16);
                    window.crypto.getRandomValues(userId);

                    const credential = await navigator.credentials.create({
                        publicKey: {
                            challenge: challenge,
                            rp: { name: "AUREA Finanzas", id: window.location.hostname },
                            user: {
                                id: userId,
                                name: usuarioActual || "jorge",
                                displayName: usuarioActual || "Usuario AUREA"
                            },
                            pubKeyCredParams: [
                                { type: "public-key", alg: -7 },   // ES256
                                { type: "public-key", alg: -257 }  // RS256
                            ],
                            authenticatorSelection: {
                                authenticatorAttachment: "platform",
                                userVerification: "required"
                            },
                            timeout: 60000
                        }
                    });

                    if (credential) {
                        localStorage.setItem('aurea_passkey_guardada', 'true');
                        await fetch('/api/v1/auth/face-id', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ enabled: true, credential_id: credential.id })
                        });
                        faceIdHabilitado = true;
                        const sw = document.getElementById('switch-faceid');
                        if (sw) sw.checked = true;
                        const btnFaceId = document.getElementById('btn-teclado-faceid');
                        if (btnFaceId) btnFaceId.style.opacity = '1';
                        alert("✓ ¡Llave de acceso Face ID guardada con éxito en tu iPhone!");
                        desbloquearApp();
                        return true;
                    }
                } catch (e) {
                    console.warn("Registro Face ID cancelado:", e);
                }
                return false;
            }

            async function activarFaceId() {
                const tienePasskey = localStorage.getItem('aurea_passkey_guardada') === 'true';

                // Si aún no ha guardado la llave de acceso con Face ID en su iPhone
                if (!tienePasskey) {
                    const desea = confirm("¿Deseas activar y guardar tu Face ID / Touch ID en este iPhone para entrar sin digitar tu PIN?");
                    if (desea) {
                        await registrarPasskeyDispositivo();
                    }
                    return;
                }

                try {
                    if (window.PublicKeyCredential) {
                        const challenge = new Uint8Array(32);
                        window.crypto.getRandomValues(challenge);

                        const assertion = await navigator.credentials.get({
                            publicKey: {
                                challenge: challenge,
                                rpId: window.location.hostname,
                                userVerification: "required",
                                timeout: 60000
                            }
                        });

                        if (assertion) {
                            const res = await fetch('/api/v1/auth/face-id-login', { method: 'POST' });
                            if (res.ok) {
                                desbloquearApp();
                                return;
                            }
                        }
                    }
                } catch (e) {
                    console.warn("Autenticación biométrica cancelada o no disponible:", e);
                }
            }

            function desbloquearApp(animar = true) {
                sesionAutenticada = true;
                sessionStorage.setItem('aurea_sesion_activa', 'true');
                pinIngresado = "";
                actualizarDotsPin();
                const pantalla = document.getElementById('pantalla-auth');
                if(pantalla) {
                    if (animar) {
                        pantalla.style.opacity = '0';
                        setTimeout(() => pantalla.classList.add('hidden'), 250);
                    } else {
                        pantalla.classList.add('hidden');
                    }
                }
                fetchDashboard();
            }

            function bloquearApp() {
                sesionAutenticada = false;
                sessionStorage.removeItem('aurea_sesion_activa');
                pinIngresado = "";
                actualizarDotsPin();
                const pantalla = document.getElementById('pantalla-auth');
                if(pantalla) {
                    pantalla.classList.remove('hidden');
                    pantalla.style.opacity = '1';
                }
                inicializarSeguridad();
            }

            async function guardarRegistroInicial() {
                const nombre = document.getElementById('reg-nombre').value.trim();
                const pin = document.getElementById('reg-pin').value.trim();

                if(!nombre || pin.length !== 4 || isNaN(pin)) {
                    alert("Por favor ingresa tu nombre y un PIN de 4 dígitos numéricos.");
                    return;
                }

                try {
                    const res = await fetch('/api/v1/auth/registro', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username: nombre, pin: pin })
                    });
                    if(res.ok) {
                        alert(`¡Bienvenido ${nombre}! Tu cuenta y PIN han sido configurados.`);
                        desbloquearApp();
                    } else {
                        const err = await res.json();
                        alert(err.detail || "Error al crear cuenta.");
                    }
                } catch(e) {
                    alert("Error de conexión al registrar.");
                }
            }

            async function toggleFaceIdSwitch() {
                const sw = document.getElementById('switch-faceid');
                const activado = sw ? sw.checked : false;

                if (activado) {
                    const ok = await registrarPasskeyDispositivo();
                    if (!ok && sw) sw.checked = false;
                } else {
                    localStorage.removeItem('aurea_passkey_guardada');
                    faceIdHabilitado = false;
                    const btnFaceId = document.getElementById('btn-teclado-faceid');
                    if (btnFaceId) btnFaceId.style.opacity = '0.5';
                    await fetch('/api/v1/auth/face-id', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ enabled: false })
                    });
                    alert("Face ID desactivado. Podrás ingresar normalmente con tu PIN.");
                }
            }

            function abrirModalCambiarPin() {
                document.getElementById('modal-cambiar-pin').classList.remove('hidden');
            }
            function cerrarModalCambiarPin() {
                document.getElementById('modal-cambiar-pin').classList.add('hidden');
                document.getElementById('chg-pin-actual').value = '';
                document.getElementById('chg-pin-nuevo').value = '';
            }
            async function ejecutarCambioPin() {
                const actual = document.getElementById('chg-pin-actual').value.trim();
                const nuevo = document.getElementById('chg-pin-nuevo').value.trim();

                if(actual.length !== 4 || nuevo.length !== 4) {
                    alert("Ambos PIN deben tener exactamente 4 dígitos.");
                    return;
                }

                try {
                    const res = await fetch('/api/v1/auth/cambiar-pin', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ pin_actual: actual, pin_nuevo: nuevo })
                    });
                    if(res.ok) {
                        alert("✓ ¡PIN actualizado con éxito!");
                        cerrarModalCambiarPin();
                    } else {
                        const err = await res.json();
                        alert(err.detail || "Error al cambiar PIN.");
                    }
                } catch(e) {
                    alert("Error de conexión.");
                }
            }

            // ==========================================
            // FORMATEO MONETARIO & MODO PRIVACIDAD
            // ==========================================
            function toggleModoPrivacidad() {
                modoPrivacidad = !modoPrivacidad;
                const icono = document.getElementById('icono-ojo');
                if(icono) {
                    icono.className = modoPrivacidad ? 'fa-solid fa-eye-slash text-blue-400' : 'fa-solid fa-eye text-slate-300';
                }
                recargarDatos();
            }

            function formatearCOP(monto) {
                if(modoPrivacidad) return '$ ••••••';
                return '$ ' + Math.round(monto || 0).toLocaleString('es-CO');
            }

            // ==========================================
            // RENDERIZADO DEL DASHBOARD APPLE HIG
            // ==========================================
            function aplicarDatosDashboard(data) {
                if(!data) return;

                // 1. Estado DB
                const badgeDb = document.getElementById('badge-db');
                if(badgeDb) {
                    if(data.es_postgresql) {
                        badgeDb.className = 'text-[9px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-[#30D158] border border-emerald-500/30';
                        badgeDb.innerText = '☁️ NUBE';
                    } else {
                        badgeDb.className = 'text-[9px] font-bold px-2 py-0.5 rounded-full bg-white/10 text-slate-300 border border-white/10';
                        badgeDb.innerText = '📱 LOCAL';
                    }
                }

                // 2. Cuentas e Instrumentos
                cuentasData = data.cuentas || [];
                transaccionesData = data.transacciones || [];
                let totalCuentas = 0;       // Dinero líquido
                let totalDeuda = 0;         // Deuda acumulada de TC
                let totalCupoDisponible = 0;// Cupo disponible total de TC

                const containerCuentas = document.getElementById('cuentas-list');
                const selectCuenta = document.getElementById('select-cuenta');
                const selectDtxCuenta = document.getElementById('dtx-cuenta');
                if(containerCuentas) containerCuentas.innerHTML = '';
                if(selectCuenta) selectCuenta.innerHTML = '';
                if(selectDtxCuenta) selectDtxCuenta.innerHTML = '';

                cuentasData.forEach(c => {
                    if(c.tipo === 'CREDITO') {
                        totalDeuda += (c.saldo_actual || 0);
                        const cupoDisp = c.cupo_disponible !== undefined ? c.cupo_disponible : Math.max(0, (c.cupo_total || 0) - (c.saldo_actual || 0));
                        totalCupoDisponible += cupoDisp;
                    } else {
                        totalCuentas += (c.saldo_actual || 0);
                    }

                    // Renderizar en pestaña de Cuentas
                    if(containerCuentas) {
                        let icon = 'fa-credit-card';
                        let iconColor = 'text-blue-400';
                        if(c.tipo === 'ALTO_RENDIMIENTO') { icon = 'fa-piggy-bank'; iconColor = 'text-fuchsia-400'; }
                        if(c.tipo === 'EFECTIVO') { icon = 'fa-money-bill-wave'; iconColor = 'text-emerald-400'; }
                        if(c.tipo === 'CREDITO') { icon = 'fa-regular fa-credit-card'; iconColor = 'text-rose-400'; }

                        const item = document.createElement('div');
                        item.className = 'ios-card p-3.5 rounded-2xl flex items-center justify-between border border-white/5 bg-[#1C1C1E]';
                        item.innerHTML = `
                            <div class="flex items-center gap-3">
                                <div class="w-9 h-9 rounded-xl bg-white/5 flex items-center justify-center ${iconColor} text-sm">
                                    <i class="fa-solid ${icon}"></i>
                                </div>
                                <div>
                                    <span class="text-sm font-bold text-white block leading-tight">${c.nombre}</span>
                                    <span class="text-[10px] text-[#8E8E93] uppercase font-semibold">${c.tipo === 'CREDITO' ? 'Tarjeta de Crédito' : c.tipo}</span>
                                </div>
                            </div>
                            <div class="flex items-center gap-2.5">
                                <div class="text-right">
                                    <span class="text-sm font-extrabold ${c.tipo === 'CREDITO' ? 'text-rose-400' : 'text-[#30D158]'} block">
                                        ${formatearCOP(c.saldo_actual)}
                                    </span>
                                    ${c.tipo === 'CREDITO' ? `<span class="text-[9px] text-emerald-400 font-medium">Cupo: ${formatearCOP(c.cupo_disponible || 0)}</span>` : ''}
                                </div>
                                <button onclick="abrirModalEditarCuenta(${c.id})" class="w-7 h-7 rounded-lg bg-white/5 hover:bg-white/15 text-slate-300 hover:text-white flex items-center justify-center text-xs transition border border-white/10" title="Editar">
                                    <i class="fa-solid fa-pen"></i>
                                </button>
                            </div>
                        `;
                        containerCuentas.appendChild(item);
                    }

                    // Selectores de modales
                    if(selectCuenta) {
                        const opt = document.createElement('option');
                        opt.value = c.id;
                        opt.innerText = c.nombre + (c.tipo === 'CREDITO' ? ' (TC)' : '');
                        selectCuenta.appendChild(opt);
                    }
                    if(selectDtxCuenta) {
                        const opt = document.createElement('option');
                        opt.value = c.id;
                        opt.innerText = c.nombre;
                        selectDtxCuenta.appendChild(opt);
                    }
                });

                const elSubCuentas = document.getElementById('subtotal-cuentas');
                if(elSubCuentas) elSubCuentas.innerText = formatearCOP(totalCuentas);

                const elSubDeuda = document.getElementById('subtotal-deuda');
                if(elSubDeuda) elSubDeuda.innerText = formatearCOP(totalDeuda);

                const elBalTotal = document.getElementById('balance-neto-total');
                if(elBalTotal) elBalTotal.innerText = formatearCOP(totalCuentas);

                // 3. Gastos Fijos (Apartados de Nómina)
                const gfData = data.gastos_fijos;
                let totalFijos = 0;
                let totalFijosPendientes = 0;
                let totalFijosCubiertos = 0;
                let itemsFijos = [];
                if(gfData) {
                    itemsFijos = gfData.items || [];
                    totalFijos = gfData.total_fijos || 0;
                    totalFijosPendientes = itemsFijos.filter(i => !i.pagado_este_mes).reduce((sum, i) => sum + i.monto, 0);
                    totalFijosCubiertos = itemsFijos.filter(i => i.pagado_este_mes).reduce((sum, i) => sum + i.monto, 0);

                    const totalGfEl = document.getElementById('total-gastos-fijos');
                    if(totalGfEl) totalGfEl.innerText = formatearCOP(totalFijos);

                    const badgeGf = document.getElementById('badge-estado-gastos-fijos');
                    if(badgeGf) {
                        if(totalFijos === 0) {
                            badgeGf.className = 'px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-white/10 text-slate-300 border border-white/10';
                            badgeGf.innerText = 'SIN COMPROMISOS';
                        } else if(totalFijosPendientes === 0) {
                            badgeGf.className = 'px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#30D158]/20 text-[#30D158] border border-[#30D158]/40';
                            badgeGf.innerText = '✓ TODOS CUBIERTOS';
                        } else {
                            badgeGf.className = 'px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#FF9F0A]/20 text-[#FF9F0A] border border-[#FF9F0A]/40';
                            badgeGf.innerText = '⏳ ' + formatearCOP(totalFijosPendientes) + ' POR PAGAR';
                        }
                    }

                    const containerGf = document.getElementById('gastos-fijos-list');
                    if(containerGf) {
                        containerGf.innerHTML = '';
                        if(itemsFijos.length === 0) {
                            containerGf.innerHTML = `
                                <div class="text-center py-4 px-3 rounded-2xl bg-[#000000]/40 border border-white/5">
                                    <p class="text-xs text-white/80 font-bold mb-1">Sin compromisos fijos registrados</p>
                                    <p class="text-[11px] text-[#8E8E93] mb-2">Registra arriendo, servicios o suscripciones fijas.</p>
                                    <button onclick="abrirModalNuevoGastoFijo()" class="text-xs text-blue-400 font-bold underline hover:text-white">Agregar Mi Primer Fijo</button>
                                </div>
                            `;
                        } else {
                            itemsFijos.forEach(item => {
                                let icon = 'fa-house';
                                const nom = (item.nombre || '').toLowerCase();
                                if(nom.includes('servicio') || nom.includes('luz') || nom.includes('agua') || nom.includes('gas') || nom.includes('enel') || nom.includes('epm')) icon = 'fa-bolt';
                                else if(nom.includes('internet') || nom.includes('wifi') || nom.includes('celular') || nom.includes('plan') || nom.includes('claro') || nom.includes('tigo') || nom.includes('movistar')) icon = 'fa-wifi';
                                else if(nom.includes('gym') || nom.includes('gimnasio') || nom.includes('smart fit')) icon = 'fa-dumbbell';
                                else if(nom.includes('netflix') || nom.includes('spotify') || nom.includes('sub') || nom.includes('youtube') || nom.includes('apple')) icon = 'fa-star';

                                const el = document.createElement('div');
                                el.className = 'p-3 rounded-2xl bg-[#000000]/50 border border-white/5 flex items-center justify-between';
                                el.innerHTML = `
                                    <div class="flex items-center gap-3">
                                        <div class="w-8 h-8 rounded-xl bg-white/5 flex items-center justify-center text-slate-300 text-xs">
                                            <i class="fa-solid ${icon}"></i>
                                        </div>
                                        <div>
                                            <span class="text-xs font-bold text-white block leading-tight">${item.nombre}</span>
                                            <span class="text-[10px] text-[#8E8E93]">Día ${item.dia_pago} de cada mes</span>
                                        </div>
                                    </div>
                                    <div class="flex items-center gap-2">
                                        <span class="text-xs font-black text-slate-200">${formatearCOP(item.monto)}</span>
                                        <button onclick="togglePagadoGastoFijo(${item.id})" class="px-2.5 py-1 rounded-lg text-[10px] font-bold transition ${item.pagado_este_mes ? 'bg-[#30D158]/20 text-[#30D158] border border-[#30D158]/40' : 'bg-[#FF9F0A]/20 text-[#FF9F0A] border border-[#FF9F0A]/40'}" title="Toca para alternar">
                                            ${item.pagado_este_mes ? '✓ Cubierto' : '⏳ Por pagar'}
                                        </button>
                                        <button onclick="eliminarGastoFijo(${item.id})" class="w-6 h-6 rounded-lg bg-rose-500/15 hover:bg-rose-500/30 text-rose-300 flex items-center justify-center text-[10px] transition" title="Eliminar">
                                            <i class="fa-solid fa-trash"></i>
                                        </button>
                                    </div>
                                `;
                                containerGf.appendChild(el);
                            });
                        }
                    }
                }

                // Subtotal apartado en Card 1 (solo los PENDIENTES)
                const elSubApartadoFijos = document.getElementById('subtotal-apartado-fijos');
                if(elSubApartadoFijos) elSubApartadoFijos.innerText = formatearCOP(totalFijosPendientes);

                const elEstadoFijosApartados = document.getElementById('estado-fijos-apartados');
                if(elEstadoFijosApartados) {
                    if(totalFijosPendientes > 0) {
                        elEstadoFijosApartados.innerText = '🔒 ' + formatearCOP(totalFijosPendientes) + ' por pagar';
                    } else if(totalFijosCubiertos > 0) {
                        elEstadoFijosApartados.innerText = '✓ Todos cubiertos este mes';
                    } else {
                        elEstadoFijosApartados.innerText = 'Sin compromisos';
                    }
                }

                // 4. Saldo Disponible para Gastar (Card 1 Principal)
                const saldoDisponibleReal = Math.max(0, totalCuentas - totalFijosPendientes);
                const elDispHoy = document.getElementById('disponible-hoy');
                if(elDispHoy) {
                    elDispHoy.innerText = formatearCOP(saldoDisponibleReal);
                }

                const badgeDisp = document.getElementById('badge-disponible');
                if(badgeDisp) {
                    if(saldoDisponibleReal <= 0) {
                        badgeDisp.className = 'px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-500/20 text-rose-300 border border-rose-500/30';
                        badgeDisp.innerText = 'SIN SALDO';
                    } else if(totalFijosPendientes > 0) {
                        badgeDisp.className = 'px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-500/15 text-amber-300 border border-amber-500/30';
                        badgeDisp.innerText = 'FIJOS APARTADOS';
                    } else {
                        badgeDisp.className = 'px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#30D158]/15 text-[#30D158] border border-[#30D158]/30';
                        badgeDisp.innerText = 'LIBRE PARA GASTAR';
                    }
                }

                // 5. Apartado 3: Múltiples Tarjetas de Crédito (Apple Wallet)
                const totalDeudaTcEl = document.getElementById('total-deuda-tc');
                if(totalDeudaTcEl) totalDeudaTcEl.innerText = formatearCOP(totalDeuda);

                const totalCupoDispEl = document.getElementById('total-cupo-disponible-tc');
                if(totalCupoDispEl) totalCupoDispEl.innerText = formatearCOP(totalCupoDisponible);

                const containerTcCards = document.getElementById('tarjetas-credito-cards');
                const tcs = cuentasData.filter(c => c.tipo === 'CREDITO');
                if(containerTcCards) {
                    containerTcCards.innerHTML = '';
                    if(tcs.length === 0) {
                        containerTcCards.innerHTML = `
                            <div class="text-center py-5 px-3 rounded-2xl bg-[#000000]/40 border border-white/5">
                                <div class="w-10 h-10 rounded-2xl bg-white/5 text-slate-300 flex items-center justify-center mx-auto mb-2 text-base">
                                    <i class="fa-regular fa-credit-card"></i>
                                </div>
                                <p class="text-xs text-white/90 font-bold mb-1">Sin tarjetas de crédito configuradas</p>
                                <p class="text-[11px] text-[#8E8E93] mb-3">Registra tus tarjetas para dar seguimiento a tus cupos y compras.</p>
                                <button onclick="abrirModalNuevaTarjeta()" class="px-3.5 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-white text-xs font-bold transition">
                                    + Agregar Mi Primera Tarjeta
                                </button>
                            </div>
                        `;
                    } else {
                        tcs.forEach(tc => {
                            const cupoTot = tc.cupo_total || 0;
                            const deuda = tc.saldo_actual || 0;
                            const cupoDisp = tc.cupo_disponible !== undefined ? tc.cupo_disponible : Math.max(0, cupoTot - deuda);
                            const porcentajeUso = cupoTot > 0 ? Math.min(100, Math.round((deuda / cupoTot) * 100)) : 0;

                            let colorBarra = 'bg-emerald-400';
                            if(porcentajeUso > 50) colorBarra = 'bg-amber-400';
                            if(porcentajeUso > 80) colorBarra = 'bg-rose-400';

                            const cardEl = document.createElement('div');
                            cardEl.className = 'apple-wallet-card rounded-2xl p-4 relative overflow-hidden transition active:scale-[0.99]';
                            cardEl.innerHTML = `
                                <div class="flex justify-between items-start mb-3">
                                    <div class="flex items-center gap-2">
                                        <i class="fa-solid fa-microchip text-amber-300/80 text-lg"></i>
                                        <i class="fa-solid fa-wifi text-white/40 text-xs rotate-90"></i>
                                        <span class="text-sm font-extrabold text-white tracking-tight ml-1">${tc.nombre}</span>
                                    </div>
                                    <span class="text-[10px] font-mono text-white/50">•••• ${String(tc.id).padStart(4, '0')}</span>
                                </div>

                                <div class="mb-3">
                                    <span class="text-[10px] font-bold text-[#8E8E93] uppercase tracking-wider block">Cupo Disponible</span>
                                    <div class="text-2xl font-black text-white tracking-tight">${formatearCOP(cupoDisp)}</div>
                                </div>

                                <div class="space-y-1.5 pt-2 border-t border-white/10">
                                    <div class="flex justify-between text-[10px] text-[#8E8E93] font-semibold">
                                        <span>Deuda: <strong class="text-rose-400">${formatearCOP(deuda)}</strong></span>
                                        <span>Cupo Total: ${formatearCOP(cupoTot)}</span>
                                    </div>
                                    <div class="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
                                        <div class="h-full rounded-full ${colorBarra} transition-all duration-300" style="width: ${porcentajeUso}%"></div>
                                    </div>
                                </div>

                                <div class="mt-3 pt-2.5 border-t border-white/5 flex justify-between items-center">
                                    <span class="text-[10px] text-white/60 font-medium">${porcentajeUso}% de cupo utilizado</span>
                                    <button onclick="abrirGastoConTarjetaEspecifica(${tc.id})" class="px-2.5 py-1 rounded-lg bg-white/15 hover:bg-white/25 text-white font-bold text-[10px] active:scale-95 transition">
                                        + Gasto con esta tarjeta
                                    </button>
                                </div>
                            `;
                            containerTcCards.appendChild(cardEl);
                        });
                    }
                }

                // Lista de compras a crédito en Apartado 3
                const containerTcList = document.getElementById('transacciones-tc-list');
                const tcAccountIds = new Set(tcs.map(c => c.id));
                const txsTc = transaccionesData.filter(t => 
                    (t.cuenta_origen_id && tcAccountIds.has(t.cuenta_origen_id)) ||
                    t.cuenta_tipo === 'CREDITO' ||
                    t.medio === 'CREDITO' ||
                    (t.cuenta_nombre && tcs.some(c => c.nombre === t.cuenta_nombre))
                );

                if(containerTcList) {
                    containerTcList.innerHTML = '';
                    if(txsTc.length === 0) {
                        containerTcList.innerHTML = '<div class="text-center py-2.5 text-[#8E8E93] text-xs">Sin compras recientes con tarjeta de crédito.</div>';
                    } else {
                        txsTc.slice(0, 4).forEach(t => {
                            const item = document.createElement('div');
                            item.className = 'p-2.5 rounded-xl bg-[#000000]/40 border border-white/5 flex items-center justify-between cursor-pointer hover:bg-white/5 active:scale-98 transition';
                            item.onclick = () => abrirDetalleTransaccion(t.id);
                            item.innerHTML = `
                                <div class="flex items-center gap-2.5">
                                    <div class="w-7 h-7 rounded-lg bg-rose-500/15 flex items-center justify-center text-rose-400 text-xs">
                                        <i class="fa-regular fa-credit-card"></i>
                                    </div>
                                    <div>
                                        <span class="text-xs font-bold text-white block leading-tight">${t.comercio}</span>
                                        <span class="text-[10px] text-[#8E8E93]">${t.cuenta_nombre || 'TC'}</span>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <span class="text-xs font-extrabold text-rose-300 block">- ${formatearCOP(t.monto)}</span>
                                    <span class="text-[9px] text-[#8E8E93]">Toca para ver detalle</span>
                                </div>
                            `;
                            containerTcList.appendChild(item);
                        });
                    }
                }

                // 6. Rendimientos Nu
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

                // 7. Lista General de Transacciones (con clic para abrir detalle modal)
                const containerTx = document.getElementById('transacciones-list');
                const elConteoTx = document.getElementById('conteo-tx');
                if(elConteoTx) elConteoTx.innerText = transaccionesData.length + ' movimientos';
                if(containerTx) {
                    containerTx.innerHTML = '';
                    if(transaccionesData.length === 0) {
                        containerTx.innerHTML = '<div class="text-center py-8 text-[#8E8E93] text-xs">No hay movimientos registrados aún. Toca (+) para registrar uno.</div>';
                    } else {
                        transaccionesData.forEach(t => {
                            const item = document.createElement('div');
                            item.className = 'ios-card p-3 rounded-2xl flex items-center justify-between border border-white/5 bg-[#1C1C1E] cursor-pointer hover:border-white/20 active:scale-[0.99] transition';
                            item.onclick = () => abrirDetalleTransaccion(t.id);
                            item.innerHTML = `
                                <div>
                                    <span class="text-xs font-bold text-white block">${t.comercio}</span>
                                    <div class="flex items-center gap-1.5 mt-0.5">
                                        <span class="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-white/10 text-slate-300">${t.medio}</span>
                                        <span class="text-[9px] text-[#8E8E93]">${t.cuenta_nombre || ''}</span>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <span class="text-xs font-black ${t.tipo === 'INGRESO' ? 'text-[#30D158]' : t.tipo === 'EGRESO' ? 'text-[#FF453A]' : 'text-blue-400'} block">
                                        ${t.tipo === 'INGRESO' ? '+' : '-'} ${formatearCOP(t.monto)}
                                    </span>
                                    <span class="text-[9px] text-[#8E8E93]">Toca para editar</span>
                                </div>
                            `;
                            containerTx.appendChild(item);
                        });
                    }
                }
            }

            // ==========================================
            // DETALLE Y EDICIÓN DE MOVIMIENTOS
            // ==========================================
            let detalleTipoActual = 'EGRESO';

            async function abrirDetalleTransaccion(txId) {
                try {
                    const res = await fetch('/api/v1/transacciones/' + txId);
                    if(!res.ok) return;
                    const tx = await res.json();

                    document.getElementById('dtx-id').value = tx.id;
                    document.getElementById('dtx-comercio-titulo').innerText = tx.comercio;
                    document.getElementById('dtx-comercio').value = tx.comercio;
                    document.getElementById('dtx-monto').value = tx.monto;
                    
                    const fechaObj = tx.fecha ? new Date(tx.fecha) : new Date();
                    document.getElementById('dtx-fecha-hora').innerText = fechaObj.toLocaleString('es-CO', {
                        weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
                    });

                    const selCuenta = document.getElementById('dtx-cuenta');
                    if(selCuenta) selCuenta.value = tx.cuenta_origen_id;

                    setDetalleTipo(tx.tipo);

                    const cuotasCont = document.getElementById('dtx-cuotas-container');
                    const inputCuotas = document.getElementById('dtx-cuotas');
                    if(tx.cuotas_totales && tx.cuotas_totales > 1) {
                        cuotasCont.classList.remove('hidden');
                        inputCuotas.value = tx.cuotas_totales;
                    } else {
                        cuotasCont.classList.add('hidden');
                    }

                    document.getElementById('modal-detalle-tx').classList.remove('hidden');
                } catch(e) {
                    console.error("Error al abrir detalle:", e);
                }
            }

            function cerrarDetalleTransaccion() {
                document.getElementById('modal-detalle-tx').classList.add('hidden');
            }

            function setDetalleTipo(tipo) {
                detalleTipoActual = tipo;
                const btnEgreso = document.getElementById('dtx-btn-egreso');
                const btnIngreso = document.getElementById('dtx-btn-ingreso');
                if(tipo === 'EGRESO') {
                    btnEgreso.className = 'py-2.5 rounded-xl font-bold bg-rose-500/20 text-rose-300 border border-rose-500/50';
                    btnIngreso.className = 'py-2.5 rounded-xl font-bold bg-[#000000] text-[#8E8E93] border border-white/5';
                } else {
                    btnIngreso.className = 'py-2.5 rounded-xl font-bold bg-[#30D158]/20 text-[#30D158] border border-[#30D158]/50';
                    btnEgreso.className = 'py-2.5 rounded-xl font-bold bg-[#000000] text-[#8E8E93] border border-white/5';
                }
            }

            async function guardarCambiosDetalleMovimiento() {
                const txId = document.getElementById('dtx-id').value;
                const monto = parseFloat(document.getElementById('dtx-monto').value);
                const comercio = document.getElementById('dtx-comercio').value.trim();
                const cuentaId = parseInt(document.getElementById('dtx-cuenta').value);

                if(!monto || !comercio || !cuentaId) {
                    alert("Ingresa monto, comercio y cuenta válidos.");
                    return;
                }

                try {
                    const res = await fetch('/api/v1/transacciones/' + txId, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            monto: monto,
                            comercio: comercio,
                            cuenta_origen_id: cuentaId,
                            tipo: detalleTipoActual
                        })
                    });
                    if(res.ok) {
                        cerrarDetalleTransaccion();
                        fetchDashboard();
                    } else {
                        alert("No se pudo actualizar la transacción.");
                    }
                } catch(e) {
                    alert("Error de conexión al actualizar.");
                }
            }

            async function eliminarMovimientoActual() {
                const txId = document.getElementById('dtx-id').value;
                if(!confirm("¿Deseas eliminar este movimiento? Su saldo se revertirá automáticamente.")) return;

                try {
                    const res = await fetch('/api/v1/transacciones/' + txId, { method: 'DELETE' });
                    if(res.ok) {
                        cerrarDetalleTransaccion();
                        fetchDashboard();
                    } else {
                        alert("No se pudo eliminar.");
                    }
                } catch(e) {
                    alert("Error al eliminar.");
                }
            }

            // ==========================================
            // GESTIÓN DE TARJETAS Y CUENTAS
            // ==========================================
            function adaptarFormularioCuenta() {
                const tipo = document.getElementById('nueva-cuenta-tipo').value;
                const camposTc = document.getElementById('campos-tc');
                const camposSaldo = document.getElementById('campos-saldo-estandar');
                if(tipo === 'CREDITO') {
                    camposTc.classList.remove('hidden');
                    camposSaldo.classList.add('hidden');
                } else {
                    camposTc.classList.add('hidden');
                    camposSaldo.classList.remove('hidden');
                }
            }

            function actualizarPrevisualizacionDeuda() {
                const total = parseFloat(document.getElementById('nueva-cuenta-cupo-total').value) || 0;
                const disp = parseFloat(document.getElementById('nueva-cuenta-cupo-disponible').value) || 0;
                const deuda = Math.max(0, total - disp);
                const elPrev = document.getElementById('tc-deuda-preview');
                if(elPrev) {
                    elPrev.innerHTML = `Deuda actual calculada: <strong class="text-rose-400">${formatearCOP(deuda)}</strong>`;
                }
            }

            function abrirModalNuevaTarjeta() {
                abrirModalNuevaCuenta();
                const sel = document.getElementById('nueva-cuenta-tipo');
                if(sel) {
                    sel.value = 'CREDITO';
                    adaptarFormularioCuenta();
                }
            }

            function abrirGastoConTarjetaEspecifica(cuentaId) {
                abrirModalGasto();
                const sel = document.getElementById('select-cuenta');
                if(sel) sel.value = cuentaId;
                setTipoMovimiento('EGRESO');
            }

            function abrirModalGastoTC() {
                const tcs = cuentasData.filter(c => c.tipo === 'CREDITO');
                if(tcs.length === 0) {
                    if(confirm("Aún no tienes registrada una Tarjeta de Crédito. ¿Deseas agregar una ahora?")) {
                        abrirModalNuevaTarjeta();
                    }
                    return;
                }
                abrirModalGasto();
                const sel = document.getElementById('select-cuenta');
                if(sel) sel.value = tcs[0].id;
                setTipoMovimiento('EGRESO');
            }

            function abrirModalNuevaCuenta() {
                document.getElementById('modal-nueva-cuenta').classList.remove('hidden');
                adaptarFormularioCuenta();
                document.getElementById('nueva-cuenta-nombre').focus();
            }
            function cerrarModalNuevaCuenta() {
                document.getElementById('modal-nueva-cuenta').classList.add('hidden');
                document.getElementById('nueva-cuenta-nombre').value = '';
                document.getElementById('nueva-cuenta-cupo-total').value = '';
                document.getElementById('nueva-cuenta-cupo-disponible').value = '';
                document.getElementById('nueva-cuenta-saldo').value = '';
            }

            async function guardarNuevaCuenta() {
                const nombre = document.getElementById('nueva-cuenta-nombre').value.trim();
                const tipo = document.getElementById('nueva-cuenta-tipo').value;

                if(!nombre) {
                    alert("Ingresa el nombre del instrumento");
                    return;
                }

                let payload = { nombre: nombre, tipo: tipo };
                if(tipo === 'CREDITO') {
                    const cupoTot = parseFloat(document.getElementById('nueva-cuenta-cupo-total').value) || 0;
                    const cupoDisp = parseFloat(document.getElementById('nueva-cuenta-cupo-disponible').value) || 0;
                    payload.cupo_total = cupoTot;
                    payload.cupo_disponible = cupoDisp;
                } else {
                    payload.saldo_actual = parseFloat(document.getElementById('nueva-cuenta-saldo').value) || 0;
                    payload.tasa_ea = (tipo === 'ALTO_RENDIMIENTO') ? 12.5 : 0;
                }

                try {
                    const res = await fetch('/api/v1/cuentas', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    if(res.ok) {
                        cerrarModalNuevaCuenta();
                        fetchDashboard();
                    } else {
                        alert("Error al guardar cuenta.");
                    }
                } catch(e) {
                    alert("Error de conexión.");
                }
            }

            function abrirModalEditarCuenta(id) {
                const c = cuentasData.find(x => x.id == id);
                if(!c) return;

                document.getElementById('edit-cuenta-id').value = c.id;
                document.getElementById('edit-nombre-input').value = c.nombre;
                document.getElementById('edit-nombre-cuenta').innerText = c.nombre;
                document.getElementById('edit-tipo-cuenta').innerText = c.tipo;

                const contSaldo = document.getElementById('edit-container-saldo');
                const contCupo = document.getElementById('edit-container-cupo');

                if(c.tipo === 'CREDITO') {
                    contSaldo.classList.add('hidden');
                    contCupo.classList.remove('hidden');
                    document.getElementById('edit-cupo-total').value = c.cupo_total || 0;
                    document.getElementById('edit-cupo-disponible').value = c.cupo_disponible !== undefined ? c.cupo_disponible : Math.max(0, (c.cupo_total || 0) - (c.saldo_actual || 0));
                } else {
                    contSaldo.classList.remove('hidden');
                    contCupo.classList.add('hidden');
                    document.getElementById('edit-saldo').value = c.saldo_actual || 0;
                }

                document.getElementById('modal-editar-cuenta').classList.remove('hidden');
            }
            function cerrarModalEditarCuenta() {
                document.getElementById('modal-editar-cuenta').classList.add('hidden');
            }

            async function guardarEdicionSaldo() {
                const id = document.getElementById('edit-cuenta-id').value;
                const c = cuentasData.find(x => x.id == id);
                if(!c) return;

                const nuevoNombre = document.getElementById('edit-nombre-input').value.trim();
                let payload = { nombre: nuevoNombre || undefined };

                if(c.tipo === 'CREDITO') {
                    payload.cupo_total = parseFloat(document.getElementById('edit-cupo-total').value) || 0;
                    payload.cupo_disponible = parseFloat(document.getElementById('edit-cupo-disponible').value) || 0;
                } else {
                    payload.saldo_actual = parseFloat(document.getElementById('edit-saldo').value) || 0;
                }

                try {
                    await fetch('/api/v1/cuentas/' + id, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    cerrarModalEditarCuenta();
                    fetchDashboard();
                } catch(e) {
                    alert("Error al actualizar cuenta.");
                }
            }

            async function eliminarCuentaActual() {
                const id = document.getElementById('edit-cuenta-id').value;
                if(!confirm("¿Seguro que deseas eliminar esta cuenta y sus registros?")) return;
                try {
                    await fetch('/api/v1/cuentas/' + id, { method: 'DELETE' });
                    cerrarModalEditarCuenta();
                    fetchDashboard();
                } catch(e) {
                    alert("Error al eliminar.");
                }
            }

            // ==========================================
            // GASTOS FIJOS
            // ==========================================
            function setEstadoNuevoFijo(cubierto) {
                nuevoFijoPagado = cubierto;
                const btnCubierto = document.getElementById('btn-fijo-cubierto');
                const btnPendiente = document.getElementById('btn-fijo-pendiente');
                const ayuda = document.getElementById('ayuda-estado-fijo');
                if(!btnCubierto || !btnPendiente) return;
                if(cubierto) {
                    btnCubierto.className = 'py-2.5 px-2 rounded-xl text-[11px] font-bold bg-[#30D158]/20 text-[#30D158] border border-[#30D158]/40 transition';
                    btnPendiente.className = 'py-2.5 px-2 rounded-xl text-[11px] font-bold bg-[#000000] text-[#8E8E93] border border-white/10 transition';
                    if(ayuda) ayuda.innerText = '✓ No se descontará de tu saldo disponible actual porque ya fue cubierto.';
                } else {
                    btnPendiente.className = 'py-2.5 px-2 rounded-xl text-[11px] font-bold bg-[#FF9F0A]/20 text-[#FF9F0A] border border-[#FF9F0A]/40 transition';
                    btnCubierto.className = 'py-2.5 px-2 rounded-xl text-[11px] font-bold bg-[#000000] text-[#8E8E93] border border-white/10 transition';
                    if(ayuda) ayuda.innerText = '⏳ Se apartará y descontará de tu saldo disponible para proteger este pago.';
                }
            }

            function abrirModalNuevoGastoFijo() {
                setEstadoNuevoFijo(true);
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
                    alert('Por favor ingresa un concepto y monto válido.');
                    return;
                }

                try {
                    const res = await fetch('/api/v1/gastos-fijos', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            nombre: nombre, 
                            monto: monto, 
                            dia_pago: diaPago,
                            pagado_este_mes: nuevoFijoPagado
                        })
                    });
                    if(res.ok) {
                        cerrarModalNuevoGastoFijo();
                        fetchDashboard();
                    } else {
                        alert('Error al guardar gasto fijo.');
                    }
                } catch(e) {
                    alert('Error de conexión.');
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

            // ==========================================
            // MODAL GASTO MANUAL
            // ==========================================
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
                    btnEgreso.className = 'py-2.5 rounded-xl text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/50';
                    btnIngreso.className = 'py-2.5 rounded-xl text-xs font-bold bg-[#2C2C2E] text-[#8E8E93] border border-white/5';
                } else {
                    btnIngreso.className = 'py-2.5 rounded-xl text-xs font-bold bg-[#30D158]/20 text-[#30D158] border border-[#30D158]/50';
                    btnEgreso.className = 'py-2.5 rounded-xl text-xs font-bold bg-[#2C2C2E] text-[#8E8E93] border border-white/5';
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

                try {
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
                    fetchDashboard();
                } catch(e) {
                    alert('Error al registrar movimiento.');
                }
            }

            // ==========================================
            // NAVEGACIÓN ENTRE TABS
            // ==========================================
            let tabActual = 'billetera';

            function cambiarTab(tab) {
                tabActual = tab;
                const tabs = ['billetera', 'movimientos', 'cuentas', 'ajustes'];
                const titulos = {
                    'billetera': 'Billetera',
                    'movimientos': 'Movimientos',
                    'cuentas': 'Cuentas',
                    'ajustes': 'Ajustes'
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
                        if (btnEl) btnEl.className = 'flex flex-col items-center text-[#0A84FF] py-1 transition-colors';
                    } else {
                        if (viewEl) viewEl.classList.add('hidden');
                        if (btnEl) btnEl.className = 'flex flex-col items-center text-[#8E8E93] hover:text-white py-1 transition-colors';
                    }
                });

                window.scrollTo({ top: 0, behavior: 'smooth' });

                if (tab === 'ajustes') {
                    cargarDatosPerfilAjustes();
                }
            }

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
                    const elWebhook = document.getElementById('url-webhook-endpoint');
                    if(elWebhook) elWebhook.value = origin + '/api/v1/webhooks/ios-shortcut';
                } catch(e) {
                    console.error("Error al cargar perfil:", e);
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
                        alert('✓ ¡Ajustes de nómina guardados correctamente!');
                        fetchDashboard();
                    }
                } catch(e) {
                    alert('Error al guardar ajustes.');
                }
            }

            function copiarUrlWebhook() {
                const input = document.getElementById('url-webhook-endpoint');
                navigator.clipboard.writeText(input.value).then(() => {
                    alert('✓ ¡URL copiada! Pégala en Atajos de Apple.');
                }).catch(() => {
                    input.select();
                    document.execCommand('copy');
                    alert('✓ ¡URL copiada!');
                });
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

            // ==========================================
            // SINCRONIZACIÓN Y RECARGA AUTOMÁTICA
            // ==========================================
            async function fetchDashboard() {
                try {
                    const res = await fetch('/api/v1/metricas/dashboard');
                    if(!res.ok) return;
                    const data = await res.json();
                    aplicarDatosDashboard(data);
                    localStorage.setItem('aurea_dashboard_cache', JSON.stringify(data));
                } catch(e) {
                    console.warn("Conexión con servidor lenta o en espera", e);
                }
            }

            function recargarDatos() {
                fetchDashboard();
            }

            // Inicialización al cargar PWA
            const cacheInicial = localStorage.getItem('aurea_dashboard_cache');
            if(cacheInicial) {
                try { aplicarDatosDashboard(JSON.parse(cacheInicial)); } catch(e) {}
            }

            inicializarSeguridad();
            cargarDatosPerfilAjustes();
            setInterval(() => { if(sesionAutenticada) fetchDashboard(); }, 8000);

            document.addEventListener('visibilitychange', () => {
                if (!document.hidden && sesionAutenticada) fetchDashboard();
            });
            window.addEventListener('focus', () => {
                if(sesionAutenticada) fetchDashboard();
            });
        </script>
    </body>
    </html>
    """
    return html_content
