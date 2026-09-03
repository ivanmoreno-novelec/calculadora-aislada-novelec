import streamlit as st
import pandas as pd
import math

# Configuración de página
st.set_page_config(
    page_title="Novelec - Calculadora Solar Aislada Interactiva",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo corporativo personalizado (Identidad Novelec)
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
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
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
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
        border-left: 5px solid #002f54;
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #002f54;
        margin-top: 0.2rem;
    }
    .metric-title {
        font-size: 0.9rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado principal de marca
st.image("https://raw.githubusercontent.com/novelec/branding/main/logo.png", width=220) # Fallback elegante si no carga
st.title("☀️ Calculadora Solar Aislada Inteligente")
st.markdown("**Diseño y Sizing de Ingeniería Avanzada para Instalaciones Off-Grid - Novelec Servicios Técnicos**")
st.markdown("---")

# Inicialización de bases de datos
PANELS_DB = {
    "LONGi LR7-54HVB-495M (495Wp)": {"p_pico": 495, "voc": 39.5, "isc": 14.1, "desc": "HPBC 2.0 Full-Black"},
    "LONGi LR7-60HVH-545M (545Wp)": {"p_pico": 545, "voc": 44.98, "isc": 15.35, "desc": "Alta eficiencia 24.8% BC"},
    "LONGi LR7-60HVH-560M (560Wp)": {"p_pico": 560, "voc": 45.4, "isc": 15.6, "desc": "Alta eficiencia 24.8% BC"}
}

INVERTER_DB = {
    "PMP482305010": {"nombre": "Victron MultiPlus-II 48/3000/35-32", "pvp": 624.0, "current": 100},
    "PMP482505010": {"nombre": "Victron MultiPlus-II 48/5000/70-50", "pvp": 844.0, "current": 200},
    "PMP482805000": {"nombre": "Victron MultiPlus-II 48/8000/110-100", "pvp": 1551.0, "current": 300},
    "PMP483105000": {"nombre": "Victron MultiPlus-II 48/10000/140-100", "pvp": 1853.0, "current": 400},
    "PMP483150000": {"nombre": "Victron MultiPlus-II 48/15000/200-100", "pvp": 2585.0, "current": 500}
}

# Sidebar - Parámetros Geográficos y Técnicos
st.sidebar.header("⚙️ Parámetros de Diseño")

# 1. Cubierta
roof_type = st.sidebar.selectbox(
    "Tipo de Cubierta",
    ["Inclinada Teja", "Inclinada Chapa (Sándwich)", "Plana"]
)

# 2. Orientación e Inclinación (para HSP)
orientation = st.sidebar.selectbox("Orientación", ["Sur", "Este", "Oeste"])
tilt = st.sidebar.selectbox("Inclinación", ["5º", "7º", "10º", "15º", "30º", "45º"], index=3)

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
    hsp = 2.0 # En cubierta plana el HSP de invierno se fija a 2.0 según la calculadora excel

st.sidebar.markdown(f"**HSP Invierno Calculada:** `{hsp} h` ❄️")

# 3. Datos de Instalación
st.sidebar.subheader("🔌 Configuración Eléctrica")
system_efficiency = st.sidebar.slider("Rendimiento del Sistema (%)", 70, 95, 85) / 100.0
autonomy_days = st.sidebar.slider("Días de Autonomía", 1, 5, 2)
dod_max = st.sidebar.slider("DoD Máxima Baterías (%)", 50, 100, 90) / 100.0

st.sidebar.subheader("📐 Disposición Estructural")
num_rows = st.sidebar.number_input("Número de filas", min_value=1, max_value=10, value=3)

# Pestañas principales
tab1, tab2, tab3 = st.tabs(["📋 Consumos y Dimensionamiento", "🛠️ Resumen de Materiales (BOM)", "⚡ Manual de Instalación"])

with tab1:
    st.subheader("💡 Estimación de Consumo Diario")
    st.markdown("Introduce la potencia y horas de uso estimadas de los receptores activos en la vivienda:")
    
    # Creación de tabla de cargas
    appliances_data = [
        {"Electrodoméstico": "Nevera (Consumo medio integrado)", "Potencia (W)": 80, "Cant.": 1, "Horas": 8.75},
        {"Electrodoméstico": "Bomba de agua de presión", "Potencia (W)": 500, "Cant.": 1, "Horas": 0.50},
        {"Electrodoméstico": "Ventiladores de techo con luz", "Potencia (W)": 50, "Cant.": 2, "Horas": 6.00},
        {"Electrodoméstico": "Iluminación LED general", "Potencia (W)": 10, "Cant.": 5, "Horas": 4.00},
        {"Electrodoméstico": "Cafetera Nespresso", "Potencia (W)": 1450, "Cant.": 1, "Horas": 0.10},
        {"Electrodoméstico": "Bomba de calor y aire (Inverter)", "Potencia (W)": 800, "Cant.": 1, "Horas": 4.00},
        {"Electrodoméstico": "Lavadora (Prorrata diaria)", "Potencia (W)": 70, "Cant.": 1, "Horas": 0.07},
        {"Electrodoméstico": "Televisor LED compacto", "Potencia (W)": 60, "Cant.": 1, "Horas": 4.00},
        {"Electrodoméstico": "Ordenador portátil", "Potencia (W)": 65, "Cant.": 1, "Horas": 3.00},
        {"Electrodoméstico": "Microondas", "Potencia (W)": 1200, "Cant.": 1, "Horas": 0.20},
        {"Electrodoméstico": "Termo eléctrico (100l) — [1500W]", "Potencia (W)": 1500, "Cant.": 1, "Horas": 1.50}
    ]
    
    edited_df = st.data_editor(
        pd.DataFrame(appliances_data),
        num_rows="dynamic",
        use_container_width=True
    )
    
    # Cálculos de Energía y Potencia Simultánea
    edited_df["Consumo Diario (Wh/día)"] = edited_df["Potencia (W)"] * edited_df["Cant."] * edited_df["Horas"]
    total_daily_energy = edited_df["Consumo Diario (Wh/día)"].sum()
    total_simultaneous_power = (edited_df["Potencia (W)"] * edited_df["Cant."]).sum()
    
    # Coeficiente de simultaneidad y VA
    sim_coeff = 0.70
    power_va = (total_simultaneous_power * sim_coeff) / 0.80
    
    # Paneles Sizing
    st.markdown("---")
    st.subheader("📊 Resultados de Dimensionamiento")
    
    # Selector de paneles
    selected_panel_name = st.selectbox("Selecciona el Panel Solar LONGi", list(PANELS_DB.keys()), index=1)
    panel_specs = PANELS_DB[selected_panel_name]
    
    # Cálculo real de paneles
    energy_adjusted = total_daily_energy / system_efficiency
    min_pv_power = energy_adjusted / hsp
    min_panels_theoretical = math.ceil(min_pv_power / panel_specs["p_pico"])
    
    # Paneles reales configurados en estructura (Cálculo dinámico basado en consumo y simetría de filas)
    total_panels_configured = math.ceil(min_panels_theoretical / num_rows) * num_rows
    panels_per_row = total_panels_configured // num_rows
    total_pv_power_real = total_panels_configured * panel_specs["p_pico"]
    
    # Baterías Sizing
    useful_acc_required = total_daily_energy * autonomy_days / dod_max
    batteries_qty = math.ceil(useful_acc_required / 5040)  # Cada TBB ES100II tiene 5,04 kWh útiles nominales
    
    # Renderizar tarjetas de métricas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Consumo Diario</div>
            <div class="metric-value">{total_daily_energy/1000:.2f} kWh</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Potencia Requerida</div>
            <div class="metric-value">{power_va:.0f} VA</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Paneles Montados</div>
            <div class="metric-value">{total_panels_configured} uds ({total_pv_power_real/1000:.2f} kWp)</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Baterías TBB</div>
            <div class="metric-value">{batteries_qty} uds ({batteries_qty*5.04:.2f} kWh)</div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.subheader("📦 Resumen de Materiales y Presupuesto Inteligente (BOM)")
    st.markdown("La calculadora selecciona dinámicamente las referencias y aplica un **43% de descuento profesional** sobre el material de Victron Energy:")
    
    # 1. Inverter Sizing & Manual Override
    auto_inverter_ref = "PMP482305010"
    if power_va < 3000:
        auto_inverter_ref = "PMP482305010"
    elif power_va < 5000:
        auto_inverter_ref = "PMP482505010"
    elif power_va < 8000:
        auto_inverter_ref = "PMP482805000"
    elif power_va < 10000:
        auto_inverter_ref = "PMP483105000"
    else:
        auto_inverter_ref = "PMP483150000"
        
    manual_inverter_choice = st.selectbox(
        "Forzar Inversor / Cargador (Opcional)",
        ["Automático (Recomendado)"] + [f"{k} - {v['nombre']}" for k, v in INVERTER_DB.items()]
    )
    
    if manual_inverter_choice == "Automático (Recomendado)":
        final_inverter_ref = auto_inverter_ref
    else:
        final_inverter_ref = manual_inverter_choice.split(" - ")[0]
        
    inverter_specs = INVERTER_DB[final_inverter_ref]
    
    # 2. Regulator Sizing
    if total_pv_power_real <= 5800:
        regulator_ref = "SCC125110412"
        regulator_name = "Victron SmartSolar MPPT 250/100-Tr VE.Can"
        regulator_pvp = 654.00
    else:
        regulator_ref = "SCC145110512"
        regulator_name = "Victron SmartSolar MPPT RS 450/100-MC4 (2 seguidores de alta tensión)"
        regulator_pvp = 1182.00
        
    # 3. Gave Box selection
    if regulator_ref == "SCC125110412":
        gave_ref = "STM40480P20"
        gave_name = "Caja Solartec 4 strings (80A seccionador, sobretensiones Tipo II)"
        gave_pvp = 445.85
    else:
        gave_ref = "STM210NSP20"
        gave_name = "Caja Solartec 2 strings 1000V (Protección sobretensiones Tipo II para MPPT RS)"
        gave_pvp = 288.21

    # 4. Battery unweighted max calculations
    battery_current = max(100, inverter_specs["current"])
    
    # Fuse Sizing for batteries based on max operational currents
    if battery_current <= 125:
        bat_fuse_ref = "CIP138125020"
        bat_fuse_name = "Victron MEGA-fuse 125A/80V para CC (Paquete de 5 uds)"
    elif battery_current <= 200:
        bat_fuse_ref = "CIP138200020"
        bat_fuse_name = "Victron MEGA-fuse 200A/80V para CC (Paquete de 5 uds)"
    elif battery_current <= 300:
        bat_fuse_ref = "CIP138300020"
        bat_fuse_name = "Victron MEGA-fuse 300A/80V para CC (Paquete de 5 uds)"
    else:
        bat_fuse_ref = "CIP138500020"
        bat_fuse_name = "Victron MEGA-fuse 500A/80V para CC (Paquete de 5 uds)"

    # Contrucción del Presupuesto
    bom_items = []
    
    # Módulos Solares
    bom_items.append({
        "Categoría": "Generación Solar",
        "Referencia": panel_specs["desc"],
        "Descripción": f"Panel solar {selected_panel_name}",
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
            "Referencia": "26H-A-15-C",
            "Descripción": "Kit Inicial Sunfer 26H 15º Crudo (Doble Horizontal)",
            "Cantidad": num_rows,
            "Unidad": "uds",
            "PVP Tarifa (€)": 204.90,
            "Descuento": 0.0,
            "Is_Victron": False
        })
        if total_panels_configured > num_rows:
            bom_items.append({
                "Categoría": "Estructura de Soporte",
                "Referencia": "26H-B-15-C",
                "Descripción": "Kit Ampliación Sunfer 26H 15º Crudo (Doble Horizontal)",
                "Cantidad": total_panels_configured - num_rows,
                "Unidad": "uds",
                "PVP Tarifa (€)": 112.20,
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
        
        perfiles_qty = math.ceil((2 * panels_per_row * 1.134) / 4.8) * num_rows
        uniones_qty = max(0, (math.ceil((panels_per_row * 1.134) / 4.8) - 1) * 2 * num_rows)
        
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
            "Cantidad": 2 * panels_per_row * num_rows,
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
            "Cantidad": 2 * (panels_per_row - 1) * num_rows,
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
        "Descuento": 0.43,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Regulador de Carga",
        "Referencia": regulator_ref,
        "Descripción": regulator_name,
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": regulator_pvp,
        "Descuento": 0.43,
        "Is_Victron": True
    })
    
    # Baterías y brackets
    bom_items.append({
        "Categoría": "Acumulación (Batería)",
        "Referencia": "TBB ES100II",
        "Descripción": "Batería Litio TBB LiFePO4 ES100 II 48V 105Ah (5.04 kWh)",
        "Cantidad": batteries_qty,
        "Unidad": "uds",
        "PVP Tarifa (€)": 935.0,
        "Descuento": 0.0,
        "Is_Victron": False
    })
    bom_items.append({
        "Categoría": "Acumulación (Soporte)",
        "Referencia": "Brackets ES100II",
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
        "Descuento": 0.43,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Monitorización y GX",
        "Referencia": "BPP900455050",
        "Descripción": "Victron GX Touch 50 (Pantalla táctil a color de 5 pulgadas)",
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 235.0,
        "Descuento": 0.43,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Monitorización y GX",
        "Referencia": "BPP900465050",
        "Descripción": "Soporte de pared para pantalla GX Touch 50 Wall Mount",
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 16.0,
        "Descuento": 0.43,
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
        "Descuento": 0.43,
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
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 37.0,
        "Descuento": 0.43,
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
        "Descuento": 0.43,
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
            "Descuento": 0.43,
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
            "Descuento": 0.43,
            "Is_Victron": True
        })
        
    bom_items.append({
        "Categoría": "Cable de Datos",
        "Referencia": "ASS030710118",
        "Descripción": "Cable BMS VE.Can a CAN-bus, Tipo A 1.8 m (TBB a Cerbo)",
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 15.0,
        "Descuento": 0.43,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Cable de Datos",
        "Referencia": "ASS030700000",
        "Descripción": "Terminadores RJ45 VE.Can (Bolsa de 2 unidades)",
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 10.0,
        "Descuento": 0.43,
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
    
    # Fusibles MEGA desglosados unitariamente (Fraccionados de caja de 5 uds a 7,60€ PVP)
    bom_items.append({
        "Categoría": "Fusibles de Potencia",
        "Referencia": "CIP138125020",
        "Descripción": "Victron MEGA-fuse 125A/80V para CC (Paquete de 5 uds)",
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 7.60,
        "Descuento": 0.43,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Fusibles de Potencia",
        "Referencia": bat_fuse_ref,
        "Descripción": bat_fuse_name,
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 7.60,
        "Descuento": 0.43,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Fusibles de Potencia",
        "Referencia": "CIP138200020",
        "Descripción": "Victron MEGA-fuse 200A/80V para CC (Paquete de 5 uds)",
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 7.60,
        "Descuento": 0.43,
        "Is_Victron": True
    })

    # Procesado de DataFrame final
    df_bom = pd.DataFrame(bom_items)
    df_bom["Precio Unit. Neto (€)"] = df_bom["PVP Tarifa (€)"] * (1 - df_bom["Descuento"])
    df_bom["Precio Total Neto (€)"] = df_bom["Cantidad"] * df_bom["Precio Unit. Neto (€)"]
    
    # Visualizar presupuesto
    df_display = df_bom[["Categoría", "Referencia", "Descripción", "Cantidad", "Unidad", "PVP Tarifa (€)", "Descuento", "Precio Unit. Neto (€)", "Precio Total Neto (€)"]]
    st.dataframe(df_display.style.format({
        "PVP Tarifa (€)": "{:,.2f} €",
        "Descuento": "{:.0%}",
        "Precio Unit. Neto (€)": "{:,.2f} €",
        "Precio Total Neto (€)": "{:,.2f} €"
    }), use_container_width=True, height=600)
    
    total_net = df_bom["Precio Total Neto (€)"].sum()
    
    col_t1, col_t2 = st.columns(2)
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
    Es un error frecuente en obra tratar de conectar reguladores de alta tensión mediante cable VE.Direct. Sigue esta pauta obligatoria:
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
