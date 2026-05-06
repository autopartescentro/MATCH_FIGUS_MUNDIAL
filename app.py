
import streamlit as st
import json
from pathlib import Path
from math import radians, sin, cos, sqrt, atan2

DB = Path("database.json")

def load_db():
    if DB.exists():
        return json.loads(DB.read_text(encoding="utf-8"))
    return {"users": {}, "messages": []}

def save_db(db):
    DB.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")

db = load_db()

st.title("⚽ Cambio de Figuritas")

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    user = st.text_input("Nombre de usuario")
    city = st.text_input("Ciudad")
    if st.button("Ingresar"):
        if user:
            if user not in db["users"]:
                db["users"][user] = {
                    "city": city,
                    "faltantes": [],
                    "repetidas": []
                }
                save_db(db)
            st.session_state.user = user
            st.rerun()

user = st.session_state.user

if user:
    st.success(f"Conectado como {user}")

    faltantes = st.text_area(
        "Figuritas faltantes (separadas por coma)",
        ",".join(db["users"][user]["faltantes"])
    )

    repetidas = st.text_area(
        "Figuritas repetidas (separadas por coma)",
        ",".join(db["users"][user]["repetidas"])
    )

    if st.button("Guardar álbum"):
        db["users"][user]["faltantes"] = [
            x.strip().upper() for x in faltantes.split(",") if x.strip()
        ]
        db["users"][user]["repetidas"] = [
            x.strip().upper() for x in repetidas.split(",") if x.strip()
        ]
        save_db(db)
        st.success("Álbum guardado")

    st.header("🤝 Matches")

    current = db["users"][user]

    for other, data in db["users"].items():
        if other == user:
            continue

        yo_necesito = set(current["faltantes"])
        yo_tengo = set(current["repetidas"])

        el_necesita = set(data["faltantes"])
        el_tiene = set(data["repetidas"])

        me_puede_dar = yo_necesito.intersection(el_tiene)
        yo_puedo_dar = yo_tengo.intersection(el_necesita)

        if me_puede_dar and yo_puedo_dar:
            st.subheader(f"✅ Match con {other}")
            st.write(f"📍 Ciudad: {data['city']}")
            st.write("Te puede dar:", ", ".join(sorted(me_puede_dar)))
            st.write("Vos le podés dar:", ", ".join(sorted(yo_puedo_dar)))

            msg = st.text_input(f"Mensaje para {other}", key=other)

            if st.button(f"Enviar a {other}"):
                db["messages"].append({
                    "from": user,
                    "to": other,
                    "msg": msg
                })
                save_db(db)
                st.success("Mensaje enviado")

    st.header("📩 Mensajes")

    for m in db["messages"]:
        if m["to"] == user:
            st.info(f"De {m['from']}: {m['msg']}")
