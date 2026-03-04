import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
from datetime import datetime

# --- 1. CONFIGURATION & BASE DE DONNÉES ---
st.set_page_config(page_title="Bioumina AppStock", page_icon="📡", layout="wide")

def connecter_db():
    return sqlite3.connect('bioumina.db', check_same_thread=False)

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
        c.execute("INSERT INTO users VALUES (?, ?, ?)", ("admin", hashed, "admin"))
    conn.commit()
    conn.close()

# --- 2. LOGIQUE DE SÉCURITÉ ---
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
        if res and bcrypt.checkpw(p.encode('utf-8'), res[0]):
            st.session_state.connecte = True
            st.session_state.user = u
            st.session_state.role = res[1]
            st.rerun()
        else:
            st.error("Identifiants incorrects")
else:
    # --- 3. MENU PRINCIPAL ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("🚪 Déconnexion"):
        st.session_state.connecte = False
        st.rerun()

    menu = ["⚡️ Vente", "📦 Stock (Admin)"] if st.session_state.role == "admin" else ["⚡️ Vente"]
    choix = st.sidebar.radio("Navigation", menu)

    if choix == "⚡️ Vente":
        st.subheader("Faire une Vente")
        # Ici ton code de vente (terminal_vente)
        st.info("Sélectionnez un décodeur et remplissez les infos client.")
        
    elif choix == "📦 Stock (Admin)":
        st.subheader("Gestion du Stock")
        vendeur = st.text_input("Nom du Vendeur")
        liste = st.text_area("Numéros (séparés par virgule)")
        if st.button("🚀 Affecter"):
            st.success("Stock mis à jour !")