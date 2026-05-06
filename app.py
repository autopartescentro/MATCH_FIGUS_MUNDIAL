
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
                    "city": ciudad,
                    "faltantes": [],
                    "repetidas": []
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
usuario = db["users"][user]

tab1, tab2, tab3 = st.tabs(["📒 Mi Álbum", "🤝 Matches", "📩 Mensajes"])

with tab1:

    st.header("Mis figuritas")

    faltantes_guardadas = set(usuario.get("faltantes", []))
    repetidas_guardadas = set(usuario.get("repetidas", []))

    nuevas_faltantes = set()
    nuevas_repetidas = set()

    for pais in PAISES:

        st.markdown(f"## 🌎 {pais}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ✅ Tengo repetidas")

            cols_rep = st.columns(5)

            for i, num in enumerate(NUMEROS):
                figu = f"{pais}{num}"

                with cols_rep[i % 5]:
                    rep = st.checkbox(
                        figu,
                        value=figu in repetidas_guardadas,
                        key=f"rep_{figu}"
                    )

                    if rep:
                        nuevas_repetidas.add(figu)

        with col2:
            st.markdown("### ❌ Me faltan")

            cols_fal = st.columns(5)

            for i, num in enumerate(NUMEROS):
                figu = f"{pais}{num}"

                with cols_fal[i % 5]:
                    fal = st.checkbox(
                        figu,
                        value=figu in faltantes_guardadas,
                        key=f"fal_{figu}"
                    )

                    if fal:
                        nuevas_faltantes.add(figu)

        st.divider()

    if st.button("💾 Guardar álbum"):

        conflicto = nuevas_faltantes.intersection(nuevas_repetidas)

        if conflicto:
            st.error(
                "Estas figuritas están marcadas como repetidas y faltantes al mismo tiempo: "
                + ", ".join(sorted(conflicto))
            )
        else:
            db["users"][user]["faltantes"] = sorted(nuevas_faltantes)
            db["users"][user]["repetidas"] = sorted(nuevas_repetidas)

            save_db(db)

            st.success("Álbum guardado correctamente")

with tab2:

    st.header("🤝 Matches")

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

with tab3:

    st.header("📩 Mensajes")

    mensajes = [m for m in db["messages"] if m["to"] == user]

    if not mensajes:
        st.info("Todavía no recibiste mensajes")

    for m in mensajes:

        with st.container(border=True):
            st.write(f"📨 De: {m['from']}")
            st.write(m['msg'])
