import streamlit as st
import pandas as pd
import math
import tempfile
import os
from fpdf import FPDF
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configuration
st.set_page_config(
    page_title="Novelec - Calculadora Solar Aislada Interactiva",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="collapsed" # Collapsed by default for a clean mobile-first view
)

# Estilo corporativo personalizado (Identidad Novelec) con mejoras para móvil (touch-friendly)
st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }
    .stApp header {
        background-color: #002f54;
    }
    div.stButton > button:first-child {
        background-color: #002f54;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: bold;
        width: 100%; /* Botones grandes y fáciles de pulsar en móvil */
        font-size: 1.1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    div.stButton > button:first-child:hover {
        background-color: #004b7c;
        color: white;
    }
    h1, h2, h3 {
        color: #002f54;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .metric-card {
        background-color: white;
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        border-left: 6px solid #002f54;
        margin-bottom: 0.8rem;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: bold;
        color: #002f54;
        margin-top: 0.2rem;
    }
    .metric-title {
        font-size: 0.85rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    /* Estilos para que los inputs no queden pegados y sean touch-friendly */
    .stNumberInput div[data-baseweb="input"] {
        padding: 2px 0px;
    }
    /* Añadir un aviso visual de que la configuración está arriba en móvil */
    .mobile-notice {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 0.8rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        border-left: 4px solid #0284c7;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado principal de marca (Logotipo oficial de Novelec en formato vectorial SVG para funcionamiento 100% offline y pantallas HD)
st.markdown("""
<div style="text-align: left; margin-bottom: 1.5rem;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450 110" width="320" style="max-width: 100%; height: auto;">
  <!-- Icono corporativo oficial Novelec: Hoja/escudo azul con la 'n' en espacio negativo -->
  <path d="M 15,15 H 70 A 25,25 0 0,1 95,40 V 70 A 25,25 0 0,1 70,95 H 40 A 25,25 0 0,1 15,70 Z" fill="#004b7c" />
  <!-- La 'n' blanca interior perfectamente delineada y estilizada -->
  <path d="M 38,72 V 48 A 12,12 0 0,1 62,48 V 72" fill="none" stroke="#ffffff" stroke-width="13" stroke-linecap="round" stroke-linejoin="round" />
  
  <!-- Texto de la marca: novelec en tipografía corporativa sans-serif moderna -->
  <text x="115" y="62" font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif" font-weight="700" font-size="50" fill="#002f54" letter-spacing="-1.5">novelec</text>
  
  <!-- Slogan oficial en catalán: El valor del servei -->
  <text x="115" y="88" font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif" font-size="18" font-weight="500" fill="#64748b" letter-spacing="0.5">El valor del servei</text>
</svg>
</div>
""", unsafe_allow_html=True)
st.title("☀️ Calculadora Solar Aislada Inteligente")
st.markdown("**Diseño y Sizing de Ingeniería Avanzada para Instalaciones Off-Grid - Novelec Servicios Técnicos**")
st.markdown("---")

# Inicialización de bases de datos
PANELS_DB = {
    "LONGi LR7-54HVB-495M (495Wp)": {"p_pico": 495, "voc": 39.5, "vmp": 32.9, "isc": 14.1, "imp": 15.05, "ref": "LR7-54HVB-495M", "desc": "Panel solar LONGi HPBC 2.0 Full-Black"},
    "LONGi LR7-60HVH-545M (545Wp)": {"p_pico": 545, "voc": 44.98, "vmp": 37.88, "isc": 15.35, "imp": 14.39, "ref": "LR7-60HVH-545M", "desc": "Panel solar LONGi alta eficiencia 24.8% BC"},
    "LONGi LR7-60HVH-560M (560Wp)": {"p_pico": 560, "voc": 45.4, "vmp": 38.2, "isc": 15.6, "imp": 14.66, "ref": "LR7-60HVH-560M", "desc": "Panel solar LONGi alta eficiencia 24.8% BC"}
}

INVERTER_DB = {
    "PMP482305010": {"nombre": "Victron MultiPlus-II 48/3000/35-32", "pvp": 624.0, "current": 100, "charger_current": 35},
    "PMP482505012": {"nombre": "Victron MultiPlus-II 48/5000/70-50", "pvp": 844.0, "current": 200, "charger_current": 70},
    "PMP482805000": {"nombre": "Victron MultiPlus-II 48/8000/110-100", "pvp": 1551.0, "current": 300, "charger_current": 110},
    "PMP483105000": {"nombre": "Victron MultiPlus-II 48/10000/140-100", "pvp": 1853.0, "current": 400, "charger_current": 140},
    "PMP483150000": {"nombre": "Victron MultiPlus-II 48/15000/200-100", "pvp": 2585.0, "current": 500, "charger_current": 200}
}

REGULATOR_DB = {
    "SCC115035210": {
        "nombre": "Victron SmartSolar MPPT 150/35 (12/24/48V, 35A)",
        "pvp": 197.00,
        "max_current": 35,
        "max_voc": 150,
        "max_power": 2000,
        "max_isc": 40,
        "min_voc": 0
    },
    "SCC115045212": {
        "nombre": "Victron SmartSolar MPPT 150/45 (12/24/48V, 45A)",
        "pvp": 233.00,
        "max_current": 45,
        "max_voc": 150,
        "max_power": 2600,
        "max_isc": 50,
        "min_voc": 0
    },
    "SCC115060211": {
        "nombre": "Victron SmartSolar MPPT 150/60-Tr (12/24/48V, 60A)",
        "pvp": 375.00,
        "max_current": 60,
        "max_voc": 150,
        "max_power": 3400,
        "max_isc": 50,
        "min_voc": 0
    },
    "SCC115070411": {
        "nombre": "Victron SmartSolar MPPT 150/70-Tr VE.Can",
        "pvp": 443.00,
        "max_current": 70,
        "max_voc": 150,
        "max_power": 4000,
        "max_isc": 50,
        "min_voc": 0
    },
    "SCC115085411": {
        "nombre": "Victron SmartSolar MPPT 150/85-Tr VE.Can",
        "pvp": 483.00,
        "max_current": 85,
        "max_voc": 150,
        "max_power": 4900,
        "max_isc": 70,
        "min_voc": 0
    },
    "SCC115110411": {
        "nombre": "Victron SmartSolar MPPT 150/100-Tr VE.Can",
        "pvp": 552.00,
        "max_current": 100,
        "max_voc": 150,
        "max_power": 5800,
        "max_isc": 70,
        "min_voc": 0
    },
    "SCC125060221": {
        "nombre": "Victron SmartSolar MPPT 250/60-Tr",
        "pvp": 443.00,
        "max_current": 60,
        "max_voc": 250,
        "max_power": 3400,
        "max_isc": 50,
        "min_voc": 0
    },
    "SCC125070421": {
        "nombre": "Victron SmartSolar MPPT 250/70-Tr VE.Can",
        "pvp": 545.00,
        "max_current": 70,
        "max_voc": 250,
        "max_power": 4000,
        "max_isc": 50,
        "min_voc": 0
    },
    "SCC125085411": {
        "nombre": "Victron SmartSolar MPPT 250/85-Tr VE.Can",
        "pvp": 586.00,
        "max_current": 85,
        "max_voc": 250,
        "max_power": 4900,
        "max_isc": 70,
        "min_voc": 0
    },
    "SCC125110412": {
        "nombre": "Victron SmartSolar MPPT 250/100-Tr VE.Can",
        "pvp": 654.00,
        "max_current": 100,
        "max_voc": 250,
        "max_power": 5800,
        "max_isc": 70,
        "min_voc": 0
    },
    "SCC145110512": {
        "nombre": "Victron SmartSolar MPPT RS 450/100-MC4 (2 seguidores de alta tensión)",
        "pvp": 1182.00,
        "max_current": 100,
        "max_voc": 450,
        "max_power": 11500,
        "max_isc": 50,
        "min_voc": 120
    },
    "SCC145120512": {
        "nombre": "Victron SmartSolar MPPT RS 450/200-MC4 (2 seguidores de alta tensión)",
        "pvp": 2069.00,
        "max_current": 200,
        "max_voc": 450,
        "max_power": 23000,
        "max_isc": 50,
        "min_voc": 120
    }
}

MEGA_FUSES = [
    {"rating": 60, "ref": "CIP138060020", "name": "Victron MEGA-fuse 60A/80V para CC (Paquete de 5 uds)"},
    {"rating": 80, "ref": "CIP138080020", "name": "Victron MEGA-fuse 80A/80V para CC (Paquete de 5 uds)"},
    {"rating": 100, "ref": "CIP138100020", "name": "Victron MEGA-fuse 100A/80V para CC (Paquete de 5 uds)"},
    {"rating": 125, "ref": "CIP138125020", "name": "Victron MEGA-fuse 125A/80V para CC (Paquete de 5 uds)"},
    {"rating": 150, "ref": "CIP138150020", "name": "Victron MEGA-fuse 150A/80V para CC (Paquete de 5 uds)"},
    {"rating": 200, "ref": "CIP138200020", "name": "Victron MEGA-fuse 200A/80V para CC (Paquete de 5 uds)"},
    {"rating": 250, "ref": "CIP138250020", "name": "Victron MEGA-fuse 250A/80V para CC (Paquete de 5 uds)"},
    {"rating": 300, "ref": "CIP138300020", "name": "Victron MEGA-fuse 300A/80V para CC (Paquete de 5 uds)"},
    {"rating": 400, "ref": "CIP138400020", "name": "Victron MEGA-fuse 400A/80V para CC (Paquete de 5 uds)"},
    {"rating": 500, "ref": "CIP138500020", "name": "Victron MEGA-fuse 500A/80V para CC (Paquete de 5 uds)"}
]

def select_victron_fuse(target_current, apply_safety_factor=True):
    req = target_current * 1.25 if apply_safety_factor else target_current
    for f in MEGA_FUSES:
        if f["rating"] >= req:
            return f
    return MEGA_FUSES[-1]


# ────────────────────────────────────────────────────────────────────────
# VERIFICACIÓN DE SEGURIDAD ELÉCTRICA Y RIESGOS EN REGULADORES DE CARGA
# ────────────────────────────────────────────────────────────────────────

def check_regulator_safety(regulator_ref, total_pv_power_real, S_series, P_parallel, panel_voc, panel_isc, temp_factor=1.078):
    dangers = []
    warnings = []
    
    reg_info = REGULATOR_DB.get(regulator_ref, REGULATOR_DB["SCC125110412"])
    reg_name = reg_info["nombre"].split(" (")[0]
    max_voc = float(reg_info.get("max_voc", 250.0))
    max_isc = float(reg_info.get("max_isc", 70.0))
    max_power = float(reg_info.get("max_power", 5800.0))
    min_voc = float(reg_info.get("min_voc", 0.0))
    max_current = reg_info.get("max_current", 100)
    
    string_voc_stc = S_series * panel_voc
    string_voc_temp = string_voc_stc * temp_factor if S_series > 0 else 0
    total_isc = P_parallel * panel_isc
    
    # 1. Minimum start voltage check
    if min_voc > 0 and string_voc_stc < min_voc and total_pv_power_real > 0:
        dangers.append(
            f"🛑 **El Regulador NO Arrancará:** La tensión nominal solar (**{string_voc_stc:.1f} V**) es inferior "
            f"al umbral mínimo de arranque de **{min_voc:.0f} VCC** del {reg_name}. "
            f"Con cadenas de solo {S_series} paneles en serie, el regulador jamás se activará."
        )
        
    # 2. Maximum Voc voltage check
    if string_voc_temp > max_voc:
        dangers.append(
            f"💥 **Riesgo de Destrucción Irreversible:** La tensión Voc de string ({S_series} en serie) "
            f"corregida por temperatura (-5 ºC en Girona) es de **{string_voc_temp:.1f} V**, lo que supera el límite absoluto de **{max_voc:.0f} V** "
            f"del {reg_name}. ¡Conectar {S_series} paneles en serie destruirá el regulador y anulará la garantía!"
        )
    elif string_voc_temp > max_voc - 15.0 and max_voc <= 250.0:
        warnings.append(
            f"⚠️ **Tensión de string elevada:** La tensión estimada a baja temperatura (-5 ºC) es de **{string_voc_temp:.1f} V**. "
            f"Está muy cerca del límite máximo de {max_voc:.0f} V del equipo."
        )
        
    # 3. Maximum Isc short-circuit current check
    if total_isc > max_isc:
        dangers.append(
            f"🔥 **Sobrecorriente CC Crítica:** La corriente total de cortocircuito de los {P_parallel} strings en paralelo "
            f"es de **{total_isc:.2f} A**, superando el límite máximo admitido de **{max_isc:.0f} A** del {reg_name}. Existe riesgo de arco eléctrico."
        )
        
    # 4. Power / Clipping check
    if total_pv_power_real > max_power * 1.35:
        warnings.append(
            f"⚠️ **Exceso de Potencia FV:** La potencia total del campo solar (**{total_pv_power_real/1000:.2f} kWp**) "
            f"supera holgadamente la capacidad recomendada ({max_power/1000:.1f} kWp) para el {reg_name}."
        )
    elif max_power < total_pv_power_real <= max_power * 1.35 and string_voc_temp <= max_voc and total_isc <= max_isc:
        warnings.append(
            f"ℹ️ **Configuración Totalmente Compatible (Victron MPPT Calculator):** El {reg_name} admite los "
            f"**{total_pv_power_real/1000:.2f} kWp** en agrupación **{S_series}S{P_parallel}P** ({string_voc_temp:.1f}V Voc a -5ºC, {total_isc:.1f}A Isc). "
            f"El regulador limitará la carga a {max_current}A (~{(max_current*58)/1000:.1f} kW en batería a 48V), maximizando el rendimiento en invierno de forma 100% segura."
        )
        
    return dangers, warnings

def auto_select_mppt(total_pv_power_real, total_panels, panel_voc, panel_vmp, panel_isc, panel_imp):
    for ref, reg in REGULATOR_DB.items():
        S, P, voc_stc, voc_cold, vmp_stc, isc_total, imp_total, candidates = get_mppt_electrical_grouping(
            total_panels, panel_voc, panel_vmp, panel_isc, panel_imp, ref
        )
        has_valid_grouping = any(c['is_valid'] for c in candidates)
        if not has_valid_grouping:
            continue
        
        required_current = total_pv_power_real / 52.0
        if reg['max_current'] >= required_current or total_pv_power_real <= reg['max_power'] * 1.30:
            return ref
            
    return 'SCC145120512' 

def get_mppt_electrical_grouping(total_panels, panel_voc, panel_vmp, panel_isc, panel_imp, regulator_ref, temp_factor=1.078):
    if total_panels <= 0 or panel_voc <= 0:
        return 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, []
    
    max_voc_limit = 250.0 if regulator_ref == "SCC125110412" else 450.0
    min_voc_limit = 0.0 if regulator_ref == "SCC125110412" else 120.0
    max_isc_limit = 70.0 if regulator_ref == "SCC125110412" else 50.0
    
    candidates = []
    for S in range(1, total_panels + 1):
        if total_panels % S == 0:
            P = total_panels // S
            voc_stc = S * panel_voc
            voc_cold = voc_stc * temp_factor
            vmp_stc = S * panel_vmp
            isc_total = P * panel_isc
            imp_total = P * panel_imp
            
            is_valid_voc_max = (voc_cold <= max_voc_limit)
            is_valid_voc_min = (voc_stc >= min_voc_limit)
            is_valid_isc = (isc_total <= max_isc_limit)
            
            is_valid = is_valid_voc_max and is_valid_voc_min and is_valid_isc
            
            candidates.append({
                'S': S,
                'P': P,
                'voc_stc': voc_stc,
                'voc_cold': voc_cold,
                'vmp_stc': vmp_stc,
                'isc_total': isc_total,
                'imp_total': imp_total,
                'is_valid': is_valid
            })
            
    valid_candidates = [c for c in candidates if c['is_valid']]
    if valid_candidates:
        best = max(valid_candidates, key=lambda c: c['S'])
    else:
        safe_voc = [c for c in candidates if c['voc_cold'] <= max_voc_limit]
        if safe_voc:
            best = max(safe_voc, key=lambda c: c['S'])
        else:
            best = min(candidates, key=lambda c: c['voc_cold'])
            
    return (
        best['S'],
        best['P'],
        best['voc_stc'],
        best['voc_cold'],
        best['vmp_stc'],
        best['isc_total'],
        best['imp_total'],
        candidates
    )


# ────────────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES: GENERACIÓN DE CROQUIS Y PDF (NOVELEC STANDARD)
# ────────────────────────────────────────────────────────────────────────

def generate_system_sketch(total_panels_configured, total_pv_power_real, batteries_qty, power_va, has_generator, regulator_ref, filename):
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.set_xlim(-0.5, 15.5)
    ax.set_ylim(-0.5, 4)
    ax.axis('off')
    
    def draw_block(x, y, w, h, title, subtitle, bg_color, text_color="white"):
        p = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08", facecolor=bg_color, edgecolor="none")
        ax.add_patch(p)
        ax.text(x + w/2, y + h*0.6, title, fontsize=7.5, fontweight='bold', color=text_color, ha='center', va='center')
        ax.text(x + w/2, y + h*0.25, subtitle, fontsize=6.5, color=text_color, ha='center', va='center')
        
    # 1. Panels Block
    draw_block(0, 2.0, 2.2, 0.9, "GENERACION SOL", f"{total_panels_configured} Placas LONGi\n({total_pv_power_real/1000:.2f} kWp)", "#0284c7")
    
    # 2. Gave CC Box Block
    draw_block(2.8, 2.0, 2.2, 0.9, "PROTECCIONES CC", "Caja Gave Solartec\n(Sobretensiones TII)", "#475569")
    
    # 3. MPPT Regulator Block
    reg_name = "SmartSolar MPPT" if regulator_ref == "SCC125110412" else "SmartSolar MPPT RS"
    draw_block(5.6, 2.0, 2.2, 0.9, "REGULADOR MPPT", f"Victron {reg_name}\n(Carga Inteligente)", "#ea580c")
    
    # 4. Lynx Power In CC Busbar
    draw_block(8.4, 1.0, 2.2, 0.9, "DISTRIBUCION CC", "Victron Lynx Power In\n(CC Centralizado)", "#334155")
    
    # 5. Batteries Block
    draw_block(5.6, 0.0, 2.2, 0.9, "ACUMULACION", f"{batteries_qty} Baterias TBB\n({batteries_qty*5.04:.1f} kWh)", "#002f54")
    
    # 6. Inverter Block
    inv_name = f"MultiPlus-II {power_va:.0f}VA"
    draw_block(11.2, 1.0, 2.2, 0.9, "INVERSOR / CARG.", f"Victron {inv_name}\n(48V a 230V CA)", "#1e3a8a")
    
    # 7. AC Loads Block
    draw_block(14.0, 1.0, 1.2, 0.9, "VIVIENDA", "Consumos\nCA 230V", "#16a34a")
    
    # 8. Generator Block (Optional)
    if has_generator == "Sí":
        draw_block(11.2, 2.8, 2.2, 0.7, "G. ELECTROGENO", "Grupo Auxiliar\n(Entrada AC-In)", "#dc2626")
        
    # Draw Arrows with custom markers
    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", lw=1.2, color="#64748b", mutation_scale=10))
        if label:
            if x1 == 12.3: # Vertical arrow
                ax.text(12.0, 2.35, "AC", fontsize=6, fontweight='bold', color="#475569", ha='right', va='center')
            else:
                ax.text((x1+x2)/2, (y1+y2)/2 + 0.15, label, fontsize=6, fontweight='bold', color="#475569", ha='center', va='center')
            
    # Connect Blocks
    draw_arrow(2.2, 2.45, 2.8, 2.45, "CC") # Panels -> Gave
    draw_arrow(5.0, 2.45, 5.6, 2.45, "CC") # Gave -> MPPT
    draw_arrow(7.8, 2.45, 8.4, 1.7, "CC") # MPPT -> Lynx (angle)
    draw_arrow(7.8, 0.45, 8.4, 1.2, "48V") # Batteries -> Lynx (angle)
    draw_arrow(10.6, 1.45, 11.2, 1.45, "48V") # Lynx -> Inverter
    draw_arrow(13.4, 1.45, 14.0, 1.45, "230V") # Inverter -> Loads
    
    if has_generator == "Sí":
        draw_arrow(12.3, 2.8, 12.3, 1.9, "AC") # Generator -> Inverter
        
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()

class NovelecPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.doc_title = "RESUMEN TÉCNICO Y PROPUESTA DE INSTALACIÓN"
        self.doc_subtitle = "Novelec Servicios Técnicos"

    def header(self):
        if self.page_no() == 1:
            self.set_fill_color(0, 47, 84) # Novelec Navy #002f54
            self.rect(0, 0, 210, 32, "F")
            self.set_text_color(255, 255, 255)
            self.set_font("helvetica", "B", 18)
            self.text(15, 14, "NOVELEC - SERVEIS TECNICS")
            self.set_font("helvetica", "I", 8.5)
            self.text(15, 20, "El valor del servei - Soluciones Fotovoltaicas Off-Grid")
            self.set_fill_color(2, 132, 199) # Novelec light blue #0284c7
            self.rect(170, 0, 40, 32, "F")
            self.set_text_color(255, 255, 255)
            self.set_font("helvetica", "B", 14)
            self.text(178, 18, "SOLAR")
            self.set_text_color(30, 41, 59) # Slate #1e293b
            self.set_y(38)
        else:
            self.set_fill_color(0, 47, 84) # Novelec Navy
            self.rect(0, 0, 210, 12, "F")
            self.set_text_color(255, 255, 255)
            self.set_font("helvetica", "B", 8)
            self.text(15, 8, "NOVELEC  |  Dossier Tecnico de Instalacion Aislada")
            self.set_text_color(30, 41, 59)
            self.set_y(18)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f"Pagina {self.page_no()} | Propuesta Fotovoltaica Novelec", align="C")

def generate_pdf_bytes(total_daily_energy, power_va, total_panels_configured, total_pv_power_real, batteries_qty, has_generator, selected_panel_name, roof_type, orientation, tilt, hsp, active_appliances, autonomy_days, dod_max, regulator_ref, regulator_name):
    pdf = NovelecPDF()
    pdf.add_page()
    
    # Title
    pdf.set_y(38)
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(0, 47, 84) # Novelec Navy
    pdf.cell(0, 8, "DOSSIER TECNICO: PROYECTO SOL-AISLADA", ln=1)
    pdf.set_font("helvetica", "I", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, "Ingenieria de Dimensionamiento Fotovoltaico y Presupuesto Tecnico", ln=1)
    pdf.ln(4)
    
    # Project Info Shaded Panel (Fixed Overlap!)
    box_y = pdf.get_y()
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(10, box_y, 190, 22, "F") # Shaded background rectangle
    
    # Text inside the shaded panel
    pdf.set_y(box_y + 3)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(30, 41, 59)
    
    pdf.cell(95, 5, f"  Tipo de Cubierta:  {roof_type}")
    pdf.cell(95, 5, f"  HSP Invierno (Girona):  {hsp:.1f} h")
    pdf.ln(5)
    pdf.cell(95, 5, f"  Orientacion:  {orientation}")
    pdf.cell(95, 5, f"  Rendimiento del Sistema:  85% (Fijo)")
    pdf.ln(5)
    pdf.cell(95, 5, f"  Inclinacion:  {tilt}")
    pdf.cell(95, 5, f"  Grupo Electrogeno Auxiliar:  {has_generator}")
    
    # Position cursor safely below the panel
    pdf.set_y(box_y + 26)
    
    # 1. Estimacion de Consumo Diario
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(0, 47, 84)
    pdf.cell(0, 8, "1. Estimacion de Consumo Diario", ln=1)
    pdf.ln(2)
    
    # Table headers
    pdf.set_fill_color(0, 47, 84) # Navy header
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 9)
    
    pdf.cell(80, 8, "  Receptor / Electrodomestico", fill=True)
    pdf.cell(25, 8, "Potencia (W)", fill=True, align="C")
    pdf.cell(20, 8, "Cant.", fill=True, align="C")
    pdf.cell(20, 8, "Horas/dia", fill=True, align="C")
    pdf.cell(45, 8, "Consumo (Wh/dia)", fill=True, align="R")
    pdf.ln(8)
    
    pdf.set_text_color(30, 41, 59)
    pdf.set_font("helvetica", "", 9)
    
    alt = False
    for app in active_appliances:
        if alt:
            pdf.set_fill_color(248, 250, 252)
        else:
            pdf.set_fill_color(255, 255, 255)
        
        # Strip or replace accented characters to be fully safe in Latin-1
        clean_name = app['Electrodoméstico'].replace("ó", "o").replace("é", "e").replace("á", "a").replace("í", "i").replace("ú", "u").replace("—", "-")
        pdf.cell(80, 6.5, f"  {clean_name}", fill=True)
        pdf.cell(25, 6.5, f"{app['Potencia (W)']:.0f} W", fill=True, align="C")
        pdf.cell(20, 6.5, f"{app['Cant.']:.0f}", fill=True, align="C")
        pdf.cell(20, 6.5, f"{app['Horas']:.2f} h", fill=True, align="C")
        pdf.cell(45, 6.5, f"{app['Potencia (W)']*app['Cant.']*app['Horas']:.2f} Wh ", fill=True, align="R")
        pdf.ln(6.5)
        alt = not alt
        
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(145, 7.5, "  ENERGIA TOTAL DIARIA REQUERIDA", fill=True)
    pdf.cell(45, 7.5, f"{total_daily_energy/1000:.3f} kWh ", fill=True, align="R")
    pdf.ln(7.5)
    
    pdf.cell(145, 7.5, "  POTENCIA SIMULTANEA DE INVERSION (Sim. Coeff = 0.7)", fill=True)
    pdf.cell(45, 7.5, f"{power_va:.0f} VA ", fill=True, align="R")
    pdf.ln(10)
    
    # Page 2
    pdf.add_page()
    
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(0, 47, 84)
    pdf.cell(0, 8, "2. Resultados del Dimensionamiento de Ingenieria", ln=1)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(30, 41, 59)
    
    pdf.set_fill_color(248, 250, 252)
    pdf.cell(90, 11, f"  Generacion Solar: {total_panels_configured} Placas LONGi ({total_pv_power_real/1000:.2f} kWp)", fill=True)
    pdf.cell(10, 11, "")
    pdf.cell(90, 11, f"  Acumulacion Litio: {batteries_qty} Baterias TBB ({batteries_qty*5.04:.2f} kWh)", fill=True)
    pdf.ln(14)
    
    pdf.cell(90, 11, f"  Inversor / Cargador: Victron MultiPlus-II {power_va:.0f} VA", fill=True)
    pdf.cell(10, 11, "")
    pdf.cell(90, 11, f"  Regulador Solar: {regulator_name.split(' (')[0]}", fill=True)
    pdf.ln(14)
    
    pdf.cell(90, 11, f"  Autonomia Garantizada: {autonomy_days} Dias (DoD: {dod_max*100:.0f}%)", fill=True)
    pdf.cell(10, 11, "")
    pdf.cell(90, 11, f"  Puesta a Tierra: Red Equipotencial CC", fill=True)
    pdf.ln(15)
    
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(0, 47, 84)
    pdf.cell(0, 8, "3. Esquema de Principio y Flujo de Energia (Croquis)", ln=1)
    pdf.ln(2)
    
    temp_dir = tempfile.gettempdir()
    croquis_path = os.path.join(temp_dir, "croquis_instalacion.png")
    generate_system_sketch(total_panels_configured, total_pv_power_real, batteries_qty, power_va, has_generator, regulator_ref, croquis_path)
    
    pdf.image(croquis_path, x=10, y=pdf.get_y(), w=190, h=95)
    pdf.ln(97)
    

    
    return bytes(pdf.output())


# Inicialización del Session State para electrodomésticos personalizados y configuración
if "custom_appliances" not in st.session_state:
    st.session_state.custom_appliances = []
if "manual_inverter" not in st.session_state:
    st.session_state.manual_inverter = "Automático (Recomendado)"
if "manual_regulator" not in st.session_state:
    st.session_state.manual_regulator = "Automático (Recomendado)"

# MÓVIL-FIRST: Los parámetros de diseño ya no están escondidos en la barra lateral.
# Ahora están en un Expander prominente en la página principal, eliminando la necesidad de la barra lateral.
with st.expander("⚙️ CONFIGURACIÓN DEL TEJADO Y PARÁMETROS DE DISEÑO", expanded=True):
    col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
    with col_c1:
        roof_type = st.selectbox(
            "Tipo de Cubierta",
            ["Inclinada Teja", "Inclinada Chapa (Sándwich)", "Plana"],
            key="config_roof_type"
        )
    with col_c2:
        orientation = st.selectbox(
            "Orientación",
            ["Sur", "Este", "Oeste"],
            key="config_orientation",
            disabled=(roof_type == "Plana")
        )
    with col_c3:
        tilt = st.selectbox(
            "Inclinación",
            ["5º", "7º", "10º", "15º", "30º", "45º"],
            index=3,
            key="config_tilt",
            disabled=(roof_type == "Plana")
        )

    system_efficiency = 0.85  # Rendimiento de sistema fijado al 85% para un dimensionamiento seguro
    col_c4, col_c5 = st.columns([1, 1])
    with col_c4:
        autonomy_days = st.slider("Días de Autonomía", 1, 5, 2, key="config_autonomy")
    with col_c5:
        dod_max = st.slider("DoD Máxima Baterías (%)", 50, 100, 90, key="config_dod") / 100.0

    col_c7, col_c8, col_c9 = st.columns([1, 1, 1])
    with col_c7:
        num_rows = st.number_input("Número de filas de paneles", min_value=1, max_value=10, value=3, key="config_rows")
    with col_c8:
        has_generator = st.selectbox("¿Existe Grupo Electrógeno?", ["No", "Sí"], key="config_generator")
    with col_c9:
        st.markdown("<div style='padding-top:25px;'></div>", unsafe_allow_html=True)
        # Matriz HSP d'hivern (Catalunya)
        hsp_matrix = {
            "5º": {"Sur": 2.0, "Este": 1.9, "Oeste": 1.9},
            "7º": {"Sur": 2.0, "Este": 1.8, "Oeste": 1.8},
            "10º": {"Sur": 2.0, "Este": 1.7, "Oeste": 1.7},
            "15º": {"Sur": 2.0, "Este": 1.6, "Oeste": 1.6},
            "30º": {"Sur": 2.5, "Este": 1.8, "Oeste": 1.8},
            "45º": {"Sur": 3.0, "Este": 2.0, "Oeste": 2.0}
        }
        if roof_type != "Plana":
            hsp = hsp_matrix[tilt][orientation]
        else:
            hsp = 2.0
            
        st.markdown(f"📊 **HSP Invierno:** `{hsp} h` (Diciembre)")

# Pestañas principales
tab1, tab2, tab3 = st.tabs(["📋 Consumos y Dimensionamiento", "🛠️ Resumen de Materiales (BOM)", "⚡ Manual de Instalación"])

with tab1:
    st.subheader("💡 Estimación de Consumo Diario")
    st.markdown("Activa los receptores de la vivienda y configura su cantidad y uso con controles táctiles optimizados:")

    # Base de datos de electrodomésticos agrupados por categorías para móvil (Con potencias actualizadas e interfaz touch-friendly)
    CATEGORIZED_DEFAULT_APPLIANCES = {
        "❄️ Climatización y Refrigeración": [
            {"name": "Nevera (Consumo medio integrado)", "w": 200, "qty": 1, "hours": 3.50},
            {"name": "Bomba de calor y aire (Inverter)", "w": 800, "qty": 1, "hours": 4.00},
            {"name": "Termo eléctrico (100l) — [1500W]", "w": 1500, "qty": 1, "hours": 1.50}
        ],
        "🍳 Cocina, Lavado y Agua": [
            {"name": "Bomba de agua de presión", "w": 700, "qty": 1, "hours": 0.50},
            {"name": "Cafetera Nespresso", "w": 1450, "qty": 1, "hours": 0.10},
            {"name": "Vitrocerámica", "w": 1500, "qty": 1, "hours": 0.50},
            {"name": "Microondas", "w": 800, "qty": 1, "hours": 0.20},
            {"name": "Lavadora (Prorrata diaria)", "w": 700, "qty": 1, "hours": 0.07}
        ],
        "🔌 Iluminación y Ocio": [
            {"name": "Iluminación LED general", "w": 10, "qty": 5, "hours": 4.00},
            {"name": "Ventiladores de techo con luz", "w": 50, "qty": 2, "hours": 6.00},
            {"name": "Televisor LED compacto", "w": 250, "qty": 1, "hours": 4.00},
            {"name": "Ordenador portátil", "w": 65, "qty": 1, "hours": 3.00},
            {"name": "Cargador de móvil/tablet", "w": 15, "qty": 2, "hours": 3.00}
        ]
    }

    active_appliances = []

    # Renderizado táctil amigable por grupos (Permitiendo ajustar la potencia directamente)
    for category, items in CATEGORIZED_DEFAULT_APPLIANCES.items():
        with st.expander(category, expanded=True):
            for item in items:
                # Línea de cabecera con checkbox táctil grande
                is_active = st.checkbox(
                    f"**{item['name']}**",
                    value=True,
                    key=f"check_{item['name']}"
                )
                if is_active:
                    if item['name'] == "Termo eléctrico (100l) — [1500W]":
                        col_w, col_q, col_u, col_t = st.columns([1, 1, 1, 1.5])
                        with col_w:
                            w = st.number_input(
                                "Potencia (W)",
                                min_value=100,
                                max_value=6000,
                                value=item["w"],
                                key=f"w_{item['name']}"
                            )
                        with col_q:
                            qty = st.number_input(
                                "Cantidad",
                                min_value=1,
                                max_value=5,
                                value=item["qty"],
                                key=f"qty_{item['name']}"
                            )
                        with col_u:
                            thermo_users = st.number_input(
                                "Nº de Usuarios (Personas)",
                                min_value=1,
                                max_value=12,
                                value=4,
                                key="thermo_users"
                            )
                        with col_t:
                            season = st.selectbox(
                                "Temp. Entrada (Girona)",
                                ["Épocas Templadas (Agua a 15ºC)", "Invierno / Fría (Agua a 10ºC)"],
                                index=0,
                                key="thermo_season"
                            )
                        
                        # Cálculo Termodinámico Exacto de Horas de Funcionamiento
                        # 28 litros/persona/día a 60ºC (Estándar CTE DB-HE-4)
                        # Calor específico del agua = 1.163 Wh/litro·ºC
                        # Pérdidas térmicas estáticas de mantenimiento (aislamiento) = 1200 Wh/día
                        temp_in = 15.0 if "Templadas" in season else 10.0
                        temp_out = 60.0
                        delta_temp = temp_out - temp_in
                        
                        energy_heating_wh = thermo_users * 28.0 * delta_temp * 1.163
                        total_energy_with_losses_wh = energy_heating_wh + 1200.0
                        # Horas necesarias para cada termo
                        hours_calculated = total_energy_with_losses_wh / w
                        hours = round(hours_calculated, 2)
                        
                        # Mostrar el resultado dinámico en un formato bonito
                        st.info(f"🌡️ **Cálculo Termodinámico (CTE):** Para **{thermo_users} personas** a una ΔT de {delta_temp:.0f}ºC, la resistencia de {w}W funcionará **{hours:.2f} horas/día** (Consumo: **{total_energy_with_losses_wh/1000:.2f} kWh/día** por termo).")
                    else:
                        col_w, col_q, col_h = st.columns(3)
                        with col_w:
                            w = st.number_input(
                                "Potencia (W)",
                                min_value=1,
                                max_value=6000,
                                value=item["w"],
                                key=f"w_{item['name']}"
                            )
                        with col_q:
                            qty = st.number_input(
                                "Cantidad",
                                min_value=1,
                                max_value=50,
                                value=item["qty"],
                                key=f"qty_{item['name']}"
                            )
                        with col_h:
                            hours = st.number_input(
                                "Horas/día",
                                min_value=0.01,
                                max_value=24.0,
                                value=item["hours"],
                                step=0.25,
                                key=f"hours_{item['name']}"
                            )
                    active_appliances.append({
                        "Electrodoméstico": item["name"],
                        "Potencia (W)": w,
                        "Cant.": qty,
                        "Horas": hours
                    })
                else:
                    # Si no está activo se computa con 0 consumo
                    pass
                st.markdown("<hr style='margin: 0.5rem 0px; border-color:#e2e8f0;'/>", unsafe_allow_html=True)

    # Bloque de Electrodomésticos Personalizados (Ideal para móvil)
    with st.expander("➕ Electrodomésticos Personalizados", expanded=len(st.session_state.custom_appliances) > 0):
        # Campos de entrada rápidos para añadir uno nuevo
        col_new1, col_new2 = st.columns([2, 1])
        with col_new1:
            new_name = st.text_input("Nombre del aparato", placeholder="ej: Horno, Depuradora piscina", key="new_app_name")
        with col_new2:
            new_w = st.number_input("Potencia (W)", min_value=1, max_value=6000, value=100, key="new_app_w")
            
        if st.button("Añadir Receptáculo Personalizado"):
            if new_name:
                st.session_state.custom_appliances.append({
                    "name": new_name,
                    "w": new_w,
                    "qty": 1,
                    "hours": 1.00
                })
                st.rerun()

        # Renderizar personalizados activos
        for idx, item in enumerate(st.session_state.custom_appliances):
            col_p_title, col_p_del = st.columns([3, 1])
            with col_p_title:
                st.markdown(f"**{item['name']}** ({item['w']} W)")
            with col_p_del:
                if st.button("Eliminar", key=f"del_custom_{idx}"):
                    st.session_state.custom_appliances.pop(idx)
                    st.rerun()
            
            col_p_q, col_p_h = st.columns(2)
            with col_p_q:
                custom_qty = st.number_input(
                    "Cantidad",
                    min_value=1,
                    max_value=50,
                    value=item["qty"],
                    key=f"qty_custom_{idx}"
                )
                st.session_state.custom_appliances[idx]["qty"] = custom_qty
            with col_p_h:
                custom_hours = st.number_input(
                    "Horas/día",
                    min_value=0.01,
                    max_value=24.0,
                    value=item["hours"],
                    step=0.25,
                    key=f"hours_custom_{idx}"
                )
                st.session_state.custom_appliances[idx]["hours"] = custom_hours
                
            active_appliances.append({
                "Electrodoméstico": item["name"],
                "Potencia (W)": item["w"],
                "Cant.": custom_qty,
                "Horas": custom_hours
            })
            st.markdown("<hr style='margin: 0.5rem 0px; border-color:#e2e8f0;'/>", unsafe_allow_html=True)

    # Conversión a DataFrame para los cálculos matemáticos internos
    if len(active_appliances) > 0:
        df_appliances = pd.DataFrame(active_appliances)
        df_appliances["Consumo Diario (Wh/día)"] = df_appliances["Potencia (W)"] * df_appliances["Cant."] * df_appliances["Horas"]
        total_daily_energy = df_appliances["Consumo Diario (Wh/día)"].sum()
        total_simultaneous_power = (df_appliances["Potencia (W)"] * df_appliances["Cant."]).sum()
    else:
        total_daily_energy = 0
        total_simultaneous_power = 0

    # Coeficiente de simultaneidad y VA
    sim_coeff = 0.70
    power_va = (total_simultaneous_power * sim_coeff) / 0.80
    
    # Paneles Sizing
    st.markdown("---")
    # Paneles Sizing
    st.markdown("---")
    st.subheader("📊 Resultados de Dimensionamiento")
    
    # Selector de paneles y modo de ajuste
    col_p_sel, col_p_mode = st.columns([1.5, 1])
    with col_p_sel:
        selected_panel_name = st.selectbox("Selecciona el Panel Solar LONGi", list(PANELS_DB.keys()), index=1)
        panel_specs = PANELS_DB[selected_panel_name]
    with col_p_mode:
        panel_mode = st.radio("Ajuste de Paneles", ["Automático (Por consumo)", "Manual (Personalizado)"], horizontal=True, key="panel_mode")
    
    # Cálculo recomendado de paneles
    energy_adjusted = total_daily_energy / system_efficiency
    min_pv_power = energy_adjusted / hsp if hsp > 0 else 0
    min_panels_theoretical = math.ceil(min_pv_power / panel_specs["p_pico"]) if panel_specs["p_pico"] > 0 else 0
    auto_panels_configured = math.ceil(min_panels_theoretical / num_rows) * num_rows if num_rows > 0 else 0

    if panel_mode == "Manual (Personalizado)":
        col_m1, col_m2 = st.columns([1, 2])
        with col_m1:
            manual_panels_input = st.number_input(
                "Nº Total de Paneles Solares",
                min_value=1,
                max_value=60,
                value=auto_panels_configured if auto_panels_configured > 0 else 6,
                step=1,
                key="manual_panels_input"
            )
        if num_rows > 0:
            panels_per_row = math.ceil(manual_panels_input / num_rows)
            total_panels_configured = panels_per_row * num_rows
        else:
            total_panels_configured = manual_panels_input
            panels_per_row = total_panels_configured
            
        with col_m2:
            st.markdown("<div style='padding-top:25px;'></div>", unsafe_allow_html=True)
            if total_panels_configured != manual_panels_input:
                st.info(f"📐 **Ajuste de Simetría Estructural:** Para **{num_rows} filas** simétricas, se configuran **{total_panels_configured} paneles** ({panels_per_row} por fila).")
            else:
                st.caption(f"Distribuidos simétricamente en {num_rows} filas de {panels_per_row} paneles.")
    else:
        total_panels_configured = auto_panels_configured
        panels_per_row = total_panels_configured // num_rows if num_rows > 0 else 0

    total_pv_power_real = total_panels_configured * panel_specs["p_pico"]
    
    # Generación Solar Producida (kWh/día) y Cobertura
    daily_pv_generation_net_kwh = (total_pv_power_real * hsp * system_efficiency) / 1000
    daily_pv_generation_gross_kwh = (total_pv_power_real * hsp) / 1000
    daily_consumption_kwh = total_daily_energy / 1000
    solar_coverage_pct = (daily_pv_generation_net_kwh / daily_consumption_kwh * 100) if daily_consumption_kwh > 0 else 100.0

    # Baterías Sizing y Autonomía
    useful_acc_required = total_daily_energy * autonomy_days / dod_max
    batteries_qty = math.ceil(useful_acc_required / 5040)  # Cada TBB ES100II tiene 5,04 kWh útiles nominales
    
    total_battery_kwh = batteries_qty * 5.04
    useful_battery_kwh = total_battery_kwh * dod_max
    autonomy_days_calc = (useful_battery_kwh / daily_consumption_kwh) if daily_consumption_kwh > 0 else autonomy_days
    
    # Renderizar tarjetas de métricas optimizadas en 2 filas de 3 columnas
    st.markdown("""<div class="row">""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Consumo Diario</div>
            <div class="metric-value">{daily_consumption_kwh:.2f} kWh</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Generación Solar Est.</div>
            <div class="metric-value">{daily_pv_generation_net_kwh:.2f} kWh/día</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Potencia Requerida</div>
            <div class="metric-value">{power_va:.0f} VA</div>
        </div>
        """, unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Paneles Montados</div>
            <div class="metric-value">{total_panels_configured} uds ({total_pv_power_real/1000:.2f} kWp)</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Baterías TBB</div>
            <div class="metric-value">{batteries_qty} uds ({total_battery_kwh:.2f} kWh)</div>
        </div>
        """, unsafe_allow_html=True)
    with col6:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Autonomía Baterías</div>
            <div class="metric-value">{autonomy_days_calc:.1f} días ({useful_battery_kwh:.1f} kWh útil)</div>
        </div>
        """, unsafe_allow_html=True)

    # Balance Energético
    if daily_consumption_kwh > 0:
        if daily_pv_generation_net_kwh >= daily_consumption_kwh:
            st.success(f"☀️ **Instalación Autosuficiente (Cobertura {solar_coverage_pct:.0f}%):** La generación solar estimada en invierno (**{daily_pv_generation_net_kwh:.2f} kWh/día**) cubre la demanda diaria (**{daily_consumption_kwh:.2f} kWh/día**). El banco de baterías aporta **{autonomy_days_calc:.1f} días** de reserva completa sin sol.")
        else:
            st.warning(f"⚠️ **Cobertura Solar Parcial ({solar_coverage_pct:.0f}%):** La generación solar estimada en invierno (**{daily_pv_generation_net_kwh:.2f} kWh/día**) es inferior a la demanda diaria (**{daily_consumption_kwh:.2f} kWh/día**). Déficit diario de **{daily_consumption_kwh - daily_pv_generation_net_kwh:.2f} kWh/día**.")

    # ── SELECCIÓN DE ELECTRÓNICA DE POTENCIA EN PÁGINA PRINCIPAL ──
    st.markdown("---")
    st.markdown("### 🔌 SELECCIÓN DE ELECTRÓNICA DE POTENCIA (INVERSOR Y REGULADOR)")
    st.markdown("Ajusta o confirma la selección de equipos Victron Energy para la instalación:")

    col_inv, col_reg = st.columns(2)
    
    with col_inv:
        st.markdown("#### ⚡ Inversor / Cargador Victron MultiPlus-II")
        auto_inverter_ref = "PMP482305010"
        if power_va < 3000:
            auto_inverter_ref = "PMP482305010"
        elif power_va < 5000:
            auto_inverter_ref = "PMP482505012"
        elif power_va < 8000:
            auto_inverter_ref = "PMP482805000"
        elif power_va < 10000:
            auto_inverter_ref = "PMP483105000"
        else:
            auto_inverter_ref = "PMP483150000"
            
        manual_inverter_choice = st.selectbox(
            "Seleccionar Inversor / Cargador",
            ["Automático (Recomendado)"] + [f"{k} - {v['nombre']}" for k, v in INVERTER_DB.items()],
            key='manual_inverter'
        )
        
        if manual_inverter_choice == "Automático (Recomendado)":
            final_inverter_ref = auto_inverter_ref
            st.caption(f"✨ **Recomendación Automática ({power_va:.0f} VA):** `{INVERTER_DB[auto_inverter_ref]['nombre']}`")
        else:
            final_inverter_ref = manual_inverter_choice.split(" - ")[0]
            st.caption(f"🔧 **Inversor Seleccionado Manualmente:** `{INVERTER_DB[final_inverter_ref]['nombre']}`")
            
        inverter_specs = INVERTER_DB[final_inverter_ref]

    with col_reg:
        st.markdown("#### ☀️ Regulador de Carga Solar Victron SmartSolar")
        
        # Test auto recommendation based on optimal grouping for MPPT 250/100
        S_auto, P_auto, voc_stc_auto, voc_cold_auto, vmp_stc_auto, isc_auto, imp_auto, _ = get_mppt_electrical_grouping(
            total_panels_configured, panel_specs["voc"], panel_specs["vmp"], panel_specs["isc"], panel_specs["imp"], "SCC125110412"
        )
        
        if voc_cold_auto <= 250.0 and isc_auto <= 70.0 and total_pv_power_real <= 7500:
            auto_regulator_ref = "SCC125110412"
        else:
            auto_regulator_ref = "SCC145110512"
            
        manual_regulator_choice_val = st.selectbox(
            "Seleccionar Regulador de Carga",
            ["Automático (Recomendado)"] + [f"{k} - {v['nombre']}" for k, v in REGULATOR_DB.items()],
            key='manual_regulator'
        )
        
        if manual_regulator_choice_val == "Automático (Recomendado)":
            final_regulator_ref = auto_regulator_ref
            st.caption(f"✨ **Recomendación Automática ({total_pv_power_real/1000:.2f} kWp):** `{REGULATOR_DB[auto_regulator_ref]['nombre'].split(' (')[0]}`")
        else:
            final_regulator_ref = manual_regulator_choice_val.split(" - ")[0]
            st.caption(f"🔧 **Regulador Seleccionado Manualmente:** `{REGULATOR_DB[final_regulator_ref]['nombre'].split(' (')[0]}`")
            
        reg_specs = REGULATOR_DB[final_regulator_ref]
        regulator_ref = final_regulator_ref
        regulator_name = reg_specs["nombre"]
        regulator_pvp = reg_specs["pvp"]

    # Calculate optimal electrical grouping FOR THE FINAL SELECTED REGULATOR
    S_series, P_parallel, string_voc_stc_ui, string_voc_cold_ui, string_vmp_stc_ui, total_isc_ui, total_imp_ui, grouping_candidates = get_mppt_electrical_grouping(
        total_panels_configured, panel_specs["voc"], panel_specs["vmp"], panel_specs["isc"], panel_specs["imp"], regulator_ref
    )

    # Safety Verification
    dangers, warnings = check_regulator_safety(
        regulator_ref=regulator_ref,
        total_pv_power_real=total_pv_power_real,
        S_series=S_series,
        P_parallel=P_parallel,
        panel_voc=panel_specs["voc"],
        panel_isc=panel_specs["isc"]
    )

    if dangers or warnings:
        st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 🚨 VERIFICACIÓN DE SEGURIDAD ELÉCTRICA")
        for danger in dangers:
            st.error(danger)
        for warning in warnings:
            st.warning(warning)

    # ── PARÁMETROS ELÉCTRICOS DEL CAMPO SOLAR (VICTRON MPPT CALCULATOR) ──
    with st.expander("⚡ PARÁMETROS ELÉCTRICOS DEL CAMPO SOLAR (Victron MPPT Calculator)", expanded=True):
        col_e1, col_e2, col_e3, col_e4 = st.columns(4)
        with col_e1:
            st.metric("Agrupación Eléctrica", f"{S_series}S{P_parallel}P", f"{P_parallel} ramas de {S_series} paneles en serie")
        with col_e2:
            st.metric("Tensión Voc (-5ºC / STC)", f"{string_voc_cold_ui:.1f} V", f"Nominal STC: {string_voc_stc_ui:.1f} V")
        with col_e3:
            st.metric("Tensión Vmp Trabajo", f"{string_vmp_stc_ui:.1f} V", f"{S_series}x {panel_specs['vmp']}V")
        with col_e4:
            st.metric(f"Corriente Isc Campo ({P_parallel}P)", f"{total_isc_ui:.2f} A", f"Imp Trabajo: {total_imp_ui:.2f} A")

    with st.expander("🛡️ CÁLCULO Y PROTECCIÓN DE FUSIBLES CC (NOVELEC STANDARD)", expanded=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            st.metric(
                "Fusible Regulador MPPT",
                f"{mppt_fuse_spec['rating']} A",
                f"I_out MPPT: {mppt_charge_current} A ({mppt_fuse_spec['ref']})"
            )
        with col_f2:
            st.metric(
                "Fusible Inversor MultiPlus-II",
                f"{inverter_fuse_spec['rating']} A",
                f"I_max Descarga: {inverter_max_current} A ({inverter_fuse_spec['ref']})"
            )
        with col_f3:
            st.metric(
                "Fusible Bancada Baterías",
                f"{bat_fuse_spec['rating']} A",
                f"Carga Comb: {total_combined_charge_current} A ({mppt_charge_current}A MPPT + {inverter_charge_current}A AC)"
            )
        st.caption(
            f"ℹ️ **Criterio de Cálculo de Fusibles:** "
            f"1) **MPPT:** Carga de salida de {mppt_charge_current}A x factor 1.25 -> Fusible de {mppt_fuse_spec['rating']}A. "
            f"2) **Inversor:** Descarga máx de {inverter_max_current}A / Carga AC de {inverter_charge_current}A -> Fusible de {inverter_fuse_spec['rating']}A. "
            f"3) **Baterías / Lynx:** Corriente combinada de carga máxima ({mppt_charge_current}A MPPT + {inverter_charge_current}A Inversor Cargador = {total_combined_charge_current}A) frente a descarga pico ({inverter_max_current}A) -> Fusible de {bat_fuse_spec['rating']}A."
        )


    # 3. Gave Box selection
    if regulator_ref == "SCC125110412":
        gave_ref = "STM40480P20"
        gave_name = "Caja Solartec 4 strings (80A seccionador, sobretensiones Tipo II)"
        gave_pvp = 445.85
    else:
        gave_ref = "STM210NSP20"
        gave_name = "Caja Solartec 2 strings 1000V (Protección sobretensiones Tipo II para MPPT RS)"
        gave_pvp = 288.21

    # 4. Cálculo de Fusibles de Potencia CC (Novelec Standard)
    mppt_charge_current = reg_specs["max_current"]
    inverter_max_current = inverter_specs["current"]
    inverter_charge_current = inverter_specs["charger_current"]
    
    mppt_fuse_spec = select_victron_fuse(mppt_charge_current, apply_safety_factor=True)
    inverter_fuse_spec = select_victron_fuse(inverter_max_current, apply_safety_factor=False)
    
    total_combined_charge_current = mppt_charge_current + inverter_charge_current
    max_battery_circuit_current = max(total_combined_charge_current, inverter_max_current)
    bat_fuse_spec = select_victron_fuse(max_battery_circuit_current, apply_safety_factor=False)
    
    bat_fuse_ref = bat_fuse_spec["ref"]
    bat_fuse_name = bat_fuse_spec["name"]

    # Contrucción del Presupuesto
    bom_items = []
    
    # Módulos Solares
    bom_items.append({
        "Categoría": "Generación Solar",
        "Referencia": panel_specs["ref"],
        "Descripción": f"Panel solar LONGi {panel_specs['desc']} ({panel_specs['p_pico']}Wp)",
        "Cantidad": total_panels_configured,
        "Unidad": "uds",
        "PVP Tarifa (€)": 95.0,
        "Descuento": 0.0,
        "Is_Victron": False
    })
    
    # Estructura Sunfer
    if roof_type == "Plana":
        bom_items.append({
            "Categoría": "Estructura de Soporte",
            "Referencia": "29.1H-A-15-C",
            "Descripción": "Kit Inicial Sunfer 29.1H 15º Crudo (Simple Horizontal)",
            "Cantidad": num_rows,
            "Unidad": "uds",
            "PVP Tarifa (€)": 139.37,
            "Descuento": 0.0,
            "Is_Victron": False
        })
        if total_panels_configured > num_rows:
            bom_items.append({
                "Categoría": "Estructura de Soporte",
                "Referencia": "29.1H-B-15-C",
                "Descripción": "Kit Ampliación Sunfer 29.1H 15º Crudo (Simple Horizontal)",
                "Cantidad": total_panels_configured - num_rows,
                "Unidad": "uds",
                "PVP Tarifa (€)": 139.94,
                "Descuento": 0.0,
                "Is_Victron": False
            })
        bom_items.append({
            "Categoría": "Estructura de Soporte",
            "Referencia": "WB-2279-15-1",
            "Descripción": "Deflector de Viento Trasero 15º Crudo (WB-2279)",
            "Cantidad": total_panels_configured,
            "Unidad": "uds",
            "PVP Tarifa (€)": 14.48,
            "Descuento": 0.0,
            "Is_Victron": False
        })
        bom_items.append({
            "Categoría": "Estructura de Soporte",
            "Referencia": "WBL-15-1",
            "Descripción": "Tapa Cortavientos Lateral 15º Crudo (WBL-15)",
            "Cantidad": 2 * num_rows,
            "Unidad": "uds",
            "PVP Tarifa (€)": 20.33,
            "Descuento": 0.0,
            "Is_Victron": False
        })
    else:
        # Cómputo geométrico avanzado para inclinada (Teja o Chapa)
        ref_anclaje = "S01-250-CL-C" if roof_type == "Inclinada Teja" else "S04-ZN"
        desc_anclaje = "Salvatejas Regulable de Aluminio Sunfer S01 (Teja)" if roof_type == "Inclinada Teja" else "Soporte Chapa / Tornillo Doble Rosca S04-ZN (Metal)"
        pvp_anclaje = 5.53 if roof_type == "Inclinada Teja" else 3.80
        
        perfiles_qty = math.ceil((2 * panels_per_row * 1.134) / 4.8) * num_rows if panels_per_row > 0 else 0
        uniones_qty = max(0, (math.ceil((panels_per_row * 1.134) / 4.8) - 1) * 2 * num_rows) if panels_per_row > 0 else 0
        
        bom_items.append({
            "Categoría": "Estructura de Soporte",
            "Referencia": "G1-4800-1-C",
            "Descripción": "Perfil de Aluminio Sunfer G1 Crudo (4800 mm)",
            "Cantidad": perfiles_qty,
            "Unidad": "uds",
            "PVP Tarifa (€)": 59.19,
            "Descuento": 0.0,
            "Is_Victron": False
        })
        if uniones_qty > 0:
            bom_items.append({
                "Categoría": "Estructura de Soporte",
                "Referencia": "UG1-C",
                "Descripción": "Kit de Unión de Perfiles G1 (Crudo)",
                "Cantidad": uniones_qty,
                "Unidad": "uds",
                "PVP Tarifa (€)": 3.115,
                "Descuento": 0.0,
                "Is_Victron": False
            })
        bom_items.append({
            "Categoría": "Estructura de Soporte",
            "Referencia": ref_anclaje,
            "Descripción": desc_anclaje,
            "Cantidad": 2 * (panels_per_row + 1) * num_rows,
            "Unidad": "uds",
            "PVP Tarifa (€)": pvp_anclaje,
            "Descuento": 0.0,
            "Is_Victron": False
        })
        bom_items.append({
            "Categoría": "Estructura de Soporte",
            "Referencia": "S10-C",
            "Descripción": "Presor / Grapa Lateral de Aluminio Sunfer (35-50 mm)",
            "Cantidad": 4 * num_rows,
            "Unidad": "uds",
            "PVP Tarifa (€)": 2.37,
            "Descuento": 0.0,
            "Is_Victron": False
        })
        bom_items.append({
            "Categoría": "Estructura de Soporte",
            "Referencia": "S11-C",
            "Descripción": "Presor / Grapa Central de Aluminio Sunfer (Omega)",
            "Cantidad": 2 * max(0, panels_per_row - 1) * num_rows,
            "Unidad": "uds",
            "PVP Tarifa (€)": 1.765,
            "Descuento": 0.0,
            "Is_Victron": False
        })
        bom_items.append({
            "Categoría": "Estructura de Soporte",
            "Referencia": "S13",
            "Descripción": "Tapón / Tapa Extremo para Perfil G1",
            "Cantidad": 2 * panels_per_row * num_rows,
            "Unidad": "uds",
            "PVP Tarifa (€)": 0.471,
            "Descuento": 0.0,
            "Is_Victron": False
        })
        bom_items.append({
            "Categoría": "Estructura de Soporte",
            "Referencia": "TG1",
            "Descripción": "Tornillo de Puesta a Tierra para Módulo / Perfil",
            "Cantidad": 4 * num_rows,
            "Unidad": "uds",
            "PVP Tarifa (€)": 1.20,
            "Descuento": 0.0,
            "Is_Victron": False
        })

    # Electrónica de potencia
    bom_items.append({
        "Categoría": "Inversor / Cargador",
        "Referencia": final_inverter_ref,
        "Descripción": inverter_specs["nombre"],
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": inverter_specs["pvp"],
        "Descuento": 0.0,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Regulador de Carga",
        "Referencia": regulator_ref,
        "Descripción": regulator_name,
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": regulator_pvp,
        "Descuento": 0.0,
        "Is_Victron": True
    })
    
    # Baterías y brackets
    bom_items.append({
        "Categoría": "Acumulación (Batería)",
        "Referencia": "ES100II",
        "Descripción": "Batería Litio TBB LiFePO4 ES100 II 48V 105Ah (5.04 kWh)",
        "Cantidad": batteries_qty,
        "Unidad": "uds",
        "PVP Tarifa (€)": 935.0,
        "Descuento": 0.0,
        "Is_Victron": False
    })
    bom_items.append({
        "Categoría": "Acumulación (Soporte)",
        "Referencia": "Brackets 3U",
        "Descripción": "Brackets ES100II 3U (contiene 2 unidades)",
        "Cantidad": batteries_qty,
        "Unidad": "uds",
        "PVP Tarifa (€)": 60.0,
        "Descuento": 0.0,
        "Is_Victron": False
    })

    # GX Monitorización
    bom_items.append({
        "Categoría": "Monitorización y GX",
        "Referencia": "BPP900450110",
        "Descripción": "Victron Cerbo GX MK2 (Centro de control y comunicaciones)",
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 265.0,
        "Descuento": 0.0,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Monitorización y GX",
        "Referencia": "BPP900455050",
        "Descripción": "Victron GX Touch 50 (Pantalla táctil a color de 5 pulgadas)",
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 235.0,
        "Descuento": 0.0,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Monitorización y GX",
        "Referencia": "BPP900465050",
        "Descripción": "Soporte de pared para pantalla GX Touch 50 Wall Mount",
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 16.0,
        "Descuento": 0.0,
        "Is_Victron": True
    })

    # Distribución y protecciones
    bom_items.append({
        "Categoría": "Protección y Distribución",
        "Referencia": "LYN020102010",
        "Descripción": "Victron Lynx Power In (M10) - Embarrado CC centralizado",
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 150.0,
        "Descuento": 0.0,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Protección y Distribución",
        "Referencia": gave_ref,
        "Descripción": gave_name,
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": gave_pvp,
        "Descuento": 0.0,
        "Is_Victron": False
    })
    bom_items.append({
        "Categoría": "Protección y Distribución",
        "Referencia": "VBS127010010",
        "Descripción": "Victron Interruptor/Desconectador de batería 275 A",
        "Cantidad": 1 if batteries_qty > 0 else 0,
        "Unidad": "uds",
        "PVP Tarifa (€)": 37.0,
        "Descuento": 0.0,
        "Is_Victron": True
    })

    # Cables de datos
    bom_items.append({
        "Categoría": "Cable de Datos",
        "Referencia": "ASS030064951",
        "Descripción": "Cable RJ45 UTP 1.8 m (VE.Bus - Inversor a Cerbo)",
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 11.0,
        "Descuento": 0.0,
        "Is_Victron": True
    })
    
    # Lógica inteligente para cable de datos del MPPT
    if regulator_ref == "SCC125110412":
        bom_items.append({
            "Categoría": "Cable de Datos",
            "Referencia": "ASS030530218",
            "Descripción": "Cable VE.Direct 1.8 m (MPPT a Cerbo)",
            "Cantidad": 1,
            "Unidad": "uds",
            "PVP Tarifa (€)": 15.0,
            "Descuento": 0.0,
            "Is_Victron": True
        })
    else: # Si es MPPT RS se conecta por VE.Can, por tanto usa RJ45
        bom_items.append({
            "Categoría": "Cable de Datos",
            "Referencia": "ASS030064951",
            "Descripción": "Cable RJ45 UTP 1.8 m (VE.Can - MPPT RS a Cerbo)",
            "Cantidad": 1,
            "Unidad": "uds",
            "PVP Tarifa (€)": 11.0,
            "Descuento": 0.0,
            "Is_Victron": True
        })
        
    bom_items.append({
        "Categoría": "Cable de Datos",
        "Referencia": "ASS030710118",
        "Descripción": "Cable BMS VE.Can a CAN-bus, Tipo A 1.8 m (TBB a Cerbo)",
        "Cantidad": 1 if batteries_qty > 0 else 0,
        "Unidad": "uds",
        "PVP Tarifa (€)": 15.0,
        "Descuento": 0.0,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Cable de Datos",
        "Referencia": "ASS030700000",
        "Descripción": "Terminadores RJ45 VE.Can (Bolsa de 2 unidades)",
        "Cantidad": 1 if batteries_qty > 0 else 0,
        "Unidad": "uds",
        "PVP Tarifa (€)": 10.0,
        "Descuento": 0.0,
        "Is_Victron": True
    })

    # Cables de potencia y fusibles
    bom_items.append({
        "Categoría": "Cable de Potencia CC",
        "Referencia": "Solar PV ZZ-F 6mm²",
        "Descripción": "Conductor de cobre rojo/negro de 6 mm² para strings PV",
        "Cantidad": 60,
        "Unidad": "metros",
        "PVP Tarifa (€)": 1.50,
        "Descuento": 0.0,
        "Is_Victron": False
    })
    bom_items.append({
        "Categoría": "Cable de Potencia CC",
        "Referencia": "Solar PV ZZ-F 25mm²",
        "Descripción": "Conductor de cobre rojo/negro de 25 mm² de Caja CC a MPPT",
        "Cantidad": 30,
        "Unidad": "metros",
        "PVP Tarifa (€)": 3.50,
        "Descuento": 0.0,
        "Is_Victron": False
    })
    bom_items.append({
        "Categoría": "Cable de Potencia CC",
        "Referencia": "H07V-K 35mm²",
        "Descripción": "Conductor de cobre para potencia a 48V (MPPT / Baterías)",
        "Cantidad": 4,
        "Unidad": "metros",
        "PVP Tarifa (€)": 4.80,
        "Descuento": 0.0,
        "Is_Victron": False
    })
    bom_items.append({
        "Categoría": "Cable de Potencia CC",
        "Referencia": "H07V-K 70mm²",
        "Descripción": "Conductor de cobre para potencia a 48V del Inversor a Lynx",
        "Cantidad": 4,
        "Unidad": "metros",
        "PVP Tarifa (€)": 9.50,
        "Descuento": 0.0,
        "Is_Victron": False
    })
    
    # Fusibles MEGA desglosados unitariamente según corrientes calculadas
    bom_items.append({
        "Categoría": "Fusibles de Potencia",
        "Referencia": mppt_fuse_spec["ref"],
        "Descripción": f"Victron MEGA-fuse {mppt_fuse_spec['rating']}A/80V para salida MPPT ({mppt_charge_current}A nominal)",
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 7.60,
        "Descuento": 0.0,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Fusibles de Potencia",
        "Referencia": bat_fuse_spec["ref"],
        "Descripción": f"Victron MEGA-fuse {bat_fuse_spec['rating']}A/80V para bancada Batería TBB (Carga Comb: {total_combined_charge_current}A [{mppt_charge_current}A MPPT + {inverter_charge_current}A AC])",
        "Cantidad": 1 if batteries_qty > 0 else 0,
        "Unidad": "uds",
        "PVP Tarifa (€)": 7.60,
        "Descuento": 0.0,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Fusibles de Potencia",
        "Referencia": inverter_fuse_spec["ref"],
        "Descripción": f"Victron MEGA-fuse {inverter_fuse_spec['rating']}A/80V para Inversor MultiPlus-II ({inverter_max_current}A máx)",
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 7.60,
        "Descuento": 0.0,
        "Is_Victron": True
    })

    # Procesado de DataFrame final
    df_bom = pd.DataFrame(bom_items)
    df_bom["Precio Unit. Neto (€)"] = df_bom["PVP Tarifa (€)"] * (1 - df_bom["Descuento"])
    df_bom["Precio Total Neto (€)"] = df_bom["Cantidad"] * df_bom["Precio Unit. Neto (€)"]
    
    # Visualizar presupuesto
    df_display = df_bom[["Categoría", "Referencia", "Descripción", "Cantidad", "Unidad", "PVP Tarifa (€)", "Descuento", "Precio Unit. Neto (€)", "Precio Total Neto (€)"]]
    total_net = df_bom["Precio Total Neto (€)"].sum()

    st.markdown("---")
    st.subheader("📄 Generar Resumen del Proyecto en PDF")
    st.markdown("Genera un informe técnico corporativo en PDF (2 páginas) con los consumos, dimensionamiento, secuencia de arranque y un **croquis técnico del flujo de energía**.")
    
    # Generate PDF Bytes on demand
    try:
        pdf_bytes = generate_pdf_bytes(
            total_daily_energy=total_daily_energy,
            power_va=power_va,
            total_panels_configured=total_panels_configured,
            total_pv_power_real=total_pv_power_real,
            batteries_qty=batteries_qty,
            has_generator=has_generator,
            selected_panel_name=selected_panel_name,
            roof_type=roof_type,
            orientation=orientation,
            tilt=tilt,
            hsp=hsp,
            active_appliances=active_appliances,
            autonomy_days=autonomy_days_calc,
            dod_max=dod_max,
            regulator_ref=regulator_ref,
            regulator_name=regulator_name
        )
        
        col_down1, col_down2 = st.columns(2)
        with col_down1:
            st.download_button(
                label="📥 Descargar Dossier Resumen (PDF)",
                data=pdf_bytes,
                file_name="resumen_instalacion_novelec.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with col_down2:
            csv_data = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Presupuesto en CSV",
                data=csv_data,
                file_name="presupuesto_solar_novelec.csv",
                mime="text/csv",
                use_container_width=True
            )
    except Exception as e:
        st.error(f"Error al generar la descarga: {e}")

with tab2:
    st.subheader("📦 Resumen de Materiales y Presupuesto Inteligente (BOM)")
    st.markdown("La calculadora selecciona dinámicamente las referencias de catálogo y calcula el presupuesto a PVP de tarifa oficial (sin descuentos aplicados):")
    
    # Filtro opcional por categorías en móvil
    cat_filter = st.multiselect("Filtrar por Categoría (BOM)", list(df_display["Categoría"].unique()), default=None)
    if cat_filter:
        df_display_filtered = df_display[df_display["Categoría"].isin(cat_filter)]
    else:
        df_display_filtered = df_display

    st.dataframe(df_display_filtered.style.format({
        "PVP Tarifa (€)": "{:,.2f} €",
        "Descuento": "{:.0%}",
        "Precio Unit. Neto (€)": "{:,.2f} €",
        "Precio Total Neto (€)": "{:,.2f} €"
    }), use_container_width=True, height=500)
    
    total_net = df_bom["Precio Total Neto (€)"].sum()
    
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.markdown(f"### 💰 Presupuesto Neto Total (Sin IVA): `{total_net:,.2f} €`")
    with col_t2:
        # Botón de descarga de CSV
        csv_data = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Presupuesto en CSV",
            data=csv_data,
            file_name="presupuesto_solar_novelec.csv",
            mime="text/csv"
        )
with tab3:
    st.subheader("⚡ Manual de Obra y Secuencia de Arranque Segura")
    
    st.markdown("""
    ### 🔌 1. Esquema de Datos y Cableado de Comunicaciones
    Es un error frecuente en obra conectar reguladores de alta tensión mediante cable VE.Direct. Sigue esta pauta obligatoria:
    *   **Inversor MultiPlus-II ➔ Cerbo GX:** Conectar usando cable RJ45 estándar (`ASS030064951`) al puerto **VE.Bus** del Cerbo GX.
    *   **Regulador MPPT (Si es MPPT RS):** Conectar mediante cable RJ45 estándar (`ASS030064951`) al puerto **VE.Can** del Cerbo GX. Colocar obligatoriamente los **terminadores azules** en los extremos libres.
    *   **Regulador MPPT (Si es 250/100):** Conectar mediante cable **VE.Direct** (`ASS030530218`) al puerto VE.Direct del Cerbo GX.
    *   **Baterías TBB ES100II ➔ Cerbo GX:** Conectar la batería maestra al puerto **BMS-Can** del Cerbo GX usando el cable de datos especial **BMS-CAN Tipo A** (`ASS030710118`). Colocar los terminadores correspondientes.
    
    ### 🛡️ 2. Protocolo de Arranque y Encendido del Sistema (Paso a Paso)
    Para proteger la electrónica y sincronizar los microprocesadores del sistema de potencia, los instaladores deben seguir este orden estricto de obra:
    1.  **Cierre de Fusibles de Batería:** Conecta el fusible MEGA principal de baterías en el Lynx Power In y cierra el interruptor desconectador manual (`VBS127010010`).
    2.  **Encendido del BMS de las Baterías TBB:** Pulsa el botón de encendido de la batería maestra. Espera a que los módulos de litio sincronicen y se enciendan los LEDs de estado.
    3.  **Encendido del Inversor MultiPlus-II:** Coloca el interruptor del inversor en posición **I (ON)**. El inversor cargará sus condensadores de entrada y arrancará sin provocar arcos eléctricos dañinos.
    4.  **Cierre del Seccionador de Campo Solar:** Cierra el interruptor rotativo de la caja Gave Solartec (CC). El regulador MPPT detectará tensión solar.
    5.  **Encendido del Regulador MPPT:** Enciende el disyuntor o fusible de salida del regulador solar. Éste comenzará a inyectar corriente de carga en el Lynx Power In de forma sincronizada con el control DVCC del Cerbo GX.
    """)
