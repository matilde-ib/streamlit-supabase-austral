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
        estado = st.selectbox("Estado", ["", "Disponible", "Reservado", "Enviado"])

    # Construir query - CORREGIDO: usar la tabla correcta
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
        
        # Mostrar tejidos en formato de tabla más limpio
        for i, row in tejidos.iterrows():
            with st.expander(f"🧬 {row['tipo']} - {row.get('ubicacion', 'N/A')} ({row['estado']})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**ID:** {row['id']}")
                    st.write(f"**Tipo:** {row['tipo']}")
                    if 'ubicacion' in row and row['ubicacion']:
                        st.write(f"**Ubicación:** {row['ubicacion']}")
                    st.write(f"**Estado:** {row['estado']}")
                    if 'unidades' in row and row['unidades'] is not None:
                        st.write(f"**Unidades Disponibles:** {row['unidades']}")
                    if 'condicion_recoleccion' in row and row['condicion_recoleccion']:
                        st.write(f"**Condición:** {row['condicion_recoleccion']}")
                
                with col2:
                    # Verificar si el tejido está disponible para solicitud
                    unidades_disponibles = row.get('unidades', 0) if row.get('unidades') is not None else 0
                    
                    if row["estado"] == "disponible" and unidades_disponibles > 0:
                        if st.button(f"🚀 Solicitar", key=f"solicitar_{row['id']}", type="primary"):
                            # Obtener datos del médico y tejido
                            medico_id = int(st.session_state.get("user_id"))
                            tipo_tejido = row['tipo']
                            ubicacion_tejido = row.get('ubicacion', '') or ''
                            
                            # Verificar que no exista ya una solicitud pendiente para este tejido
                            verificar_query = """
                                SELECT id FROM solicitud 
                                WHERE medico_id = %s AND tipo = %s AND ubicacion = %s AND estado = 'pendiente'
                            """
                            solicitud_existente = execute_query(
                                verificar_query,
                                conn=conn,
                                params=(medico_id, tipo_tejido, ubicacion_tejido),
                                is_select=True
                            )
                            
                            if not solicitud_existente.empty:
                                st.warning("⚠️ Ya tienes una solicitud pendiente para este tipo de tejido en esta ubicación.")
                            else:
                                # Crear la solicitud
                                solicitud_query = """
                                    INSERT INTO solicitud (medico_id, tipo, ubicacion, estado, fecha_solicitud)
                                    VALUES (%s, %s, %s, 'pendiente', NOW())
                                """
                                success = execute_query(
                                    solicitud_query,
                                    conn=conn,
                                    params=(medico_id, tipo_tejido, ubicacion_tejido),
                                    is_select=False
                                )
                                
                                if success:
                                    st.success("✅ ¡Solicitud enviada correctamente!")
                                    st.info("Puedes ver tu solicitud en la sección 'Tus Solicitudes'")
                                    # Pequeña pausa para que el usuario vea el mensaje
                                    import time
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ No se pudo enviar la solicitud. Inténtalo nuevamente.")
                    else:
                        if row["estado"] != "disponible":
                            st.info(f"Estado: {row['estado']}")
                        elif unidades_disponibles <= 0:
                            st.warning("Sin unidades")
                        else:
                            st.info("No disponible")

# --------------------------------------------
# 📦 SECCIÓN 2: TUS SOLICITUDES
# --------------------------------------------
elif opcion == "📦 Tus Solicitudes":
    st.header("📦 Historial de tus Solicitudes")
    
    medico_id = int(st.session_state["user_id"])

    # Consulta para obtener las solicitudes del médico
    solicitud_query = """
    SELECT id, fecha_solicitud, estado, tipo, ubicacion
    FROM solicitud
    WHERE medico_id = %s
    ORDER BY fecha_solicitud DESC
    """

    solicitudes = execute_query(solicitud_query, conn=conn, params=(medico_id,), is_select=True)

    if solicitudes.empty:
        st.info("🔍 Aún no has realizado solicitudes.")
        st.markdown("💡 **Consejo:** Ve a la sección 'Ver Tejidos' para solicitar tejidos disponibles.")
    else:
        st.success(f"📋 Tienes {len(solicitudes)} solicitudes registradas")
        
        # Mostrar estadísticas rápidas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            pendientes = len(solicitudes[solicitudes['estado'] == 'pendiente'])
            st.metric("🟡 Pendientes", pendientes)
        with col2:
            aprobadas = len(solicitudes[solicitudes['estado'] == 'aprobada'])
            st.metric("🟢 Aprobadas", aprobadas)
        with col3:
            rechazadas = len(solicitudes[solicitudes['estado'] == 'rechazada'])
            st.metric("🔴 Rechazadas", rechazadas)
        with col4:
            enviadas = len(solicitudes[solicitudes['estado'] == 'enviada'])
            st.metric("📦 Enviadas", enviadas)
        
        st.markdown("---")
        
        # Filtro por estado
        estados_disponibles = ["Todos"] + list(solicitudes['estado'].unique())
        filtro_estado = st.selectbox("Filtrar por estado:", estados_disponibles)
        
        # Aplicar filtro
        if filtro_estado != "Todos":
            solicitudes_filtradas = solicitudes[solicitudes['estado'] == filtro_estado]
        else:
            solicitudes_filtradas = solicitudes
        
        # Mostrar solicitudes en cards
        if solicitudes_filtradas.empty:
            st.info(f"No hay solicitudes con estado '{filtro_estado}'")
        else:
            for i, row in solicitudes_filtradas.iterrows():
                # Determinar color según estado
                if row['estado'] == 'pendiente':
                    estado_color = "🟡"
                elif row['estado'] == 'aprobada':
                    estado_color = "🟢"
                elif row['estado'] == 'rechazada':
                    estado_color = "🔴"
                elif row['estado'] == 'enviada':
                    estado_color = "📦"
                else:
                    estado_color = "⚪"
                
                with st.expander(f"{estado_color} Solicitud #{row['id']} - {row['tipo']} ({row['estado'].upper()})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**ID Solicitud:** {row['id']}")
                        st.write(f"**Tipo de Tejido:** {row['tipo']}")
                        st.write(f"**Ubicación:** {row['ubicacion']}")
                    with col2:
                        st.write(f"**Estado:** {row['estado'].upper()}")
                        st.write(f"**Fecha de Solicitud:** {row['fecha_solicitud']}")
                        
                        # Mostrar acciones según el estado
                        if row['estado'] == 'pendiente':
                            st.info("⏳ Tu solicitud está siendo revisada")
                        elif row['estado'] == 'aprobada':
                            st.success("✅ Solicitud aprobada - Pendiente de envío")
                        elif row['estado'] == 'enviada':
                            st.success("📦 Tejido enviado - Revisa tu correo")
                        elif row['estado'] == 'rechazada':
                            st.error("❌ Solicitud rechazada")
        
        # Opción para actualizar
        if st.button("🔄 Actualizar solicitudes"):
            st.rerun()

# Cerrar conexión al final
if conn:
    conn.close()