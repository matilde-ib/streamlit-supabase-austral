import streamlit as st
from functions import connect_to_supabase, execute_query  # importar tu archivo
import pandas as pd

# Título
st.title("Registro de Usuario 🩺")

# Formulario
with st.form("form_registro"):
    nombre = st.text_input("Nombre")
    apellido = st.text_input("Apellido")
    dni = st.text_input("DNI", max_chars=10)
    
    submit = st.form_submit_button("Registrar")

# Conexión a la base de datos
conn = connect_to_supabase()

if submit:
    if not nombre or not apellido or not dni:
        st.warning("Por favor completá todos los campos.")
    else:
        try:
            dni_int = int(dni)
            query = f"""
                INSERT INTO medico (nombre, apellido, dni)
                VALUES ('{nombre}', '{apellido}', {dni_int});
            """
            result = execute_query(query, conn=conn, is_select=False)
            
            if result:
                st.success("✅ Médico registrado correctamente.")
                # Redirigir a la página de inicio de sesión después del registro exitoso
                st.info("Redirigiendo al inicio de sesión...")
                st.experimental_rerun()  # Usar rerun o bien actualizar el estado para redirigir
            else:
                st.error("❌ Error al registrar el médico.")
        except ValueError:
            st.error("El DNI debe ser un número.")
        except Exception as e:
            st.error(f"Error: {e}")
