import streamlit as st
import sys
import os
import hashlib # Para un hashing básico de contraseñas (¡no uses esto en producción sin un algoritmo más fuerte!)

# Asegúrate de que 'functions.py' sea importable.
# Si 'app.py' está en la raíz y 'functions.py' también, la siguiente línea no sería necesaria.
# Pero si 'app.py' está en 'pages/' y 'functions.py' en la raíz, entonces sí.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from functions import connect_to_supabase, execute_query
# No necesitas 'streamlit_extras.switch_page_button' si estás manejando la navegación
# dentro de la misma página principal con st.session_state.

# --- Configuración de la página ---
st.set_page_config(
    page_title="TissBank",
    page_icon="🧬",
    layout="centered"
)

# --- Logo centrado ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("images/logo.png", width=300)

# --- Inicializar estado de sesión ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_identifier" not in st.session_state: # Usamos user_identifier para DNI/Telefono
    st.session_state["user_identifier"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "show_register" not in st.session_state:
    st.session_state["show_register"] = False

# --- Hashing de Contraseñas (Básico, para ejemplo. Usa bcrypt en producción) ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Función para autenticar usuario ---
def authenticate_user(identifier, password):
    """
    Autentica un usuario verificando en las tablas de medico y hospital.
    Retorna (True, role, id_del_usuario) si es exitoso, (False, None, None) de lo contrario.
    `identifier` será DNI para médicos y Teléfono para hospitales.
    """
    conn = connect_to_supabase()
    if conn is None:
        st.error("No se pudo conectar a la base de datos para autenticación.")
        return False, None, None

    hashed_password = hash_password(password)

    # Intentar autenticar como Médico (usando DNI como identificador)
    query_medico = "SELECT id, dni FROM medico WHERE dni = %s AND password = %s"
    medico_data = execute_query(query_medico, conn=conn, params=(identifier, hashed_password), is_select=True)
    if not medico_data.empty:
        user_id = medico_data.iloc[0]['id']
        conn.close()
        return True, "Médico", user_id

    # Intentar autenticar como Hospital (usando Teléfono como identificador)
    query_hospital = "SELECT id, telefono FROM hospital WHERE telefono = %s AND password = %s"
    hospital_data = execute_query(query_hospital, conn=conn, params=(identifier, hashed_password), is_select=True)
    if not hospital_data.empty:
        user_id = hospital_data.iloc[0]['id']
        conn.close()
        return True, "Hospital", user_id
    
    conn.close()
    return False, None, None

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

            dni_int = int(dni)
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

            # No es necesario convertir a int si el teléfono puede tener caracteres especiales o guiones.
            # Aseguramos que sea string para el guardado.
            telefono_str = str(telefono)
            query = "INSERT INTO hospital (nombre, direccion, telefono, password) VALUES (%s, %s, %s, %s)"
            success = execute_query(query, conn=conn, params=(nombre, direccion, telefono_str, hashed_password), is_select=False)
        except Exception as e:
            st.error(f"Error al registrar hospital: {e}")
    
    conn.close()
    return success

# --- Función para mostrar el formulario de login ---
def show_login_form():
    st.subheader("Inicio de sesión")
    with st.form("login_form"):
        # El usuario ingresa su DNI o Teléfono según su rol
        identifier = st.text_input("Usuario (DNI para Médicos, Teléfono para Hospitales)")
        password = st.text_input("Clave", type="password")
        submitted = st.form_submit_button("Iniciar sesión")

        if submitted:
            if identifier and password:
                is_authenticated, role, user_id = authenticate_user(identifier, password)
                if is_authenticated:
                    st.session_state["logged_in"] = True
                    st.session_state["user_identifier"] = identifier # Guardamos DNI/Teléfono
                    st.session_state["role"] = role
                    st.session_state["user_id"] = user_id # Guardamos el ID del usuario
                    st.success(f"¡Bienvenido/a, {identifier} ({role})!")
                    st.rerun() # Recargar para mostrar el contenido para usuarios logueados
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
                        st.session_state["show_register"] = False # Volver al login
                        st.rerun()
                    # El error ya se maneja dentro de register_user
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
                        st.session_state["show_register"] = False # Volver al login
                        st.rerun()
                    # El error ya se maneja dentro de register_user

# --- Lógica principal de la aplicación ---
if not st.session_state.get("logged_in", False):
    if st.session_state["show_register"]:
        show_register_form()
        st.markdown("---") # Separador visual
        if st.button("Volver al Inicio de Sesión"):
            st.session_state["show_register"] = False
            st.rerun()
    else:
        show_login_form()
        st.markdown("---") # Separador visual
        if st.button("¿No tenés cuenta? Registrate acá"):
            st.session_state["show_register"] = True
            st.rerun()
else:
    # Contenido para usuarios logueados
    st.success(f"¡Hola {st.session_state.get('user_identifier')} ({st.session_state.get('role')})!")
    st.info("Usá el menú lateral para navegar por el sistema.")

    # Ejemplo de contenido dinámico basado en el rol
    if st.session_state["role"] == "Médico":
        st.write(f"¡Bienvenido, Médico! Tu ID de usuario es: {st.session_state.get('user_id')}")
        st.markdown("Aquí puedes ver tus pacientes, historial, etc.")
        # Aquí podrías añadir enlaces a otras páginas de Streamlit para médicos
        # st.page_link("pages/dashboard_medico.py", label="Ir a mi Dashboard Médico", icon="🩺")

    elif st.session_state["role"] == "Hospital":
        st.write(f"¡Bienvenido, Hospital! Tu ID de usuario es: {st.session_state.get('user_id')}")
        st.markdown("Aquí puedes gestionar tus médicos, citas, etc.")
        # Aquí podrías añadir enlaces a otras páginas de Streamlit para hospitales
        # st.page_link("pages/dashboard_hospital.py", label="Ir a mi Dashboard Hospital", icon="🏥")

    st.markdown("---") # Separador visual
    if st.button("Cerrar sesión"):
        for key in ["logged_in", "user_identifier", "role", "user_id"]: # Limpiar user_id también
            st.session_state.pop(key, None)
        st.rerun()
        