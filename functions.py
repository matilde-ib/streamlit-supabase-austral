# functions.py

import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import streamlit as st # Importa streamlit aquí para usar st.error

load_dotenv() # Cargar variables de entorno del archivo .env

# --- CÓDIGO DE DIAGNÓSTICO (TEMPORAL) ---
print("--- INICIANDO DIAGNÓSTICO DE VARIABLES DE ENTORNO ---")
host = os.getenv("SUPABASE_DB_HOST")
db_name = os.getenv("SUPABASE_DB_NAME")
user = os.getenv("SUPABASE_DB_USER")
password = os.getenv("SUPABASE_DB_PASSWORD")
port = os.getenv("SUPABASE_DB_PORT")

print(f"HOST LEÍDO: {host}")
print(f"DB_NAME LEÍDO: {db_name}")
print(f"USER LEÍDO: {user}")
# Por seguridad, no imprimimos la contraseña real, solo si la encontró o no.
print(f"PASSWORD LEÍDO: {'******' if password else None}")
print(f"PORT LEÍDO: {port}")
print("--- FIN DEL DIAGNÓSTICO ---")
# --- FIN DEL CÓDIGO DE DIAGNÓSTICO ---

def connect_to_supabase():
    """
    Establece una conexión con la base de datos Supabase usando psycopg2.
    Retorna el objeto de conexión si es exitoso, None en caso contrario.
    """
    try:
        # Re-leemos las variables aquí para asegurarnos de que la función las usa.
        db_host = os.getenv("SUPABASE_DB_HOST")
        db_name = os.getenv("SUPABASE_DB_NAME")
        db_user = os.getenv("SUPABASE_DB_USER")
        db_password = os.getenv("SUPABASE_DB_PASSWORD")
        db_port = os.getenv("SUPABASE_DB_PORT")
        
        # Verificación para asegurarnos de que las variables no son None
        if not all([db_host, db_name, db_user, db_password, db_port]):
            st.error("Una o más variables de entorno de Supabase no están definidas.")
            return None

        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        return conn
    except Exception as e:
        # Usamos st.error para mostrar el error en la interfaz de Streamlit
        st.error(f"Error al conectar con Supabase: {e}")
        return None

def execute_query(query, conn=None, params=None, is_select=True):
    """
    Ejecuta una consulta SQL en la base de datos Supabase.
    `query`: La cadena SQL a ejecutar.
    `conn`: Una conexión a la base de datos (opcional). Si no se proporciona, se crea una nueva.
    `params`: Una tupla o lista de parámetros para la consulta (opcional).
    `is_select`: Booleano, True si es una consulta SELECT, False para INSERT/UPDATE/DELETE.

    Si is_select es True, retorna un DataFrame con los resultados.
    Si is_select es False, retorna True si la operación fue exitosa, False en caso contrario.
    """
    _conn = conn # Usar la conexión provista o None
    if _conn is None:
        _conn = connect_to_supabase()
        if _conn is None:
            # st.error("execute_query: No se pudo establecer conexión a la base de datos.") # Debugging
            return pd.DataFrame() if is_select else False

    try:
        with _conn.cursor() as cur:
            if params is not None: # Usar 'is not None' para manejar correctamente tuplas vacías o None
                cur.execute(query, params)
            else:
                cur.execute(query)

            if is_select:
                column_names = [desc[0] for desc in cur.description]
                data = cur.fetchall()
                return pd.DataFrame(data, columns=column_names)
            else:
                _conn.commit() # Confirmar cambios para INSERT, UPDATE, DELETE
                return True
    except Exception as e:
        st.error(f"Error al ejecutar la consulta '{query[:50]}...': {e}") # Muestra parte de la query para debug
        _conn.rollback() # Revertir cambios en caso de error para operaciones no-SELECT
        return pd.DataFrame() if is_select else False
    finally:
        # Solo cerrar la conexión si fue creada dentro de esta función y no fue proporcionada externamente
        if conn is None and _conn is not None:
            _conn.close()