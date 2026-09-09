import streamlit as st
import pandas as pd
import math
import tempfile
import os
from fpdf import FPDF

# Configuration
st.set_page_config(
    page_title="Novelec - Calculadora de Sección de Cables CC/CA",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilo corporativo personalizado (Identidad Novelec) con diseño touch-friendly para móvil
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
        width: 100%;
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
        font-size: 1.8rem;
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
    .metric-subtitle {
        font-size: 0.8rem;
        color: #0284c7;
        margin-top: 0.2rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado principal de marca Novelec (SVG Oficial Vectorial)
st.markdown("""
<div style="text-align: left; margin-bottom: 1.5rem;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450 110" width="320" style="max-width: 100%; height: auto;">
  <path d="M 15,15 H 70 A 25,25 0 0,1 95,40 V 70 A 25,25 0 0,1 70,95 H 40 A 25,25 0 0,1 15,70 Z" fill="#004b7c" />
  <path d="M 38,72 V 48 A 12,12 0 0,1 62,48 V 72" fill="none" stroke="#ffffff" stroke-width="13" stroke-linecap="round" stroke-linejoin="round" />
  <text x="115" y="62" font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif" font-weight="700" font-size="50" fill="#002f54" letter-spacing="-1.5">novelec</text>
  <text x="115" y="88" font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif" font-size="18" font-weight="500" fill="#64748b" letter-spacing="0.5">El valor del servei</text>
</svg>
</div>
""", unsafe_allow_html=True)

st.title("⚡ Calculadora de Sección de Cableado Eléctrico")
st.markdown("**Cálculo de Secciones por Caída de Tensión y Capacidad Térmica REBT / UNE 20460 - Novelec Servicios Técnicos**")
st.markdown("---")

# Tablas de Secciones Comerciales Estandarizadas e Intensidades Máximas Admisibles (REBT ITC-BT-19 / UNE 20460)
STANDARD_SECTIONS = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]

# Capacidades térmicas aproximadas en Amperios (Cobre / Aislamiento XLPE-EPR 90ºC B2/C)
IZ_COPPER_XLPE = {
    1.5: 18.5,
    2.5: 25.0,
    4: 34.0,
    6: 43.0,
    10: 60.0,
    16: 80.0,
    25: 106.0,
    35: 131.0,
    50: 159.0,
    70: 202.0,
    95: 244.0,
    120: 282.0,
    150: 324.0,
    185: 371.0,
    240: 436.0,
    300: 500.0
}

# Conductividades de materiales (m / (Ohm * mm²)) a temperatura de trabajo continuado (70ºC / 90ºC)
CONDUCTIVITY = {
    "Cobre (Cu)": 48.0,      # Cobre a 70ºC (Estándar de seguridad REBT)
    "Aluminio (Al)": 30.0    # Aluminio a 70ºC
}

# Clase FPDF para informe
class CablePDF(FPDF):
    def header(self):
        self.set_fill_color(0, 47, 84) # Novelec Navy
        self.rect(0, 0, 210, 28, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 16)
        self.text(15, 12, "NOVELEC - SERVEIS TECNICS")
        self.set_font("helvetica", "I", 8.5)
        self.text(15, 18, "El valor del servei - Informe Tecnico de Dimensionamiento de Cableado")
        self.set_fill_color(2, 132, 199) # Light blue
        self.rect(170, 0, 40, 28, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 12)
        self.text(178, 16, "CABLES")
        self.set_y(32)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f"Pagina {self.page_no()} | Memoria de Calculo Novelec", align="C")

def generate_pdf_report(system_type, voltage, current, length, max_vdrop_pct, max_vdrop_v, 
                        material, conductivity, s_calc, s_chosen, vdrop_real_v, 
                        vdrop_real_pct, power_loss_w, power_loss_pct, iz_max):
    pdf = CablePDF()
    pdf.add_page()
    
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(0, 47, 84)
    pdf.cell(0, 8, "CÁLCULO Y SELECCIÓN DE SECCIÓN DE CONDUCTOR", ln=1)
    pdf.set_font("helvetica", "I", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, "Verificacion por Caida de Tension y Capacidad Termica de Corriente", ln=1)
    pdf.ln(4)
    
    # Tabla de Entrada
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(10, pdf.get_y(), 190, 32, "F")
    pdf.set_y(pdf.get_y() + 3)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(30, 41, 59)
    
    pdf.cell(95, 5, f"  Tipo de Sistema: {system_type}")
    pdf.cell(95, 5, f"  Tension Nominal: {voltage:.1f} V")
    pdf.ln(5)
    pdf.cell(95, 5, f"  Corriente Nominal (I): {current:.2f} A")
    pdf.cell(95, 5, f"  Longitud de Linea (L): {length:.1f} m")
    pdf.ln(5)
    pdf.cell(95, 5, f"  Caida de Tension Max. Admisible: {max_vdrop_pct:.2f}% ({max_vdrop_v:.2f} V)")
    pdf.cell(95, 5, f"  Material Conductor: {material} (g={conductivity:.0f})")
    pdf.ln(12)
    
    # Resultados Destacados
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(0, 47, 84)
    pdf.cell(0, 8, "RESULTADOS DEL DIMENSIONAMIENTO", ln=1)
    pdf.ln(2)
    
    pdf.set_fill_color(0, 47, 84)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(95, 8, "  Parametro de Calculo", fill=True)
    pdf.cell(95, 8, "Valor Obtenido", fill=True, align="C")
    pdf.ln(8)
    
    pdf.set_text_color(30, 41, 59)
    pdf.set_font("helvetica", "", 9)
    
    data = [
        ("Sección Teórica Calculada", f"{s_calc:.3f} mm²"),
        ("SECCIÓN COMERCIAL RECOMENDADA", f"{s_chosen:.1f} mm²"),
        ("Caída de Tensión Real Obtenida", f"{vdrop_real_v:.2f} V  ({vdrop_real_pct:.2f}%)"),
        ("Pérdida de Potencia por Efecto Joule", f"{power_loss_w:.1f} W  ({power_loss_pct:.2f}%)"),
        ("Intensidad Máx. Admisible Térmica (Iz)", f"{iz_max:.0f} A  (Margen: {iz_max - current:+.1f} A)")
    ]
    
    alt = False
    for label, val in data:
        pdf.set_fill_color(248, 250, 252) if alt else pdf.set_fill_color(255, 255, 255)
        pdf.cell(95, 7, f"  {label}", fill=True)
        pdf.cell(95, 7, f"{val}", fill=True, align="C")
        pdf.ln(7)
        alt = not alt
        
    return bytes(pdf.output())

# ────────────────────────────────────────────────────────────────────────
# INTERFAZ Y CONTROLES TÁCTILES MÓVIL
# ────────────────────────────────────────────────────────────────────────

st.subheader("⚙️ Parámetros Eléctricos de la Línea")

col_i1, col_i2, col_i3 = st.columns([1, 1, 1])

with col_i1:
    system_type = st.selectbox(
        "Tipo de Circuito / Sistema",
        ["Corriente Continua (CC / DC)", "Corriente Alterna Monofásica (CA 230V)", "Corriente Alterna Trifásica (CA 400V)"],
        index=0
    )

with col_i2:
    if "Continua" in system_type:
        voltage = st.number_input("Tensión Nominal (V)", min_value=1.0, max_value=1500.0, value=48.0, step=12.0)
    elif "Monofásica" in system_type:
        voltage = st.number_input("Tensión Nominal (V)", min_value=110.0, max_value=250.0, value=230.0, step=10.0)
    else:
        voltage = st.number_input("Tensión Nominal (V)", min_value=200.0, max_value=1000.0, value=400.0, step=10.0)

with col_i3:
    current = st.number_input("Corriente Nominal I (Amperios)", min_value=0.1, max_value=1000.0, value=25.0, step=1.0)

col_i4, col_i5, col_i6 = st.columns([1, 1, 1])

with col_i4:
    length = st.number_input("Longitud de la Línea L (metros)", min_value=0.5, max_value=2000.0, value=20.0, step=1.0)

with col_i5:
    max_vdrop_pct = st.number_input("Caída Tensión Máx. (%)", min_value=0.1, max_value=20.0, value=1.5, step=0.1)

with col_i6:
    material = st.selectbox("Material del Conductor", ["Cobre (Cu)", "Aluminio (Al)"], index=0)

# Factor de potencia para CA Trifásica
cos_phi = 1.0
if "Trifásica" in system_type:
    cos_phi = st.slider("Factor de Potencia (cos φ)", min_value=0.7, max_value=1.0, value=0.95, step=0.01)

# ────────────────────────────────────────────────────────────────────────
# MOTOR DE CÁLCULO FÍSICO Y TÉRMICO
# ────────────────────────────────────────────────────────────────────────

# Caída de tensión máxima admisible en Voltios
max_vdrop_v = (voltage * max_vdrop_pct) / 100.0

# Conductividad elegida
gamma = CONDUCTIVITY[material]

# Sección teórica por caída de tensión
if "Trifásica" in system_type:
    s_calc = (math.sqrt(3) * length * current * cos_phi) / (gamma * max_vdrop_v)
else:
    # Para CC y CA Monofásica (Ida y vuelta -> factor 2)
    s_calc = (2.0 * length * current) / (gamma * max_vdrop_v)

# Selección de la sección comercial estandarizada inmediatamente superior por caída de tensión
s_com_vdrop = next((s for s in STANDARD_SECTIONS if s >= s_calc), STANDARD_SECTIONS[-1])

# Comprobación por Capacidad Térmica de Corriente (Iz REBT)
s_com_thermal = next((s for s in STANDARD_SECTIONS if IZ_COPPER_XLPE.get(s, 999) >= current), STANDARD_SECTIONS[-1])

# Sección Final Recomendada (El máximo entre Caída de Tensión y Térmica)
s_chosen = max(s_com_vdrop, s_com_thermal)

# Recálculo de valores reales obtenidos con la sección comercial elegida
if "Trifásica" in system_type:
    vdrop_real_v = (math.sqrt(3) * length * current * cos_phi) / (gamma * s_chosen)
    power_loss_w = math.sqrt(3) * vdrop_real_v * current * cos_phi
else:
    vdrop_real_v = (2.0 * length * current) / (gamma * s_chosen)
    power_loss_w = vdrop_real_v * current

vdrop_real_pct = (vdrop_real_v / voltage) * 100.0
total_active_power_w = voltage * current if "Trifásica" not in system_type else math.sqrt(3) * voltage * current * cos_phi
power_loss_pct = (power_loss_w / total_active_power_w * 100.0) if total_active_power_w > 0 else 0.0
iz_max = IZ_COPPER_XLPE.get(s_chosen, 0.0)

# ────────────────────────────────────────────────────────────────────────
# PRESENTACIÓN DE RESULTADOS MÓVIL-FIRST
# ────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("📊 Resultados de Dimensionamiento de Conductor")

col_r1, col_r2, col_r3 = st.columns(3)

with col_r1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Sección Comercial Recomendada</div>
        <div class="metric-value">{s_chosen:.1f} mm²</div>
        <div class="metric-subtitle">Sección Teórica: {s_calc:.2f} mm²</div>
    </div>
    """, unsafe_allow_html=True)

with col_r2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Caída de Tensión Real</div>
        <div class="metric-value">{vdrop_real_pct:.2f}%</div>
        <div class="metric-subtitle">{vdrop_real_v:.2f} V (Máx. permitido: {max_vdrop_v:.2f} V)</div>
    </div>
    """, unsafe_allow_html=True)

with col_r3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Pérdida por Efecto Joule</div>
        <div class="metric-value">{power_loss_w:.1f} W</div>
        <div class="metric-subtitle">{power_loss_pct:.2f}% de la potencia transportada</div>
    </div>
    """, unsafe_allow_html=True)

# Evaluación de Seguridad
if s_com_thermal > s_com_vdrop:
    st.warning(f"⚠️ **Criterio Térmico Dominante:** Aunque por caída de tensión bastaría una sección de {s_com_vdrop} mm², la intensidad nominal de {current:.1f} A requiere aumentar la sección a **{s_chosen} mm²** para evitar el sobrecalentamiento del aislamiento según REBT (Iz = {iz_max} A).")
else:
    st.success(f"✅ **Línea Garantizada:** La sección comercial de **{s_chosen} mm²** cumple holgadamente tanto el criterio de caída de tensión ({vdrop_real_pct:.2f}% ≤ {max_vdrop_pct:.2f}%) como la capacidad térmica de corriente (Iz = {iz_max} A ≥ {current:.1f} A).")

# Desglose en expansor
with st.expander("📋 Desglose Técnico Completo y Descarga de Informe", expanded=True):
    df_res = pd.DataFrame([
        {"Parámetro": "Tipo de Sistema", "Valor": system_type},
        {"Parámetro": "Tensión Nominal", "Valor": f"{voltage:.1f} V"},
        {"Parámetro": "Corriente Nominal (I)", "Valor": f"{current:.2f} A"},
        {"Parámetro": "Longitud de Línea (L)", "Valor": f"{length:.1f} m"},
        {"Parámetro": "Caída Tensión Máx. Permitida", "Valor": f"{max_vdrop_pct:.2f}% ({max_vdrop_v:.2f} V)"},
        {"Parámetro": "Sección Teórica Calculada", "Valor": f"{s_calc:.3f} mm²"},
        {"Parámetro": "Sección Comercial Seleccionada", "Valor": f"{s_chosen:.1f} mm²"},
        {"Parámetro": "Caída de Tensión Real", "Valor": f"{vdrop_real_v:.2f} V ({vdrop_real_pct:.2f}%)"},
        {"Parámetro": "Pérdida de Potencia (Efecto Joule)", "Valor": f"{power_loss_w:.1f} W ({power_loss_pct:.2f}%)"},
        {"Parámetro": "Intensidad Máx. Admisible Térmica (Iz)", "Valor": f"{iz_max:.0f} A"}
    ])
    st.table(df_res)
    
    # Botones de Descarga de Ficha Técnica
    try:
        pdf_data = generate_pdf_report(
            system_type=system_type,
            voltage=voltage,
            current=current,
            length=length,
            max_vdrop_pct=max_vdrop_pct,
            max_vdrop_v=max_vdrop_v,
            material=material,
            conductivity=gamma,
            s_calc=s_calc,
            s_chosen=s_chosen,
            vdrop_real_v=vdrop_real_v,
            vdrop_real_pct=vdrop_real_pct,
            power_loss_w=power_loss_w,
            power_loss_pct=power_loss_pct,
            iz_max=iz_max
        )
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="📥 Descargar Ficha Técnica en PDF",
                data=pdf_data,
                file_name="calculo_seccion_cable_novelec.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with col_d2:
            csv_data = df_res.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Resumen en CSV",
                data=csv_data,
                file_name="calculo_seccion_cable_novelec.csv",
                mime="text/csv",
                use_container_width=True
            )
    except Exception as e:
        st.error(f"Error al generar la descarga: {e}")
