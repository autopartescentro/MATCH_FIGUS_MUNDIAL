
import streamlit as st
import json
from pathlib import Path
import re
from math import radians, sin, cos, sqrt, atan2
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from streamlit_js_eval import get_geolocation

DB = Path("database.json")

PAISES = {
    "MEX": "🇲🇽 México",
    "RSA": "🇿🇦 Sudáfrica",
    "COR": "🇰🇷 Corea",
    "CZE": "🇨🇿 República Checa",
    "POR": "🇵🇹 Portugal",
    "FRA": "🇫🇷 Francia",
    "ARG": "🇦🇷 Argentina",
    "BRA": "🇧🇷 Brasil",
    "ESP": "🇪🇸 España",
    "GER": "🇩🇪 Alemania",
    "ITA": "🇮🇹 Italia",
    "URU": "🇺🇾 Uruguay",
    "CHI": "🇨🇱 Chile",
    "COL": "🇨🇴 Colombia",
    "USA": "🇺🇸 Estados Unidos",
    "CAN": "🇨🇦 Canadá",
    "JPN": "🇯🇵 Japón",
    "KOR": "🇰🇷 Corea del Sur",
    "AUS": "🇦🇺 Australia",
    "MAR": "🇲🇦 Marruecos"
}

NUMEROS = list(range(1, 21))

def todas_las_figus():
    return [f"{codigo}{num}" for codigo in PAISES.keys() for num in NUMEROS]

def calcular_faltantes(album):
    return sorted(set(todas_las_figus()) - set(album))

def distancia_km(lat1, lon1, lat2, lon2):
    try:
        R = 6371
        dlat = radians(float(lat2) - float(lat1))
        dlon = radians(float(lon2) - float(lon1))
        a = sin(dlat / 2) ** 2 + cos(radians(float(lat1))) * cos(radians(float(lat2))) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return round(R * c, 1)
    except Exception:
        return None

def load_db():
    if DB.exists():
        db = json.loads(DB.read_text(encoding="utf-8"))
    else:
        db = {"users": {}, "messages": [], "notifications": []}

    if "messages" not in db:
        db["messages"] = []
    if "notifications" not in db:
        db["notifications"] = []

    for usuario, data in db.get("users", {}).items():
        if "album" not in data:
            antiguas_faltantes = set(data.get("faltantes", []))
            data["album"] = sorted(set(todas_las_figus()) - antiguas_faltantes)
        if "repetidas" not in data:
            data["repetidas"] = []
        if "city" not in data:
            data["city"] = ""
        if "lat" not in data:
            data["lat"] = None
        if "lon" not in data:
            data["lon"] = None
        if "seen_matches" not in data:
            data["seen_matches"] = []
        data["faltantes"] = calcular_faltantes(data.get("album", []))

    return db

def save_db(db):
    for usuario, data in db.get("users", {}).items():
        data["album"] = sorted(set(data.get("album", [])))
        data["repetidas"] = sorted(set(data.get("repetidas", [])))
        data["faltantes"] = calcular_faltantes(data.get("album", []))
    DB.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")

def normalizar_texto(texto):
    texto = texto.upper()
    for x in [" ", "-", "_", ".", ":", "|", "\n", "\t"]:
        texto = texto.replace(x, "")
    texto = texto.replace("O", "0") if re.search(r"\d", texto) else texto
    return texto

def detectar_figu(texto):
    limpio = normalizar_texto(texto)

    correcciones = {
        "ESPI4": "ESP14", "ESP1A": "ESP14", "ESP14": "ESP14",
        "ARGI": "ARG1", "BRAI": "BRA1", "MEXI": "MEX1"
    }
    for mal, bien in correcciones.items():
        if mal in limpio:
            return bien

    for codigo in PAISES.keys():
        match = re.search(rf"{codigo}([0-9]{{1,2}})", limpio)
        if match:
            numero = int(match.group(1))
            if 1 <= numero <= 20:
                return f"{codigo}{numero}"

    for codigo in PAISES.keys():
        if codigo in limpio:
            numeros = re.findall(r"\d{1,2}", limpio)
            for n in numeros:
                numero = int(n)
                if 1 <= numero <= 20:
                    return f"{codigo}{numero}"
    return None

def preparar_zona_codigo(img):
    ancho, alto = img.size
    izquierda = int(ancho * 0.50)
    arriba = int(alto * 0.00)
    derecha = int(ancho * 1.00)
    abajo = int(alto * 0.28)
    zona = img.crop((izquierda, arriba, derecha, abajo))
    zona = zona.resize((zona.width * 5, zona.height * 5))
    zona = zona.convert("L")
    zona = ImageEnhance.Contrast(zona).enhance(4)
    zona = zona.filter(ImageFilter.SHARPEN)
    zona = zona.filter(ImageFilter.SHARPEN)
    return zona

def ocr_imagen(img):
    try:
        zona = preparar_zona_codigo(img)
        textos = []
        for config in ["--psm 7", "--psm 8", "--psm 6"]:
            textos.append(pytesseract.image_to_string(zona, config=config))
        return "\n".join(textos), zona
    except Exception:
        return "", None

def calcular_matches(db, user):
    current = db["users"][user]
    salida = []
    for other, data in db["users"].items():
        if other == user:
            continue

        yo_necesito = set(current.get("faltantes", calcular_faltantes(current.get("album", []))))
        yo_tengo = set(current.get("repetidas", []))
        el_necesita = set(data.get("faltantes", calcular_faltantes(data.get("album", []))))
        el_tiene = set(data.get("repetidas", []))

        me_puede_dar = sorted(yo_necesito.intersection(el_tiene))
        yo_puedo_dar = sorted(yo_tengo.intersection(el_necesita))

        if me_puede_dar and yo_puedo_dar:
            dist = None
            if current.get("lat") and current.get("lon") and data.get("lat") and data.get("lon"):
                dist = distancia_km(current["lat"], current["lon"], data["lat"], data["lon"])
            salida.append({
                "usuario": other,
                "zona": data.get("city", "Sin cargar"),
                "distancia": dist,
                "me_puede_dar": me_puede_dar,
                "yo_puedo_dar": yo_puedo_dar
            })

    salida.sort(key=lambda x: x["distancia"] if x["distancia"] is not None else 999999)
    return salida

def mobile_css():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #f6f7fb 0%, #ffffff 100%);
    }
    section[data-testid="stSidebar"] {
        display: none;
    }
    .block-container {
        max-width: 520px;
        padding-top: 1rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }
    div[data-testid="stVerticalBlock"] div[style*="flex-direction: column"] {
        gap: 0.4rem;
    }
    .app-card {
        background: white;
        border-radius: 22px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,0,0,0.04);
    }
    .hero {
        background: linear-gradient(135deg, #1d5cff, #00b894);
        color: white;
        border-radius: 26px;
        padding: 22px;
        margin-bottom: 16px;
        box-shadow: 0 12px 30px rgba(29,92,255,0.25);
    }
    .hero h1 {
        color: white;
        font-size: 30px;
        margin-bottom: 4px;
    }
    .badge {
        display: inline-block;
        background: #eef3ff;
        color: #1d5cff;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 700;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .match-card {
        background: white;
        border-radius: 20px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 6px solid #00b894;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    }
    .stButton>button {
        border-radius: 999px;
        min-height: 42px;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

mobile_css()

db = load_db()

st.markdown("""
<div class="hero">
<h1>⚽ Match Figus</h1>
<div>Intercambiá figuritas cerca tuyo</div>
</div>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.subheader("Ingresar")
    username = st.text_input("Nombre de usuario")
    ciudad = st.text_input("Ciudad / barrio")

    if st.button("Entrar"):
        username = username.strip()
        if username:
            if username not in db["users"]:
                db["users"][username] = {
                    "city": ciudad.strip(),
                    "album": [],
                    "repetidas": [],
                    "faltantes": todas_las_figus(),
                    "lat": None,
                    "lon": None,
                    "seen_matches": []
                }
                save_db(db)
            st.session_state.user = username
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

user = st.session_state.user
db = load_db()

if user not in db["users"]:
    db["users"][user] = {
        "city": "",
        "album": [],
        "repetidas": [],
        "faltantes": todas_las_figus(),
        "lat": None,
        "lon": None,
        "seen_matches": []
    }
    save_db(db)

usuario = db["users"][user]
matches_actuales = calcular_matches(db, user)
match_ids_actuales = [m["usuario"] + "|" + ",".join(m["me_puede_dar"]) + "|" + ",".join(m["yo_puedo_dar"]) for m in matches_actuales]
nuevos_matches = [m for m, mid in zip(matches_actuales, match_ids_actuales) if mid not in usuario.get("seen_matches", [])]

if nuevos_matches:
    st.toast(f"🎉 Tenés {len(nuevos_matches)} match nuevo/s", icon="🎉")
    st.success(f"🎉 Tenés {len(nuevos_matches)} match nuevo/s. Entrá a Matches para verlos.")

st.caption(f"Conectado como: {user}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Inicio", "Álbum", "Escanear", "Matches", "Mensajes"])

with tab1:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.subheader("📍 Ubicación")
    st.write("Activá la ubicación para ordenar los matches por cercanía.")

    geo = get_geolocation()
    if geo and "coords" in geo:
        lat = geo["coords"]["latitude"]
        lon = geo["coords"]["longitude"]
        db["users"][user]["lat"] = lat
        db["users"][user]["lon"] = lon
        save_db(db)
        st.success("Ubicación guardada correctamente.")
    else:
        st.info("Cuando el navegador pregunte, tocá Permitir ubicación.")

    ciudad_actual = usuario.get("city", "")
    nueva_ciudad = st.text_input("Ciudad / barrio", value=ciudad_actual)
    if st.button("Guardar zona"):
        db["users"][user]["city"] = nueva_ciudad.strip()
        save_db(db)
        st.success("Zona guardada.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.subheader("Resumen")
    album = usuario.get("album", [])
    repetidas = usuario.get("repetidas", [])
    faltantes = calcular_faltantes(album)
    st.markdown(f'<span class="badge">📒 {len(album)} en álbum</span><span class="badge">❌ {len(faltantes)} faltantes</span><span class="badge">✅ {len(repetidas)} repetidas</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Cerrar sesión"):
        st.session_state.user = None
        st.rerun()

with tab2:
    st.subheader("📒 Mi álbum")
    st.info("Marcá las que ya tenés y las repetidas. Las faltantes se calculan solas.")

    album_guardado = set(usuario.get("album", []))
    repetidas_guardadas = set(usuario.get("repetidas", []))
    nuevo_album = set()
    nuevas_repetidas = set()

    for codigo, nombre_pais in PAISES.items():
        with st.expander(f"{nombre_pais} — {codigo}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📌 Ya la tengo**")
                cols_album = st.columns(4)
                for i, num in enumerate(NUMEROS):
                    figu = f"{codigo}{num}"
                    with cols_album[i % 4]:
                        if st.checkbox(figu, value=figu in album_guardado, key=f"album_{figu}"):
                            nuevo_album.add(figu)
            with col2:
                st.markdown("**✅ Repetida**")
                cols_rep = st.columns(4)
                for i, num in enumerate(NUMEROS):
                    figu = f"{codigo}{num}"
                    with cols_rep[i % 4]:
                        if st.checkbox(figu, value=figu in repetidas_guardadas, key=f"rep_{figu}"):
                            nuevas_repetidas.add(figu)

    album_final = set(nuevo_album).union(nuevas_repetidas)
    faltantes = calcular_faltantes(album_final)

    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.write(f"📒 Tenés: {len(album_final)} de {len(todas_las_figus())}")
    st.write(f"❌ Faltan: {len(faltantes)}")
    st.write(f"✅ Repetidas: {len(nuevas_repetidas)}")
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("Ver faltantes"):
        st.write(", ".join(faltantes) if faltantes else "¡Álbum completo!")

    if st.button("💾 Guardar álbum"):
        db["users"][user]["album"] = sorted(album_final)
        db["users"][user]["repetidas"] = sorted(nuevas_repetidas)
        db["users"][user]["faltantes"] = calcular_faltantes(album_final)
        save_db(db)
        st.success("Guardado correctamente.")

with tab3:
    st.subheader("📷 Escanear figuritas")
    st.info("Podés subir varias fotos juntas. La app busca el código arriba a la derecha del dorso.")

    modo = st.radio("Modo", ["Subir varias fotos", "Usar cámara"])

    imagenes = []

    if modo == "Subir varias fotos":
        archivos = st.file_uploader("Subí fotos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        if archivos:
            for archivo in archivos:
                imagenes.append((archivo.name, Image.open(archivo)))
    else:
        foto = st.camera_input("Sacá foto de una figurita")
        if foto:
            imagenes.append(("foto_camara", Image.open(foto)))

    detectadas = []

    if imagenes and st.button("🔎 Detectar todas"):
        for nombre, img in imagenes:
            texto, zona = ocr_imagen(img)
            figu = detectar_figu(texto)
            st.markdown('<div class="app-card">', unsafe_allow_html=True)
            st.write(f"Imagen: {nombre}")
            st.image(img, width=220)
            if zona:
                st.image(zona, caption="Zona leída", width=220)
            st.code(texto if texto else "No se pudo leer texto")
            if figu:
                st.success(f"Detectada: {figu}")
                detectadas.append(figu)
            else:
                st.warning("No detectada")
            st.markdown('</div>', unsafe_allow_html=True)

        st.session_state.detectadas = sorted(set(detectadas))

    detectadas_guardadas = st.session_state.get("detectadas", [])

    if detectadas_guardadas:
        st.subheader("Guardar detectadas")
        st.write(", ".join(detectadas_guardadas))
        destino = st.radio("Guardar como", ["Ya la tengo en el álbum", "Repetidas para cambiar"])

        if st.button("➕ Agregar detectadas"):
            db = load_db()
            for figu in detectadas_guardadas:
                if figu not in db["users"][user]["album"]:
                    db["users"][user]["album"].append(figu)
                if destino == "Repetidas para cambiar":
                    if figu not in db["users"][user]["repetidas"]:
                        db["users"][user]["repetidas"].append(figu)
            db["users"][user]["album"] = sorted(set(db["users"][user]["album"]))
            db["users"][user]["repetidas"] = sorted(set(db["users"][user]["repetidas"]))
            db["users"][user]["faltantes"] = calcular_faltantes(db["users"][user]["album"])
            save_db(db)
            st.success("Figuritas agregadas.")

    st.subheader("Carga manual rápida")
    col_a, col_b = st.columns(2)
    with col_a:
        pais_manual = st.selectbox("País", list(PAISES.keys()))
    with col_b:
        numero_manual = st.selectbox("Número", NUMEROS)
    destino_manual = st.radio("Guardar manual como", ["Ya la tengo en el álbum", "Repetida para cambiar"], key="destino_manual")
    if st.button("Agregar manual"):
        figu = f"{pais_manual}{numero_manual}"
        db = load_db()
        if figu not in db["users"][user]["album"]:
            db["users"][user]["album"].append(figu)
        if destino_manual == "Repetida para cambiar" and figu not in db["users"][user]["repetidas"]:
            db["users"][user]["repetidas"].append(figu)
        save_db(db)
        st.success(f"{figu} agregada.")

with tab4:
    st.subheader("🤝 Matches")
    db = load_db()
    matches = calcular_matches(db, user)

    if st.button("Marcar matches como vistos"):
        db["users"][user]["seen_matches"] = match_ids_actuales
        save_db(db)
        st.success("Matches marcados como vistos.")

    if not matches:
        st.warning("Todavía no hay matches.")
    else:
        for m in matches:
            dist_txt = f" — a {m['distancia']} km" if m["distancia"] is not None else ""
            st.markdown(f"""
            <div class="match-card">
            <h3>✅ {m['usuario']}</h3>
            <p>📍 {m['zona']}{dist_txt}</p>
            <p><b>Te puede dar:</b> {", ".join(m['me_puede_dar'])}</p>
            <p><b>Vos le podés dar:</b> {", ".join(m['yo_puedo_dar'])}</p>
            </div>
            """, unsafe_allow_html=True)

            mensaje = st.text_input(f"Mensaje para {m['usuario']}", value=f"Hola {m['usuario']}, hacemos intercambio?", key=f"msg_{m['usuario']}")
            if st.button(f"Enviar a {m['usuario']}", key=f"send_{m['usuario']}"):
                db["messages"].append({"from": user, "to": m["usuario"], "msg": mensaje})
                save_db(db)
                st.success("Mensaje enviado.")

with tab5:
    st.subheader("📩 Mensajes")
    db = load_db()
    mensajes = [m for m in db["messages"] if m["to"] == user]

    if not mensajes:
        st.info("Todavía no recibiste mensajes.")

    for m in mensajes:
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.write(f"📨 De: {m['from']}")
        st.write(m["msg"])
        st.markdown('</div>', unsafe_allow_html=True)
