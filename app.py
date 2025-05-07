import streamlit as st
import pandas as pd
import random
from datetime import datetime
import os
import io
from PIL import Image
import matplotlib.pyplot as plt
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import json
from streamlit.components.v1 import html as st_html
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Baby Shower 🎀",
    page_icon="👶",
    layout="wide",
)

# --- ESTILOS CSS PARA MÓVIL ---
st.markdown(
    """
    <style>
      .main .block-container {
        max-width: 600px;
        padding-left: 1rem;
        padding-right: 1rem;
      }
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

# Ruta para persistir los cupos
cat_file = "categorias.csv"

# CARGAR O CREAR CATEGORÍAS CON CUPO
if os.path.exists(cat_file):
    df_cat = pd.read_csv(cat_file)
    categorias = dict(zip(df_cat["Categoría"], df_cat["Cupo total"]))
else:
    categorias = {
        "Vestimenta": 5,
        "Higiene y Baño": 5,
        "Alimentación": 5,
        "Juguetes y Estimulación": 5,
        "Cambio de Pañal": 5,
        "Hora de Dormir": 5
    }
    # guardar inicial
    pd.DataFrame([
        {"Categoría": c, "Cupo total": categorias[c]}
        for c in categorias
    ]).to_csv(cat_file, index=False)

# Diccionario de imágenes por categoría
img_map = {
    "Vestimenta": "assets/vestimenta.png",
    "Higiene y Baño": "assets/higieneyba.png",
    "Alimentación": "assets/alimentacion.png",
    "Juguetes y Estimulación": "assets/juguetes.png",
    "Cambio de Pañal": "assets/cambiopa.png",
    "Hora de Dormir": "assets/dormir.png"
}

# --- CARGAR O CREAR CSV ---
csv_file = "inscritos.csv"
if os.path.exists(csv_file):
    inscritos = pd.read_csv(csv_file)
else:
    inscritos = pd.DataFrame(columns=["Nombre", "Celular", "Categoría", "Fecha", "Acompañantes"])

st.image("assets/banner.png", use_container_width=True)

# --- BARRA DE NAVEGACIÓN EN PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["📝 Registro", "🔍 Consultar", "⚙️ Configuración"])

# --- CONSTANTES DE ANIMACIÓN ---
ANIMATION_DURATION_MS = 6000
ANIMATION_DURATION_S  = ANIMATION_DURATION_MS / 1000 + 0.1  # segundos + buffer

# --- Función para generar el anillo 3D horizontal con duración parametrizada ---
def build_wheel_3d_horizontal(cats, elegido, dur=6000):
    n = len(cats)
    step = 360 / n
    idx = cats.index(elegido)
    base = -idx * step
    colors = ["#FFB6C1", "#FFDAB9", "#E6E6FA", "#FFFACD", "#C1FFC1", "#B0E0E6"]
    
    panels_html = ""
    for i, cat in enumerate(cats):
        panels_html += f'''
      <div class="panel" data-idx="{i}"
           style="
             position:absolute;
             top:50%; left:50%;
             width:160px; height:60px;
             margin:-30px 0 0 -80px;
             line-height:60px;
             text-align:center;
             font-size:1rem;
             color:#333;
             background:{colors[i % len(colors)]};
             transform: rotateY({i * step}deg) translateZ(150px);
             opacity:0.1;
             transition: opacity 0.5s;
           ">
        {cat}
      </div>'''

    return f'''
<div id="scene" style="perspective: 800px; width:320px; height:240px; margin:auto; overflow:visible;">
  <div id="cylinder" style="width:100%; height:100%; position:relative; transform-style: preserve-3d; transform: rotateY({base}deg);">
    {panels_html}
  </div>
</div>

<script>
  const cyl    = document.getElementById('cylinder');
  const panels = cyl.querySelectorAll('.panel');
  const spins  = 3;
  const dur    = {dur};
  const base   = {base};

  // 1) Iniciar la animación sumando las vueltas completas
  setTimeout(() => {{
    cyl.style.transition = `transform ${{dur}}ms ease-out`;
    cyl.style.transform  = `rotateY(${{base - spins * 360}}deg)`;
  }}, 100);

  // 2) Al terminar la transición, destacar solo el ganador
  cyl.addEventListener('transitionend', () => {{
    panels.forEach(p => {{
      p.style.opacity = (+p.dataset.idx === {idx}) ? '1' : '0.1';
    }});
  }});
</script>

<style>
  .panel {{
    transform-origin: center center -150px;
    backface-visibility: hidden;
  }}
</style>
'''

# --- PESTAÑA 1: REGISTRO ---
with tab1:
    st.subheader("🎁 Registro y asignación de Categoría")

    # ---------- FORMULARIO ----------
    with st.form("registro_form"):
        nombre = st.text_input("Nombre completo")
        acompañantes = st.text_input("Número de acompañantes (opcional)", max_chars=6, value="0")
        celular = st.text_input("Número de celular (sin espacios ni +57)", max_chars=10)
        enviado = st.form_submit_button("Registrarme")

    # ---------- PROCESAMIENTO ----------
    if enviado:
        # 1) Validaciones básicas
        if not nombre or not celular:
            st.warning("Por favor completa todos los campos.")
            st.stop()
        if not celular.isdigit() or len(celular) != 10:
            st.warning("Ingresa un número válido de 10 dígitos (sin +57 ni espacios).")
            st.stop()
        if celular in inscritos["Celular"].astype(str).values:
            st.error("Este número ya ha sido registrado.")
            st.stop()

        # 2) Verificar categorías con cupo disponible
        conteo = inscritos["Categoría"].value_counts().to_dict()
        disponibles = [cat for cat, cupo in categorias.items() if conteo.get(cat, 0) < cupo]
        if not disponibles:
            st.error("Ya se asignaron todas las categorías disponibles.")
            st.stop()

        # 3) Elegir la categoría definitiva
        asignada = random.choice(disponibles)

        # 1) Mostrar anillo 3D con duración parametrizada
        st_html(
            build_wheel_3d_horizontal(disponibles, asignada, dur=ANIMATION_DURATION_MS),
            height=250
        )

        # 2) Esperar a que termine la animación
        time.sleep(ANIMATION_DURATION_S)
        

        # 4) Guardar registro
        nueva = {
            "Nombre": nombre,
            "Celular": celular,
            "Categoría": asignada,
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Acompañantes": acompañantes
        }
        inscritos = pd.concat([inscritos, pd.DataFrame([nueva])], ignore_index=True)
        inscritos.to_csv(csv_file, index=False)

        st.success(f"Gracias por registrarte, **{nombre}** 🎉")
        st.markdown(f"🧸 Tu categoría asignada es: **{asignada}**")
        img_path = img_map.get(asignada, "assets/baby_icon.png")
        st.image(img_path, width=400)

        mensaje = f"Hola {nombre}, tu categoría asignada para el baby shower es: {asignada} 🎁"
        enc = mensaje.replace(" ", "%20").replace(":", "%3A").replace("\n", "%0A")
        link = f"https://wa.me/57{celular}?text={enc}"
        st.markdown(f"📲 [Enviar por WhatsApp]({link})", unsafe_allow_html=True)

# --- PESTAÑA 2: CONSULTA DE CATEGORÍA ---
with tab2:
    st.subheader("🔍 Consulta tu categoría asignada")
    celular_consulta = st.text_input("Ingresa tu número de celular (10 dígitos)", key="consulta")
    if st.button("Consultar", key="btn_consulta"):
        if not celular_consulta.isdigit() or len(celular_consulta) != 10:
            st.warning("Ingresa un número válido de 10 dígitos.")
        else:
            df_filtrado = inscritos[inscritos["Celular"].astype(str) == celular_consulta]
            if not df_filtrado.empty:
                registro = df_filtrado.iloc[-1]
                st.write(f"**Nombre:** {registro['Nombre']}")
                st.write(f"**Categoría:** {registro['Categoría']}")
                st.write(f"**Fecha:** {registro['Fecha']}")
                st.write(f"**Acompañantes:** {registro['Acompañantes']}")
            else:
                st.error("No se encontró ningún registro con ese número.")

# --- PESTAÑA CONFIGURACIÓN ---
with tab3:
    st.subheader("⚙️ Configuración (Admin)")
    pwd = st.text_input("Clave", type="password")
    if pwd == "7560":
        st.success("Acceso concedido")

        # 1) Mostrar invitados
        st.subheader("🧾 Lista de invitados registrados")
        st.dataframe(inscritos)

        # 2) Mostrar estado actual de categorías
        counts = inscritos["Categoría"].value_counts().to_dict()
        data_cats = [
            {
                "Categoría": cat,
                "Cupo total": categorias[cat],
                "Asignadas": counts.get(cat, 0)
            }
            for cat in categorias
        ]
        df_cats = pd.DataFrame(data_cats)
        st.subheader("📊 Estado de categorías")
        st.table(df_cats)

        # 3) Ajustar cupo de una categoría específica (al final)
        st.subheader("✏️ Ajustar cupo por categoría")
        cat_sel = st.selectbox(
            "Selecciona la categoría a editar",
            options=list(categorias.keys()),
            key="sel_categoria"
        )
        nuevo_cupo = st.number_input(
            label=f"Cupo total para «{cat_sel}»",
            min_value=0,
            value=categorias[cat_sel],
            step=1,
            key=f"cupo_{cat_sel}"
        )
        if st.button("Actualizar cupo", key="btn_actualizar_cupo"):
            categorias[cat_sel] = nuevo_cupo

            # Guardar en CSV para persistencia
            pd.DataFrame([
                {"Categoría": c, "Cupo total": categorias[c]}
                for c in categorias
            ]).to_csv(cat_file, index=False)

            st.success(f"Cupo de «{cat_sel}» actualizado a {nuevo_cupo}")


       # 4) 👤 Gestionar invitado: buscar, mostrar y permitir editar o eliminar
        st.subheader("👤 Gestionar Invitado")
        if not inscritos.empty:
            sel = st.selectbox("Selecciona el número de celular:", inscritos['Celular'], key="admin_sel")
            rec = inscritos[inscritos['Celular'] == sel].iloc[0]
            with st.form("admin_form"):
                nom = st.text_input("Nombre", value=rec['Nombre'])
                cel_new = st.text_input("Celular", value=rec['Celular'])
                cat = st.text_input("Categoría", value=rec['Categoría'])
                fecha = st.text_input("Fecha", value=rec['Fecha'])
                acomp = st.number_input("Acompañantes", min_value=0, value=int(rec['Acompañantes']), step=1)
                btn_save = st.form_submit_button("Guardar Cambios")
                btn_del = st.form_submit_button("Eliminar Invitado")

            if btn_save:
                # Validar unicidad contra otros registros
                otros = inscritos[inscritos['Celular'] != sel]['Celular'].astype(str).tolist()
                if cel_new in otros:
                    st.error("El número de celular ya existe en otro registro.")
                else:
                    inscritos.loc[inscritos['Celular'] == sel, ['Nombre','Celular','Categoría','Fecha','Acompañantes']] = [
                        nom, cel_new, cat, fecha, acomp
                    ]
                    inscritos.to_csv(csv_file, index=False)
                    st.success("Invitado actualizado correctamente.")
                    try:
                        st.experimental_rerun()
                    except AttributeError:
                        pass

            if btn_del:
                inscritos = inscritos[inscritos['Celular'] != sel]
                inscritos.to_csv(csv_file, index=False)
                st.success("Invitado eliminado correctamente.")
                try:
                    st.experimental_rerun()
                except AttributeError:
                    pass
        else:
            st.info("No hay invitados registrados.")
