# pages/dashboard_medico.py

import streamlit as st
import pandas as pd
from functions import connect_to_supabase, execute_query

st.set_page_config(page_title="Dashboard Médico", page_icon="🩺", layout="wide")
st.title("🩺 Dashboard del Médico")

# Verificación de sesión
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("No estás logueado. Por favor, iniciá sesión desde la página principal.")
    st.stop()

st.sidebar.title("Menú Médico")
opcion = st.sidebar.radio("Navegación", ["📋 Ver Tejidos", "📦 Tus Solicitudes"])

# Conexión
conn = connect_to_supabase()

# --------------------------------------------
# 📋 SECCIÓN 1: VER TODOS LOS TEJIDOS
# --------------------------------------------
if opcion == "📋 Ver Tejidos":
    st.header("📋 Todos los Tejidos Disponibles")

    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        tipo = st.text_input("Filtrar por Tipo")
    with col2:
        ubicacion = st.text_input("Filtrar por Ubicación")
    with col3:
        estado = st.selectbox("Estado", ["", "disponible", "reservado", "enviado"])

    # Construir query
    query = "SELECT * FROM tejidos WHERE TRUE"
    params = []

    if tipo:
        query += " AND tipo ILIKE %s"
        params.append(f"%{tipo}%")
    if ubicacion:
        query += " AND ubicacion ILIKE %s"
        params.append(f"%{ubicacion}%")
    if estado:
        query += " AND estado = %s"
        params.append(estado)

    tejidos = execute_query(query, conn=conn, params=tuple(params), is_select=True)

    if tejidos.empty:
        st.warning("No se encontraron tejidos.")
    else:
        st.success(f"Se encontraron {len(tejidos)} tejidos.")
        for i, row in tejidos.iterrows():
            with st.expander(f"🧬 {row['tipo']} - {row['ubicacion']} ({row['estado']})"):
                st.write(f"**ID:** {row['id']}")
                st.write(f"**Tipo:** {row['tipo']}")
                st.write(f"**Ubicación:** {row['ubicacion']}")
                st.write(f"**Estado:** {row['estado']}")
                st.write(f"**Unidades Disponibles:** {row['unidades']}")

                if row["estado"] == "disponible" and row["unidades"] > 0:
                    if st.button(f"Solicitar Tejido {row['id']}", key=f"solicitar_{row['id']}"):
                        medico_id = st.session_state.get("user_id")
                        solicitud_query = """
                            INSERT INTO solicitudes (medico_id, tejido_id, estado, fecha_solicitud)
                            VALUES (%s, %s, 'pendiente', NOW())
                        """
                        success = execute_query(solicitud_query, conn=conn, params=(medico_id, row['id']), is_select=False)
                        if success:
                            st.success("✅ Solicitud enviada correctamente.")
                        else:
                            st.error("❌ No se pudo enviar la solicitud.")

# --------------------------------------------
# 📦 SECCIÓN 2: TUS SOLICITUDES
# --------------------------------------------
elif opcion == "📦 Tus Solicitudes":
    st.header("📦 Historial de tus Solicitudes")

    medico_id = st.session_state.get("user_id")
    solicitud_query = """
        SELECT s.id, s.fecha_solicitud, s.estado AS estado_solicitud,
               t.tipo, t.ubicacion, t.estado AS estado_tejido
        FROM solicitudes s
        JOIN tejido t ON s.tejido_id = t.id
        WHERE s.medico_id = %s
        ORDER BY s.fecha_solicitud DESC
    """

    solicitudes = execute_query(solicitud_query, conn=conn, params=(medico_id,), is_select=True)

    if solicitudes.empty:
        st.info("Aún no realizaste solicitudes.")
    else:
        st.dataframe(solicitudes.rename(columns={
            "id": "ID Solicitud",
            "fecha_solicitud": "Fecha",
            "estado_solicitud": "Estado Solicitud",
            "tipo": "Tipo de Tejido",
            "ubicacion": "Ubicación",
            "estado_tejido": "Estado del Tejido"
        }))
