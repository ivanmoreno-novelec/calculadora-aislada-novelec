import streamlit as st
import pandas as pd
import math

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

# Encabezado principal de marca
st.image("https://raw.githubusercontent.com/novelec/branding/main/logo.png", width=220)
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

# Inicialización del Session State para electrodomésticos personalizados
if "custom_appliances" not in st.session_state:
    st.session_state.custom_appliances = []

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

    col_c4, col_c5, col_c6 = st.columns([1, 1, 1])
    with col_c4:
        system_efficiency = st.slider("Rendimiento del Sistema (%)", 70, 95, 85, key="config_losses") / 100.0
    with col_c5:
        autonomy_days = st.slider("Días de Autonomía", 1, 5, 2, key="config_autonomy")
    with col_c6:
        dod_max = st.slider("DoD Máxima Baterías (%)", 50, 100, 90, key="config_dod") / 100.0

    col_c7, col_c8 = st.columns([1, 2])
    with col_c7:
        num_rows = st.number_input("Número de filas de paneles", min_value=1, max_value=10, value=3, key="config_rows")
    with col_c8:
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
            
        st.markdown(f"📊 **HSP Invierno Catalunya:** `{hsp} h` (Mes crítico de Diciembre)")

# Pestañas principales
tab1, tab2, tab3 = st.tabs(["📋 Consumos y Dimensionamiento", "🛠️ Resumen de Materiales (BOM)", "⚡ Manual de Instalación"])

with tab1:
    st.subheader("💡 Estimación de Consumo Diario")
    st.markdown("Activa los receptores de la vivienda y configura su cantidad y uso con controles táctiles optimizados:")

    # Base de datos de electrodomésticos agrupados por categorías para móvil
    CATEGORIZED_DEFAULT_APPLIANCES = {
        "❄️ Climatización y Refrigeración": [
            {"name": "Nevera (Consumo medio integrado)", "w": 80, "qty": 1, "hours": 8.75},
            {"name": "Bomba de calor y aire (Inverter)", "w": 800, "qty": 1, "hours": 4.00},
            {"name": "Termo eléctrico (100l) — [1500W]", "w": 1500, "qty": 1, "hours": 1.50}
        ],
        "🍳 Cocina, Lavado y Agua": [
            {"name": "Bomba de agua de presión", "w": 500, "qty": 1, "hours": 0.50},
            {"name": "Cafetera Nespresso", "w": 1450, "qty": 1, "hours": 0.10},
            {"name": "Microondas", "w": 1200, "qty": 1, "hours": 0.20},
            {"name": "Lavadora (Prorrata diaria)", "w": 70, "qty": 1, "hours": 0.07}
        ],
        "🔌 Iluminación y Ocio": [
            {"name": "Iluminación LED general", "w": 10, "qty": 5, "hours": 4.00},
            {"name": "Ventiladores de techo con luz", "w": 50, "qty": 2, "hours": 6.00},
            {"name": "Televisor LED compacto", "w": 60, "qty": 1, "hours": 4.00},
            {"name": "Ordenador portátil", "w": 65, "qty": 1, "hours": 3.00}
        ]
    }

    active_appliances = []

    # Renderizado táctil amigable por grupos
    for category, items in CATEGORIZED_DEFAULT_APPLIANCES.items():
        with st.expander(category, expanded=True):
            for item in items:
                # Línea de cabecera con checkbox táctil grande
                is_active = st.checkbox(
                    f"**{item['name']}** ({item['w']} W)",
                    value=True,
                    key=f"check_{item['name']}"
                )
                if is_active:
                    col_q, col_h = st.columns(2)
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
                        "Potencia (W)": item["w"],
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
    st.subheader("📊 Resultados de Dimensionamiento")
    
    # Selector de paneles
    selected_panel_name = st.selectbox("Selecciona el Panel Solar LONGi", list(PANELS_DB.keys()), index=1)
    panel_specs = PANELS_DB[selected_panel_name]
    
    # Cálculo real de paneles
    energy_adjusted = total_daily_energy / system_efficiency
    min_pv_power = energy_adjusted / hsp if hsp > 0 else 0
    min_panels_theoretical = math.ceil(min_pv_power / panel_specs["p_pico"]) if panel_specs["p_pico"] > 0 else 0
    
    # Paneles reales configurados en estructura (Cálculo dinámico basado en consumo y simetría de filas)
    if num_rows > 0:
        total_panels_configured = math.ceil(min_panels_theoretical / num_rows) * num_rows
        panels_per_row = total_panels_configured // num_rows
    else:
        total_panels_configured = 0
        panels_per_row = 0
        
    total_pv_power_real = total_panels_configured * panel_specs["p_pico"]
    
    # Baterías Sizing
    useful_acc_required = total_daily_energy * autonomy_days / dod_max
    batteries_qty = math.ceil(useful_acc_required / 5040)  # Cada TBB ES100II tiene 5,04 kWh útiles nominales
    
    # Renderizar tarjetas de métricas optimizadas para pantalla móvil (apilables verticalmente)
    st.markdown("""<div class="row">""", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
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
    st.markdown("La calculadora selecciona dinámicamente las referencias de catálogo y calcula el presupuesto a PVP de tarifa oficial (sin descuentos aplicados):")
    
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
    
    # Fusibles MEGA desglosados unitariamente (Fraccionados de caja de 5 uds a 7,60€ PVP)
    bom_items.append({
        "Categoría": "Fusibles de Potencia",
        "Referencia": "CIP138125020",
        "Descripción": "Victron MEGA-fuse 125A/80V para CC (Paquete de 5 uds)",
        "Cantidad": 1,
        "Unidad": "uds",
        "PVP Tarifa (€)": 7.60,
        "Descuento": 0.0,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Fusibles de Potencia",
        "Referencia": bat_fuse_ref,
        "Descripción": bat_fuse_name,
        "Cantidad": 1 if batteries_qty > 0 else 0,
        "Unidad": "uds",
        "PVP Tarifa (€)": 7.60,
        "Descuento": 0.0,
        "Is_Victron": True
    })
    bom_items.append({
        "Categoría": "Fusibles de Potencia",
        "Referencia": "CIP138200020",
        "Descripción": "Victron MEGA-fuse 200A/80V para CC (Paquete de 5 uds)",
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
