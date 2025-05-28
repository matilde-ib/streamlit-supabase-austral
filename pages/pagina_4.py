# pages/dashboard_medico.py (pagina 4) - Dashboard para Médicos

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Ajusta el path para importar 'functions.py' desde el directorio padre
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from functions import connect_to_supabase, execute_query

# --- Configuración de la página ---
st.set_page_config(
    page_title="TissBank - Dashboard Médico",
    page_icon="🩺",
    layout="wide"
)

# --- Verificar si el usuario está logueado y es Médico ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"] or st.session_state["role"] != "Médico":
    st.warning("¡No tenés permiso para acceder a esta página! Por favor, iniciá sesión como Médico.")
    if st.button("Volver al inicio de sesión"):
        st.session_state["logged_in"] = False
        st.switch_page("app.py") # Redirige al app.py principal
    st.stop() # Detiene la ejecución de la página

# Obtener datos de sesión del médico
medico_id = st.session_state.get("user_id")
medico_nombre = st.session_state.get("user_name")
medico_dni = st.session_state.get("user_identifier")

st.title(f"Bienvenido, Dr./Dra. {medico_nombre}.")
st.markdown(f"**DNI:** {medico_dni}")
st.markdown("---")

st.sidebar.title("Menú Médico")
# Inicializar la selección del menú del dashboard en la sesión de esta página
if "medico_menu_selection" not in st.session_state:
    st.session_state["medico_menu_selection"] = "Bienvenida"

st.session_state["medico_menu_selection"] = st.sidebar.radio(
    "Navegación",
    ["Bienvenida", "Mis Pacientes", "Registrar Recolección de Tejido", "Consultar Tejidos Disponibles"],
    key="medico_dashboard_menu" # Clave única para esta página
)

# Contenido principal basado en la selección del menú del dashboard
if st.session_state["medico_menu_selection"] == "Bienvenida":
    st.write("Aquí podrás gestionar tus actividades como médico en TissBank.")
    st.info("Esta sección está diseñada para tus necesidades como médico.")
    st.markdown("""
    Desde aquí podrás:
    * **Gestionar tus pacientes.** (Requiere tabla de pacientes)
    * **Registrar nuevas recolecciones de tejidos.**
    * **Consultar los tejidos disponibles** en el banco.
    """)

elif st.session_state["medico_menu_selection"] == "Mis Pacientes":
    st.header("📋 Mis Pacientes")
    st.write("Listado y gestión de tus pacientes.")
    st.warning("Esta sección requiere la creación de una tabla `paciente` y una tabla de relación `medico_paciente` en tu base de datos.")
    
    conn = connect_to_supabase()
    if conn:
        # Ejemplo: Si tuvieras una tabla 'paciente' y una tabla de unión 'medico_paciente'
        # query_pacientes = """
        # SELECT p.id, p.nombre, p.apellido, p.dni
        # FROM paciente p
        # JOIN medico_paciente mp ON p.id = mp.id_paciente
        # WHERE mp.id_medico = %s
        # ORDER BY p.apellido, p.nombre;
        # """
        # pacientes_df = execute_query(query_pacientes, conn=conn, params=(medico_id,), is_select=True)
        st.info("Funcionalidad de listado de pacientes pendiente de la estructura de la base de datos.")
        pacientes_df = pd.DataFrame({
            'ID Paciente': [101, 102],
            'Nombre': ['Juan', 'María'],
            'Apellido': ['Pérez', 'García'],
            'DNI': ['12345678', '87654321']
        })
        conn.close()
    else:
        pacientes_df = pd.DataFrame()
        st.error("No se pudo conectar a la base de datos para obtener pacientes.")

    if not pacientes_df.empty:
        st.dataframe(pacientes_df, use_container_width=True)
    else:
        st.info("No hay pacientes registrados o asociados a tu perfil.")

elif st.session_state["medico_menu_selection"] == "Registrar Recolección de Tejido":
    st.header("💉 Registrar Nueva Recolección de Tejido")
    st.write("Completa el siguiente formulario para registrar la recolección de un nuevo tejido.")

    with st.form("form_register_recoleccion"):
        conn_types = connect_to_supabase()
        if conn_types:
            types_df = execute_query("SELECT tipo, descripcion FROM detalles_tejido ORDER BY descripcion", conn=conn_types, is_select=True)
            conn_types.close()
        else:
            types_df = pd.DataFrame({'tipo': [], 'descripcion': []})

        tejido_tipo_options = types_df.apply(lambda row: f"{row['descripcion']} ({row['tipo']})", axis=1).tolist()
        selected_tejido_display = st.selectbox("Tipo de Tejido Recolectado", ["Seleccione un tipo"] + tejido_tipo_options)
        
        selected_tejido_code = None
        if selected_tejido_display and selected_tejido_display != "Seleccione un tipo":
            selected_tejido_code = selected_tejido_display.split('(')[-1][:-1]

        col_donante, col_hospital_destino = st.columns(2)
        with col_donante:
            id_donante = st.number_input("ID del Donante (opcional, si ya existe)", min_value=1, value=None, format="%d", help="Deja en blanco si el donante aún no está registrado o no aplica directamente.")
            # Opción para registrar un nuevo donante aquí, si es necesario
            st.info("Si el donante no existe, primero debes registrarlo en la sección 'Donantes' del Dashboard del Hospital o añadir un formulario aquí.")
        with col_hospital_destino:
            # Aquí se asume que el médico selecciona a qué hospital enviará el tejido
            conn_hospitals = connect_to_supabase()
            if conn_hospitals:
                hospitals_df = execute_query("SELECT id, nombre FROM hospital ORDER BY nombre", conn=conn_hospitals, is_select=True)
                conn_hospitals.close()
            else:
                hospitals_df = pd.DataFrame({'id': [], 'nombre': []})
            
            hospital_options = hospitals_df.apply(lambda row: f"{row['nombre']} (ID: {row['id']})", axis=1).tolist()
            selected_hospital_display = st.selectbox("Hospital al que se envía el tejido", ["Seleccione un Hospital"] + hospital_options)
            
            selected_hospital_id = None
            if selected_hospital_display and selected_hospital_display != "Seleccione un Hospital":
                selected_hospital_id = int(selected_hospital_display.split('(ID: ')[-1][:-1])

        fecha_recoleccion = st.date_input("Fecha de Recolección", datetime.now().date())
        condicion_recoleccion = st.text_area("Condición de Recolección (ej. 'viable', 'no apto para trasplante')", height=70)
        estado_inicial = st.selectbox("Estado Inicial", ["Disponible", "En Cuarentena", "Rechazado", "En Proceso"])
        
        submit_recoleccion = st.form_submit_button("Registrar Recolección")

        if submit_recoleccion:
            if selected_tejido_code is None:
                st.warning("Por favor, seleccioná un tipo de tejido.")
            elif selected_hospital_id is None:
                st.warning("Por favor, seleccioná el hospital al que se envía el tejido.")
            elif not condicion_recoleccion:
                st.warning("Por favor, ingresa la condición de recolección.")
            else:
                try:
                    conn_recoleccion = connect_to_supabase()
                    if conn_recoleccion:
                        donante_id_val = id_donante if id_donante else None

                        if donante_id_val:
                            check_donante = execute_query("SELECT id FROM donante WHERE id = %s", conn=conn_recoleccion, params=(donante_id_val,), is_select=True)
                            if check_donante.empty:
                                st.error(f"El ID de Donante {donante_id_val} no existe. Por favor, asegúrate de que el donante esté registrado o deja el campo en blanco.")
                                conn_recoleccion.close()
                                st.stop()
                        
                        query_add_tejido = """
                        INSERT INTO tejidos (tipo, id_donante, id_medico, id_hospital, fecha_recoleccion, condicion_recoleccion, estado, fecha_de_estado)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        params_add_tejido = (
                            selected_tejido_code,
                            donante_id_val,
                            medico_id, # El ID del médico logueado
                            selected_hospital_id, # El ID del hospital seleccionado
                            fecha_recoleccion,
                            condicion_recoleccion,
                            estado_inicial,
                            datetime.now().date()
                        )
                        if execute_query(query_add_tejido, conn=conn_recoleccion, params=params_add_tejido, is_select=False):
                            st.success("✅ Recolección de tejido registrada correctamente.")
                            st.rerun()
                        else:
                            st.error("❌ Error al registrar la recolección del tejido.")
                        conn_recoleccion.close()
                    else:
                        st.error("No se pudo conectar a la base de datos.")
                except Exception as e:
                    st.error(f"Ocurrió un error inesperado al registrar la recolección: {e}")

elif st.session_state["medico_menu_selection"] == "Consultar Tejidos Disponibles":
    st.header("🔍 Consultar Tejidos Disponibles")
    st.write("Puedes buscar tejidos disponibles en la red de hospitales. Contacta al hospital propietario para solicitar un tejido.")

    st.subheader("Filtros de Búsqueda")
    col_tipo, col_estado = st.columns(2)
    with col_tipo:
        conn_types_search = connect_to_supabase()
        if conn_types_search:
            types_df_search = execute_query("SELECT tipo, descripcion FROM detalles_tejido ORDER BY descripcion", conn=conn_types_search, is_select=True)
            conn_types_search.close()
        else:
            types_df_search = pd.DataFrame({'tipo': [], 'descripcion': []})
        
        tejido_tipo_options_search = types_df_search.apply(lambda row: f"{row['descripcion']} ({row['tipo']})", axis=1).tolist()
        search_tejido_display = st.selectbox("Filtrar por Tipo de Tejido", ["Todos"] + tejido_tipo_options_search)
        
        search_tejido_code = None
        if search_tejido_display != "Todos":
            search_tejido_code = search_tejido_display.split('(')[-1][:-1]

    with col_estado:
        search_estado = st.selectbox("Filtrar por Estado", ["Todos", "Disponible", "En Cuarentena", "En Proceso"])
    
    st.subheader("Resultados de la Búsqueda")
    conn_search = connect_to_supabase()
    if conn_search:
        query_search = """
        SELECT 
            t.id AS "ID Tejido", 
            dt.descripcion AS "Tipo de Tejido", 
            t.estado AS "Estado Actual", 
            t.fecha_recoleccion AS "Fecha Recolección", 
            h.nombre AS "Hospital Propietario",
            h.direccion AS "Dirección Hospital",
            h.telefono AS "Teléfono Hospital",
            m.nombre AS "Médico Recolector"
        FROM tejidos AS t
        JOIN detalles_tejido AS dt ON t.tipo = dt.tipo
        JOIN hospital AS h ON t.id_hospital = h.id
        LEFT JOIN medico AS m ON t.id_medico = m.id
        WHERE 1=1
        """
        params_search = []

        if search_tejido_code:
            query_search += " AND t.tipo = %s"
            params_search.append(search_tejido_code)
        
        if search_estado != "Todos":
            query_search += " AND t.estado = %s"
            params_search.append(search_estado)
        
        query_search += " ORDER BY t.fecha_recoleccion DESC;"
        
        search_results_df = execute_query(query_search, conn=conn_search, params=tuple(params_search), is_select=True)
        conn_search.close()
    else:
        search_results_df = pd.DataFrame()
        st.error("No se pudo conectar a la base de datos para buscar tejidos.")

    if not search_results_df.empty:
        st.dataframe(search_results_df, use_container_width=True)
        st.info("Para solicitar un tejido, por favor contacta directamente al Hospital Propietario usando la información provista.")
    else:
        st.info("No se encontraron tejidos con los filtros seleccionados.")