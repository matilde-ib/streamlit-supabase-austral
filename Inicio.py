# Inicio.py - App Principal de Login/Registro y Redirección

import streamlit as st
import sys
import os
import hashlib
import pandas as pd
from datetime import datetime

# Ajusta el path para importar 'functions.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from functions import connect_to_supabase, execute_query

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

# --- Super Host Settings ---
SUPER_HOST_TELEFONO = "1127289095"
SUPER_HOST_PASSWORD = "mati123"

def es_super_host(identifier, password):
    return (identifier == SUPER_HOST_TELEFONO) and (password == SUPER_HOST_PASSWORD)

# --- Inicializar estado de sesión ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_identifier" not in st.session_state:
    st.session_state["user_identifier"] = ""
if "plain_password" not in st.session_state:
    st.session_state["plain_password"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""
if "show_register" not in st.session_state:
    st.session_state["show_register"] = False

# --- Hashing de Contraseñas (Básico, para ejemplo) ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Función para autenticar usuario ---
def authenticate_user(identifier, password):
    conn = connect_to_supabase()
    if conn is None:
        st.error("No se pudo conectar a la base de datos para autenticación.")
        return False, None, None, None

    hashed_password = hash_password(password)

    query_medico = "SELECT id, dni, nombre FROM medico WHERE dni = %s AND password = %s"
    medico_data = execute_query(query_medico, conn=conn, params=(identifier, hashed_password), is_select=True)
    if not medico_data.empty:
        user_id = medico_data.iloc[0]['id']
        user_name = medico_data.iloc[0]['nombre']
        conn.close()
        return True, "Médico", user_id, user_name

    query_hospital = "SELECT id, telefono, nombre FROM hospital WHERE telefono = %s AND password = %s"
    hospital_data = execute_query(query_hospital, conn=conn, params=(identifier, hashed_password), is_select=True)
    if not hospital_data.empty:
        user_id = hospital_data.iloc[0]['id']
        user_name = hospital_data.iloc[0]['nombre']
        conn.close()
        return True, "Hospital", user_id, user_name
    
    conn.close()
    return False, None, None, None

# --- Función para registrar usuario (Centralizada) ---
def register_user(role, data):
    conn = connect_to_supabase()
    if conn is None:
        st.error("No se pudo conectar a la base de datos para el registro.")
        return False

    success = False
    hashed_password = hash_password(data.get("password"))

    if role == "Médico":
        nombre = data.get("nombre")
        apellido = data.get("apellido")
        dni = data.get("dni")
        
        if not all([nombre, apellido, dni, data.get("password")]):
            st.warning("Por favor completá todos los campos del médico.")
            conn.close()
            return False
        
        try:
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
        telefono = data.get("telefono")
        
        if not all([nombre, direccion, telefono, data.get("password")]):
            st.warning("Por favor completá todos los campos del hospital.")
            conn.close()
            return False
        
        try:
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
                    st.session_state["plain_password"] = password  # GUARDAMOS LA PASSWORD PLANA PARA VALIDAR SUPER HOST
                    st.session_state["role"] = role
                    st.session_state["user_id"] = user_id
                    st.session_state["user_name"] = user_name
                    st.success(f"¡Bienvenido/a, {user_name} ({role})!")
                    # Redirigir al usuario
                    if role == "Médico":
                        st.page_link("pages/Portal_Médico.py", label="Ir a mi Dashboard de Médico", icon="🩺")
                    elif role == "Hospital":
                        st.page_link("pages/Portal_Hospitalario.py", label="Ir a mi Dashboard de Hospital", icon="🏥")
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
        # SOLO el Super Host puede ver este bloque:
        if (
            st.session_state.get("logged_in")
            and es_super_host(st.session_state.get("user_identifier", ""), st.session_state.get("plain_password", ""))
        ):
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
        else:
            st.error("Sólo el super host puede crear usuarios hospitalarios. Iniciá sesión como super host para continuar.")

# --- Lógica principal de la aplicación ---
if not st.session_state.get("logged_in", False):
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
    st.success(f"Sesión activa: {st.session_state['user_name']} ({st.session_state['role']}).")
    st.write("Por favor, usa los enlaces de la barra lateral para navegar a tu dashboard.")

    if st.session_state["role"] == "Médico":
        st.page_link("pages/Portal_Médico.py", label="Ir a mi Dashboard de Médico", icon="🩺")
    elif st.session_state["role"] == "Hospital":
        st.page_link("pages/Portal_Hospitalario.py", label="Ir a mi Dashboard de Hospital", icon="🏥")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar sesión", key="logout_button"):
        # Limpiar todas las variables de sesión relevantes al cerrar sesión
        for key in list(st.session_state.keys()):
            st.session_state.pop(key, None)
        st.session_state["logged_in"] = False
        st.rerun()
