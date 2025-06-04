import streamlit as st
import pandas as pd
from functions import connect_to_supabase, execute_query

st.set_page_config(page_title="Dashboard Médico", page_icon="🩺", layout="wide")
st.title("🩺 Dashboard del Médico")

# Verificación de sesión y obtención de información del médico
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("No estás logueado. Por favor, iniciá sesión desde la página principal.")
    st.stop()

# Obtener y validar información del médico logueado
medico_id = st.session_state.get("user_id")
if not medico_id:
    st.error("❌ Error: No se pudo obtener tu ID de usuario. Por favor, vuelve a iniciar sesión.")
    st.stop()

try:
    medico_id = int(medico_id)
except (ValueError, TypeError):
    st.error("❌ Error: ID de usuario inválido. Por favor, vuelve a iniciar sesión.")
    st.stop()

# Conexión
conn = connect_to_supabase()

# Verificar que el médico existe en la base de datos
verificar_medico_query = """
    SELECT id, nombre, apellido FROM medico WHERE id = %s
"""
medico_info = execute_query(
    verificar_medico_query,
    conn=conn,
    params=(medico_id,),
    is_select=True
)

if medico_info.empty:
    st.error(f"❌ Error: Tu perfil de médico (ID: {medico_id}) no existe en el sistema. Por favor, contacta al administrador.")
    if conn:
        conn.close()
    st.stop()

# Mostrar información del médico en el sidebar
medico_nombre = medico_info.iloc[0]['nombre']
medico_apellido = medico_info.iloc[0]['apellido']

st.sidebar.title("Menú Médico")
st.sidebar.success(f"👨‍⚕️ {medico_nombre} {medico_apellido}")
st.sidebar.write(f"ID: {medico_id}")
opcion = st.sidebar.radio("Navegación", ["📋 Ver Tejidos", "📦 Tus Solicitudes"])

# Conexión ya establecida arriba

# --------------------------------------------
# 📋 SECCIÓN 1: VER TODOS LOS TEJIDOS (TABLA UNIFICADA)
# --------------------------------------------
if opcion == "📋 Ver Tejidos":
    st.header("📋 Todos los Tejidos Disponibles")

    # Filtros en columnas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filtro_tipo = st.text_input("🔍 Filtrar por Tipo")
    with col2:
        filtro_ubicacion = st.text_input("📍 Filtrar por Ubicación")
    with col3:
        filtro_estado = st.selectbox("📊 Estado", ["", "Disponible", "Reservado", "Enviado"])
    with col4:
        filtro_descripcion = st.text_input("📝 Filtrar por Descripción")

    # Query unificada de tejidos con detalles_tejido (SIN unidades)
    query = """
    SELECT 
        t.tipo,
        COALESCE(dt.descripcion, '') as descripcion,
        COALESCE(dt.ubicacion, '') as ubicacion,
        t.estado,
        t.condicion_recoleccion,
        t.fecha_recoleccion,
        t.fecha_de_estado,
        t.id as tejido_id
    FROM tejidos t
    LEFT JOIN detalles_tejido dt ON t.tipo = dt.tipo
    WHERE TRUE
    """
    params = []

    # Aplicar filtros
    if filtro_tipo:
        query += " AND t.tipo ILIKE %s"
        params.append(f"%{filtro_tipo}%")
    if filtro_ubicacion:
        query += " AND dt.ubicacion ILIKE %s"
        params.append(f"%{filtro_ubicacion}%")
    if filtro_estado:
        query += " AND t.estado = %s"
        params.append(filtro_estado)
    if filtro_descripcion:
        query += " AND dt.descripcion ILIKE %s"
        params.append(f"%{filtro_descripcion}%")

    query += " ORDER BY t.tipo, dt.ubicacion"

    tejidos = execute_query(query, conn=conn, params=tuple(params), is_select=True)

    if tejidos.empty:
        st.warning("No se encontraron tejidos con los filtros aplicados.")
    else:
        st.success(f"Se encontraron {len(tejidos)} tejidos.")
        
        # Preparar datos para mostrar (sin IDs)
        tejidos_display = tejidos.copy()
        # Eliminar la columna tejido_id para no mostrarla
        if 'tejido_id' in tejidos_display.columns:
            tejidos_display = tejidos_display.drop('tejido_id', axis=1)
        
        # Renombrar columnas para mejor presentación
        column_mapping = {
            'tipo': 'Tipo de Tejido',
            'descripcion': 'Descripción',
            'ubicacion': 'Ubicación',
            'estado': 'Estado',
            'condicion_recoleccion': 'Condición de Recolección',
            'fecha_recoleccion': 'Fecha de Recolección',
            'fecha_de_estado': 'Fecha de Estado'
        }
        
        tejidos_display = tejidos_display.rename(columns=column_mapping)
        
        # Mostrar tabla
        st.dataframe(
            tejidos_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Estado": st.column_config.TextColumn(
                    "Estado",
                    help="Estado actual del tejido"
                )
            }
        )
        
        # Sección de solicitud de tejido (parte inferior)
        st.markdown("---")
        st.subheader("🚀 Solicitar Tejido")
        
        # Crear formulario de solicitud
        with st.form("form_solicitud_tejido"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Obtener tipos únicos disponibles
                tipos_disponibles = tejidos[tejidos['estado'] == 'Disponible']['tipo'].unique().tolist()
                tipo_solicitud = st.selectbox("Tipo de Tejido a Solicitar", tipos_disponibles)
            
            with col2:
                # Filtrar ubicaciones según el tipo seleccionado
                if tipo_solicitud:
                    ubicaciones_disponibles = tejidos[
                        (tejidos['tipo'] == tipo_solicitud) & 
                        (tejidos['estado'] == 'Disponible')
                    ]['ubicacion'].unique().tolist()
                    ubicacion_solicitud = st.selectbox("Ubicación", ubicaciones_disponibles)
                else:
                    ubicacion_solicitud = st.selectbox("Ubicación", [])
            
            with col3:
                # Mostrar estado de disponibilidad
                if tipo_solicitud and ubicacion_solicitud:
                    tejido_seleccionado = tejidos[
                        (tejidos['tipo'] == tipo_solicitud) & 
                        (tejidos['ubicacion'] == ubicacion_solicitud) &
                        (tejidos['estado'] == 'Disponible')
                    ]
                    if not tejido_seleccionado.empty:
                        st.success("✅ Disponible")
                    else:
                        st.error("❌ No disponible")
                else:
                    st.info("Selecciona tipo y ubicación")
            
            # Botón de envío
            submitted = st.form_submit_button("📤 Enviar Solicitud", type="primary", use_container_width=True)
            
            if submitted:
                if not tipo_solicitud or not ubicacion_solicitud:
                    st.error("⚠️ Por favor selecciona un tipo de tejido y una ubicación.")
                else:
                    # Verificar disponibilidad
                    tejido_disponible = tejidos[
                        (tejidos['tipo'] == tipo_solicitud) & 
                        (tejidos['ubicacion'] == ubicacion_solicitud) &
                        (tejidos['estado'] == 'Disponible')
                    ]
                    
                    if tejido_disponible.empty:
                        st.error("❌ El tejido seleccionado no está disponible.")
                    else:
                        # El medico_id ya fue validado al inicio del script
                        # Verificar solicitud existente
                        verificar_query = """
                            SELECT id FROM solicitud 
                            WHERE medico_id = %s AND tipo = %s AND ubicacion = %s AND estado = 'pendiente'
                        """
                        solicitud_existente = execute_query(
                            verificar_query,
                            conn=conn,
                            params=(medico_id, tipo_solicitud, ubicacion_solicitud),
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
                                params=(medico_id, tipo_solicitud, ubicacion_solicitud),
                                is_select=False
                            )
                            
                            if success:
                                st.success("✅ ¡Solicitud enviada correctamente!")
                                st.info("Puedes ver tu solicitud en la sección 'Tus Solicitudes'")
                                # Recargar la página para actualizar datos
                                import time
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ No se pudo enviar la solicitud. Inténtalo nuevamente.")

# --------------------------------------------
# 📦 SECCIÓN 2: TUS SOLICITUDES
# --------------------------------------------
elif opcion == "📦 Tus Solicitudes":
    st.header("📦 Historial de tus Solicitudes")
    
    # El medico_id ya fue validado al inicio del script
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
        
        # Preparar datos para mostrar (sin ID de solicitud)
        if not solicitudes_filtradas.empty:
            solicitudes_display = solicitudes_filtradas.copy()
            
            # Renombrar columnas
            column_mapping = {
                'fecha_solicitud': 'Fecha de Solicitud',
                'estado': 'Estado',
                'tipo': 'Tipo de Tejido',
                'ubicacion': 'Ubicación'
            }
            
            solicitudes_display = solicitudes_display.rename(columns=column_mapping)
            
            # Eliminar columna ID
            if 'id' in solicitudes_display.columns:
                solicitudes_display = solicitudes_display.drop('id', axis=1)
            
            # Mostrar tabla de solicitudes
            st.dataframe(
                solicitudes_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Estado": st.column_config.TextColumn(
                        "Estado",
                        help="Estado actual de la solicitud"
                    ),
                    "Fecha de Solicitud": st.column_config.DatetimeColumn(
                        "Fecha de Solicitud",
                        help="Fecha y hora de la solicitud"
                    )
                }
            )
        else:
            st.info(f"No hay solicitudes con estado '{filtro_estado}'")
        
        # Opción para actualizar
        if st.button("🔄 Actualizar solicitudes"):
            st.rerun()

# Cerrar conexión al final
if conn:
    conn.close()