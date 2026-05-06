
import streamlit as st
import json
from pathlib import Path

DB = Path("database.json")

ADMIN_USER = "admin"
ADMIN_PASSWORD = "Regina2026"

SECCIONES = {
    "ARG":"🇦🇷 Argentina","BRA":"🇧🇷 Brasil","ESP":"🇪🇸 España","FRA":"🇫🇷 Francia",
    "GER":"🇩🇪 Alemania","ITA":"🇮🇹 Italia","POR":"🇵🇹 Portugal","ENG":"🏴 England",
    "CRO":"🇭🇷 Croatia","URU":"🇺🇾 Uruguay","COL":"🇨🇴 Colombia","MEX":"🇲🇽 México",
    "USA":"🇺🇸 USA","CAN":"🇨🇦 Canadá","MAR":"🇲🇦 Marruecos","JPN":"🇯🇵 Japón",
    "FWC":"🏆 FIFA World Cup History","CC":"🥤 Coca-Cola"
}

CANTIDADES = {
    "FWC":19,
    "CC":14
}

for k in list(SECCIONES.keys()):
    if k not in CANTIDADES:
        CANTIDADES[k] = 20

def todas():
    salida=[]
    for cod,cant in CANTIDADES.items():
        for n in range(1,cant+1):
            salida.append(f"{cod}{n}")
    return salida

def load_db():
    if DB.exists():
        return json.loads(DB.read_text(encoding="utf-8"))
    return {"users":{}, "messages":[]}

def save_db(db):
    DB.write_text(json.dumps(db,indent=2,ensure_ascii=False),encoding="utf-8")

st.set_page_config(page_title="Match Figus", page_icon="⚽", layout="wide")

st.title("⚽ Match Figus Mundial 2026")

db = load_db()

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:

    modo = st.radio("Ingreso",["Login","Crear usuario","Admin"])

    if modo == "Admin":
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")

        if st.button("Entrar admin"):
            if u == ADMIN_USER and p == ADMIN_PASSWORD:
                st.session_state.user = "__admin__"
                st.rerun()
            else:
                st.error("Datos incorrectos")

    elif modo == "Crear usuario":
        nuevo = st.text_input("Nombre usuario")
        if st.button("Crear"):
            key = nuevo.lower().strip()

            if key in db["users"]:
                st.error("Ese usuario ya existe")
            elif key:
                db["users"][key] = {
                    "display": nuevo,
                    "album": [],
                    "repetidas": []
                }
                save_db(db)
                st.session_state.user = key
                st.rerun()

    else:
        user = st.text_input("Usuario")

        if st.button("Entrar"):
            key = user.lower().strip()

            if key in db["users"]:
                st.session_state.user = key
                st.rerun()
            else:
                st.error("Usuario inexistente")

    st.stop()

if st.session_state.user == "__admin__":

    st.header("📊 Panel Admin")

    st.metric("Usuarios", len(db["users"]))
    st.metric("Mensajes", len(db["messages"]))

    total_album = sum(len(u.get("album",[])) for u in db["users"].values())
    total_rep = sum(len(u.get("repetidas",[])) for u in db["users"].values())

    st.metric("Figuritas cargadas", total_album)
    st.metric("Repetidas", total_rep)

    st.subheader("Usuarios")

    for k,v in db["users"].items():
        with st.container(border=True):
            st.write(v.get("display",k))
            st.write("Álbum:", len(v.get("album",[])))
            st.write("Repetidas:", len(v.get("repetidas",[])))

    if st.button("Cerrar admin"):
        st.session_state.user = None
        st.rerun()

    st.stop()

user = st.session_state.user
usuario = db["users"][user]

tab1,tab2,tab3 = st.tabs(["📒 Álbum","🤝 Matches","📩 Mensajes"])

with tab1:

    st.subheader("Mi álbum")

    album = set(usuario.get("album",[]))
    reps = set(usuario.get("repetidas",[]))

    nuevo_album = set(album)
    nuevas_rep = set(reps)

    for cod,nombre in SECCIONES.items():

        with st.expander(f"{nombre} — {cod}"):

            col1,col2 = st.columns(2)

            with col1:
                st.markdown("### Tengo")
                cols = st.columns(4)

                for i in range(1,CANTIDADES[cod]+1):
                    figu = f"{cod}{i}"
                    with cols[(i-1)%4]:
                        if st.checkbox(figu, value=figu in album, key=f"a_{figu}"):
                            nuevo_album.add(figu)
                        else:
                            nuevo_album.discard(figu)

            with col2:
                st.markdown("### Repetidas")
                cols = st.columns(4)

                for i in range(1,CANTIDADES[cod]+1):
                    figu = f"{cod}{i}"
                    with cols[(i-1)%4]:
                        if st.checkbox(figu, value=figu in reps, key=f"r_{figu}"):
                            nuevas_rep.add(figu)
                        else:
                            nuevas_rep.discard(figu)

    if st.button("Guardar álbum"):
        db["users"][user]["album"] = sorted(list(nuevo_album))
        db["users"][user]["repetidas"] = sorted(list(nuevas_rep))
        save_db(db)
        st.success("Guardado")

with tab2:

    st.subheader("Matches")

    mis_faltantes = set(todas()) - set(usuario.get("album",[]))
    mis_rep = set(usuario.get("repetidas",[]))

    encontrado = False

    for other,data in db["users"].items():

        if other == user:
            continue

        otro_faltantes = set(todas()) - set(data.get("album",[]))
        otro_rep = set(data.get("repetidas",[]))

        me_da = mis_faltantes.intersection(otro_rep)
        yo_doy = mis_rep.intersection(otro_faltantes)

        if me_da and yo_doy:

            encontrado = True

            with st.container(border=True):

                st.subheader(f"✅ {data.get('display',other)}")

                st.write("Te puede dar:")
                st.success(", ".join(sorted(me_da)))

                st.write("Vos le podés dar:")
                st.info(", ".join(sorted(yo_doy)))

                msg = st.text_input(
                    f"Mensaje para {other}",
                    value="Hola! hacemos intercambio?",
                    key=f"m_{other}"
                )

                if st.button(f"Enviar a {other}"):

                    db["messages"].append({
                        "from": user,
                        "to": other,
                        "msg": msg
                    })

                    save_db(db)
                    st.success("Mensaje enviado")

    if not encontrado:
        st.warning("Todavía no hay matches")

with tab3:

    st.subheader("Mensajes")

    mensajes = [m for m in db["messages"] if m["to"] == user]

    if not mensajes:
        st.info("No tenés mensajes")

    for m in mensajes:

        remitente = db["users"].get(m["from"],{}).get("display",m["from"])

        with st.container(border=True):
            st.write(f"📨 De: {remitente}")
            st.write(m["msg"])

if st.button("Cerrar sesión"):
    st.session_state.user = None
    st.rerun()
