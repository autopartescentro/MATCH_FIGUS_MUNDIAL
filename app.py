
import streamlit as st
import json
from pathlib import Path

DB = Path("database.json")

PAISES = [
    "MEX", "RSA", "COR", "CZE", "POR", "FRA", "ARG", "BRA",
    "ESP", "GER", "ITA", "URU", "CHI", "COL", "USA", "CAN",
    "JPN", "KOR", "AUS", "MAR"
]

NUMEROS = list(range(1, 21))

def load_db():
    if DB.exists():
        return json.loads(DB.read_text(encoding="utf-8"))
    return {"users": {}, "messages": []}

def save_db(db):
    DB.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")

db = load_db()

st.set_page_config(page_title="Cambio de Figuritas", page_icon="⚽", layout="wide")
st.title("⚽ App para cambiar figuritas")

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
                    "faltantes": [],
                    "repetidas": []
                }
                save_db(db)

            st.session_state.user = username
            st.rerun()
    st.stop()

user = st.session_state.user
st.success(f"Conectado como: {user}")

if st.button("Cerrar sesión"):
    st.session_state.user = None
    st.rerun()

db = load_db()

if user not in db["users"]:
    db["users"][user] = {"city": "", "faltantes": [], "repetidas": []}
    save_db(db)

usuario = db["users"][user]

tab1, tab2, tab3 = st.tabs(["📒 Mi álbum", "🤝 Matches", "📩 Mensajes"])

with tab1:
    st.header("Cargar mis figuritas")

    ciudad_actual = usuario.get("city", "")
    nueva_ciudad = st.text_input("Ciudad / barrio", value=ciudad_actual)

    st.info("Marcá con tilde las figuritas que te faltan y las que tenés repetidas.")

    faltantes_seleccionadas = set(usuario.get("faltantes", []))
    repetidas_seleccionadas = set(usuario.get("repetidas", []))

    nuevas_faltantes = set()
    nuevas_repetidas = set()

    for pais in PAISES:
        with st.expander(f"🌎 {pais}", expanded=False):
            st.write(f"Figuritas de {pais}")

            cols = st.columns(4)

            for i, num in enumerate(NUMEROS):
                figu = f"{pais}{num}"
                col = cols[i % 4]

                with col:
                    falta = st.checkbox(
                        f"Me falta {figu}",
                        value=figu in faltantes_seleccionadas,
                        key=f"faltante_{figu}"
                    )

                    repetida = st.checkbox(
                        f"Tengo repetida {figu}",
                        value=figu in repetidas_seleccionadas,
                        key=f"repetida_{figu}"
                    )

                    if falta:
                        nuevas_faltantes.add(figu)

                    if repetida:
                        nuevas_repetidas.add(figu)

    if st.button("💾 Guardar mis figuritas"):
        conflicto = nuevas_faltantes.intersection(nuevas_repetidas)

        if conflicto:
            st.error(
                "Hay figuritas marcadas como faltantes y repetidas al mismo tiempo: "
                + ", ".join(sorted(conflicto))
            )
        else:
            db["users"][user]["city"] = nueva_ciudad.strip()
            db["users"][user]["faltantes"] = sorted(nuevas_faltantes)
            db["users"][user]["repetidas"] = sorted(nuevas_repetidas)
            save_db(db)
            st.success("Tus figuritas quedaron guardadas correctamente.")

    st.subheader("Resumen")
    st.write("Te faltan:", ", ".join(sorted(nuevas_faltantes)) if nuevas_faltantes else "Ninguna cargada")
    st.write("Tenés repetidas:", ", ".join(sorted(nuevas_repetidas)) if nuevas_repetidas else "Ninguna cargada")

with tab2:
    st.header("Matches de intercambio")

    db = load_db()
    current = db["users"][user]

    encontrados = 0

    for other, data in db["users"].items():
        if other == user:
            continue

        yo_necesito = set(current.get("faltantes", []))
        yo_tengo = set(current.get("repetidas", []))

        el_necesita = set(data.get("faltantes", []))
        el_tiene = set(data.get("repetidas", []))

        me_puede_dar = yo_necesito.intersection(el_tiene)
        yo_puedo_dar = yo_tengo.intersection(el_necesita)

        if me_puede_dar and yo_puedo_dar:
            encontrados += 1

            with st.container(border=True):
                st.subheader(f"✅ Match con {other}")
                st.write(f"📍 Cercanía / zona: {data.get('city', 'Sin cargar')}")
                st.write("📥 Te puede dar:", ", ".join(sorted(me_puede_dar)))
                st.write("📤 Vos le podés dar:", ", ".join(sorted(yo_puedo_dar)))

                mensaje = st.text_input(
                    f"Mensaje para {other}",
                    value=f"Hola {other}, hacemos cambio de figuritas?",
                    key=f"msg_{other}"
                )

                if st.button(f"Enviar mensaje a {other}", key=f"send_{other}"):
                    db["messages"].append({
                        "from": user,
                        "to": other,
                        "msg": mensaje
                    })
                    save_db(db)
                    st.success("Mensaje enviado.")

    if encontrados == 0:
        st.warning("Todavía no hay matches. Probá cargar más faltantes y repetidas.")

with tab3:
    st.header("Mensajes recibidos")

    db = load_db()
    mensajes = [m for m in db["messages"] if m["to"] == user]

    if not mensajes:
        st.info("Todavía no recibiste mensajes.")
    else:
        for m in mensajes:
            st.info(f"De {m['from']}: {m['msg']}")
