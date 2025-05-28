# pages/dashboard_hospital.py (pagina 3) - Dashboard para Hospitales

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Ajusta el path para importar 'functions.py' desde el directorio padre
# Esto asume que 'functions.py' está en el mismo nivel que la carpeta 'pages'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from functions import connect_to_supabase, execute_query

# --- Configuración de la página ---
st.set_page_config(
    page_title="TissBank - Dashboard Hospital",
    page_icon="🏥",
    layout="wide"
)

# --- Verificar si el usuario está logueado y es Hospital ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"] or st.session_state["role"] != "Hospital":
    st.warning("¡No tenés permiso para acceder a esta página! Por favor, iniciá sesión como Hospital.")
    if st.button("Volver al inicio de sesión"):
        st.session_state["logged_in"] = False
        st.switch_page("app.py") # Redirige al app.py principal
    st.stop() # Detiene la ejecución de la página

# Obtener datos de sesión del hospital
hospital_id = st.session_state.get("user_id")
hospital_nombre = st.session_state.get("user_name")
hospital_telefono = st.session_state.get("user_identifier")

# --- CORRECCIÓN CLAVE AQUÍ: Convertir hospital_id a int nativo de Python ---
# Esto es crucial para evitar el error 'numpy.int64'
if hospital_id is not None:
    hospital_id = int(hospital_id) # Convertimos el ID a int al principio de la página
else:
    st.error("Error: ID de hospital no disponible en la sesión. Por favor, reinicia la sesión.")
    st.stop() # Detener la ejecución si no hay ID válido

# Recuperar la dirección del hospital usando el ID convertido a int
conn_hospital_info = connect_to_supabase()
hospital_direccion = "No disponible" # Default
if conn_hospital_info:
    # Usamos el 'hospital_id' ya convertido a int
    hospital_info_df = execute_query("SELECT direccion FROM hospital WHERE id = %s", conn=conn_hospital_info, params=(hospital_id,), is_select=True)
    if not hospital_info_df.empty:
        hospital_direccion = hospital_info_df.iloc[0]['direccion']
    conn_hospital_info.close()
else:
    st.error("No se pudo conectar a la base de datos para obtener la dirección del hospital.")

# --- INICIO DEL CÓDIGO CSS PARA LA ESTÉTICA ---
# Estas clases de CSS son heurísticas y pueden cambiar con las actualizaciones de Streamlit.
# 'st-emotion-cache-...' son nombres de clases generados por Streamlit.
# Podrías necesitar ajustarlos si Streamlit cambia su estructura interna.
st.markdown("""
<style>
/* Estilo para el contenedor general de la barra lateral */
.st-emotion-cache-1wvypca { /* O el selector que envuelva toda la sidebar */
    background-color: #e0f2f7; /* Color de fondo claro similar al de la imagen */
    padding: 20px;
    border-radius: 10px;
}

/* Estilo para los botones de la barra lateral (radio buttons) */
.st-emotion-cache-vk3305 { /* Esto apunta al div que envuelve la etiqueta del radio button */
    border-radius: 8px; /* Bordes redondeados para las opciones del radio */
    padding: 10px 15px;
    margin-bottom: 5px;
    background-color: #cce7ed; /* Color de fondo un poco más oscuro para las opciones */
    color: #333; /* Color del texto */
    font-weight: bold;
    transition: background-color 0.3s ease;
}
.st-emotion-cache-vk3305:hover {
    background-color: #aaddf4; /* Color al pasar el mouse */
}
/* Asegura que el texto dentro de la etiqueta del radio button sea el color correcto */
.st-emotion-cache-vk3305 div[role="radiogroup"] > label > div {
    color: #333;
}
/* Estilo para el botón de Streamlit, como el de "Volver al inicio de sesión" */
.st-emotion-cache-z5fcl4 { /* Esto puede apuntar a botones generales */
    background-color: #6aabcc; /* Un azul/celeste más intenso */
    color: white;
    padding: 10px 20px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    transition: background-color 0.3s ease;
}
.st-emotion-cache-z5fcl4:hover {
    background-color: #5599bb;
}

/* Para centrar la imagen */
.st-emotion-cache-1t2w76v { /* Clase para st.image div */
    display: flex;
    justify-content: center;
    align-items: center;
}
.st-emotion-cache-1t2w76v img {
    margin: 0 auto; /* Asegura que la imagen misma esté centrada si no lo hace el flex */
}

</style>
""", unsafe_allow_html=True)
# --- FIN DEL CÓDIGO CSS PARA LA ESTÉTICA ---

st.title(f"Bienvenido, Hospital {hospital_nombre}.")
st.markdown(f"**Teléfono:** {hospital_telefono} | **Dirección:** {hospital_direccion}")
st.markdown("---")

# Barra lateral para navegación interna del dashboard
st.sidebar.title("Menú Hospital")
# Inicializar la selección del menú del dashboard en la sesión de esta página
if "hospital_menu_selection" not in st.session_state:
    st.session_state["hospital_menu_selection"] = "Bienvenida"

st.session_state["hospital_menu_selection"] = st.sidebar.radio(
    "Navegación",
    ["Bienvenida", "Tu Inventario", "Hospitales Afiliados", "Historial de Tejidos", "Solicitudes", "Donantes"],
    key="hospital_dashboard_menu" # Clave única para esta página
)

# Contenido principal basado en la selección del menú del dashboard
if st.session_state["hospital_menu_selection"] == "Bienvenida":
    # Logo en la parte superior del contenido principal, ahora más grande y centrado
    st.image("images/logo.png", width=300) # Aumentado el ancho para que sea más grande

    st.header("Bienvenido al Dashboard de Hospital")
    st.write(f"""
    Aquí podrás acceder a toda la información relevante para la gestión de tejidos.
    Desde esta ventana podrás:
    * **Consultar el inventario actual** de tejidos disponibles en el banco (que gestiona tu hospital).
    * **Visualizar un mapa** con todos los hospitales afiliados.
    * **Revisar el historial** de tejidos registrados en el banco (o los que gestiona tu hospital).
    * **Ver y gestionar solicitudes** activas de tejidos.
    * **Registrar y consultar donantes.**
    """)
    st.info("Explora las opciones en la barra lateral para empezar a gestionar tus tejidos.")

elif st.session_state["hospital_menu_selection"] == "Tu Inventario":
    st.header("📦 Tu Inventario de Tejidos")
    st.write("Aquí se mostrará el inventario actual de tejidos que pertenecen a tu hospital.")

    st.subheader("Inventario Actual de Tejidos")
    query_inventory = """
    SELECT 
        t.id AS "ID Tejido", 
        dt.descripcion AS "Tipo de Tejido", 
        t.tipo AS "Código Tipo", 
        t.fecha_recoleccion AS "Fecha Recolección", 
        t.estado AS "Estado Actual", 
        t.fecha_de_estado AS "Fecha Último Estado",
        d.nombre AS "Nombre Donante",
        d.apellido AS "Apellido Donante",
        m.nombre AS "Nombre Médico Recolector",
        m.apellido AS "Apellido Médico Recolector"
    FROM tejidos AS t
    JOIN detalles_tejido AS dt ON t.tipo = dt.tipo
    LEFT JOIN donante AS d ON t.id_donante = d.id
    LEFT JOIN medico AS m ON t.id_medico = m.id
    WHERE t.id_hospital = %s
    ORDER BY t.fecha_recoleccion DESC;
    """
    
    conn = connect_to_supabase()
    if conn:
        inventory_df = execute_query(query_inventory, conn=conn, params=(hospital_id,), is_select=True)
        conn.close()
    else:
        inventory_df = pd.DataFrame()
        st.error("No se pudo conectar a la base de datos para el inventario.")

    if not inventory_df.empty:
        st.dataframe(inventory_df, use_container_width=True)
    else:
        st.info("No hay tejidos registrados en el inventario de tu hospital.")
    
    st.subheader("Gestionar Tejidos (Recepción/Cambio de Estado)")
    
    with st.expander("➕ Registrar Nuevo Tejido Recibido"):
        with st.form("form_add_tejido"):
            # --- LÓGICA DE CARGA DE TIPOS DE TEJIDO (Mantenemos la robustez) ---
            default_tejido_types = pd.DataFrame([
                {'tipo': 'CORNEA', 'descripcion': 'Córnea Ocular'},
                {'tipo': 'PIEL', 'descripcion': 'Tejido Cutáneo'},
                {'tipo': 'HUESO_LARGO', 'descripcion': 'Hueso Largo'},
                {'tipo': 'HUESO_CORTO', 'descripcion': 'Hueso Corto'},
                {'tipo': 'VALVULA_CARD', 'descripcion': 'Válvula Cardíaca'},
                {'tipo': 'VA_SANGUINEO', 'descripcion': 'Vaso Sanguíneo'},
                {'tipo': 'MENISCO', 'descripcion': 'Menisco'},
                {'tipo': 'TENDON', 'descripcion': 'Tendón'},
                {'tipo': 'CARTILAGO', 'descripcion': 'Cartílago Articular'},
                {'tipo': 'MO', 'descripcion': 'Médula Ósea'},
                {'tipo': 'CEL_MADRE', 'descripcion': 'Células Madre'},
                {'tipo': 'LIGAMENTO', 'descripcion': 'Ligamento'},
                {'tipo': 'MEMBRANA', 'descripcion': 'Membrana Amniótica'},
                {'tipo': 'PANCREAS', 'descripcion': 'Páncreas'},
                {'tipo': 'HIGADO', 'descripcion': 'Hígado'},
                {'tipo': 'RINON', 'descripcion': 'Riñón'},
                {'tipo': 'PULMON', 'descripcion': 'Pulmón'},
                {'tipo': 'CORAZON', 'descripcion': 'Corazón'},
                {'tipo': 'INTESTINO', 'descripcion': 'Intestino'},
                {'tipo': 'ESTOMAGO', 'descripcion': 'Estómago'},
                {'tipo': 'BAZO', 'descripcion': 'Bazo'},
                {'tipo': 'OVARIO', 'descripcion': 'Ovario'},
                {'tipo': 'TESTICULO', 'descripcion': 'Testículo'},
                {'tipo': 'GLANDULA', 'descripcion': 'Glándula (ej. tiroides)'},
                {'tipo': 'NERVIO', 'descripcion': 'Nervio'}
            ])

            types_df = pd.DataFrame() 

            try:
                conn_types = connect_to_supabase()
                if conn_types:
                    db_types_df = execute_query("SELECT tipo, descripcion FROM detalles_tejido ORDER BY descripcion", conn=conn_types, is_select=True)
                    conn_types.close()
                    
                    if not db_types_df.empty:
                        types_df = db_types_df
                        st.info("Tipos de tejido cargados desde la base de datos.")
                    else:
                        st.warning("La tabla 'detalles_tejido' de la base de datos está vacía o no se encontraron datos. Usando lista predeterminada de respaldo.")
                        types_df = default_tejido_types
                else:
                    st.error("No se pudo establecer conexión con la base de datos para obtener tipos de tejido. Usando lista predeterminada de respaldo.")
                    types_df = default_tejido_types
            except Exception as e:
                st.error(f"Error al cargar tipos de tejido desde la base de datos: {e}. Usando lista predeterminada de respaldo.")
                types_df = default_tejido_types

            if 'tipo' not in types_df.columns or 'descripcion' not in types_df.columns:
                types_df = default_tejido_types

            tejido_tipo_options = types_df.apply(lambda row: f"{row['descripcion']} ({row['tipo']})", axis=1).tolist()
            selected_tejido_display = st.selectbox("Tipo de Tejido", ["Seleccione un tipo"] + tejido_tipo_options)
            
            selected_tejido_code = None
            if selected_tejido_display and selected_tejido_display != "Seleccione un tipo":
                selected_tejido_code = selected_tejido_display.split('(')[-1][:-1]

            # --- ID DONANTE AUTOMÁTICO ---
            # Define el ID del donante por defecto. ¡ASEGÚRATE DE QUE ESTE ID EXISTA EN TU TABLA 'donante' EN SUPABASE!
            # Por ejemplo, puedes crear un donante con ID 1 y nombre "Donante Genérico".
            id_donante_auto = 1 # <--- ¡CAMBIA ESTO AL ID DE TU DONANTE POR DEFECTO/GENÉRICO EN SUPABASE!
            st.info(f"El ID del donante se asignará automáticamente a: **{id_donante_auto}** (Donante Genérico/Por Defecto).")
            
            # --- ID MÉDICO AUTOMÁTICO ---
            # Define el ID del médico por defecto. ¡ASEGÚRATE DE QUE ESTE ID EXISTA EN TU TABLA 'medico' EN SUPABASE!
            # Por ejemplo, puedes crear un médico con ID 1 y nombre "Dr. Banco Tejidos".
            id_medico_auto = 1 # <--- ¡CAMBIA ESTO AL ID DE TU MÉDICO POR DEFECTO/GENÉRICO EN SUPABASE!
            st.info(f"El ID del médico recolector se asignará automáticamente a: **{id_medico_auto}** (Médico por Defecto).")
            
            fecha_recoleccion = st.date_input("Fecha de Recolección", datetime.now().date())
            condicion_recoleccion = st.text_area("Condición de Recolección (ej. 'óptima', 'no apto para trasplante')", height=70)
            estado_inicial = st.selectbox("Estado Inicial", ["Disponible", "En Cuarentena", "Rechazado", "En Proceso"])
            
            submit_add_tejido = st.form_submit_button("Registrar Tejido")

            if submit_add_tejido:
                if selected_tejido_code is None:
                    st.warning("Por favor, seleccioná un tipo de tejido.")
                elif not condicion_recoleccion:
                    st.warning("Por favor, ingresa la condición de recolección.")
                else:
                    try:
                        conn_add = connect_to_supabase()
                        if conn_add:
                            query_add_tejido = """
                            INSERT INTO tejidos (tipo, id_donante, id_medico, id_hospital, fecha_recoleccion, condicion_recoleccion, estado, fecha_de_estado)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            params_add_tejido = (
                                selected_tejido_code,
                                id_donante_auto, # Usamos el ID del donante automático
                                id_medico_auto,  # Usamos el ID del médico automático
                                hospital_id, # Usamos el hospital_id ya convertido a int
                                fecha_recoleccion,
                                condicion_recoleccion,
                                estado_inicial,
                                datetime.now().date()
                            )
                            if execute_query(query_add_tejido, conn=conn_add, params=params_add_tejido, is_select=False):
                                st.success("✅ Tejido registrado correctamente.")
                                st.rerun()
                            else:
                                st.error("❌ Error al registrar el tejido.")
                            conn_add.close()
                        else:
                            st.error("No se pudo conectar a la base de datos.")
                    except Exception as e:
                        st.error(f"Ocurrió un error inesperado al registrar el tejido: {e}")

    with st.expander("🔄 Actualizar Estado de Tejido Existente"):
        with st.form("form_update_tejido_estado"):
            tejido_id_to_update = st.number_input("ID del Tejido a Actualizar", min_value=1, format="%d")
            new_estado = st.selectbox("Nuevo Estado", ["Disponible", "En Cuarentena", "Rechazado", "En Proceso", "Enviado", "Consumido"])
            
            submit_update_tejido = st.form_submit_button("Actualizar Estado")

            if submit_update_tejido:
                if not tejido_id_to_update:
                    st.warning("Por favor, ingresá el ID del tejido.")
                else:
                    try:
                        conn_update = connect_to_supabase()
                        if conn_update:
                            check_ownership_query = "SELECT id FROM tejidos WHERE id = %s AND id_hospital = %s"
                            owner_check = execute_query(check_ownership_query, conn=conn_update, params=(tejido_id_to_update, hospital_id), is_select=True) # Usamos hospital_id ya convertido

                            if owner_check.empty:
                                st.error("No tenés permiso para modificar este tejido o el ID no existe en tu inventario.")
                            else:
                                query_update_tejido = """
                                UPDATE tejidos
                                SET estado = %s, fecha_de_estado = %s
                                WHERE id = %s AND id_hospital = %s
                                """
                                params_update_tejido = (new_estado, datetime.now().date(), tejido_id_to_update, hospital_id) # Usamos hospital_id ya convertido
                                if execute_query(query_update_tejido, conn=conn_update, params=params_update_tejido, is_select=False):
                                    st.success(f"✅ Estado del tejido {tejido_id_to_update} actualizado a '{new_estado}'.")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Error al actualizar el estado del tejido {tejido_id_to_update}.")
                                conn_update.close()
                        else:
                            st.error("No se pudo conectar a la base de datos.")
                    except Exception as e:
                        st.error(f"Ocurrió un error inesperado al actualizar el tejido: {e}")

elif st.session_state["hospital_menu_selection"] == "Hospitales Afiliados":
    st.header("🏥 Hospitales Afiliados")
    st.write("Aquí podrás ver una lista de todos los hospitales afiliados a la red y su ubicación.")
    
    st.subheader("Mapa de Hospitales (Placeholder)")
    st.markdown("![Mapa de Hospitales](https://via.placeholder.com/600x400?text=Mapa+de+Hospitales)")
    st.write("_(Se integraría un mapa interactivo aquí usando la columna 'direccion' de la tabla hospital)_")

    st.subheader("Lista de Hospitales")
    conn = connect_to_supabase()
    if conn:
        query_all_hospitals = "SELECT nombre, direccion, telefono FROM hospital ORDER BY nombre"
        all_hospitals_df = execute_query(query_all_hospitals, conn=conn, is_select=True)
        conn.close()
    else:
        all_hospitals_df = pd.DataFrame()
        st.error("No se pudo conectar a la base de datos para obtener la lista de hospitales.")

    if not all_hospitals_df.empty:
        st.dataframe(all_hospitals_df, use_container_width=True)
    else:
        st.info("No se encontraron hospitales afiliados.")

elif st.session_state["hospital_menu_selection"] == "Historial de Tejidos":
    st.header("⏳ Historial de Tejidos")
    st.write("Aquí se muestra el registro de todos los tejidos y sus cambios de estado en la plataforma.")
    
    st.subheader("Filtrar Historial")
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        start_date = st.date_input("Fecha Inicio", datetime(datetime.now().year, 1, 1).date())
    with col_date2:
        end_date = st.date_input("Fecha Fin", datetime.now().date())
    
    filter_by_hospital_hist = st.checkbox("Filtrar solo por tejidos de mi hospital")

    conn = connect_to_supabase()
    if conn:
        query_history_base = """
        SELECT 
            t.id AS "ID Tejido", 
            dt.descripcion AS "Tipo de Tejido", 
            t.estado AS "Estado", 
            t.fecha_de_estado AS "Fecha del Estado",
            t.fecha_recoleccion AS "Fecha Recolección",
            h.nombre AS "Hospital Propietario",
            m.nombre AS "Médico Recolector",
            d.nombre AS "Donante"
        FROM tejidos AS t
        JOIN detalles_tejido AS dt ON t.tipo = dt.tipo
        LEFT JOIN hospital AS h ON t.id_hospital = h.id
        LEFT JOIN medico AS m ON t.id_medico = m.id
        LEFT JOIN donante AS d ON t.id_donante = d.id
        WHERE t.fecha_de_estado BETWEEN %s AND %s
        """
        params_history = [start_date, end_date]

        if filter_by_hospital_hist:
            query_history_base += " AND t.id_hospital = %s"
            params_history.append(hospital_id) # Usamos hospital_id ya convertido
        
        query_history_base += " ORDER BY t.fecha_de_estado DESC;"
        
        history_df = execute_query(query_history_base, conn=conn, params=tuple(params_history), is_select=True)
        conn.close()
    else:
        history_df = pd.DataFrame()
        st.error("No se pudo conectar a la base de datos para el historial.")

    if st.button("Buscar Historial"):
        if not history_df.empty:
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("No se encontró historial para las fechas seleccionadas y filtros aplicados.")

elif st.session_state["hospital_menu_selection"] == "Solicitudes":
    st.header("📝 Solicitudes de Tejidos")
    st.write("Gestiona tus solicitudes de tejidos: realiza nuevas, revisa el estado de las existentes y visualiza las aprobadas.")
    
    st.warning("⚠️ **ATENCIÓN:** La tabla `solicitudes` no se encuentra en tu diagrama de base de datos. Las funcionalidades a continuación son simuladas o requerirán que crees esta tabla en Supabase.")

    st.subheader("Mis Solicitudes Activas (Simulado)")
    requests_data = {
        'ID Solicitud': ['SOL001', 'SOL002', 'SOL003'],
        'Tipo Tejido Solicitado': ['Córnea', 'Piel', 'Hueso'],
        'Cantidad': [2, 5, 1],
        'Fecha Solicitud': ['2024-04-10', '2024-05-01', '2024-05-20'],
        'Fecha Necesaria': ['2024-06-01', '2024-05-25', '2024-06-15'],
        'Estado': ['Pendiente', 'Aprobada', 'Pendiente']
    }
    active_requests_df = pd.DataFrame(requests_data)
    st.dataframe(active_requests_df, use_container_width=True)

    st.subheader("Crear Nueva Solicitud (Simulado)")
    with st.expander("Haz clic para crear una nueva solicitud"):
        with st.form("form_nueva_solicitud_sim"):
            # --- LÓGICA DE CARGA DE TIPOS DE TEJIDO PARA SOLICITUDES ---
            default_tejido_types_req = pd.DataFrame([
                {'tipo': 'CORNEA', 'descripcion': 'Córnea Ocular'},
                {'tipo': 'PIEL', 'descripcion': 'Tejido Cutáneo'},
                {'tipo': 'HUESO_LARGO', 'descripcion': 'Hueso Largo'},
                {'tipo': 'HUESO_CORTO', 'descripcion': 'Hueso Corto'},
                {'tipo': 'VALVULA_CARD', 'descripcion': 'Válvula Cardíaca'},
                {'tipo': 'VA_SANGUINEO', 'descripcion': 'Vaso Sanguíneo'},
                {'tipo': 'MENISCO', 'descripcion': 'Menisco'},
                {'tipo': 'TENDON', 'descripcion': 'Tendón'},
                {'tipo': 'CARTILAGO', 'descripcion': 'Cartílago Articular'},
                {'tipo': 'MO', 'descripcion': 'Médula Ósea'},
                {'tipo': 'CEL_MADRE', 'descripcion': 'Células Madre'},
                {'tipo': 'LIGAMENTO', 'descripcion': 'Ligamento'},
                {'tipo': 'MEMBRANA', 'descripcion': 'Membrana Amniótica'},
                {'tipo': 'PANCREAS', 'descripcion': 'Páncreas'},
                {'tipo': 'HIGADO', 'descripcion': 'Hígado'},
                {'tipo': 'RINON', 'descripcion': 'Riñón'},
                {'tipo': 'PULMON', 'descripcion': 'Pulmón'},
                {'tipo': 'CORAZON', 'descripcion': 'Corazón'},
                {'tipo': 'INTESTINO', 'descripcion': 'Intestino'},
                {'tipo': 'ESTOMAGO', 'descripcion': 'Estómago'},
                {'tipo': 'BAZO', 'descripcion': 'Bazo'},
                {'tipo': 'OVARIO', 'descripcion': 'Ovario'},
                {'tipo': 'TESTICULO', 'descripcion': 'Testículo'},
                {'tipo': 'GLANDULA', 'descripcion': 'Glándula (ej. tiroides)'},
                {'tipo': 'NERVIO', 'descripcion': 'Nervio'}
            ])
            
            types_df_req = pd.DataFrame()

            try:
                conn_types_req = connect_to_supabase()
                if conn_types_req:
                    db_types_df_req = execute_query("SELECT tipo, descripcion FROM detalles_tejido ORDER BY descripcion", conn=conn_types_req, is_select=True)
                    conn_types_req.close()
                    
                    if not db_types_df_req.empty:
                        types_df_req = db_types_df_req
                    else:
                        st.warning("La tabla 'detalles_tejido' para solicitudes está vacía. Usando lista predeterminada de respaldo.")
                        types_df_req = default_tejido_types_req
                else:
                    st.error("No se pudo establecer conexión con la base de datos para tipos de tejido de solicitud. Usando lista predeterminada de respaldo.")
                    types_df_req = default_tejido_types_req
            except Exception as e:
                st.error(f"Error al cargar tipos de tejido para solicitud: {e}. Usando lista predeterminada de respaldo.")
                types_df_req = default_tejido_types_req

            if 'tipo' not in types_df_req.columns or 'descripcion' not in types_df_req.columns:
                types_df_req = default_tejido_types_req

            tejido_tipo_options_req = types_df_req.apply(lambda row: f"{row['descripcion']} ({row['tipo']})", axis=1).tolist()
            selected_tejido_display_req = st.selectbox("Tipo de Tejido Solicitado", ["Seleccione un tipo"] + tejido_tipo_options_req)
            
            selected_tejido_code_req = None
            if selected_tejido_display_req and selected_tejido_display_req != "Seleccione un tipo":
                selected_tejido_code_req = selected_tejido_display_req.split('(')[-1][:-1]

            cantidad = st.number_input("Cantidad Solicitada", min_value=1, value=1)
            fecha_necesidad = st.date_input("Fecha Necesaria (aproximada)", datetime.now().date())
            
            submit_request = st.form_submit_button("Enviar Solicitud")
            
            if submit_request:
                if selected_tejido_code_req is None:
                    st.warning("Por favor, seleccioná un tipo de tejido.")
                else:
                    st.success(f"✔️ Solicitud de {cantidad} de {selected_tejido_code_req} para {fecha_necesidad} enviada (simulado).")
                    st.info("Recordá que necesitas crear la tabla `solicitudes` en tu base de datos para que esta funcionalidad sea real.")

elif st.session_state["hospital_menu_selection"] == "Donantes":
    st.header("👤 Gestión de Donantes")
    st.write("Aquí podrás registrar nuevos donantes y consultar la información de donantes existentes.")

    st.subheader("Lista de Donantes")
    conn = connect_to_supabase()
    if conn:
        query_donantes = "SELECT id, nombre, apellido, dni, sexo FROM donante ORDER BY apellido, nombre"
        donantes_df = execute_query(query_donantes, conn=conn, is_select=True)
        conn.close()
    else:
        donantes_df = pd.DataFrame()
        st.error("No se pudo conectar a la base de datos para obtener los donantes.")

    if not donantes_df.empty:
        st.dataframe(donantes_df, use_container_width=True)
    else:
        st.info("No hay donantes registrados.")

    st.subheader("Registrar Nuevo Donante")
    with st.expander("➕ Haz clic para registrar un nuevo donante"):
        with st.form("form_add_donante"):
            nombre_donante = st.text_input("Nombre del Donante")
            apellido_donante = st.text_input("Apellido del Donante")
            dni_donante = st.text_input("DNI del Donante (Solo números)", max_chars=10)
            sexo_donante = st.selectbox("Sexo", ["Masculino", "Femenino", "Otro", "No Especificado"])

            submit_add_donante = st.form_submit_button("Registrar Donante")

            if submit_add_donante:
                if not all([nombre_donante, apellido_donante, dni_donante, sexo_donante]):
                    st.warning("Por favor, completá todos los campos del donante.")
                else:
                    try:
                        dni_int = int(dni_donante)
                        conn_donante = connect_to_supabase()
                        if conn_donante:
                            check_dni_query = "SELECT id FROM donante WHERE dni = %s"
                            existing_dni = execute_query(check_dni_query, conn=conn_donante, params=(dni_int,), is_select=True)
                            if not existing_dni.empty:
                                st.error("El DNI ingresado ya corresponde a un donante registrado.")
                                conn_donante.close()
                            else:
                                query_add_donante = """
                                INSERT INTO donante (nombre, apellido, dni, sexo)
                                VALUES (%s, %s, %s, %s)
                                """
                                params_add_donante = (nombre_donante, apellido_donante, dni_int, sexo_donante)
                                if execute_query(query_add_donante, conn=conn_donante, params=params_add_donante, is_select=False):
                                    st.success("✅ Donante registrado correctamente.")
                                    st.rerun()
                                else:
                                    st.error("❌ Error al registrar el donante.")
                                conn_donante.close()
                        else:
                            st.error("No se pudo conectar a la base de datos.")
                    except ValueError:
                        st.error("El DNI debe contener solo números. Por favor, verifica el formato.")
                    except Exception as e:
                        st.error(f"Ocurrió un error inesperado al registrar el donante: {e}")