
import streamlit as st
import json
from pathlib import Path
import re
from PIL import Image
import pytesseract

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

def calcular_faltantes(tengo_album):
    return sorted(set(todas_las_figus()) - set(tengo_album))

def load_db():
    if DB.exists():
        db = json.loads(DB.read_text(encoding="utf-8"))
    else:
        db = {"users": {}, "messages": []}

    # Compatibilidad con versiones anteriores
    for user, data in db.get("users", {}).items():
        if "album" not in data:
            antiguas_faltantes = set(data.get("faltantes", []))
            data["album"] = sorted(set(todas_las_figus()) - antiguas_faltantes)
        if "repetidas" not in data:
            data["repetidas"] = []
        data["faltantes"] = calcular_faltantes(data.get("album", []))

    return db

def save_db(db):
    for user, data in db.get("users", {}).items():
        data["faltantes"] = calcular_faltantes(data.get("album", []))
    DB.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")

def normalizar_texto(texto):
    texto = texto.upper()
    texto = texto.replace(" ", "")
    texto = texto.replace("-", "")
    texto = texto.replace("_", "")
    return texto

def detectar_figu(texto):
    texto = normalizar_texto(texto)

    for codigo in PAISES.keys():
        match = re.search(rf"{codigo}([0-9]{{1,2}})", texto)
        if match:
            numero = int(match.group(1))
            if 1 <= numero <= 20:
                return f"{codigo}{numero}"

    for codigo in PAISES.keys():
        if codigo in texto:
            numeros = re.findall(r"\d{1,2}", texto)
            for n in numeros:
                numero = int(n)
                if 1 <= numero <= 20:
                    return f"{codigo}{numero}"

    return None

def ocr_imagen(img):
    try:
        return pytesseract.image_to_string(img)
    except Exception:
        return ""

db = load_db()

st.set_page_config(page_title="Match Figus Mundial", page_icon="⚽", layout="wide")
st.title("⚽ Match Figus Mundial")

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
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
                    "faltantes": todas_las_figus()
                }
                save_db(db)

            st.session_state.user = username
            st.rerun()

    st.stop()

user = st.session_state.user
st.success(f"Conectado como {user}")

if st.button("Cerrar sesión"):
    st.session_state.user = None
    st.rerun()

db = load_db()

if user not in db["users"]:
    db["users"][user] = {
        "city": "",
        "album": [],
        "repetidas": [],
        "faltantes": todas_las_figus()
    }
    save_db(db)

usuario = db["users"][user]

tab1, tab2, tab3, tab4 = st.tabs(["📒 Mi álbum", "📷 Escanear", "🤝 Matches", "📩 Mensajes"])

with tab1:
    st.header("Mi álbum")

    st.info("Marcá las figuritas que YA TENÉS en tu álbum. Las faltantes se calculan solas por descarte.")

    ciudad_actual = usuario.get("city", "")
    nueva_ciudad = st.text_input("Ciudad / barrio", value=ciudad_actual)

    album_guardado = set(usuario.get("album", []))
    repetidas_guardadas = set(usuario.get("repetidas", []))

    nuevo_album = set()
    nuevas_repetidas = set()

    total_album = len(todas_las_figus())

    for codigo, nombre_pais in PAISES.items():
        st.markdown(f"## {nombre_pais} — {codigo}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📌 Ya la tengo en el álbum")
            cols_album = st.columns(5)

            for i, num in enumerate(NUMEROS):
                figu = f"{codigo}{num}"
                with cols_album[i % 5]:
                    tengo = st.checkbox(
                        figu,
                        value=figu in album_guardado,
                        key=f"album_{figu}"
                    )
                    if tengo:
                        nuevo_album.add(figu)

        with col2:
            st.markdown("### ✅ Tengo repetida para cambiar")
            cols_rep = st.columns(5)

            for i, num in enumerate(NUMEROS):
                figu = f"{codigo}{num}"
                with cols_rep[i % 5]:
                    rep = st.checkbox(
                        figu,
                        value=figu in repetidas_guardadas,
                        key=f"rep_{figu}"
                    )
                    if rep:
                        nuevas_repetidas.add(figu)

        st.divider()

    faltantes_calculadas = calcular_faltantes(nuevo_album)

    st.subheader("Resumen automático")
    st.write(f"📒 Tenés en el álbum: {len(nuevo_album)} de {total_album}")
    st.write(f"❌ Te faltan: {len(faltantes_calculadas)}")
    st.write(f"✅ Repetidas para cambiar: {len(nuevas_repetidas)}")

    with st.expander("Ver figuritas faltantes calculadas"):
        st.write(", ".join(faltantes_calculadas) if faltantes_calculadas else "¡Álbum completo!")

    if st.button("💾 Guardar álbum"):
        # Si una figurita está repetida, también debe estar en el álbum
        album_final = set(nuevo_album).union(nuevas_repetidas)

        db["users"][user]["city"] = nueva_ciudad.strip()
        db["users"][user]["album"] = sorted(album_final)
        db["users"][user]["repetidas"] = sorted(nuevas_repetidas)
        db["users"][user]["faltantes"] = calcular_faltantes(album_final)

        save_db(db)
        st.success("Álbum guardado. Las faltantes se calcularon automáticamente.")

with tab2:
    st.header("📷 Escanear figurita")

    st.info("Escaneá una figurita y guardala como 'ya la tengo en el álbum' o como 'repetida'. Si la guardás como repetida, también se marca automáticamente como que ya la tenés.")

    modo = st.radio("Elegí cómo cargar la imagen", ["Usar cámara", "Subir foto"])

    imagen = None

    if modo == "Usar cámara":
        foto = st.camera_input("Sacá foto de la figurita")
        if foto:
            imagen = Image.open(foto)
    else:
        archivo = st.file_uploader("Subí una imagen", type=["jpg", "jpeg", "png"])
        if archivo:
            imagen = Image.open(archivo)

    if imagen:
        st.image(imagen, caption="Imagen cargada", width=300)

        if st.button("🔎 Detectar figurita"):
            texto = ocr_imagen(imagen)
            figu_detectada = detectar_figu(texto)

            st.write("Texto leído por la app:")
            st.code(texto if texto else "No se pudo leer texto")

            if figu_detectada:
                st.success(f"Figurita detectada: {figu_detectada}")
                st.session_state.figu_detectada = figu_detectada
            else:
                st.warning("No pude detectar la figurita automáticamente. Podés elegirla manualmente abajo.")

    st.subheader("Agregar figurita")

    figu_base = st.session_state.get("figu_detectada", "")

    col_a, col_b = st.columns(2)

    with col_a:
        pais_manual = st.selectbox("País", list(PAISES.keys()))

    with col_b:
        numero_manual = st.selectbox("Número", NUMEROS)

    figu_manual = f"{pais_manual}{numero_manual}"

    opciones = []
    if figu_base:
        opciones.append(figu_base)
    opciones.append(figu_manual)

    figu_final = st.radio("Qué figurita querés guardar", opciones, index=0)

    destino = st.radio("Guardar como", ["Ya la tengo en el álbum", "Repetida para cambiar"])

    if st.button("➕ Agregar"):
        if figu_final:
            db = load_db()

            if figu_final not in db["users"][user]["album"]:
                db["users"][user]["album"].append(figu_final)

            if destino == "Repetida para cambiar":
                if figu_final not in db["users"][user]["repetidas"]:
                    db["users"][user]["repetidas"].append(figu_final)

            db["users"][user]["album"] = sorted(set(db["users"][user]["album"]))
            db["users"][user]["repetidas"] = sorted(set(db["users"][user]["repetidas"]))
            db["users"][user]["faltantes"] = calcular_faltantes(db["users"][user]["album"])

            save_db(db)
            st.success(f"{figu_final} agregada correctamente.")

with tab3:
    st.header("🤝 Matches")

    db = load_db()
    current = db["users"][user]

    encontrados = 0

    for other, data in db["users"].items():
        if other == user:
            continue

        yo_necesito = set(current.get("faltantes", calcular_faltantes(current.get("album", []))))
        yo_tengo_repetida = set(current.get("repetidas", []))

        el_necesita = set(data.get("faltantes", calcular_faltantes(data.get("album", []))))
        el_tiene_repetida = set(data.get("repetidas", []))

        me_puede_dar = yo_necesito.intersection(el_tiene_repetida)
        yo_puedo_dar = yo_tengo_repetida.intersection(el_necesita)

        if me_puede_dar and yo_puedo_dar:
            encontrados += 1

            with st.container(border=True):
                st.subheader(f"✅ Match con {other}")
                st.write(f"📍 Zona: {data.get('city', 'Sin cargar')}")

                st.write("📥 Te puede dar:")
                st.success(", ".join(sorted(me_puede_dar)))

                st.write("📤 Vos le podés dar:")
                st.info(", ".join(sorted(yo_puedo_dar)))

                mensaje = st.text_input(
                    f"Mensaje para {other}",
                    value=f"Hola {other}, hacemos intercambio?",
                    key=f"msg_{other}"
                )

                if st.button(f"Enviar a {other}", key=f"send_{other}"):
                    db["messages"].append({
                        "from": user,
                        "to": other,
                        "msg": mensaje
                    })
                    save_db(db)
                    st.success("Mensaje enviado")

    if encontrados == 0:
        st.warning("Todavía no hay matches")

with tab4:
    st.header("📩 Mensajes")

    db = load_db()
    mensajes = [m for m in db["messages"] if m["to"] == user]

    if not mensajes:
        st.info("Todavía no recibiste mensajes")

    for m in mensajes:
        with st.container(border=True):
            st.write(f"📨 De: {m['from']}")
            st.write(m["msg"])
