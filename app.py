import streamlit as st
import pandas as pd
import random
from datetime import datetime
import os

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Baby Shower 🎀",
    page_icon="👶",
    layout="wide",             # 1) layout ancho para mejor responsividad
)

# --- ESTILOS CSS PARA MÓVIL ---
st.markdown(
    """
    <style>
      /* Centrar el contenido y limitar ancho máximo */
      .main .block-container {
        max-width: 600px;
        padding-left: 1rem;
        padding-right: 1rem;
      }
      /* Inputs y botones un poco más grandes para tocar con el dedo */
      input, textarea, .stTextInput>div>div>input {
        font-size: 1.1rem;
        padding: 0.5rem;
      }
      .stButton>button {
        font-size: 1.1rem;
        padding: 0.6rem 1.2rem;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# --- ENCABEZADO ---
st.image("assets/banner.png", use_container_width=True)
st.title("🎁 Registro y asignación de Categoría")

# --- CATEGORÍAS CON CUPO ---
categorias = {
    "Vestimenta": 5,
    "Higiene y Baño": 5,
    "Alimentación": 5,
    "Juguetes y Estimulación": 5,
    "Cambio de Pañal": 5,
    "Hora de Dormir": 5
}

# --- CARGAR O CREAR CSV ---
csv_file = "inscritos.csv"
if os.path.exists(csv_file):
    inscritos = pd.read_csv(csv_file)
else:
    inscritos = pd.DataFrame(columns=["Nombre", "Celular", "Categoría", "Fecha"])

# --- FORMULARIO ---
with st.form("registro_form"):
    nombre = st.text_input("Nombre completo")
    celular = st.text_input("Número de celular (sin espacios ni +57)", max_chars=10)
    enviado = st.form_submit_button("Registrarme")

if enviado:
    if not nombre or not celular:
        st.warning("Por favor completa todos los campos.")
        st.stop()
    if not celular.isdigit() or len(celular) != 10:
        st.warning("Ingresa un número válido de 10 dígitos (sin +57 ni espacios).")
        st.stop()

    # Duplicado
    if celular in inscritos["Celular"].astype(str).values:
        st.error("Este número ya ha sido registrado.")
        st.stop()

    # Asignación
    conteo = inscritos["Categoría"].value_counts().to_dict()
    disponibles = [
        cat for cat, cupo in categorias.items()
        if conteo.get(cat, 0) < cupo
    ]
    if not disponibles:
        st.error("Ya se asignaron todas las categorías disponibles.")
        st.stop()

    asignada = random.choice(disponibles)
    nueva = {
        "Nombre": nombre,
        "Celular": celular,
        "Categoría": asignada,
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    inscritos = pd.concat([inscritos, pd.DataFrame([nueva])], ignore_index=True)
    inscritos.to_csv(csv_file, index=False)

    st.success(f"Gracias por registrarte, **{nombre}** 🎉")
    st.markdown(f"🧸 Tu categoría asignada es: **{asignada}**")
    st.image("assets/baby_icon.png", width=120)

    mensaje = f"Hola {nombre}, tu categoría asignada para el baby shower es: {asignada} 🎁"
    enc = mensaje.replace(" ", "%20").replace(":", "%3A").replace("\n", "%0A")
    link = f"https://wa.me/57{celular}?text={enc}"
    st.markdown(f"📲 [Enviar por WhatsApp]({link})", unsafe_allow_html=True)

# --- PANEL ADMINISTRADOR ---
with st.expander("🔒 Ver inscritos (solo admin)"):
    admin_code = st.text_input("Código de acceso", type="password")
    if admin_code == "admin123":
        st.subheader("🧾 Lista de invitados registrados")
        st.dataframe(inscritos)

        # Tabla de estado de categorías
        counts = inscritos["Categoría"].value_counts().to_dict()
        data_cats = [
            {"Categoría": cat, "Cupo total": cupo, "Asignadas": counts.get(cat, 0)}
            for cat, cupo in categorias.items()
        ]
        df_cats = pd.DataFrame(data_cats)
        st.subheader("📊 Estado de categorías")
        st.table(df_cats)