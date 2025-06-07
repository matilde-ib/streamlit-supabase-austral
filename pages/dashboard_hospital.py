# pages/dashboard_hospital.py (Versión Completa, Funcional y Corregida)

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
from math import radians, sin, cos, sqrt, atan2

# --- Configuración de Path y Conexión ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from functions import connect_to_supabase, execute_query

# --- Configuración de la Página ---
st.set_page_config(page_title="TissBank - Portal Hospitalario", page_icon="🏥", layout="wide")

# --- INYECCIÓN DE CSS PARA ESTÉTICA PROFESIONAL ---
def load_css():
    st.markdown("""
        <style>
            :root {
                --primary-color: #0078D4; --background-color: #F8F9FA; --card-background-color: #FFFFFF;
                --text-color: #212529; --border-color: #DEE2E6; --font-family: 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
            }
            [data-testid="stAppViewContainer"] > .main { background-color: var(--background-color); }
            .st-expander {
                border: 1px solid var(--border-color); box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                border-radius: 12px; background: var(--card-background-color); margin-bottom: 2rem;
            }
            .st-expander header { font-size: 1.2rem; font-weight: 600; color: var(--primary-color); padding: 1rem; }
            .stButton>button {
                font-weight: 600; border-radius: 8px; border: 2px solid var(--primary-color);
                background-color: var(--primary-color); color: white; padding: 0.6rem 1.2rem;
                transition: all 0.2s ease-in-out;
            }
            .stButton>button:hover { background-color: white; color: var(--primary-color); }
        </style>
    """, unsafe_allow_html=True)

# --- Funciones de Utilidad y Carga de Datos ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371; dlat = radians(lat2 - lat1); dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a)); return R * c

@st.cache_data
def get_hospitales_principales():
    data = [
        {"name": "Hospital Italiano", "address": "Tte. Gral. Juan Domingo Perón 4190, CABA", "lat": -34.6066, "lon": -58.4250},
        {"name": "Hospital Alemán", "address": "Av. Pueyrredón 1640, CABA", "lat": -34.5938, "lon": -58.4033},
        {"name": "Hospital Británico", "address": "Perdriel 74, CABA", "lat": -34.6284, "lon": -58.3840},
        {"name": "Hospital Garrahan", "address": "Pichincha 1890, CABA", "lat": -34.6293, "lon": -58.3908},
        {"name": "Hospital Fernández", "address": "Av. Cerviño 3356, CABA", "lat": -34.5822, "lon": -58.4111},
        {"name": "Hospital de Clínicas", "address": "Av. Córdoba 2351, CABA", "lat": -34.5989, "lon": -58.4005},
        {"name": "Sanatorio Güemes", "address": "Francisco Acuña de Figueroa 1240, CABA", "lat": -34.5983, "lon": -58.4214},
        {"name": "FLENI", "address": "Montañeses 2325, CABA", "lat": -34.5501, "lon": -58.4485},
        {"name": "Hospital Austral", "address": "Av. J. D. Perón 1500, Pilar", "lat": -34.4528, "lon": -58.9133},
        {"name": "Hospital Argerich", "address": "Pi y Margall 750, CABA", "lat": -34.6241, "lon": -58.3662},
        {"name": "Hospital Rivadavia", "address": "Av. Gral. Las Heras 2670, CABA", "lat": -34.5880, "lon": -58.3990},
        {"name": "Hospital Durand", "address": "Av. Díaz Vélez 5044, CABA", "lat": -34.6112, "lon": -58.4442},
        {"name": "Hospital Santojanni", "address": "Pilar 950, CABA", "lat": -34.6465, "lon": -58.5134},
        {"name": "Sanatorio Finochietto", "address": "Av. Córdoba 2678, CABA", "lat": -34.6043, "lon": -58.4045},
        {"name": "Fundación Favaloro", "address": "Av. Belgrano 1746, CABA", "lat": -34.6120, "lon": -58.3900}
    ]
    return pd.DataFrame(data)

@st.cache_data(ttl=300)
def get_donantes(_conn):
    return execute_query("SELECT id, nombre, apellido, dni FROM donante ORDER BY apellido, nombre", conn=_conn, is_select=True)

@st.cache_data(ttl=300)
def get_medicos(_conn):
    return execute_query("SELECT id, nombre, apellido, dni FROM medico ORDER BY apellido, nombre", conn=_conn, is_select=True)

@st.cache_data(ttl=300)
def get_tipos_tejido(_conn):
    return execute_query("SELECT tipo, descripcion FROM detalles_tejido ORDER BY descripcion", conn=_conn, is_select=True)

# --- INICIO DE LA APLICACIÓN ---
load_css()

if not st.session_state.get("logged_in") or st.session_state.get("role") != "Hospital":
    st.warning("No tienes permiso para acceder. Por favor, inicia sesión."); st.stop()

conn = connect_to_supabase()
if conn is None: st.error("Error fatal de conexión a la base de datos."); st.stop()

hospital_id = int(st.session_state.get("user_id", 0))
hospital_nombre = st.session_state.get("user_name", "Desconocido")

# --- BARRA LATERAL CON TODAS LAS OPCIONES ---
st.sidebar.title("Portal Hospitalario")
st.sidebar.info(f"**{hospital_nombre}**")
st.sidebar.markdown("---")
st.sidebar.header("Utilidades")
opcion_utilidades = st.sidebar.radio(
    "Seleccione una herramienta:",
    ["Gestión de Inventario", "Gestión de Solicitudes", "Dashboard Analítico", "Trazabilidad de Tejidos", "Red de Hospitales y Logística"]
)

# --- CONTENIDO PRINCIPAL ---

if opcion_utilidades == "Gestión de Inventario":
    st.title("📦 Gestión de Inventario")
    st.markdown("Registre nuevas unidades y actualice el estado del stock.")
    st.markdown("---")
    
    with st.expander("➕ **Registrar Nuevo Tejido**", expanded=False):
        if "tipo_donante" not in st.session_state: st.session_state.tipo_donante = "Nuevo Donante"
        st.radio("Paso 1: Tipo de donante", ["Nuevo Donante", "Donante Existente"], key="tipo_donante", horizontal=True)
        with st.form("form_registro_final"):
            if st.session_state.tipo_donante == "Donante Existente":
                st.subheader("Seleccionar Donante")
                donantes_df = get_donantes(conn)
                if not donantes_df.empty:
                    opciones_donante = [f"{row['apellido']}, {row['nombre']} (DNI: {row['dni']})" for _, row in donantes_df.iterrows()]
                    donante_sel = st.selectbox("Donante", opciones_donante, index=None, placeholder="Elige un donante existente...")
            else:
                st.subheader("Datos del Nuevo Donante")
                c1, c2 = st.columns(2); nombre_donante = c1.text_input("Nombre(s)"); apellido_donante = c2.text_input("Apellido(s)")
                c3, c4 = st.columns(2); dni_donante = c3.text_input("DNI (solo números)"); sexo_donante = c4.selectbox("Sexo", ["Masculino", "Femenino"])
            st.markdown("---")
            st.subheader("Paso 2: Datos de Recolección")
            medicos_df = get_medicos(conn)
            if not medicos_df.empty:
                opciones_medico = [f"{row['apellido']}, {row['nombre']} (DNI: {row['dni']})" for _, row in medicos_df.iterrows()]
                medico_sel = st.selectbox("Médico Recolector", opciones_medico, index=None, placeholder="Elige un médico...")
            else:
                st.error("No hay médicos registrados."); medico_sel = None
            tipos_tejido_df = get_tipos_tejido(conn)
            if not tipos_tejido_df.empty:
                opciones_tejido = [f"{row['descripcion']} ({row['tipo']})" for _, row in tipos_tejido_df.iterrows()]
                tejido_sel = st.selectbox("Tipo de Tejido", opciones_tejido, index=None, placeholder="Elige un tipo de tejido...")
            else:
                st.error("No se encontraron tipos de tejido."); tejido_sel = None
            c5, c6 = st.columns(2)
            fecha_recoleccion = c5.date_input("Fecha de Recolección", datetime.now().date())
            estado_inicial = c6.selectbox("Estado Inicial", ['Disponible', 'En Cuarentena'])
            condicion_recoleccion = st.text_area("Condición de Recolección", placeholder="Ej: óptima, sin patologías...")
            submitted = st.form_submit_button("Registrar Tejido", use_container_width=True)
            if submitted:
                # Lógica de registro completa y funcional
                id_donante_final = None
                if st.session_state.tipo_donante == "Nuevo Donante":
                    if all([nombre_donante, apellido_donante, dni_donante]):
                        try:
                            dni_int = int(dni_donante)
                            insert_query = "INSERT INTO donante (nombre, apellido, dni, sexo) VALUES (%s, %s, %s, %s) RETURNING id"
                            new_id_df = execute_query(insert_query, conn, (nombre_donante, apellido_donante, dni_int, sexo_donante), is_select=True)
                            if new_id_df is not None and not new_id_df.empty:
                                id_donante_final = int(new_id_df.iloc[0]['id'])
                        except Exception as e: st.error(f"Error al registrar donante: {e}")
                    else: st.error("Faltan datos del nuevo donante.")
                else:
                    if 'donante_sel' in locals() and donante_sel:
                        dni_sel_val = int(donante_sel.split("DNI: ")[1][:-1])
                        id_donante_final = int(donantes_df[donantes_df['dni'] == dni_sel_val].iloc[0]['id'])
            
                id_medico_final = None
                if medico_sel:
                    dni_medico_sel_val = int(medico_sel.split("DNI: ")[1][:-1])
                    id_medico_final = int(medicos_df[medicos_df['dni'] == dni_medico_sel_val].iloc[0]['id'])

                if id_donante_final and id_medico_final and tejido_sel:
                    tejido_code = tejido_sel.split('(')[-1][:-1]
                    query = "INSERT INTO tejidos (tipo, id_donante, id_medico, id_hospital, fecha_recoleccion, condicion_recoleccion, estado, fecha_de_estado) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())"
                    params = (tejido_code, id_donante_final, id_medico_final, hospital_id, fecha_recoleccion, condicion_recoleccion, estado_inicial)
                    if execute_query(query, conn, params, is_select=False):
                        st.success("✅ ¡Tejido registrado exitosamente!")
                        st.cache_data.clear(); st.rerun()
                else:
                    if not id_donante_final: st.error("Error de validación: El donante no fue definido.")
                    if not id_medico_final: st.error("Error de validación: El médico no fue seleccionado.")
                    if not tejido_sel: st.error("Error de validación: El tipo de tejido no fue seleccionado.")

    with st.expander("🔄 **Actualizar Estado de Tejido Existente**"):
        query_inventory_update = "SELECT t.id, dt.descripcion, t.estado, t.fecha_recoleccion, d.nombre || ' ' || d.apellido as donante FROM tejidos t LEFT JOIN detalles_tejido dt ON t.tipo = dt.tipo LEFT JOIN donante d ON t.id_donante = d.id WHERE t.id_hospital = %s ORDER BY t.id DESC"
        inventory_df_update = execute_query(query_inventory_update, conn=conn, params=(hospital_id,), is_select=True)
        
        if not inventory_df_update.empty:
            with st.form("form_update_estado_final"):
                opciones_tejido = [f"ID: {row['id']} - {row['descripcion']} (Donante: {row['donante']}, Rec: {row['fecha_recoleccion']})" for _, row in inventory_df_update.iterrows()]
                tejido_sel_update = st.selectbox("Tejido a actualizar", opciones_tejido)
                estados_validos = ['Disponible', 'En Cuarentena', 'Reservado', 'Enviado', 'Rechazado']
                new_estado = st.selectbox("Nuevo Estado", estados_validos)
                submitted_update = st.form_submit_button("Actualizar Estado", use_container_width=True)

                if submitted_update:
                    id_to_update = int(tejido_sel_update.split(' ')[1])
                    query_update = "UPDATE tejidos SET estado = %s, fecha_de_estado = NOW() WHERE id = %s"
                    if execute_query(query_update, conn, (new_estado, id_to_update), is_select=False):
                        st.success(f"✅ Estado del tejido ID {id_to_update} actualizado a '{new_estado}'.")
                        st.cache_data.clear(); st.rerun()
        else:
            st.info("No hay tejidos en tu inventario para actualizar.")

    st.markdown("---")
    st.subheader("Inventario Actual")
    inventory_df_final = execute_query(f"SELECT t.id, dt.descripcion, t.estado, t.fecha_recoleccion, d.nombre || ' ' || d.apellido as donante FROM tejidos t LEFT JOIN detalles_tejido dt ON t.tipo = dt.tipo LEFT JOIN donante d ON t.id_donante = d.id WHERE t.id_hospital = {hospital_id} ORDER BY t.id DESC", conn, is_select=True)
    st.dataframe(inventory_df_final, use_container_width=True, hide_index=True)


elif opcion_utilidades == "Gestión de Solicitudes":
    st.title("📬 Gestión de Solicitudes de Médicos")
    st.markdown("Revise y procese las solicitudes de tejido pendientes.")
    
    query = """
        SELECT s.id, s.fecha_solicitud, s.tipo, s.ubicacion, m.nombre, m.apellido 
        FROM solicitud s JOIN medico m ON s.medico_id = m.id WHERE s.estado = 'pendiente' ORDER BY s.fecha_solicitud ASC;
    """
    solicitudes_df = execute_query(query, conn=conn, is_select=True)

    if solicitudes_df.empty:
        st.info("No hay solicitudes pendientes para revisar.")
    else:
        st.subheader(f"Solicitudes Pendientes: {len(solicitudes_df)}")
        st.markdown("---")
        for _, row in solicitudes_df.iterrows():
            with st.container(border=True):
                st.markdown(f"**ID:** {row['id']} | **Fecha:** {row['fecha_solicitud'].strftime('%d/%m/%Y')} | **Médico:** {row['nombre']} {row['apellido']}")
                st.markdown(f"**Tejido Solicitado:** {row['tipo']} ({row['ubicacion']})")
                c1, c2, _ = st.columns([1, 1, 8])
                if c1.button("✅ Aprobar", key=f"approve_{row['id']}"):
                    tejido_disponible_q = "SELECT id FROM tejidos WHERE tipo = %s AND estado = 'Disponible' AND id_hospital = %s LIMIT 1"
                    tejido_disp_df = execute_query(tejido_disponible_q, conn, (row['tipo'], hospital_id), is_select=True)
                    if not tejido_disp_df.empty:
                        id_tejido_a_reservar = tejido_disp_df.iloc[0]['id']
                        update_tejido_q = "UPDATE tejidos SET estado = 'Reservado' WHERE id = %s"
                        execute_query(update_tejido_q, conn, (id_tejido_a_reservar,), is_select=False)
                        update_solicitud_q = "UPDATE solicitud SET estado = 'aprobada' WHERE id = %s"
                        execute_query(update_solicitud_q, conn, (row['id'],), is_select=False)
                        st.success(f"Solicitud {row['id']} aprobada. Tejido ID {id_tejido_a_reservar} ha sido reservado.")
                        st.rerun()
                    else:
                        st.warning(f"No hay tejidos de tipo '{row['tipo']}' disponibles para aprobar esta solicitud.")
                
                if c2.button("❌ Rechazar", key=f"reject_{row['id']}"):
                    update_solicitud_q = "UPDATE solicitud SET estado = 'rechazada' WHERE id = %s"
                    execute_query(update_solicitud_q, conn, (row['id'],), is_select=False)
                    st.success(f"Solicitud {row['id']} rechazada.")
                    st.rerun()

elif opcion_utilidades == "Dashboard Analítico":
    st.title("📊 Dashboard Analítico")
    st.markdown("Métricas y visualizaciones clave sobre la operación.")
    
    tejidos_df = execute_query(f"SELECT estado, tipo FROM tejidos WHERE id_hospital = {hospital_id}", conn, is_select=True)
    if not tejidos_df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Tejidos en Stock", len(tejidos_df))
        c2.metric("Disponibles", len(tejidos_df[tejidos_df['estado'] == 'Disponible']))
        c3.metric("En Cuarentena", len(tejidos_df[tejidos_df['estado'] == 'En Cuarentena']))
        
        st.markdown("---")
        st.subheader("Composición del Inventario")
        composicion_df = tejidos_df['tipo'].value_counts().reset_index()
        composicion_df.columns = ['Tipo de Tejido', 'Cantidad']
        st.bar_chart(composicion_df.set_index('Tipo de Tejido'))
    else:
        st.info("No hay datos de inventario para generar estadísticas.")

elif opcion_utilidades == "Trazabilidad de Tejidos":
    st.title("🧬 Trazabilidad de Tejidos")
    st.markdown("Busque un tejido por su ID para ver su historial completo.")
    
    tejido_id_busqueda = st.text_input("Ingrese el ID del tejido a rastrear:")
    if st.button("Buscar Tejido", type="primary"):
        if tejido_id_busqueda.isdigit():
            query = """
                SELECT t.*, dt.descripcion, d.nombre as d_nombre, d.apellido as d_apellido, 
                       m.nombre as m_nombre, m.apellido as m_apellido, h.nombre as h_nombre
                FROM tejidos t
                LEFT JOIN detalles_tejido dt ON t.tipo = dt.tipo
                LEFT JOIN donante d ON t.id_donante = d.id
                LEFT JOIN medico m ON t.id_medico = m.id
                LEFT JOIN hospital h ON t.id_hospital = h.id
                WHERE t.id = %s
            """
            trace_df = execute_query(query, conn, (int(tejido_id_busqueda),), is_select=True)
            if not trace_df.empty:
                data = trace_df.iloc[0]
                st.success(f"Información encontrada para el Tejido ID: {data['id']}")
                st.subheader(f"Detalles del Tejido: {data['descripcion']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Estado Actual", data['estado'])
                c2.metric("Fecha Recolección", data['fecha_recoleccion'].strftime('%d/%m/%Y'))
                c3.metric("Última Actualización", data['fecha_de_estado'].strftime('%d/%m/%Y'))
                st.text_area("Condición de Recolección", data['condicion_recoleccion'], height=100, disabled=True)
                st.markdown("---")
                st.subheader("Información de Origen")
                st.markdown(f"**Donante:** {data['d_nombre']} {data['d_apellido']}")
                st.markdown(f"**Médico Recolector:** {data['m_nombre']} {data['m_apellido']}")
                st.markdown(f"**Hospital de Registro:** {data['h_nombre']}")
            else:
                st.error("No se encontró ningún tejido con ese ID.")
        else:
            st.warning("Por favor, ingrese un ID numérico válido.")

elif opcion_utilidades == "Red de Hospitales y Logística":
    st.title("🌐 Red de Hospitales y Logística")
    st.markdown("Visualice la red y calcule tiempos de traslado estimados.")
    st.markdown("---")
    
    hospitales_df = get_hospitales_principales()
    st.subheader("Ubicación de Hospitales en la Red")
    st.map(hospitales_df, latitude='lat', longitude='lon', zoom=10)
    
    with st.expander("Ver lista de hospitales y direcciones"):
        st.dataframe(hospitales_df[['name', 'address']].rename(columns={'name': 'Hospital', 'address': 'Dirección'}), use_container_width=True)
    
    st.markdown("---")
    st.subheader("Calculadora de Tiempo de Traslado Estimado")
    
    col1, col2 = st.columns(2)
    origen = col1.selectbox("📍 Hospital de Origen", options=hospitales_df['name'], index=0)
    destino = col2.selectbox("🏁 Hospital de Destino", options=hospitales_df['name'], index=1)
        
    if st.button("Calcular Tiempo Estimado", type="secondary", use_container_width=True):
        if origen == destino: st.warning("El hospital de origen y destino no pueden ser el mismo.")
        else:
            origen_coords = hospitales_df[hospitales_df['name'] == origen].iloc[0]
            destino_coords = hospitales_df[hospitales_df['name'] == destino].iloc[0]
            distancia = haversine(origen_coords['lat'], origen_coords['lon'], destino_coords['lat'], destino_coords['lon'])
            velocidad_promedio_kmh = 30
            tiempo_horas = distancia / velocidad_promedio_kmh
            tiempo_minutos = tiempo_horas * 60
            st.success(f"**Resultados de la estimación para la ruta: {origen} ➡️ {destino}**")
            res_col1, res_col2 = st.columns(2)
            res_col1.metric(label="Distancia en línea recta", value=f"{distancia:.2f} km")
            res_col2.metric(label="Tiempo de traslado estimado", value=f"~ {tiempo_minutos:.0f} min")
            google_maps_url = f"https://www.google.com/maps/dir/?api=1&origin={origen_coords['lat']},{origen_coords['lon']}&destination={destino_coords['lat']},{destino_coords['lon']}&travelmode=driving"
            st.link_button("Ver Ruta en Google Maps", google_maps_url, use_container_width=True)
            st.info("Nota: El tiempo estimado no considera tráfico real. El enlace a Google Maps mostrará la ruta y el tiempo real.")

# --- Cierre de conexión ---
if conn: conn.close()