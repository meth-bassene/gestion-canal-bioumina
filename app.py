import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
from datetime import datetime
import os

st.set_page_config(page_title="Bioumina AppStock", page_icon="📡", layout="wide")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bioumina.db')

def connecter_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def initialiser_bdd():
    conn = connecter_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS decodeurs 
                 (numero TEXT PRIMARY KEY, partenaire TEXT, statut TEXT, 
                  affecte_a TEXT, client_nom TEXT, client_tel TEXT, 
                  formule TEXT, prix_total REAL, date_ajout TEXT, 
                  date_activation TEXT, export_reabo INTEGER DEFAULT 0)''')
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        hashed = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
        c.execute("INSERT INTO users VALUES (?, ?, ?)", ("admin", hashed.decode('utf-8'), "admin"))
    conn.commit()
    conn.close()

initialiser_bdd()
if 'connecte' not in st.session_state:
    st.session_state.connecte = False

if not st.session_state.connecte:
    st.title("📡 Connexion Bioumina")
    u = st.text_input("Identifiant")
    p = st.text_input("Mot de passe", type="password")
    if st.button("🚀 Se connecter"):
        conn = connecter_db()
        c = conn.cursor()
        c.execute("SELECT password, role FROM users WHERE username = ?", (u,))
        res = c.fetchone()
        conn.close()
        if res:
            pwd = res[0]
            if isinstance(pwd, str):
                pwd = pwd.encode('utf-8')
            if bcrypt.checkpw(p.encode('utf-8'), pwd):
                st.session_state.connecte = True
                st.session_state.user = u
                st.session_state.role = res[1]
                st.rerun()
            else:
                st.error("Identifiants incorrects")
        else:
            st.error("Identifiants incorrects")
else:
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("🚪 Déconnexion"):
        st.session_state.connecte = False
        st.rerun()

    menu = ["⚡️ Vente", "📦 Stock (Admin)"] if st.session_state.role == "admin" else ["⚡️ Vente"]
    choix = st.sidebar.radio("Navigation", menu)

    if choix == "⚡️ Vente":
        st.subheader("Faire une Vente")
        st.info("Sélectionnez un décodeur et remplissez les infos client.")
        conn = connecter_db()
        df = pd.read_sql_query("SELECT numero, partenaire, formule FROM decodeurs WHERE statut='disponible'", conn)
        conn.close()
        if df.empty:
            st.warning("Aucun décodeur disponible en stock.")
        else:
            numero_choisi = st.selectbox("Choisir un décodeur", df['numero'].tolist())
            client_nom = st.text_input("Nom du client")
            client_tel = st.text_input("Téléphone client")
            prix = st.number_input("Prix total (FCFA)", min_value=0)
            if st.button("✅ Confirmer la vente"):
                if client_nom and client_tel:
                    conn = connecter_db()
                    c = conn.cursor()
                    c.execute("""UPDATE decodeurs SET statut='vendu', client_nom=?, client_tel=?, 
                                 prix_total=?, date_activation=? WHERE numero=?""",
                              (client_nom, client_tel, prix, datetime.now().strftime("%Y-%m-%d %H:%M"), numero_choisi))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Vente enregistrée pour {client_nom} — Décodeur {numero_choisi}")
                else:
                    st.error("Veuillez remplir le nom et le téléphone du client.")

    elif choix == "📦 Stock (Admin)":
        st.subheader("Gestion du Stock")
        conn = connecter_db()
        df_stock = pd.read_sql_query("SELECT * FROM decodeurs", conn)
        conn.close()
        if not df_stock.empty:
            st.dataframe(df_stock, use_container_width=True)
        else:
            st.info("Stock vide pour l'instant.")
        st.divider()
        st.subheader("Affecter des décodeurs")
        vendeur = st.text_input("Nom du Vendeur")
        partenaire = st.text_input("Partenaire (ex: Canal+)")
        liste = st.text_area("Numéros de décodeurs (séparés par virgule)")
        if st.button("🚀 Affecter"):
            if vendeur and liste:
                numeros = [n.strip() for n in liste.split(',') if n.strip()]
                conn = connecter_db()
                c = conn.cursor()
                for num in numeros:
                    try:
                        c.execute("""INSERT OR IGNORE INTO decodeurs 
                                     (numero, partenaire, statut, affecte_a, date_ajout) 
                                     VALUES (?, ?, 'disponible', ?, ?)""",
                                  (num, partenaire, vendeur, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    except:
                        pass
                conn.commit()
                conn.close()
                st.success(f"✅ {len(numeros)} décodeur(s) ajouté(s) pour {vendeur}")
            else:
                st.error("Veuillez remplir le vendeur et les numéros.")
