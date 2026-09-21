import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from backend.app.database import engine, Base
from backend.app.api.v1.api import api_router
from backend.app.seed import seed_data

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

from contextlib import asynccontextmanager

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
    Vista previa interactiva del Dashboard Móvil simulando un iPhone.
    Permite probar el semáforo diario, las cuentas en COP, y simular pagos con Apple Pay o SMS.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AUREA - Finanzas Personales</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background: #0B0F19; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            .ios-glass { background: rgba(22, 27, 46, 0.85); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08); }
            .glow-gold { box-shadow: 0 0 25px rgba(245, 158, 11, 0.25); }
        </style>
    </head>
    <body class="text-slate-100 flex justify-center min-h-screen p-2 sm:p-6">
        <div class="w-full max-w-md bg-[#0F172A] rounded-[44px] shadow-2xl border-4 border-slate-800 p-6 flex flex-col justify-between overflow-hidden relative">
            
            <!-- Dynamic Island / Header iPhone -->
            <div class="w-full flex flex-col items-center mb-4">
                <div class="w-28 h-5 bg-black rounded-full mb-3 flex items-center justify-end px-3">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                </div>
                <div class="w-full flex justify-between items-center">
                    <div>
                        <span class="text-xs font-semibold uppercase tracking-widest text-amber-400">AUREA • COP</span>
                        <h1 class="text-2xl font-black text-white">Mi Billetera</h1>
                    </div>
                    <a href="/docs" target="_blank" class="px-3 py-1.5 rounded-full text-xs font-bold bg-slate-800 text-amber-300 border border-amber-500/30 hover:bg-slate-700 transition">
                        <i class="fa-solid fa-code mr-1"></i> Swagger API
                    </a>
                </div>
            </div>

            <!-- Semáforo Dinámico Mensual -->
            <div id="semaforo-card" class="ios-glass rounded-3xl p-5 mb-4 glow-gold relative overflow-hidden transition-all">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <span class="text-xs font-medium text-slate-400 uppercase">Semáforo de Gasto Diario</span>
                        <div class="text-2xl font-black text-emerald-400 mt-0.5" id="disponible-hoy">$ 0 COP</div>
                    </div>
                    <span id="badge-color" class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                        VERDE
                    </span>
                </div>
                <p id="mensaje-guia" class="text-xs text-slate-300 leading-relaxed">Cargando métricas de tu nómina mensual...</p>
                
                <div class="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-slate-700/50 text-xs">
                    <div>
                        <span class="text-slate-400 block">Días restantes del mes</span>
                        <span id="dias-restantes" class="font-bold text-white text-sm">-</span>
                    </div>
                    <div>
                        <span class="text-slate-400 block">Límite diario sugerido</span>
                        <span id="limite-diario" class="font-bold text-amber-300 text-sm">-</span>
                    </div>
                </div>
            </div>

            <!-- Rendimiento Cuentas Alto Rendimiento (Nu Colombia) -->
            <div class="ios-glass rounded-2xl p-4 mb-4 border border-violet-500/30 bg-violet-950/20">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl bg-violet-600/30 flex items-center justify-center text-violet-400 text-lg">
                            <i class="fa-solid fa-arrow-trend-up"></i>
                        </div>
                        <div>
                            <span class="text-[11px] font-bold uppercase tracking-wider text-violet-300">Rendimientos Nu (12.5% E.A.)</span>
                            <div class="text-sm font-black text-white" id="rendimiento-diario">+ $ 0 COP hoy</div>
                        </div>
                    </div>
                    <span class="text-[11px] text-violet-300 font-semibold bg-violet-900/50 px-2.5 py-1 rounded-lg">Automático</span>
                </div>
            </div>

            <!-- Cuentas & Instrumentos Financieros -->
            <div class="mb-4">
                <div class="flex justify-between items-center mb-2 px-1">
                    <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Mis Instrumentos</span>
                    <span class="text-[11px] text-slate-500">4 Activos</span>
                </div>
                <div id="cuentas-list" class="space-y-2 max-h-48 overflow-y-auto pr-1">
                    <!-- Dinámico -->
                </div>
            </div>

            <!-- Botones de Prueba Rápida Atajos iOS -->
            <div class="mb-4 bg-slate-900/90 rounded-2xl p-3 border border-slate-800">
                <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-2 text-center">
                    <i class="fa-brands fa-apple mr-1"></i> Simular Ingesta de Atajos iOS
                </span>
                <div class="grid grid-cols-2 gap-2">
                    <button onclick="simularApplePay()" class="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-bold text-xs py-2 px-3 rounded-xl transition shadow-lg flex items-center justify-center gap-1.5">
                        <i class="fa-brands fa-apple"></i> Apple Pay
                    </button>
                    <button onclick="simularRetiroSMS()" class="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold text-xs py-2 px-3 rounded-xl transition shadow-lg flex items-center justify-center gap-1.5">
                        <i class="fa-solid fa-money-bill-transfer"></i> Retiro Cajero
                    </button>
                </div>
            </div>

            <!-- Barra de Navegación Inferior Estilo iOS -->
            <div class="w-full bg-slate-900/95 border border-slate-800 rounded-3xl p-3 flex justify-around items-center">
                <button class="text-amber-400 flex flex-col items-center">
                    <i class="fa-solid fa-wallet text-lg"></i>
                    <span class="text-[10px] font-semibold mt-1">Billetera</span>
                </button>
                <button onclick="recargarDatos()" class="text-slate-400 hover:text-white flex flex-col items-center">
                    <i class="fa-solid fa-arrows-rotate text-lg"></i>
                    <span class="text-[10px] font-semibold mt-1">Refrescar</span>
                </button>
                <a href="/docs" target="_blank" class="text-slate-400 hover:text-white flex flex-col items-center">
                    <i class="fa-solid fa-server text-lg"></i>
                    <span class="text-[10px] font-semibold mt-1">API REST</span>
                </a>
            </div>

        </div>

        <script>
            function formatearCOP(monto) {
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
                    if(data.color === 'VERDE') {
                        badge.className = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/40';
                    } else if(data.color === 'AMARILLO') {
                        badge.className = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-500/20 text-amber-300 border border-amber-500/40';
                    } else {
                        badge.className = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-500/20 text-rose-300 border border-rose-500/40';
                    }
                } catch (e) {
                    console.error("Error al cargar semáforo", e);
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
                    const cuentas = await res.json();
                    const container = document.getElementById('cuentas-list');
                    container.innerHTML = '';
                    cuentas.forEach(c => {
                        let icon = 'fa-credit-card';
                        let color = 'text-blue-400';
                        if(c.tipo === 'ALTO_RENDIMIENTO') { icon = 'fa-piggy-bank'; color = 'text-purple-400'; }
                        if(c.tipo === 'EFECTIVO') { icon = 'fa-money-bill-wave'; color = 'text-emerald-400'; }
                        if(c.tipo === 'CREDITO') { icon = 'fa-regular fa-credit-card'; color = 'text-amber-400'; }

                        const card = document.createElement('div');
                        card.className = 'ios-glass p-3 rounded-2xl flex items-center justify-between';
                        card.innerHTML = `
                            <div class="flex items-center gap-2.5">
                                <div class="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center ${color} text-sm">
                                    <i class="fa-solid ${icon}"></i>
                                </div>
                                <div>
                                    <span class="text-xs font-semibold text-white block">${c.nombre}</span>
                                    <span class="text-[10px] text-slate-400 uppercase tracking-wider">${c.tipo}</span>
                                </div>
                            </div>
                            <span class="text-xs font-bold ${c.tipo === 'CREDITO' ? 'text-amber-400' : 'text-emerald-400'}">
                                ${formatearCOP(c.saldo_actual)}
                            </span>
                        `;
                        container.appendChild(card);
                    });
                } catch(e) {
                    console.error("Error cuentas", e);
                }
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
                alert('¡Pago de ' + formatearCOP(monto) + ' con Apple Pay procesado por Webhook!');
                recargarDatos();
            }

            async function simularRetiroSMS() {
                const sms = "Bancolombia le informa retiro por $100.000 en CAJERO EXITO a las 11:00. 21/09/2026";
                const res = await fetch('/api/v1/webhooks/ios-shortcut', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        medio: 'SMS',
                        texto_sms: sms
                    })
                });
                const data = await res.json();
                alert('SMS procesado: ' + data.mensaje);
                recargarDatos();
            }

            function recargarDatos() {
                cargarSemaforo();
                cargarRendimientos();
                cargarCuentas();
            }

            recargarDatos();
        </script>
    </body>
    </html>
    """
    return html_content
