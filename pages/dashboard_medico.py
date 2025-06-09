import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from functions import connect_to_supabase, execute_query

st.set_page_config(page_title="Dashboard Médico", page_icon="🩺", layout="wide")

# --- FUNCIÓN PARA CALCULAR DISTANCIAS ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la Tierra en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# --- FUNCIÓN PARA OBTENER HOSPITALES ---
@st.cache_data
def get_hospitales_principales():
    data = [
        {"name": "Hospital Italiano", "address": "Tte. Gral. Juan Domingo Perón 4190, CABA", "lat": -34.6066, "lon": -58.4250},
        {"name": "Hospital Alemán", "address": "Av. Pueyrredón 1640, CABA", "lat": -34.5938, "lon": -58.4033},
        {"name": "Hospital Británico", "address": "Perdriel 74, CABA", "lat": -34.6284, "lon": -58.3840},
        {"name": "Hospital Garrahan", "address": "Pichincha 1890, CABA", "lat": -34.6293, "lon": -58.3908},
        {"name": "Hospital Fernández", "address": "Av. Cerviño 3356, CABA", "lat": -34.5822, "lon": -58.4111},
        {"name": "Hospital de Clínicas", "address": "Av. Córdoba 2351, CABA", "lat": -34.5989, "lon": -58.4005},
        {"name": "Sanatorio Güemes", "address": "Francisco Acuña de Figueroa 1240, CABA", "lat": -34.5983, "lon": -58.4214},
        {"name": "FLENI", "address": "Montañeses 2325, CABA", "lat": -34.5501, "lon": -58.4485},
        {"name": "Hospital Austral", "address": "Av. J. D. Perón 1500, Pilar", "lat": -34.4528, "lon": -58.9133},
        {"name": "Hospital Argerich", "address": "Pi y Margall 750, CABA", "lat": -34.6241, "lon": -58.3662},
        {"name": "Hospital Rivadavia", "address": "Av. Gral. Las Heras 2670, CABA", "lat": -34.5880, "lon": -58.3990},
        {"name": "Hospital Durand", "address": "Av. Díaz Vélez 5044, CABA", "lat": -34.6112, "lon": -58.4442},
        {"name": "Hospital Santojanni", "address": "Pilar 950, CABA", "lat": -34.6465, "lon": -58.5134},
        {"name": "Sanatorio Finochietto", "address": "Av. Córdoba 2678, CABA", "lat": -34.6043, "lon": -58.4045},
        {"name": "Fundación Favaloro", "address": "Av. Belgrano 1746, CABA", "lat": -34.6120, "lon": -58.3900}
    ]
    return pd.DataFrame(data)

# --- ESTILOS CSS MEJORADOS ---
def load_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto:wght@300;400;500;600;700&display=swap');

            :root {
                --primary-color: #2563EB;
                --primary-light: #3B82F6;
                --primary-dark: #1D4ED8;
                --primary-ultra-light: #EFF6FF;
                --secondary-color: #059669;
                --secondary-light: #10B981;
                --accent-color: #DC2626;
                --accent-warning: #F59E0B;
                --background-main: #F8FAFC;
                --background-card: #FFFFFF;
                --text-primary: #1E293B;
                --text-secondary: #475569;
                --border-color: #CBD5E1;
                --border-light: #E2E8F0;
                --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.07);
                --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                --radius-md: 8px;
                --radius-lg: 12px;
                --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            }

            .stApp {
                font-family: 'Inter', sans-serif;
                background: var(--background-main);
                color: var(--text-primary);
            }

            .metric-card {
                background: var(--background-card);
                border: 1px solid var(--border-light);
                border-radius: var(--radius-lg);
                padding: 1.5rem;
                box-shadow: var(--shadow-sm);
                transition: var(--transition);
                text-align: center;
            }

            .metric-card:hover {
                box-shadow: var(--shadow-md);
                transform: translateY(-2px);
            }

            .metric-value {
                font-size: 2rem;
                font-weight: 700;
                color: var(--primary-color);
                margin: 0.5rem 0;
            }

            .metric-label {
                font-size: 0.9rem;
                color: var(--text-secondary);
                font-weight: 500;
            }

            .welcome-card {
                background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
                color: white;
                padding: 2rem;
                border-radius: var(--radius-lg);
                margin-bottom: 2rem;
                text-align: center;
            }

            .feature-card {
                background: var(--background-card);
                border: 1px solid var(--border-light);
                border-radius: var(--radius-lg);
                padding: 1.5rem;
                margin: 1rem 0;
                box-shadow: var(--shadow-sm);
                transition: var(--transition);
            }

            .feature-card:hover {
                border-color: var(--primary-light);
                box-shadow: var(--shadow-md);
            }

            .status-badge {
                padding: 0.25rem 0.75rem;
                border-radius: 1rem;
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
            }

            .status-disponible { background: #DCFCE7; color: #166534; }
            .status-pendiente { background: #FEF3C7; color: #92400E; }
            .status-aprobada { background: #DCFCE7; color: #166534; }
            .status-rechazada { background: #FEE2E2; color: #DC2626; }
            .status-enviada { background: #DBEAFE; color: #1D4ED8; }

            .sidebar-metric {
                background: var(--primary-ultra-light);
                padding: 1rem;
                border-radius: var(--radius-md);
                margin: 0.5rem 0;
                text-align: center;
                border: 1px solid var(--primary-light);
            }

            .quick-action-btn {
                background: var(--secondary-color);
                color: white;
                padding: 0.75rem 1.5rem;
                border-radius: var(--radius-md);
                border: none;
                font-weight: 500;
                cursor: pointer;
                transition: var(--transition);
                width: 100%;
                margin: 0.25rem 0;
            }

            .quick-action-btn:hover {
                background: var(--secondary-light);
                transform: translateY(-1px);
            }
        </style>
    """, unsafe_allow_html=True)

load_css()

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

st.sidebar.title("Portal Médico")
st.sidebar.markdown(f"""
<div class="sidebar-metric">
    <h3 style="margin: 0; color: var(--primary-color);">👨‍⚕️ {medico_nombre} {medico_apellido}</h3>
    <p style="margin: 0.5rem 0; color: var(--text-secondary);">ID: {medico_id}</p>
</div>
""", unsafe_allow_html=True)

# Obtener estadísticas rápidas para el sidebar
solicitudes_medico = execute_query(
    "SELECT estado FROM solicitud WHERE medico_id = %s",
    conn=conn,
    params=(medico_id,),
    is_select=True
)

if not solicitudes_medico.empty:
    pendientes = len(solicitudes_medico[solicitudes_medico['estado'] == 'pendiente'])
    aprobadas = len(solicitudes_medico[solicitudes_medico['estado'] == 'aprobada'])
    total = len(solicitudes_medico)
    
    st.sidebar.markdown(f"""
    <div class="sidebar-metric">
        <strong>📊 Resumen Rápido</strong><br>
        Total solicitudes: {total}<br>
        Pendientes: {pendientes}<br>
        Aprobadas: {aprobadas}
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("---")
opcion = st.sidebar.radio(
    "Navegación", 
    ["🏠 Inicio", "📋 Ver Tejidos", "📦 Mis Solicitudes", "🌐 Red de Hospitales", "📊 Mi Dashboard", "🔬 Seguimiento de Casos"]
)

# --------------------------------------------
# 🏠 PÁGINA DE INICIO
# --------------------------------------------
if opcion == "🏠 Inicio":
    st.markdown(f"""
    <div class="welcome-card">
        <h1>¡Bienvenido, Dr. {medico_nombre} {medico_apellido}!</h1>
        <p>Portal de acceso al Banco de Tejidos - Gestión Médica Profesional</p>
        <p>Fecha: {datetime.now().strftime('%d de %B de %Y')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Estadísticas principales
    col1, col2, col3, col4 = st.columns(4)
    
    # Obtener estadísticas
    tejidos_disponibles = execute_query(
        "SELECT COUNT(*) as count FROM tejidos WHERE estado = 'Disponible'",
        conn=conn, is_select=True
    )
    
    mis_solicitudes = execute_query(
        f"SELECT estado FROM solicitud WHERE medico_id = {medico_id}",
        conn=conn, is_select=True
    )
    
    with col1:
        total_disponibles = tejidos_disponibles.iloc[0]['count'] if not tejidos_disponibles.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_disponibles}</div>
            <div class="metric-label">Tejidos Disponibles</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_solicitudes = len(mis_solicitudes) if not mis_solicitudes.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_solicitudes}</div>
            <div class="metric-label">Mis Solicitudes</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        pendientes = len(mis_solicitudes[mis_solicitudes['estado'] == 'pendiente']) if not mis_solicitudes.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{pendientes}</div>
            <div class="metric-label">Solicitudes Pendientes</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        aprobadas = len(mis_solicitudes[mis_solicitudes['estado'] == 'aprobada']) if not mis_solicitudes.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{aprobadas}</div>
            <div class="metric-label">Solicitudes Aprobadas</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Acciones rápidas
    st.subheader("🚀 Acciones Rápidas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>📋 Explorar Tejidos</h4>
            <p>Busca y filtra tejidos disponibles en el sistema</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Ver Tejidos Disponibles", use_container_width=True):
            st.session_state.opcion = "📋 Ver Tejidos"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>📦 Gestionar Solicitudes</h4>
            <p>Revisa el estado de tus solicitudes de tejidos</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Ver Mis Solicitudes", use_container_width=True):
            st.session_state.opcion = "📦 Mis Solicitudes"
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4>🌐 Red Hospitalaria</h4>
            <p>Explora la red de hospitales y logística</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Ver Red de Hospitales", use_container_width=True):
            st.session_state.opcion = "🌐 Red de Hospitales"
            st.rerun()
    
    # Solicitudes recientes
    if not mis_solicitudes.empty:
        st.markdown("---")
        st.subheader("📋 Mis Solicitudes Recientes")
        
        solicitudes_detalle = execute_query(
            """
            SELECT id, fecha_solicitud, estado, tipo, ubicacion
            FROM solicitud
            WHERE medico_id = %s
            ORDER BY fecha_solicitud DESC
            LIMIT 5
            """,
            conn=conn,
            params=(medico_id,),
            is_select=True
        )
        
        for _, solicitud in solicitudes_detalle.iterrows():
            estado_class = f"status-{solicitud['estado']}"
            st.markdown(f"""
            <div class="feature-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{solicitud['tipo']}</strong> - {solicitud['ubicacion']}<br>
                        <small>Solicitado: {solicitud['fecha_solicitud'].strftime('%d/%m/%Y')}</small>
                    </div>
                    <span class="status-badge {estado_class}">{solicitud['estado']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# --------------------------------------------
# 📋 SECCIÓN: VER TODOS LOS TEJIDOS (TABLA UNIFICADA)
# --------------------------------------------
elif opcion == "📋 Ver Tejidos":
    st.title("📋 Todos los Tejidos Disponibles")

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

    # Query unificada de tejidos con detalles_tejido
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
                                st.info("Puedes ver tu solicitud en la sección 'Mis Solicitudes'")
                                # Recargar la página para actualizar datos
                                import time
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ No se pudo enviar la solicitud. Inténtalo nuevamente.")

# --------------------------------------------
# 📦 SECCIÓN: MIS SOLICITUDES
# --------------------------------------------
elif opcion == "📦 Mis Solicitudes":
    st.title("📦 Historial de Mis Solicitudes")
    
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

# --------------------------------------------
# 🌐 SECCIÓN: RED DE HOSPITALES Y LOGÍSTICA
# --------------------------------------------
elif opcion == "🌐 Red de Hospitales":
    st.title("🌐 Red de Hospitales y Logística")
    st.markdown("Visualice la red hospitalaria y calcule tiempos de traslado estimados.")
    st.markdown("---")
    
    hospitales_df = get_hospitales_principales()
    st.subheader("Ubicación de Hospitales en la Red")
    st.map(hospitales_df, latitude='lat', longitude='lon', zoom=10)
    
    with st.expander("Ver lista de hospitales y direcciones"):
        st.dataframe(hospitales_df[['name', 'address']].rename(columns={'name': 'Hospital', 'address': 'Dirección'}), use_container_width=True)
    
    st.markdown("---")
    st.subheader("Calculadora de Tiempo de Traslado Estimado")
    
    col1, col2 = st.columns(2)
    origen = col1.selectbox("📍 Hospital de Origen", options=hospitales_df['name'], index=0)
    destino = col2.selectbox("🏁 Hospital de Destino", options=hospitales_df['name'], index=1)
        
    if st.button("Calcular Tiempo Estimado", type="secondary", use_container_width=True):
        if origen == destino: 
            st.warning("El hospital de origen y destino no pueden ser el mismo.")
        else:
            origen_coords = hospitales_df[hospitales_df['name'] == origen].iloc[0]
            destino_coords = hospitales_df[hospitales_df['name'] == destino].iloc[0]
            distancia = haversine(origen_coords['lat'], origen_coords['lon'], destino_coords['lat'], destino_coords['lon'])
            velocidad_promedio_kmh = 30
            tiempo_horas = distancia / velocidad_promedio_kmh
            tiempo_minutos = tiempo_horas * 60
            st.success(f"**Resultados de la estimación para la ruta: {origen} ➡️ {destino}**")
            res_col1, res_col2 = st.columns(2)
            res_col1.metric(label="Distancia en línea recta", value=f"{distancia:.2f} km")
            res_col2.metric(label="Tiempo de traslado estimado", value=f"~ {tiempo_minutos:.0f} min")
            google_maps_url = f"https://www.google.com/maps/dir/?api=1&origin={origen_coords['lat']},{origen_coords['lon']}&destination={destino_coords['lat']},{destino_coords['lon']}&travelmode=driving"
            st.link_button("Ver Ruta en Google Maps", google_maps_url, use_container_width=True)
            st.info("Nota: El tiempo estimado no considera tráfico real. El enlace a Google Maps mostrará la ruta y el tiempo real.")

# --------------------------------------------
# 📊 SECCIÓN: MI DASHBOARD PERSONAL
# --------------------------------------------
elif opcion == "📊 Mi Dashboard":
    st.title("📊 Mi Dashboard Personal")
    st.markdown("Análisis detallado de tu actividad médica en el banco de tejidos.")
    
    # Obtener datos para análisis
    mis_solicitudes_detalle = execute_query(
        """
        SELECT s.*, dt.descripcion 
        FROM solicitud s
        LEFT JOIN detalles_tejido dt ON s.tipo = dt.tipo
        WHERE s.medico_id = %s
        ORDER BY s.fecha_solicitud DESC
        """,
        conn=conn,
        params=(medico_id,),
        is_select=True
    )
    
    if not mis_solicitudes_detalle.empty:
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        total_solicitudes = len(mis_solicitudes_detalle)
        pendientes = len(mis_solicitudes_detalle[mis_solicitudes_detalle['estado'] == 'pendiente'])
        aprobadas = len(mis_solicitudes_detalle[mis_solicitudes_detalle['estado'] == 'aprobada'])
        tasa_aprobacion = (aprobadas / total_solicitudes * 100) if total_solicitudes > 0 else 0
        
        with col1:
            st.metric("Total Solicitudes", total_solicitudes)
        with col2:
            st.metric("Solicitudes Aprobadas", aprobadas)
        with col3:
            st.metric("Solicitudes Pendientes", pendientes)
        with col4:
            st.metric("Tasa de Aprobación", f"{tasa_aprobacion:.1f}%")
        
        st.markdown("---")
        
        # Análisis por tipo de tejido
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Solicitudes por Tipo de Tejido")
            tipo_counts = mis_solicitudes_detalle['descripcion'].value_counts()
            if not tipo_counts.empty:
                st.bar_chart(tipo_counts)
            else:
                st.info("No hay datos suficientes para mostrar el gráfico.")
        
        with col2:
            st.subheader("Solicitudes por Estado")
            estado_counts = mis_solicitudes_detalle['estado'].value_counts()
            if not estado_counts.empty:
                st.bar_chart(estado_counts)
        
        # Actividad reciente
        st.markdown("---")
        st.subheader("Actividad Reciente (Últimos 30 días)")
        
        fecha_limite = datetime.now() - timedelta(days=30)
        solicitudes_recientes = mis_solicitudes_detalle[
            mis_solicitudes_detalle['fecha_solicitud'] >= fecha_limite
        ]
        
        if not solicitudes_recientes.empty:
            st.info(f"Has realizado {len(solicitudes_recientes)} solicitudes en los últimos 30 días.")
            
            # Timeline de solicitudes recientes
            for _, solicitud in solicitudes_recientes.head(10).iterrows():
                días_transcurridos = (datetime.now().date() - solicitud['fecha_solicitud'].date()).days
                estado_emoji = {
                    'pendiente': '🟡',
                    'aprobada': '🟢',
                    'rechazada': '🔴',
                    'enviada': '📦'
                }.get(solicitud['estado'], '⚪')
                
                st.markdown(f"""
                <div class="feature-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{solicitud['descripcion'] or solicitud['tipo']}</strong><br>
                            <small>Hace {días_transcurridos} días - {solicitud['ubicacion']}</small>
                        </div>
                        <div style="text-align: right;">
                            {estado_emoji} {solicitud['estado'].title()}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No has realizado solicitudes en los últimos 30 días.")
    else:
        st.info("Aún no tienes actividad registrada en el sistema.")
        st.markdown("💡 **Sugerencia:** Comienza explorando los tejidos disponibles y realizando tu primera solicitud.")

# --------------------------------------------
# 🔬 SECCIÓN: SEGUIMIENTO DE CASOS
# --------------------------------------------
elif opcion == "🔬 Seguimiento de Casos":
    st.title("🔬 Seguimiento de Casos Clínicos")
    st.markdown("Registra y da seguimiento a tus casos que requieren tejidos específicos.")
    
    # Formulario para registrar nuevo caso
    with st.expander("➕ Registrar Nuevo Caso Clínico", expanded=False):
        with st.form("form_nuevo_caso"):
            col1, col2 = st.columns(2)
            
            with col1:
                paciente_id = st.text_input("ID del Paciente (opcional)", placeholder="P001234")
                edad_paciente = st.number_input("Edad del Paciente", min_value=0, max_value=120, value=30)
                sexo_paciente = st.selectbox("Sexo", ["Masculino", "Femenino", "Otro"])
            
            with col2:
                diagnostico = st.text_input("Diagnóstico Principal", placeholder="Ej: Quemadura de segundo grado")
                urgencia = st.selectbox("Nivel de Urgencia", ["Baja", "Media", "Alta", "Crítica"])
                fecha_cirugia = st.date_input("Fecha Estimada de Cirugía", value=datetime.now().date() + timedelta(days=7))
            
            # Obtener tipos de tejido para el caso
            tipos_tejido_df = execute_query("SELECT tipo, descripcion FROM detalles_tejido ORDER BY descripcion", conn=conn, is_select=True)
            if not tipos_tejido_df.empty:
                opciones_tejido = [f"{row['descripcion']} ({row['tipo']})" for _, row in tipos_tejido_df.iterrows()]
                tejido_requerido = st.selectbox("Tipo de Tejido Requerido", opciones_tejido)
            
            notas_adicionales = st.text_area("Notas Adicionales del Caso", height=100)
            
            submitted_caso = st.form_submit_button("📝 Registrar Caso", use_container_width=True)
            
            if submitted_caso:
                # En una implementación real, aquí guardarías el caso en una tabla de casos clínicos
                # Por ahora, simulamos el guardado
                st.success("✅ Caso clínico registrado exitosamente!")
                st.info("💡 Tip: Puedes ahora solicitar el tejido requerido desde la sección 'Ver Tejidos'")
    
    # Mostrar casos registrados (simulado)
    st.markdown("---")
    st.subheader("📋 Mis Casos Activos")
    
    # Datos simulados de casos (en una implementación real vendrían de la BD)
    casos_ejemplo = [
        {
            "id_caso": "CASO001",
            "paciente": "P123456",
            "diagnostico": "Quemadura de segundo grado",
            "tejido_requerido": "Piel",
            "urgencia": "Alta",
            "fecha_cirugia": "2025-06-15",
            "estado": "Tejido Solicitado"
        },
        {
            "id_caso": "CASO002", 
            "paciente": "P789012",
            "diagnostico": "Reconstrucción corneal",
            "tejido_requerido": "Córnea",
            "urgencia": "Crítica",
            "fecha_cirugia": "2025-06-12",
            "estado": "Pendiente de Tejido"
        }
    ]
    
    for caso in casos_ejemplo:
        urgencia_color = {
            "Baja": "🟢",
            "Media": "🟡", 
            "Alta": "🟠",
            "Crítica": "🔴"
        }.get(caso['urgencia'], "⚪")
        
        st.markdown(f"""
        <div class="feature-card">
            <div style="display: flex; justify-content: between; align-items: flex-start;">
                <div style="flex-grow: 1;">
                    <h4>{caso['id_caso']} - {caso['diagnostico']}</h4>
                    <p><strong>Paciente:</strong> {caso['paciente']}</p>
                    <p><strong>Tejido Requerido:</strong> {caso['tejido_requerido']}</p>
                    <p><strong>Cirugía Programada:</strong> {caso['fecha_cirugia']}</p>
                </div>
                <div style="text-align: right;">
                    <div>{urgencia_color} {caso['urgencia']}</div>
                    <div style="margin-top: 0.5rem;">
                        <span class="status-badge status-pendiente">{caso['estado']}</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.info("📝 **Nota:** Esta es una funcionalidad de demostración. En una implementación completa, los casos se almacenarían en la base de datos y se integrarían con el sistema de solicitudes.")

# Cerrar conexión al final
if conn:
    conn.close()