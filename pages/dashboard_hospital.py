# pages/dashboard_hospital.py

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime

# Asegúrate de que 'functions.py' sea importable.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from functions import connect_to_supabase, execute_query

# --- Configuración de la página ---
st.set_page_config(
    page_title="TissBank - Dashboard Hospital",
    page_icon="🏥",
    layout="wide"
)

# --- Verificar autenticación y rol ---
if not st.session_state.get("logged_in"):
    st.warning("Por favor, iniciá sesión para acceder a esta página.")
    st.stop() # Detiene la ejecución de la página

if st.session_state.get("role") != "Hospital":
    st.error("Acceso denegado. Esta página es solo para usuarios de Hospital.")
    st.stop() # Detiene la ejecución de la página


# --- Recuperar información del hospital logueado ---
hospital_id = st.session_state.get("user_id")
hospital_telefono_identificador = st.session_state.get("user_identifier") # Ahora es el teléfono

hospital_nombre = "Tu Hospital" # Valor por defecto
hospital_direccion = "Dirección no disponible"

if hospital_id:
    conn = connect_to_supabase()
    if conn:
        # Recuperamos nombre y direccion del hospital usando su ID
        query = "SELECT nombre, direccion FROM hospital WHERE id = %s"
        result = execute_query(query, conn=conn, params=(hospital_id,), is_select=True)
        if not result.empty:
            hospital_nombre = result.iloc[0]['nombre']
            hospital_direccion = result.iloc[0]['direccion']
        conn.close()
    else:
        st.error("No se pudo conectar a la base de datos para obtener los datos del hospital.")


# --- Barra lateral (Menú de navegación) ---
st.sidebar.image("images/logo.png", width=150)
st.sidebar.title("Menú Hospital")

menu_selection = st.sidebar.radio(
    "Navegación",
    ["Bienvenida", "Tu Inventario", "Hospitales Afiliados", "Historial de Tejidos", "Solicitudes", "Donantes"]
)

# --- Contenido Principal basado en la selección del menú ---

st.title(f"Bienvenido, Hospital {hospital_nombre}.")
st.markdown(f"**Teléfono:** {hospital_telefono_identificador} | **Dirección:** {hospital_direccion}")
st.markdown("---") # Separador visual

if menu_selection == "Bienvenida":
    st.write(f"""
    Aquí podrás acceder a toda la información relevante para la gestión de tejidos.
    Desde esta ventana podrás:
    * **Consultar el inventario actual** de tejidos disponibles en el banco (que gestiona tu hospital).
    * **Visualizar un mapa** con todos los hospitales afiliados.
    * **Revisar el historial** de tejidos registrados en el banco (o los que gestiona tu hospital).
    * **Ver y gestionar solicitudes** activas de tejidos.
    * **Registrar y consultar donantes.**
    """)
    # Si tienes una imagen específica para la bienvenida, úsala aquí
    # st.image("images/bienvenida_hospital.png", caption="TissBank Dashboard", use_column_width=True)


elif menu_selection == "Tu Inventario":
    st.header("📦 Tu Inventario de Tejidos")
    st.write("Aquí se mostrará el inventario actual de tejidos que pertenecen a tu hospital.")

    # --- Funcionalidades de Inventario ---
    st.subheader("Inventario Actual de Tejidos")
    
    # Obtener datos del inventario de tejidos de ESTE hospital
    # Usando la tabla 'tejidos' con 'id_hospital'
    # Y 'detalles_tejido' para la descripción del tipo
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
    
    # Formulario para registrar un nuevo tejido recibido
    with st.expander("➕ Registrar Nuevo Tejido Recibido"):
        with st.form("form_add_tejido"):
            # Obtener tipos de tejido disponibles de 'detalles_tejido'
            conn_types = connect_to_supabase()
            if conn_types:
                types_df = execute_query("SELECT tipo, descripcion FROM detalles_tejido ORDER BY descripcion", conn=conn_types, is_select=True)
                conn_types.close()
            else:
                types_df = pd.DataFrame({'tipo': [], 'descripcion': []})

            tejido_tipo_options = types_df.apply(lambda row: f"{row['descripcion']} ({row['tipo']})", axis=1).tolist()
            selected_tejido_display = st.selectbox("Tipo de Tejido", ["Seleccione un tipo"] + tejido_tipo_options)
            
            # Extraer el 'tipo' (código) del string seleccionado
            selected_tejido_code = None
            if selected_tejido_display and selected_tejido_display != "Seleccione un tipo":
                selected_tejido_code = selected_tejido_display.split('(')[-1][:-1] # Extrae el código entre paréntesis

            # Campos para ID de donante y médico (opcionales)
            # Validar si existen los IDs en las tablas correspondientes
            col_donante, col_medico = st.columns(2)
            with col_donante:
                id_donante = st.number_input("ID del Donante (opcional)", min_value=1, value=None, format="%d", help="Deja en blanco si no aplica o si el donante aún no está registrado.")
            with col_medico:
                id_medico_recoleccion = st.number_input("ID del Médico Recolector (opcional)", min_value=1, value=None, format="%d", help="Deja en blanco si no aplica o si el médico aún no está registrado.")
            
            fecha_recoleccion = st.date_input("Fecha de Recolección", datetime.now().date())
            condicion_recoleccion = st.text_area("Condición de Recolección (ej. 'viable', 'no apto para trasplante')", height=70)
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
                            donante_id_val = id_donante if id_donante else None
                            medico_id_val = id_medico_recoleccion if id_medico_recoleccion else None

                            # Opcional: Validar si el donante/médico existe si el ID fue proporcionado
                            if donante_id_val:
                                check_donante = execute_query("SELECT id FROM donante WHERE id = %s", conn=conn_add, params=(donante_id_val,), is_select=True)
                                if check_donante.empty:
                                    st.error(f"El ID de Donante {donante_id_val} no existe. Por favor, registrá al donante primero o dejá el campo en blanco.")
                                    conn_add.close()
                                    st.stop()
                            if medico_id_val:
                                check_medico = execute_query("SELECT id FROM medico WHERE id = %s", conn=conn_add, params=(medico_id_val,), is_select=True)
                                if check_medico.empty:
                                    st.error(f"El ID de Médico {medico_id_val} no existe. Por favor, registrá al médico primero o dejá el campo en blanco.")
                                    conn_add.close()
                                    st.stop()

                            query_add_tejido = """
                            INSERT INTO tejidos (tipo, id_donante, id_medico, id_hospital, fecha_recoleccion, condicion_recoleccion, estado, fecha_de_estado)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            params_add_tejido = (
                                selected_tejido_code,
                                donante_id_val,
                                medico_id_val,
                                hospital_id, # El hospital logueado es el que recibe el tejido
                                fecha_recoleccion,
                                condicion_recoleccion,
                                estado_inicial,
                                datetime.now().date() # Fecha del estado actual
                            )
                            if execute_query(query_add_tejido, conn=conn_add, params=params_add_tejido, is_select=False):
                                st.success("✅ Tejido registrado correctamente.")
                                st.rerun() # Recargar para ver el inventario actualizado
                            else:
                                st.error("❌ Error al registrar el tejido.")
                            conn_add.close()
                        else:
                            st.error("No se pudo conectar a la base de datos.")
                    except Exception as e:
                        st.error(f"Ocurrió un error inesperado al registrar el tejido: {e}")

    # Formulario para cambiar el estado de un tejido existente
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
                            # Validar que el tejido pertenezca a este hospital antes de actualizarlo
                            check_ownership_query = "SELECT id FROM tejidos WHERE id = %s AND id_hospital = %s"
                            owner_check = execute_query(check_ownership_query, conn=conn_update, params=(tejido_id_to_update, hospital_id), is_select=True)

                            if owner_check.empty:
                                st.error("No tenés permiso para modificar este tejido o el ID no existe en tu inventario.")
                            else:
                                query_update_tejido = """
                                UPDATE tejidos
                                SET estado = %s, fecha_de_estado = %s
                                WHERE id = %s AND id_hospital = %s
                                """
                                params_update_tejido = (new_estado, datetime.now().date(), tejido_id_to_update, hospital_id)
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


elif menu_selection == "Hospitales Afiliados":
    st.header("🏥 Hospitales Afiliados")
    st.write("Aquí podrás ver una lista de todos los hospitales afiliados a la red y su ubicación.")
    
    st.subheader("Mapa de Hospitales (Placeholder)")
    st.markdown("![Mapa de Hospitales](https://via.placeholder.com/600x400?text=Mapa+de+Hospitales)")
    st.write("_(Se integraría un mapa interactivo aquí usando la columna 'direccion' de la tabla hospital. Para esto, necesitarías convertir las direcciones en coordenadas geográficas (latitud/longitud) si no las tienes ya en la DB. Luego usar `st.map` o librerías como `folium`)_")

    st.subheader("Lista de Hospitales")
    conn = connect_to_supabase()
    if conn:
        # Obtener todos los hospitales (excluyendo el logueado si se desea)
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

elif menu_selection == "Historial de Tejidos":
    st.header("⏳ Historial de Tejidos")
    st.write("Aquí se muestra el registro de todos los tejidos y sus cambios de estado en la plataforma.")
    
    st.subheader("Filtrar Historial")
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        # Pongo una fecha de inicio por defecto que sea el inicio del año actual
        start_date = st.date_input("Fecha Inicio", datetime(datetime.now().year, 1, 1).date())
    with col_date2:
        end_date = st.date_input("Fecha Fin", datetime.now().date())
    
    # Opcional: Filtro por hospital específico
    filter_by_hospital = st.checkbox("Filtrar solo por tejidos de mi hospital")

    conn = connect_to_supabase()
    if conn:
        query_history_parts = []
        params_history = []

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
        params_history.extend([start_date, end_date])

        if filter_by_hospital:
            query_history_base += " AND t.id_hospital = %s"
            params_history.append(hospital_id)
        
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

elif menu_selection == "Solicitudes":
    st.header("📝 Solicitudes de Tejidos")
    st.write("Gestiona tus solicitudes de tejidos: realiza nuevas, revisa el estado de las existentes y visualiza las aprobadas.")
    
    st.warning("⚠️ **ATENCIÓN:** La tabla `solicitudes` no se encuentra en tu diagrama de base de datos. Las funcionalidades a continuación son simuladas o requerirán que crees esta tabla en Supabase.")

    # --- Secciones de Solicitudes (Simuladas si no existe la tabla) ---
    st.subheader("Mis Solicitudes Activas (Simulado)")
    # Si la tabla 'solicitudes' existiera, la query sería algo así:
    # query_solicitudes = "SELECT * FROM solicitudes WHERE id_hospital = %s AND estado IN ('Pendiente', 'Aprobada') ORDER BY fecha_solicitud DESC"
    # solicitudes_df = execute_query(query_solicitudes, conn=conn, params=(hospital_id,), is_select=True)

    # Datos de ejemplo para la simulación
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
            # Obtener tipos de tejido disponibles de 'detalles_tejido'
            conn_types_req = connect_to_supabase()
            if conn_types_req:
                types_df_req = execute_query("SELECT tipo, descripcion FROM detalles_tejido ORDER BY descripcion", conn=conn_types_req, is_select=True)
                conn_types_req.close()
            else:
                types_df_req = pd.DataFrame({'tipo': [], 'descripcion': []})
            
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
                    # Aquí iría la lógica para insertar en la tabla 'solicitudes'
                    # Ejemplo si tuvieras la tabla:
                    # conn_sol = connect_to_supabase()
                    # if conn_sol:
                    #     query_insert_sol = """
                    #     INSERT INTO solicitudes (id_hospital, tipo_tejido_solicitado, cantidad, fecha_solicitud, fecha_necesidad, estado)
                    #     VALUES (%s, %s, %s, %s, %s, %s)
                    #     """
                    #     params_insert_sol = (hospital_id, selected_tejido_code_req, cantidad, datetime.now().date(), fecha_necesidad, 'Pendiente')
                    #     if execute_query(query_insert_sol, conn=conn_sol, params=params_insert_sol, is_select=False):
                    #         st.success("✅ Solicitud enviada correctamente.")
                    #         st.rerun()
                    #     else:
                    #         st.error("❌ Error al enviar la solicitud.")
                    #     conn_sol.close()
                    # else:
                    #     st.error("No se pudo conectar a la base de datos para enviar la solicitud.")
                    st.success(f"✔️ Solicitud de {cantidad} de {selected_tejido_code_req} para {fecha_necesidad} enviada (simulado).")
                    st.info("Recordá que necesitas crear la tabla `solicitudes` en tu base de datos para que esta funcionalidad sea real.")


elif menu_selection == "Donantes":
    st.header("👤 Gestión de Donantes")
    st.write("Aquí podrás registrar nuevos donantes y consultar la información de donantes existentes.")

    st.subheader("Lista de Donantes")
    conn = connect_to_supabase()
    if conn:
        # Se asume que 'donante' tiene id, nombre, apellido, dni, sexo
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
            dni_donante = st.text_input("DNI del Donante (Solo números)", max_chars=10) # DNI es INTEGER en tu esquema, validar
            sexo_donante = st.selectbox("Sexo", ["Masculino", "Femenino", "Otro", "No Especificado"])

            submit_add_donante = st.form_submit_button("Registrar Donante")

            if submit_add_donante:
                if not all([nombre_donante, apellido_donante, dni_donante, sexo_donante]):
                    st.warning("Por favor, completá todos los campos del donante.")
                else:
                    try:
                        dni_int = int(dni_donante) # Intentar convertir a int
                        conn_donante = connect_to_supabase()
                        if conn_donante:
                            # Verificar si el DNI ya existe para evitar duplicados
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
                                    st.rerun() # Recargar para ver la lista actualizada
                                else:
                                    st.error("❌ Error al registrar el donante.")
                                conn_donante.close()
                        else:
                            st.error("No se pudo conectar a la base de datos.")
                    except ValueError:
                        st.error("El DNI debe contener solo números. Por favor, verifica el formato.")
                    except Exception as e:
                        st.error(f"Ocurrió un error inesperado al registrar el donante: {e}")