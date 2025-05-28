# app.py (Este archivo contendrá todo: Login, Registro y Dashboards)

import streamlit as st
import sys
import os
import hashlib # Para hashing básico (¡usa bcrypt en producción!)
import pandas as pd # Necesario para los DataFrames en los dashboards
from datetime import datetime # Necesario para manejar fechas en los dashboards

# Ajusta el path para importar 'functions.py' si está en el directorio padre
# Si app.py está en la raíz y functions.py también, esta línea no es estrictamente necesaria,
# pero no hace daño tenerla por si acaso la estructura cambia.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from functions import connect_to_supabase, execute_query # Asegúrate de que functions.py esté definido y correcto

# --- Configuración de la página ---
st.set_page_config(
    page_title="TissBank",
    page_icon="🧬",
    layout="wide" # Cambiado a 'wide' para que el dashboard tenga más espacio
)

# --- Logo centrado ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("images/logo.png", width=300)

# --- Inicializar estado de sesión ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_identifier" not in st.session_state: # Usaremos DNI o Teléfono como identificador de sesión
    st.session_state["user_identifier"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "user_id" not in st.session_state: # Almacena el ID de la tabla medico/hospital
    st.session_state["user_id"] = None
if "user_name" not in st.session_state: # Almacena el nombre del usuario/hospital
    st.session_state["user_name"] = ""
if "hospital_direccion" not in st.session_state: # Para el dashboard del hospital
    st.session_state["hospital_direccion"] = ""
if "show_register" not in st.session_state:
    st.session_state["show_register"] = False
if "dashboard_menu_selection" not in st.session_state: # Para la navegación interna del dashboard (si estás logueado)
    st.session_state["dashboard_menu_selection"] = "Bienvenida"

# --- Hashing de Contraseñas (Básico, para ejemplo. ¡Usa bcrypt en producción!) ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Función para autenticar usuario ---
def authenticate_user(identifier, password):
    """
    Autentica un usuario verificando en las tablas de medico y hospital.
    Retorna (True, role, id_del_usuario, nombre_del_usuario) si es exitoso, (False, None, None, None) de lo contrario.
    `identifier` será DNI para médicos y Teléfono para hospitales.
    """
    conn = connect_to_supabase()
    if conn is None:
        st.error("No se pudo conectar a la base de datos para autenticación.")
        return False, None, None, None

    hashed_password = hash_password(password)

    # Intentar autenticar como Médico (usando DNI como identificador)
    query_medico = "SELECT id, dni, nombre FROM medico WHERE dni = %s AND password = %s"
    medico_data = execute_query(query_medico, conn=conn, params=(identifier, hashed_password), is_select=True)
    if not medico_data.empty:
        user_id = medico_data.iloc[0]['id']
        user_name = medico_data.iloc[0]['nombre']
        conn.close()
        return True, "Médico", user_id, user_name

    # Intentar autenticar como Hospital (usando Teléfono como identificador)
    query_hospital = "SELECT id, telefono, nombre, direccion FROM hospital WHERE telefono = %s AND password = %s"
    hospital_data = execute_query(query_hospital, conn=conn, params=(identifier, hashed_password), is_select=True)
    if not hospital_data.empty:
        user_id = hospital_data.iloc[0]['id']
        user_name = hospital_data.iloc[0]['nombre']
        hospital_direccion = hospital_data.iloc[0]['direccion']
        st.session_state["hospital_direccion"] = hospital_direccion # Guardar dirección en la sesión
        conn.close()
        return True, "Hospital", user_id, user_name
    
    conn.close()
    return False, None, None, None

# --- Función para registrar usuario (Centralizada) ---
def register_user(role, data):
    """
    Registra un nuevo usuario en la base de datos según su rol.
    """
    conn = connect_to_supabase()
    if conn is None:
        st.error("No se pudo conectar a la base de datos para el registro.")
        return False

    success = False
    hashed_password = hash_password(data.get("password"))

    if role == "Médico":
        nombre = data.get("nombre")
        apellido = data.get("apellido")
        dni = data.get("dni") # Este será el identificador
        
        if not all([nombre, apellido, dni, data.get("password")]):
            st.warning("Por favor completá todos los campos del médico.")
            conn.close()
            return False
        
        try:
            # Validar si el DNI ya existe
            check_query = "SELECT id FROM medico WHERE dni = %s"
            existing_medico = execute_query(check_query, conn=conn, params=(dni,), is_select=True)
            if not existing_medico.empty:
                st.error("El DNI ya está registrado como médico.")
                conn.close()
                return False

            dni_int = int(dni) # Asegura que DNI se guarda como INTEGER
            query = "INSERT INTO medico (nombre, apellido, dni, password) VALUES (%s, %s, %s, %s)"
            success = execute_query(query, conn=conn, params=(nombre, apellido, dni_int, hashed_password), is_select=False)
        except ValueError:
            st.error("El DNI debe ser un número válido.")
        except Exception as e:
            st.error(f"Error al registrar médico: {e}")

    elif role == "Hospital":
        nombre = data.get("nombre")
        direccion = data.get("direccion")
        telefono = data.get("telefono") # Este será el identificador
        
        if not all([nombre, direccion, telefono, data.get("password")]):
            st.warning("Por favor completá todos los campos del hospital.")
            conn.close()
            return False
        
        try:
            # Validar si el Teléfono ya existe
            check_query = "SELECT id FROM hospital WHERE telefono = %s"
            existing_hospital = execute_query(check_query, conn=conn, params=(telefono,), is_select=True)
            if not existing_hospital.empty:
                st.error("El Teléfono ya está registrado como hospital.")
                conn.close()
                return False

            query = "INSERT INTO hospital (nombre, direccion, telefono, password) VALUES (%s, %s, %s, %s)"
            success = execute_query(query, conn=conn, params=(nombre, direccion, telefono, hashed_password), is_select=False)
        except Exception as e:
            st.error(f"Error al registrar hospital: {e}")
    
    conn.close()
    return success

# --- Función para mostrar el formulario de login ---
def show_login_form():
    st.subheader("Inicio de sesión")
    with st.form("login_form"):
        identifier = st.text_input("Usuario (DNI para Médicos, Teléfono para Hospitales)")
        password = st.text_input("Clave", type="password")
        submitted = st.form_submit_button("Iniciar sesión")

        if submitted:
            if identifier and password:
                is_authenticated, role, user_id, user_name = authenticate_user(identifier, password)
                if is_authenticated:
                    st.session_state["logged_in"] = True
                    st.session_state["user_identifier"] = identifier
                    st.session_state["role"] = role
                    st.session_state["user_id"] = user_id
                    st.session_state["user_name"] = user_name
                    st.success(f"¡Bienvenido/a, {user_name} ({role})!")
                    st.rerun() # Recargar para mostrar el contenido del dashboard
                else:
                    st.error("Usuario o clave incorrectos, o usuario no registrado.")
            else:
                st.error("Por favor completá todos los campos.")

# --- Función para mostrar el formulario de registro unificado ---
def show_register_form():
    st.subheader("Registro de Usuario")
    
    selected_role = st.selectbox("¿Qué tipo de usuario vas a registrar?", ["Médico", "Hospital"])

    if selected_role == "Médico":
        with st.form("form_registro_medico"):
            st.write("### Datos del Médico")
            nombre = st.text_input("Nombre")
            apellido = st.text_input("Apellido")
            dni = st.text_input("DNI (Será tu usuario para iniciar sesión)", max_chars=10)
            password = st.text_input("Contraseña", type="password")
            confirm_password = st.text_input("Confirmar Contraseña", type="password")
            
            submit = st.form_submit_button("Registrar Médico")

            if submit:
                if not all([nombre, apellido, dni, password, confirm_password]):
                    st.warning("Por favor completá todos los campos.")
                elif password != confirm_password:
                    st.error("Las contraseñas no coinciden.")
                else:
                    data = {"nombre": nombre, "apellido": apellido, "dni": dni, "password": password}
                    if register_user("Médico", data):
                        st.success("✅ Médico registrado correctamente. Ya puedes iniciar sesión.")
                        st.session_state["show_register"] = False
                        st.rerun()
    elif selected_role == "Hospital":
        with st.form("form_registro_hospital"):
            st.write("### Datos del Hospital")
            nombre = st.text_input("Nombre del Hospital")
            direccion = st.text_input("Dirección")
            telefono = st.text_input("Teléfono (Será tu usuario para iniciar sesión)", max_chars=15)
            password = st.text_input("Contraseña", type="password")
            confirm_password = st.text_input("Confirmar Contraseña", type="password")
            
            submit = st.form_submit_button("Registrar Hospital")

            if submit:
                if not all([nombre, direccion, telefono, password, confirm_password]):
                    st.warning("Por favor completá todos los campos.")
                elif password != confirm_password:
                    st.error("Las contraseñas no coinciden.")
                else:
                    data = {"nombre": nombre, "direccion": direccion, "telefono": telefono, "password": password}
                    if register_user("Hospital", data):
                        st.success("✅ Hospital registrado correctamente. Ya puedes iniciar sesión.")
                        st.session_state["show_register"] = False
                        st.rerun()

# --- Funciones para mostrar el contenido de cada dashboard ---

def show_hospital_dashboard():
    hospital_id = st.session_state.get("user_id")
    hospital_nombre = st.session_state.get("user_name")
    hospital_telefono = st.session_state.get("user_identifier")
    hospital_direccion = st.session_state.get("hospital_direccion")

    st.title(f"Bienvenido, Hospital {hospital_nombre}.")
    st.markdown(f"**Teléfono:** {hospital_telefono} | **Dirección:** {hospital_direccion}")
    st.markdown("---")

    # Barra lateral para navegación interna del dashboard
    st.sidebar.title("Menú Hospital")
    st.session_state["dashboard_menu_selection"] = st.sidebar.radio(
        "Navegación",
        ["Bienvenida", "Tu Inventario", "Hospitales Afiliados", "Historial de Tejidos", "Solicitudes", "Donantes"],
        key="hospital_dashboard_menu" # Clave única para evitar conflictos si hay otros radios
    )

    # Contenido principal basado en la selección del menú del dashboard
    if st.session_state["dashboard_menu_selection"] == "Bienvenida":
        st.write(f"""
        Aquí podrás acceder a toda la información relevante para la gestión de tejidos.
        Desde esta ventana podrás:
        * **Consultar el inventario actual** de tejidos disponibles en el banco (que gestiona tu hospital).
        * **Visualizar un mapa** con todos los hospitales afiliados.
        * **Revisar el historial** de tejidos registrados en el banco (o los que gestiona tu hospital).
        * **Ver y gestionar solicitudes** activas de tejidos.
        * **Registrar y consultar donantes.**
        """)

    elif st.session_state["dashboard_menu_selection"] == "Tu Inventario":
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
                conn_types = connect_to_supabase()
                if conn_types:
                    types_df = execute_query("SELECT tipo, descripcion FROM detalles_tejido ORDER BY descripcion", conn=conn_types, is_select=True)
                    conn_types.close()
                else:
                    types_df = pd.DataFrame({'tipo': [], 'descripcion': []})

                tejido_tipo_options = types_df.apply(lambda row: f"{row['descripcion']} ({row['tipo']})", axis=1).tolist()
                selected_tejido_display = st.selectbox("Tipo de Tejido", ["Seleccione un tipo"] + tejido_tipo_options)
                
                selected_tejido_code = None
                if selected_tejido_display and selected_tejido_display != "Seleccione un tipo":
                    selected_tejido_code = selected_tejido_display.split('(')[-1][:-1]

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

                                if donante_id_val:
                                    check_donante = execute_query("SELECT id FROM donante WHERE id = %s", conn=conn_add, params=(donante_id_val,), is_select=True)
                                    if check_donante.empty:
                                        st.error(f"El ID de Donante {donante_id_val} no existe. Registrá al donante primero o dejá el campo en blanco.")
                                        conn_add.close()
                                        st.stop()
                                if medico_id_val:
                                    check_medico = execute_query("SELECT id FROM medico WHERE id = %s", conn=conn_add, params=(medico_id_val,), is_select=True)
                                    if check_medico.empty:
                                        st.error(f"El ID de Médico {medico_id_val} no existe. Registrá al médico primero o dejá el campo en blanco.")
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
                                    hospital_id,
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

    elif st.session_state["dashboard_menu_selection"] == "Hospitales Afiliados":
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

    elif st.session_state["dashboard_menu_selection"] == "Historial de Tejidos":
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

    elif st.session_state["dashboard_menu_selection"] == "Solicitudes":
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
                        st.success(f"✔️ Solicitud de {cantidad} de {selected_tejido_code_req} para {fecha_necesidad} enviada (simulado).")
                        st.info("Recordá que necesitas crear la tabla `solicitudes` en tu base de datos para que esta funcionalidad sea real.")

    elif st.session_state["dashboard_menu_selection"] == "Donantes":
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

def show_medico_dashboard():
    # Placeholder para el dashboard del médico si decides unificarlo aquí también
    medico_id = st.session_state.get("user_id")
    medico_nombre = st.session_state.get("user_name")
    medico_dni = st.session_state.get("user_identifier")

    st.title(f"Bienvenido, Dr./Dra. {medico_nombre}.")
    st.markdown(f"**DNI:** {medico_dni}")
    st.markdown("---")

    st.sidebar.title("Menú Médico")
    st.session_state["dashboard_menu_selection"] = st.sidebar.radio(
        "Navegación",
        ["Bienvenida", "Mis Pacientes", "Registrar Donación", "Consultar Tejidos"],
        key="medico_dashboard_menu" # Clave única para evitar conflictos
    )

    if st.session_state["dashboard_menu_selection"] == "Bienvenida":
        st.write("Aquí podrás gestionar tus actividades como médico en TissBank.")
        st.info("Esta sección aún está en desarrollo. ¡Pronto tendrás más funcionalidades!")

    elif st.session_state["dashboard_menu_selection"] == "Mis Pacientes":
        st.header("📋 Mis Pacientes")
        st.write("Listado y gestión de tus pacientes.")
        st.warning("Esta sección requiere la creación de una tabla 'paciente' y 'medico_paciente'.")
        st.dataframe(pd.DataFrame({'ID Paciente': [1,2], 'Nombre': ['Paciente A', 'Paciente B']}))

    elif st.session_state["dashboard_menu_selection"] == "Registrar Donación":
        st.header("💉 Registrar Nueva Donación")
        st.write("Registra la recolección de un nuevo tejido.")
        st.info("Esta funcionalidad es similar al 'Registrar Nuevo Tejido Recibido' del hospital, pero desde la perspectiva del médico.")
        # Aquí podrías poner un formulario similar al de registrar tejido del hospital, pero quizá más enfocado en el médico.
        
    elif st.session_state["dashboard_menu_selection"] == "Consultar Tejidos":
        st.header("🔍 Consultar Tejidos Disponibles")
        st.write("Busca tejidos disponibles en la red de hospitales.")
        st.info("Aquí el médico podría buscar tejidos por tipo, estado, etc., en todo el banco.")

# --- Lógica principal de la aplicación ---
if not st.session_state.get("logged_in", False):
    # Lógica para mostrar formularios de login/registro
    if st.session_state["show_register"]:
        show_register_form()
        st.markdown("---")
        if st.button("Volver al Inicio de Sesión"):
            st.session_state["show_register"] = False
            st.rerun()
    else:
        show_login_form()
        st.markdown("---")
        if st.button("¿No tenés cuenta? Registrate acá"):
            st.session_state["show_register"] = True
            st.rerun()
else:
    # Contenido para usuarios logueados (Dashboards)
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar sesión", key="logout_button"): # Añadir clave única para el botón
        for key in ["logged_in", "user_identifier", "role", "user_id", "user_name", "hospital_direccion", "dashboard_menu_selection"]:
            st.session_state.pop(key, None)
        st.rerun()

    if st.session_state["role"] == "Médico":
        show_medico_dashboard()
    elif st.session_state["role"] == "Hospital":
        show_hospital_dashboard()