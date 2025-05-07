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
from github import Github
import altair as alt

import smtplib
from email.message import EmailMessage

# --- CONFIGURACIÓN DE GITHUB ---
def push_inscritos_to_github(csv_file, repo_name="Gabri3l756/BabyShower", path="inscritos.csv"):
    # lee token
    token = st.secrets["general"]["GITHUB_TOKEN"]
    gh    = Github(token)
    repo  = gh.get_repo(repo_name)
    # lee contenido
    with open(csv_file, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        contents = repo.get_contents(path, ref="main")
        repo.update_file(
            path=path,
            message="🤖 Actualizar lista de invitados (admin)",
            content=content,
            sha=contents.sha,
            branch="main"
        )
    except Exception:
        repo.create_file(
            path=path,
            message="🤖 Crear lista de invitados (admin)",
            content=content,
            branch="main"
        )

def notify_hosts(nueva_registro: dict):
    """
    Envía un correo a los anfitriones con los datos de la nueva inscripción.
    nueva_registro debe tener llaves: Nombre, Celular, Categoría, Fecha, Acompañantes
    """
    secrets = st.secrets["email"]
    smtp_server = secrets["SMTP_SERVER"]
    smtp_port   = secrets["SMTP_PORT"]
    user        = secrets["USER"]
    password    = secrets["PASSWORD"]
    hosts       = secrets["HOSTS"]

    # Construir el mensaje
    msg = EmailMessage()
    msg["Subject"] = f"Nuevo registro: {nueva_registro['Nombre']}"
    msg["From"]    = user
    msg["To"]      = ", ".join(hosts)
    body = f"""
    ¡Hola!

    Se ha registrado un nuevo invitado:

      • Nombre      : {nueva_registro['Nombre']}
      • Celular     : {nueva_registro['Celular']}
      • Categoría   : {nueva_registro['Categoría']}
      • Acompañantes: {nueva_registro['Acompañantes']}
      • Fecha       : {nueva_registro['Fecha']}

    ¡Saludos!
    """
    msg.set_content(body)

    # Enviar
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)
    except Exception as e:
        st.error(f"No se pudo notificar a los anfitriones: {e}")


# Mapeo de meses a español
MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

# clave admin
ADMIN_PWD = "7560"

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
tab1, tab2, tab3, tab4 = st.tabs(["📝 Registro", "🔍 Consultar", "📊 Análisis", "⚙️ Configuración"])

# --- CONSTANTES DE ANIMACIÓN ---
ANIMATION_DURATION_MS = 6000
ANIMATION_DURATION_S  = ANIMATION_DURATION_MS / 1000 + 0.1  # segundos + buffer

# --- Función para generar el anillo 3D horizontal con duración parametrizada ---
def build_wheel_3d_vertical(cats, elegido, dur=6000):
    n = len(cats)
    step = 360 / n
    idx = cats.index(elegido)
    spins = 3

    # Parte inicial está en -90 para que panel en X=0 quede de frente
    base_angle = -90
    final_angle = -idx * step + base_angle
    total_rotation = final_angle - spins * 360

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
             transform: rotateX({i * step}deg) translateZ(150px);
             opacity:0.1;
             transition: opacity 0.5s;
           ">
        {cat}
      </div>'''

    return f'''
<div id="scene" style="perspective: 800px; width:320px; height:240px; margin:auto; overflow:visible;">
  <div id="cylinder" style="width:100%; height:100%; position:relative; transform-style: preserve-3d; transform: rotateX({base_angle}deg);">
    {panels_html}
  </div>
</div>

<script>
  const cyl    = document.getElementById('cylinder');
  const panels = cyl.querySelectorAll('.panel');
  const dur    = {dur};
  const final  = {total_rotation};
  const idx    = {idx};

  setTimeout(() => {{
    cyl.style.transition = `transform ${{dur}}ms ease-out`;
    cyl.style.transform  = `rotateX(${{final}}deg)`;
  }}, 100);

  cyl.addEventListener('transitionend', () => {{
    panels.forEach(p => {{
      p.style.opacity = (+p.dataset.idx === idx) ? '1' : '0.1';
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

        # mapping de nombre->ruta de imagen si quieres mostrar íconos
        img_map = {
            "Vestimenta": "assets/vestimenta.png",
            "Higiene y Baño": "assets/higieneyba.png",
            "Alimentación": "assets/alimentacion.png",
            "Juguetes y Estimulación": "assets/juguetes.png",
            "Cambio de Pañal": "assets/cambiopa.png",
            "Hora de Dormir": "assets/dormir.png"
        }

        # placeholder para la animación
        ph = st.empty()

        # número de ciclos (vueltas completas sobre la lista)
        vueltas = 5
        # velocidad de “scroll” en segundos
        delay = 0.1

        # animación: desliza cada nombre verticalmente
        for _ in range(vueltas):
            for cat in disponibles:
                ph.markdown(f"""
        <div style="
        height:150px;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:2rem;
        color:#555;
        border:2px solid #eee;
        border-radius:8px;
        background:#fafafa;
        ">
        {cat}
        </div>
        """, unsafe_allow_html=True)
                time.sleep(delay)

        # un “paso” final para aterrizar sobre la categoría asignada
        # calculamos cuántos elementos saltamos hasta llegar a `asignada`
        start_idx = 0  # asumimos que empieza en disponibles[0] al iniciar
        offset = disponibles.index(asignada)
        for i in range(offset+1):
            cat = disponibles[i]
            ph.markdown(f"""
        <div style="
        height:150px;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:2rem;
        font-weight:bold;
        color:#222;
        border:3px solid #8bc34a;
        border-radius:8px;
        background:#e8f5e9;
        ">
        {cat}
        </div>
        """, unsafe_allow_html=True)
            time.sleep(delay)
        

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
        push_inscritos_to_github(csv_file)

        # 5) Notificar por email
        nueva = {
            "Nombre": nombre,
            "Celular": celular,
            "Categoría": asignada,
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Acompañantes": acompañantes
        }
        notify_hosts(nueva)


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
                cat = registro["Categoría"]
                st.write(f"**Nombre:** {registro['Nombre']}")
                st.write(f"**Categoría:** {cat}")

                # --- formateamos la fecha ---
                raw = registro["Fecha"]                         # e.g. "2025-05-07 14:05"
                dt  = datetime.strptime(raw, "%Y-%m-%d %H:%M")
                fecha_bonita = (
                    f"{dt.day} de {MESES[dt.month]} de {dt.year}, "
                    f"{dt.hour:02d}:{dt.minute:02d}"
                )
                # Markdown con estilo
                st.markdown(
                    f"""
                    <p style="font-size:16px; color:#555;">
                    📅 <strong style="color:#333;">Fecha:</strong> {fecha_bonita}
                    </p>
                    """,
                    unsafe_allow_html=True
                )

                st.write(f"**Acompañantes:** {registro['Acompañantes']}")

                img_path = img_map.get(cat, "assets/baby_icon.png")
                st.image(img_path, width=400)
            else:
                st.error("No se encontró ningún registro con ese número.")

# --- PESTAÑA: ANÁLISIS / DASHBOARD ---
with tab3:
    st.subheader("📊 Dashboard de Registro")
    pwd2 = st.text_input("🔒 Clave", type="password", key="dash_pwd")
    if pwd2 != ADMIN_PWD:
        st.warning("🔐 Ingresa la contraseña para acceder a Configuración")
    else:             
        # --- Métricas resumen ---
        total_invitados = inscritos.shape[0] # total de filas en el DataFrame
        total_acomp      = inscritos["Acompañantes"].astype(int).sum()
        total_asistentes   = total_invitados + total_acomp
        avg_acomp        = (total_acomp / total_invitados) if total_invitados else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("👥 Invitados", total_invitados)
        c2.metric("🤝 Acompañantes", total_acomp)
        c3.metric("🎉 Total Asistentes",       total_asistentes)
        c4.metric("📈 Acompañantes / Invitado", f"{avg_acomp:.2f}")

        st.markdown("---")

        # --- Datos por categoría ---
        counts = inscritos["Categoría"].value_counts().to_dict()
        df_stats = pd.DataFrame([
            {
                "Categoría": cat,
                "Asignadas": counts.get(cat, 0),
                "Disponibles": max(0, categorias[cat] - counts.get(cat, 0))
            }
            for cat in categorias
        ])

        # --- 1) Gráfico de barras con Altair y tooltip ---
        st.subheader("🎯 Cupos por Categoría")
        df_bars = df_stats.melt(
            id_vars="Categoría", 
            value_vars=["Asignadas", "Disponibles"], 
            var_name="Tipo", value_name="Cantidad"
        )
        bars = (
            alt.Chart(df_bars)
            .mark_bar(cornerRadiusEnd=4)
            .encode(
                x=alt.X("Categoría:N", sort=list(categorias.keys()), axis=alt.Axis(title=None)),
                y=alt.Y("Cantidad:Q", axis=alt.Axis(title="Invitados")),
                color=alt.Color("Tipo:N", scale=alt.Scale(domain=["Asignadas","Disponibles"],
                                                        range=["#636EFA","#EF553B"])),
                tooltip=["Categoría","Tipo","Cantidad"]
            )
            .properties(height=300, width="container")
        )
        st.altair_chart(bars, use_container_width=True)

        st.markdown("---")

        # --- 2) Gráfico circular (donut) con Altair ---
        st.subheader("📊 Distribución de Asignaciones")
        pie = (
            alt.Chart(df_stats)
            .mark_arc(innerRadius=50, cornerRadius=3)
            .encode(
                theta=alt.Theta("Asignadas:Q", stack=True),
                color=alt.Color("Categoría:N", legend=alt.Legend(title="Categoría")),
                tooltip=["Categoría","Asignadas"]
            )
            .properties(width=250, height=250)
        )
        st.altair_chart(pie)

        st.markdown("---")

        # --- 3) Tabla completa de invitados ---
        st.subheader("📋 Lista de Invitados")
        st.dataframe(inscritos, use_container_width=True)

        # Mostrar estado actual de categorías
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

# --- PESTAÑA CONFIGURACIÓN ---
with tab4:
    st.subheader("⚙️ Configuración (Admin)")
    pwd = st.text_input("🔒 Clave", type="password", key="config_pwd")
    if pwd != ADMIN_PWD:
        st.warning("🔐 Ingresa la contraseña para acceder a Configuración")
    else:
    # st.subheader("⚙️ Configuración (Admin)")
    # pwd = st.text_input("Clave", type="password")
    # if pwd == "7560":
    #     st.success("Acceso concedido")

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
                    push_inscritos_to_github(csv_file)
                    try:
                        st.experimental_rerun()
                    except AttributeError:
                        pass

            if btn_del:
                inscritos = inscritos[inscritos['Celular'] != sel]
                inscritos.to_csv(csv_file, index=False)
                st.success("Invitado eliminado correctamente.")
                push_inscritos_to_github(csv_file)
                try:
                    st.experimental_rerun()
                except AttributeError:
                    pass
        else:
            st.info("No hay invitados registrados.")
