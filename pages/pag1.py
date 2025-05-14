import streamlit as st
from functions import connect_to_supabase, execute_query
import pandas as pd

def mostrar_medicos():
    conn = connect_to_supabase()
    if conn:
        query = "SELECT * FROM medico"
        df = execute_query(query, conn=conn, is_select=True)
        if not df.empty:
            st.dataframe(df)
        else:
            st.warning("No se encontraron médicos en la base de datos.")
    else:
        st.error("No se pudo conectar a la base de datos.")

st.title("Medicos")
# Llamada a la función
mostrar_medicos()


switch_page = st.button("Registros")
if switch_page:
    # Switch to the selected page
    st.switch_page(Registros_medicos.py)