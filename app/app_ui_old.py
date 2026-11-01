import os
import requests
import pandas as pd
import streamlit as st

# Configuración inicial de la aplicación en Streamlit
st.set_page_config(
    page_title="Analizador Inteligente de Respuestas de Clientes",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dirección del backend de FastAPI
API_URL = os.getenv("API_URL", "http://localhost:8000")

# =========================================
# Funciones Auxiliares de Comunicación HTTP
# =========================================

def obtener_metricas():
    """Consulta las métricas consolidadas calculadas por FastAPI."""
    try:
        respuesta = requests.get(f"{API_URL}/metricas", timeout=5)
        if respuesta.status_code == 200:
            return respuesta.json()
    except Exception:
        return None
    return None

def obtener_resenas(sentimiento=None, estado_gestion=None):
    """Consulta la lista de reseñas con soporte para filtros."""
    try:
        parametros = {}
        if sentimiento and sentimiento != "Todos":
            parametros["sentimiento"] = sentimiento
        if estado_gestion and estado_gestion != "Todos":
            parametros["estado_gestion"] = estado_gestion
        
        respuesta = requests.get(f"{API_URL}/reseñas", params=parametros, timeout=5)
        if respuesta.status_code == 200:
            return respuesta.json()
    except Exception:
        return []
    return []

def actualizar_estado_resena(resena_id, nuevo_estado):
    """Envía una solicitud HTTP PATCH a FastAPI para cambiar el estado de gestión."""
    try:
        respuesta = requests.patch(
            f"{API_URL}/reseñas/{resena_id}",
            json={"estado_gestion": nuevo_estado},
            timeout=5
        )
        return respuesta.status_code == 200
    except Exception:
        return False

def enviar_resena(cliente, correo, puntuacion, comentario, categoria):
    """Registra una nueva reseña en el sistema mediante HTTP POST."""
    try:
        payload = {
            "cliente": cliente,
            "correo": correo,
            "puntuacion": int(puntuacion),
            "comentario": comentario,
            "categoria": categoria
        }
        respuesta = requests.post(f"{API_URL}/analizar-reseña", json=payload, timeout=5)
        return respuesta.status_code, respuesta.json()
    except Exception as e:
        return 500, {"detail": str(e)}

# =========================================
# Menú de Navegación Lateral
# =========================================

st.sidebar.title("🎯 Menú de Navegación")
opcion_menu = st.sidebar.radio(
    "Selecciona una vista:",
    ["📊 Dashboard de Resultados", "📝 Registrar Nueva Reseña", "🛠️ Gestión de Soporte"]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**TP2 - Programación con IA y Low-Code**\n\n"
    "**Ecosistema:**\n"
    "- Streamlit (Frontend)\n"
    "- FastAPI + Pydantic (Backend)\n"
    "- n8n (Orquestador)\n"
    "- Gemini AI (Agente LLM)\n"
    "- MySQL / SQLite (Persistencia)"
)

# =========================================
# VISTA 1: DASHBOARD DE RESULTADOS (Punto 8)
# =========================================

if opcion_menu == "📊 Dashboard de Resultados":
    st.title("📊 Dashboard de Satisfacción de Clientes")
    st.caption("Visualización de métricas deterministas (Python) e inteligencia cualitativa (Gemini AI)")

    metricas = obtener_metricas()

    if metricas is None:
        st.error(f"⚠️ No se pudo establecer conexión con el backend de FastAPI en `{API_URL}`.")
        st.warning("Asegúrate de que el contenedor de FastAPI esté activo (`docker compose up -d`).")
    else:
        # Tarjetas Métricas (st.metric)
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric(
            label="Promedio de Satisfacción",
            value=f"{metricas['promedio_satisfaccion']} / 5.0",
            delta="Objetivo ≥ 4.0" if metricas['promedio_satisfaccion'] >= 4 else "Por debajo del objetivo",
            delta_color="normal" if metricas['promedio_satisfaccion'] >= 4 else "inverse"
        )
        col2.metric(
            label="Total de Opiniones",
            value=metricas['total_resenas']
        )
        col3.metric(
            label="% Clientes Insatisfechos",
            value=f"{metricas['porcentaje_insatisfechos']}%",
            delta="Puntuación ≤ 2★",
            delta_color="inverse"
        )
        col4.metric(
            label="Alertas Críticas Activas",
            value=metricas['alertas_criticas_activas'],
            delta="Atención requerida" if metricas['alertas_criticas_activas'] > 0 else "Sin pendientes",
            delta_color="inverse"
        )

        st.markdown("---")

        # Gráfico de Distribución de Puntuaciones (1 a 5 estrellas)
        col_graf, col_info = st.columns([3, 2])

        with col_graf:
            st.subheader("📈 Distribución de Calificaciones (1 a 5 Estrellas)")
            dist_data = metricas.get("distribucion_puntuaciones", {})
            df_dist = pd.DataFrame({
                "Calificación": [f"{k} ⭐" for k in dist_data.keys()],
                "Cantidad": list(dist_data.values())
            })
            st.bar_chart(df_dist.set_index("Calificación"))

        with col_info:
            st.subheader("🤖 Diagnóstico del Sistema")
            if metricas['total_resenas'] > 0:
                st.success("✅ **Procesamiento de Métricas Operativo**")
                st.write(
                    f"- **Pendientes de Atención:** {metricas['resenas_pendientes_atencion']} caso(s)\n"
                    f"- **Regla Determinista en Python:** Las opiniones con \\(\\le 2\\) estrellas activan automáticamente `alerta_critica = True` notificando a soporte vía n8n.\n"
                    f"- **Análisis Semántico:** Gemini AI asigna las etiquetas de Sentimiento y Categoría."
                )
            else:
                st.info("Aún no hay reseñas registradas para generar indicadores.")

        st.markdown("---")
        
        # Últimas Reseñas con Clasificación de IA
        st.subheader("📋 Reseñas Recientes e Infección Cualitativa")
        resenas = obtener_resenas()
        
        if resenas:
            for r in resenas[:5]:  # Muestra las 5 reseñas más recientes
                with st.container():
                    col_det, col_tag = st.columns([4, 1])
                    with col_det:
                        st.markdown(f"**{r['cliente']}** (`{r['correo']}`) — Categoría: *{r['categoria']}*")
                        st.markdown(f"**Puntuación:** {'⭐' * r['puntuacion']} ({r['puntuacion']}/5)")
                        st.write(f"\"{r['comentario']}\"")
                        if r.get('resumen_ia'):
                            st.caption(f"🤖 **Resumen IA:** {r['resumen_ia']}")
                    with col_tag:
                        sent = r.get('sentimiento', 'Pendiente')
                        if sent == "Positivo":
                            st.success("🟢 Positivo")
                        elif sent == "Negativo":
                            st.error("🔴 Negativo")
                        elif sent == "Neutro":
                            st.warning("🟡 Neutro")
                        else:
                            st.info("⚪ Pendiente")
                            
                        if r.get('alerta_critica'):
                            st.error("⚠️ Alerta Crítica")
                    st.divider()
        else:
            st.info("Sin registros en la base de datos.")

# =========================================
# VISTA 2: REGISTRAR NUEVA RESEÑA (Punto 1)
# =========================================

elif opcion_menu == "📝 Registrar Nueva Reseña":
    st.title("📝 Formulario de Recepción de Opiniones")
    st.caption("Ingreso de datos para procesamiento inmediato y validación con Pydantic")

    with st.form("form_resena", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            cliente = st.text_input("Nombre del Cliente *", placeholder="Ej. Laura Gómez")
            correo = st.text_input("Correo Electrónico *", placeholder="Ej. laura@example.com")
        with col_b:
            puntuacion = st.select_slider(
                "Calificación de Satisfacción *",
                options=[1, 2, 3, 4, 5],
                value=5,
                format_func=lambda x: f"{x} ⭐"
            )
            categoria = st.selectbox(
                "Categoría del Producto / Servicio",
                ["General", "Atención al Cliente", "Calidad de Producto", "Envío / Logística", "Precio / Facturación"]
            )
        
        comentario = st.text_area("Comentario u Opinión *", placeholder="Escribe los detalles de tu experiencia...")
        
        submitted = st.form_submit_button("🚀 Enviar Opinión", use_container_width=True)

        if submitted:
            if not cliente or not correo or not comentario:
                st.error("⚠️ Por favor completa todos los campos obligatorios (*).")
            else:
                codigo_http, respuesta = enviar_resena(cliente, correo, puntuacion, comentario, categoria)
                
                if codigo_http in (200, 201):
                    st.success(f"✅ ¡Opinión registrada con éxito! (ID de Registro: #{respuesta.get('id')})")
                    if respuesta.get("alerta_critica"):
                        st.warning("⚠️ Su puntuación ha activado un protocolo de atención prioritaria por baja calificación.")
                    st.json(respuesta)
                elif codigo_http == 422:
                    st.error("❌ Error de validación en los datos ingresados (Pydantic HTTP 422). Verifique el correo electrónico.")
                    st.json(respuesta)
                else:
                    st.error(f"❌ Error al procesar la solicitud (Código HTTP {codigo_http}).")
                    st.write(respuesta)

# =========================================
# VISTA 3: GESTIÓN DE SOPORTE (Puntos 7 y 9)
# =========================================

elif opcion_menu == "🛠️ Gestión de Soporte":
    st.title("🛠️ Módulo de Administración y Gestión de Soporte")
    st.caption("Consulta, filtrado y actualización del estado de atención de opiniones mediante HTTP PATCH")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_sentimiento = st.selectbox("Filtrar por Sentimiento IA:", ["Todos", "Positivo", "Neutro", "Negativo", "Pendiente"])
    with col_f2:
        filtro_estado = st.selectbox("Filtrar por Estado de Gestión:", ["Todos", "Pendiente", "Atendido"])

    resenas = obtener_resenas(sentimiento=filtro_sentimiento, estado_gestion=filtro_estado)

    st.markdown(f"**Total de registros encontrados:** `{len(resenas)}`")
    st.markdown("---")

    if not resenas:
        st.info("No se encontraron opiniones que coincidan con los filtros seleccionados.")
    else:
        for r in resenas:
            with st.expander(f"Reseña #{r['id']} — {r['cliente']} | {r['puntuacion']} ⭐ | Estado: {r['estado_gestion']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Correo:** {r['correo']}")
                    st.write(f"**Categoría Inicial:** {r['categoria']}")
                    st.write(f"**Comentario:** {r['comentario']}")
                    st.write(f"**Sentimiento IA:** `{r.get('sentimiento', 'N/A')}`")
                    st.write(f"**Categoría IA:** `{r.get('categoria_ia', 'N/A')}`")
                    st.write(f"**Resumen IA:** {r.get('resumen_ia', 'Pendiente de clasificación')}")
                    st.write(f"**Fecha de Creación:** {r['fecha_creacion']}")
                
                with col2:
                    if r['alerta_critica']:
                        st.error("⚠️ Alerta Crítica")
                    
                    st.markdown("**Gestión de Estado:**")
                    estado_actual = r['estado_gestion']
                    nuevo_estado = "Atendido" if estado_actual == "Pendiente" else "Pendiente"
                    
                    if st.button(f"Marcar como {nuevo_estado}", key=f"btn_{r['id']}"):
                        if actualizar_estado_resena(r['id'], nuevo_estado):
                            st.success(f"Reseña #{r['id']} actualizada a '{nuevo_estado}'.")
                            st.rerun()
                        else:
                            st.error("No se pudo actualizar el estado de la reseña.")
