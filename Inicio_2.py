import streamlit as st
from streamlit_extras.switch_page_button import switch_page

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

# --- Inicializar estado de registro si no existe ---
if "show_register" not in st.session_state:
    st.session_state["show_register"] = False

# --- Función para mostrar el formulario de login ---
def show_login():
    st.subheader("Inicio de sesión")
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Clave", type="password")
        role = st.selectbox("Rol", ["Médico", "Hospital"])
        submitted = st.form_submit_button("Iniciar sesión")

        if submitted:
            if username and password and role:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = role
                st.success(f"¡Bienvenido/a, {username} ({role})!")
            else:
                st.error("Por favor completá todos los campos.")


# --- Mostrar el contenido según estado ---
if not st.session_state.get("logged_in", False):
    show_login()
else:
    st.success(f"¡Hola {st.session_state.get('username')} ({st.session_state.get('role')})!")
    st.info("Usá el menú lateral para navegar por el sistema.")

    if st.button("Cerrar sesión"):
        for key in ["logged_in", "username", "role"]:
            st.session_state.pop(key, None)
        st.rerun()


st.page_link("pages/Registro_medicos.py", label="¿No tenés cuenta? Registrate acá", icon="📝")