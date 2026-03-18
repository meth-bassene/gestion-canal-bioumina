import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
import os
import secrets
import io
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AppStock",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════
# CSS — NOIR & BLANC STYLE CANAL+ MODERNE
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --noir: #0a0a0a;
    --blanc: #ffffff;
    --gris: #f4f4f4;
    --gris2: #e8e8e8;
    --gris3: #999999;
    --accent: #0a0a0a;
    --rouge: #e50000;
    --vert: #00b341;
    --jaune: #f5a623;
}

* { font-family: 'DM Sans', sans-serif; }
h1, h2, h3, .page-title { font-family: 'Syne', sans-serif; }

.stApp { background: var(--gris); }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--noir) !important;
    border-right: 1px solid #222;
}
[data-testid="stSidebar"] * { color: var(--blanc) !important; }
[data-testid="stSidebar"] .stRadio > div { gap: 4px; }
[data-testid="stSidebar"] .stRadio label {
    background: transparent;
    border-radius: 8px;
    padding: 10px 14px;
    cursor: pointer;
    transition: background 0.15s;
    font-size: 0.9rem;
    border: 1px solid transparent;
}
[data-testid="stSidebar"] .stRadio label:hover { background: #1a1a1a; }
[data-testid="stSidebar"] [data-checked="true"] label,
[data-testid="stSidebar"] .stRadio [aria-checked="true"] + label { 
    background: #1a1a1a; 
    border-color: #333;
}

/* ── BOUTONS ── */
.stButton > button {
    background: var(--noir) !important;
    color: var(--blanc) !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 10px 20px !important;
    transition: all 0.15s !important;
    letter-spacing: 0.3px;
}
.stButton > button:hover {
    background: #222 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.2) !important;
}

/* ── CARDS ── */
.card {
    background: var(--blanc);
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    margin-bottom: 16px;
    border: 1px solid var(--gris2);
}

/* ── STAT CARDS ── */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card {
    background: var(--blanc);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid var(--gris2);
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.stat-card .label { font-size: 0.78rem; color: var(--gris3); font-weight: 500; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }
.stat-card .value { font-family: 'Syne', sans-serif; font-size: 1.9rem; font-weight: 800; color: var(--noir); }
.stat-card .sub { font-size: 0.8rem; color: var(--gris3); margin-top: 4px; }
.stat-card.rouge .value { color: var(--rouge); }
.stat-card.vert .value { color: var(--vert); }

/* ── PAGE TITLE ── */
.page-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--noir);
    margin-bottom: 24px;
    padding-bottom: 14px;
    border-bottom: 2px solid var(--noir);
    letter-spacing: -0.5px;
}

/* ── ALERTES ── */
.alerte { border-radius: 8px; padding: 12px 16px; margin: 6px 0; font-size: 0.88rem; }
.alerte.rouge { background: #fff0f0; border-left: 3px solid var(--rouge); }
.alerte.jaune { background: #fffbf0; border-left: 3px solid var(--jaune); }
.alerte.vert  { background: #f0fff5; border-left: 3px solid var(--vert); }

/* ── BADGE ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge.dispo { background: #e8f5e9; color: #2e7d32; }
.badge.vendu { background: #fce4ec; color: #c62828; }
.badge.top   { background: var(--noir); color: var(--blanc); }

/* ── LOGIN ── */
.login-wrap {
    max-width: 380px;
    margin: 60px auto 0;
    background: var(--blanc);
    border-radius: 16px;
    padding: 40px 36px;
    border: 1px solid var(--gris2);
    box-shadow: 0 8px 32px rgba(0,0,0,0.08);
}
.login-logo {
    font-family: 'Syne', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--noir);
    letter-spacing: -1px;
    margin-bottom: 4px;
}
.login-sub { color: var(--gris3); font-size: 0.85rem; margin-bottom: 28px; }

/* ── INPUTS ── */
.stTextInput input, .stSelectbox select, .stNumberInput input {
    border-radius: 8px !important;
    border: 1.5px solid var(--gris2) !important;
    font-family: 'DM Sans', sans-serif !important;
    background: var(--blanc) !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: var(--noir) !important;
    box-shadow: 0 0 0 3px rgba(0,0,0,0.08) !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--blanc);
    border-radius: 10px;
    padding: 4px;
    border: 1px solid var(--gris2);
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.88rem;
    color: var(--gris3) !important;
}
.stTabs [aria-selected="true"] {
    background: var(--noir) !important;
    color: var(--blanc) !important;
}

/* ── SCANNER BOX ── */
.scanner-box {
    background: var(--blanc);
    border: 2px dashed var(--gris2);
    border-radius: 12px;
    padding: 28px;
    text-align: center;
    margin: 12px 0;
    transition: border-color 0.2s;
}
.scanner-box:hover { border-color: var(--noir); }

/* ── WHATSAPP BTN ── */
.wa-btn {
    display: inline-block;
    background: #25D366;
    color: white !important;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 0.82rem;
    font-weight: 600;
    text-decoration: none;
    margin-top: 6px;
}

/* ── TOKEN BOX ── */
.token-box {
    background: var(--noir);
    color: var(--blanc);
    border-radius: 8px;
    padding: 16px 20px;
    font-family: monospace;
    font-size: 1.2rem;
    letter-spacing: 3px;
    text-align: center;
    margin: 12px 0;
}

/* ── RAPPORT PODIUM ── */
.podium-card {
    background: var(--blanc);
    border-radius: 12px;
    padding: 16px;
    border: 1px solid var(--gris2);
    text-align: center;
    margin: 8px 0;
}
.podium-emoji { font-size: 2rem; }
.podium-nom { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1rem; margin: 6px 0 2px; }
.podium-stat { font-size: 0.82rem; color: var(--gris3); }

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid var(--gris2); }

/* ── NOTIFICATION DOT ── */
.notif-dot { display:inline-block; width:8px; height:8px; background:var(--rouge); border-radius:50%; margin-left:6px; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'appstock.db')

def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        telephone TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT "vendeur",
        nom_complet TEXT,
        date_creation TEXT,
        token TEXT,
        token_expiry TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS decodeurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT UNIQUE,
        partenaire TEXT DEFAULT "Canal+",
        statut TEXT DEFAULT "disponible",
        affecte_a TEXT,
        client_nom TEXT,
        client_tel TEXT,
        formule TEXT,
        prix_total REAL,
        date_ajout TEXT,
        date_activation TEXT,
        date_expiration TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS historique_modifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        decodeur_numero TEXT,
        champ_modifie TEXT,
        ancienne_valeur TEXT,
        nouvelle_valeur TEXT,
        modifie_par TEXT,
        date_modification TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT,
        type TEXT,
        destinataire TEXT DEFAULT "tous",
        lu INTEGER DEFAULT 0,
        date_creation TEXT
    )''')

    # Admin par défaut
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        h = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        c.execute("INSERT INTO users (username, telephone, password, role, nom_complet, date_creation) VALUES (?,?,?,?,?,?)",
                  ("admin", "000000000", h.decode(), "admin", "Administrateur", datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

init_db()

# ═══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════
def get_stats():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM decodeurs WHERE statut='disponible'")
    dispo = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM decodeurs WHERE statut='vendu'")
    vendus = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(prix_total),0) FROM decodeurs WHERE statut='vendu'")
    ca = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE role='vendeur'")
    nb_v = c.fetchone()[0]
    conn.close()
    return dispo, vendus, ca, nb_v

def get_alertes():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT numero, client_nom, client_tel, date_expiration, affecte_a FROM decodeurs WHERE statut='vendu' AND date_expiration IS NOT NULL AND date_expiration != ''")
    rows = c.fetchall()
    conn.close()
    today = datetime.now().date()
    alertes = []
    for num, nom, tel, exp, vendeur in rows:
        try:
            date_exp = datetime.strptime(exp, "%Y-%m-%d").date()
            jours = (date_exp - today).days
            if jours < 0:
                alertes.append({"numero": num, "client": nom, "tel": tel, "jours": jours, "statut": "expiré", "vendeur": vendeur})
            elif jours <= 7:
                alertes.append({"numero": num, "client": nom, "tel": tel, "jours": jours, "statut": "urgent", "vendeur": vendeur})
        except:
            pass
    return alertes

def get_decodeurs_dormants():
    conn = db()
    c = conn.cursor()
    limit = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    c.execute("SELECT numero, affecte_a, date_ajout FROM decodeurs WHERE statut='disponible' AND date_ajout <= ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def notif_count(user):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM notifications WHERE lu=0 AND (destinataire=? OR destinataire='tous')", (user,))
    n = c.fetchone()[0]
    conn.close()
    return n

def push_notif(message, type_n, destinataire="tous"):
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO notifications (message, type, destinataire, date_creation) VALUES (?,?,?,?)",
              (message, type_n, destinataire, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def check_and_push_auto_notifs():
    alertes = get_alertes()
    for a in alertes:
        if a['jours'] == 1 or a['jours'] == 0:
            push_notif(f"⏰ Abonnement expire dans 24h — {a['client']} ({a['numero']})", "expiration_24h", a['vendeur'])
        elif a['jours'] <= 7 and a['jours'] > 1:
            push_notif(f"⚠️ Abonnement expire dans {a['jours']}j — {a['client']} ({a['numero']})", "expiration_7j", a['vendeur'])
    dormants = get_decodeurs_dormants()
    for num, vendeur, date_ajout in dormants:
        push_notif(f"📦 Décodeur {num} en stock depuis +1 mois sans vente", "dormant", vendeur or "admin")

def wa_link(tel, nom, jours):
    if jours < 0:
        msg = f"Bonjour {nom}, votre abonnement Canal+ a expiré. Contactez-nous pour le renouveler. — AppStock"
    else:
        msg = f"Bonjour {nom}, votre abonnement Canal+ expire dans {jours} jour(s). Contactez-nous. — AppStock"
    tel_clean = tel.replace(" ", "").replace("+", "")
    if not tel_clean.startswith("221"):
        tel_clean = "221" + tel_clean
    import urllib.parse
    return f"https://wa.me/{tel_clean}?text={urllib.parse.quote(msg)}"

def export_excel(df, nom_feuille="Données"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=nom_feuille)
    return output.getvalue()

def get_vendeurs_list():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT username, nom_complet FROM users")
    rows = c.fetchall()
    conn.close()
    return rows if rows else [("admin", "Administrateur")]

# ═══════════════════════════════════════════════════════════════
# SESSION
# ═══════════════════════════════════════════════════════════════
if 'connecte' not in st.session_state:
    st.session_state.connecte = False
if 'mode_token' not in st.session_state:
    st.session_state.mode_token = False

# ═══════════════════════════════════════════════════════════════
# PAGE LOGIN
# ═══════════════════════════════════════════════════════════════
if not st.session_state.connecte:
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        st.markdown("""
        <div class="login-wrap">
            <div class="login-logo">AppStock</div>
            <div class="login-sub">Gestion de stock professionnelle</div>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.mode_token:
            tel = st.text_input("📞 Numéro de téléphone", placeholder="Ex: 77 123 45 67")
            pwd = st.text_input("🔑 Mot de passe", type="password")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("→ Se connecter", use_container_width=True):
                    conn = db()
                    c = conn.cursor()
                    # Admin peut se connecter par username ou téléphone
                    c.execute("SELECT password, role, nom_complet, username FROM users WHERE telephone=? OR username=?", (tel, tel))
                    res = c.fetchone()
                    conn.close()
                    if res:
                        p = res[0].encode() if isinstance(res[0], str) else res[0]
                        if bcrypt.checkpw(pwd.encode(), p):
                            st.session_state.connecte = True
                            st.session_state.user = res[3]
                            st.session_state.role = res[1]
                            st.session_state.nom = res[2]
                            check_and_push_auto_notifs()
                            st.rerun()
                        else:
                            st.error("❌ Mot de passe incorrect")
                    else:
                        st.error("❌ Compte introuvable")
            with col_b:
                if st.button("Mot de passe oublié ?", use_container_width=True):
                    st.session_state.mode_token = True
                    st.rerun()
        else:
            st.markdown("### 🔑 Récupération par token")
            st.info("Contactez votre admin pour obtenir un token temporaire.")
            token_input = st.text_input("Entrez votre token", placeholder="Ex: ABC12345")
            new_pwd = st.text_input("Nouveau mot de passe", type="password")
            if st.button("→ Valider le token", use_container_width=True):
                if token_input and new_pwd:
                    conn = db()
                    c = conn.cursor()
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    c.execute("SELECT username FROM users WHERE token=? AND token_expiry >= ?", (token_input.strip().upper(), now))
                    res = c.fetchone()
                    if res:
                        h = bcrypt.hashpw(new_pwd.encode(), bcrypt.gensalt())
                        c.execute("UPDATE users SET password=?, token=NULL, token_expiry=NULL WHERE username=?", (h.decode(), res[0]))
                        conn.commit()
                        conn.close()
                        st.success("✅ Mot de passe mis à jour ! Reconnectez-vous.")
                        st.session_state.mode_token = False
                        st.rerun()
                    else:
                        conn.close()
                        st.error("❌ Token invalide ou expiré.")
            if st.button("← Retour"):
                st.session_state.mode_token = False
                st.rerun()

# ═══════════════════════════════════════════════════════════════
# APP PRINCIPALE
# ═══════════════════════════════════════════════════════════════
else:
    nc = notif_count(st.session_state.user)

    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 20px 0 16px;">
            <div style="font-family:'Syne',sans-serif; font-size:1.4rem; font-weight:800; letter-spacing:-0.5px;">AppStock</div>
            <div style="font-size:0.8rem; opacity:0.5; margin-top:2px;">📡 Canal+</div>
        </div>
        <hr style="border-color:#222; margin: 0 0 12px;">
        <div style="font-size:0.82rem; opacity:0.6; margin-bottom:4px;">{'ADMIN' if st.session_state.role=='admin' else 'VENDEUR'}</div>
        <div style="font-weight:600; font-size:0.95rem; margin-bottom:16px;">{st.session_state.nom}</div>
        """, unsafe_allow_html=True)

        notif_label = f"🔔 Notifications  {'🔴' if nc > 0 else ''}"

        if st.session_state.role == "admin":
            opts = ["🏠 Dashboard", "⚡ Vente", "📦 Stock", "🔄 Réabonnements", notif_label, "👥 Vendeurs", "📊 Rapports", "⚙️ Paramètres"]
        else:
            opts = ["🏠 Dashboard", "⚡ Vente", "🔄 Réabonnements", notif_label, "📊 Mes Rapports"]

        choix = st.radio("", opts, label_visibility="collapsed")
        st.markdown("<hr style='border-color:#222; margin-top:auto;'>", unsafe_allow_html=True)
        if st.button("Déconnexion →", use_container_width=True):
            st.session_state.connecte = False
            st.rerun()

    # ══ DASHBOARD ══════════════════════════════════════════════
    if "Dashboard" in choix:
        st.markdown('<div class="page-title">Dashboard</div>', unsafe_allow_html=True)

        dispo, vendus, ca, nb_v = get_stats()
        alertes = get_alertes()
        dormants = get_decodeurs_dormants()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="stat-card"><div class="label">Stock disponible</div><div class="value">{dispo}</div><div class="sub">décodeurs</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-card vert"><div class="label">Vendus</div><div class="value">{vendus}</div><div class="sub">décodeurs</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="stat-card"><div class="label">Chiffre d\'affaires</div><div class="value">{ca:,.0f}</div><div class="sub">FCFA</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="stat-card rouge"><div class="label">Alertes actives</div><div class="value">{len(alertes) + len(dormants)}</div><div class="sub">à traiter</div></div>', unsafe_allow_html=True)

        # Alertes réabonnements
        if alertes:
            st.markdown("#### ⚠️ Alertes Réabonnements")
            for a in alertes[:6]:
                wa = wa_link(a['tel'], a['client'], a['jours'])
                if a['statut'] == 'expiré':
                    st.markdown(f'''<div class="alerte rouge">🔴 <b>{a["client"]}</b> — {a["numero"]} — Expiré depuis {abs(a["jours"])}j — 📞 {a["tel"]} <a href="{wa}" target="_blank" class="wa-btn">WhatsApp</a></div>''', unsafe_allow_html=True)
                else:
                    st.markdown(f'''<div class="alerte jaune">🟡 <b>{a["client"]}</b> — {a["numero"]} — Expire dans {a["jours"]}j — 📞 {a["tel"]} <a href="{wa}" target="_blank" class="wa-btn">WhatsApp</a></div>''', unsafe_allow_html=True)

        # Décodeurs dormants
        if dormants:
            st.markdown("#### 📦 Décodeurs Dormants (+1 mois)")
            for num, vendeur, date_ajout in dormants[:4]:
                st.markdown(f'<div class="alerte jaune">📦 <b>{num}</b> — Vendeur: {vendeur or "Non affecté"} — Ajouté le {date_ajout}</div>', unsafe_allow_html=True)

        # Dernières ventes
        st.markdown("#### 📋 Dernières Ventes")
        conn = db()
        df_v = pd.read_sql_query("SELECT numero, client_nom, client_tel, formule, prix_total, date_activation FROM decodeurs WHERE statut='vendu' ORDER BY date_activation DESC LIMIT 8", conn)
        conn.close()
        if not df_v.empty:
            df_v.columns = ["Numéro", "Client", "Téléphone", "Formule", "Prix (FCFA)", "Date"]
            st.dataframe(df_v, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune vente pour l'instant.")

    # ══ VENTE ══════════════════════════════════════════════════
    elif "Vente" in choix:
        st.markdown('<div class="page-title">Nouvelle Vente</div>', unsafe_allow_html=True)

        conn = db()
        df_dispo = pd.read_sql_query("SELECT numero FROM decodeurs WHERE statut='disponible'", conn)
        conn.close()

        if df_dispo.empty:
            st.warning("⚠️ Aucun décodeur disponible en stock.")
        else:
            st.markdown(f'<div class="card">📦 <b>{len(df_dispo)} décodeur(s) disponible(s)</b></div>', unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                numero = st.selectbox("📡 Décodeur", df_dispo['numero'].tolist())
                client_nom = st.text_input("👤 Nom du client")
                client_tel = st.text_input("📞 Téléphone client")
            with c2:
                formule = st.selectbox("📺 Formule", ["Access", "Evasion", "Tout Canal+", "Canal+ Box", "Réabonnement"])
                prix = st.number_input("💰 Prix (FCFA)", min_value=0, step=500)
                duree = st.selectbox("⏱️ Durée", ["1 mois", "3 mois", "6 mois", "12 mois"])

            duree_map = {"1 mois": 30, "3 mois": 90, "6 mois": 180, "12 mois": 365}
            date_exp = (datetime.now() + timedelta(days=duree_map[duree])).strftime("%Y-%m-%d")
            st.info(f"📅 Expiration : **{date_exp}**")

            if st.button("✅ Confirmer la vente", use_container_width=True):
                if client_nom and client_tel:
                    confirm = st.warning("⚠️ Confirmez-vous cette vente ?")
                    col_oui, col_non = st.columns(2)
                    with col_oui:
                        if st.button("✅ Oui, confirmer"):
                            conn = db()
                            c = conn.cursor()
                            c.execute("""UPDATE decodeurs SET statut='vendu', client_nom=?, client_tel=?,
                                         formule=?, prix_total=?, date_activation=?, date_expiration=?, affecte_a=?
                                         WHERE numero=?""",
                                      (client_nom, client_tel, formule, prix,
                                       datetime.now().strftime("%Y-%m-%d %H:%M"), date_exp,
                                       st.session_state.user, numero))
                            conn.commit()
                            conn.close()
                            push_notif(f"Vente : {numero} → {client_nom} ({formule} — {prix:,.0f} FCFA)", "vente", "admin")
                            st.success(f"✅ Vente enregistrée ! {numero} → {client_nom}")
                            st.balloons()
                    with col_non:
                        if st.button("❌ Annuler"):
                            st.rerun()
                else:
                    st.error("❌ Remplissez le nom et le téléphone.")

    # ══ STOCK ══════════════════════════════════════════════════
    elif "Stock" in choix and st.session_state.role == "admin":
        st.markdown('<div class="page-title">Gestion du Stock</div>', unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["📋 Stock", "➕ Ajouter", "✏️ Modifier"])

        with tab1:
            conn = db()
            df_s = pd.read_sql_query("SELECT numero, statut, affecte_a, client_nom, client_tel, formule, prix_total, date_ajout, date_expiration FROM decodeurs ORDER BY date_ajout DESC", conn)
            conn.close()

            if not df_s.empty:
                c1, c2 = st.columns([1, 2])
                with c1:
                    filtre = st.selectbox("Statut", ["Tous", "disponible", "vendu"])
                with c2:
                    rech = st.text_input("🔍 Rechercher (numéro, client...)")

                if filtre != "Tous":
                    df_s = df_s[df_s['statut'] == filtre]
                if rech:
                    df_s = df_s[df_s.apply(lambda r: rech.lower() in str(r).lower(), axis=1)]

                df_s.columns = ["Numéro", "Statut", "Vendeur", "Client", "Tél Client", "Formule", "Prix", "Ajouté le", "Expiration"]
                st.dataframe(df_s, use_container_width=True, hide_index=True)
                st.caption(f"{len(df_s)} résultat(s)")

                excel_data = export_excel(df_s, "Stock")
                st.download_button("📥 Exporter Excel", excel_data, "stock_appstock.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.info("Stock vide.")

        with tab2:
            st.markdown('<div class="scanner-box">📷 <b>Scanner ou saisir les numéros</b><br><small>Code-barres & QR Code supportés — jusqu\'à 20 décodeurs</small></div>', unsafe_allow_html=True)

            mode = st.radio("Mode d'ajout", ["📝 Saisie manuelle", "📷 Scanner (caméra)"], horizontal=True)

            vendeurs = get_vendeurs_list()
            vendeur_opts = [f"{v[1]} ({v[0]})" for v in vendeurs]
            vendeur_sel = st.selectbox("👤 Affecter au vendeur", vendeur_opts)
            vendeur_username = vendeurs[vendeur_opts.index(vendeur_sel)][0]
            partenaire = st.text_input("🏢 Partenaire", value="Canal+")

            if mode == "📝 Saisie manuelle":
                numeros_input = st.text_area("📝 Numéros (max 20 — un par ligne ou séparés par virgule)", height=180)
                if st.button("🚀 Ajouter au stock", use_container_width=True):
                    raw = numeros_input.replace('\n', ',').replace(';', ',')
                    numeros = list(set([n.strip() for n in raw.split(',') if n.strip()]))[:20]
                    if numeros:
                        conn = db()
                        c = conn.cursor()
                        ok, doublons = 0, 0
                        for num in numeros:
                            c.execute("INSERT OR IGNORE INTO decodeurs (numero, partenaire, statut, affecte_a, date_ajout) VALUES (?,?,'disponible',?,?)",
                                      (num, partenaire, vendeur_username, datetime.now().strftime("%Y-%m-%d %H:%M")))
                            if c.rowcount > 0:
                                ok += 1
                            else:
                                doublons += 1
                        conn.commit()
                        conn.close()
                        st.success(f"✅ {ok} ajouté(s). {doublons} doublon(s) ignoré(s).")
                    else:
                        st.error("❌ Aucun numéro valide.")

            else:
                st.markdown("""
                <div class="scanner-box">
                    📷 <b>Scanner activé</b><br>
                    <small>Utilisez l'application mobile ou un scanner Bluetooth.<br>
                    Collez les numéros scannés ci-dessous automatiquement.</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Zone de collecte scanner
                if 'scanned_numbers' not in st.session_state:
                    st.session_state.scanned_numbers = []
                
                scan_input = st.text_input("📡 Scan en cours (appuyez Entrée après chaque scan)", key="scan_live")
                
                col_add, col_clear = st.columns(2)
                with col_add:
                    if st.button("➕ Ajouter ce numéro") and scan_input:
                        if scan_input.strip() not in st.session_state.scanned_numbers:
                            if len(st.session_state.scanned_numbers) < 20:
                                st.session_state.scanned_numbers.append(scan_input.strip())
                                st.success(f"✅ {scan_input.strip()} ajouté à la liste")
                            else:
                                st.error("❌ Maximum 20 décodeurs atteint.")
                with col_clear:
                    if st.button("🗑️ Vider la liste"):
                        st.session_state.scanned_numbers = []
                        st.rerun()

                if st.session_state.scanned_numbers:
                    st.markdown(f"**{len(st.session_state.scanned_numbers)} numéro(s) scanné(s) :**")
                    for n in st.session_state.scanned_numbers:
                        st.markdown(f"- `{n}`")
                    
                    if st.button("🚀 Enregistrer tous les scans", use_container_width=True):
                        conn = db()
                        c = conn.cursor()
                        ok, doublons = 0, 0
                        for num in st.session_state.scanned_numbers:
                            c.execute("INSERT OR IGNORE INTO decodeurs (numero, partenaire, statut, affecte_a, date_ajout) VALUES (?,?,'disponible',?,?)",
                                      (num, partenaire, vendeur_username, datetime.now().strftime("%Y-%m-%d %H:%M")))
                            if c.rowcount > 0:
                                ok += 1
                            else:
                                doublons += 1
                        conn.commit()
                        conn.close()
                        st.session_state.scanned_numbers = []
                        st.success(f"✅ {ok} ajouté(s). {doublons} doublon(s) ignoré(s).")

        with tab3:
            st.markdown("#### ✏️ Modifier une vente existante")
            conn = db()
            df_mod = pd.read_sql_query("SELECT numero, client_nom, client_tel, formule, prix_total FROM decodeurs WHERE statut='vendu'", conn)
            conn.close()

            if df_mod.empty:
                st.info("Aucune vente à modifier.")
            else:
                num_sel = st.selectbox("Choisir un décodeur vendu", df_mod['numero'].tolist())
                row = df_mod[df_mod['numero'] == num_sel].iloc[0]

                c1, c2 = st.columns(2)
                with c1:
                    new_nom = st.text_input("Nom client", value=str(row['client_nom'] or ''))
                    new_tel = st.text_input("Téléphone", value=str(row['client_tel'] or ''))
                with c2:
                    new_formule = st.selectbox("Formule", ["Access", "Evasion", "Tout Canal+", "Canal+ Box", "Réabonnement"],
                                               index=["Access", "Evasion", "Tout Canal+", "Canal+ Box", "Réabonnement"].index(row['formule']) if row['formule'] in ["Access", "Evasion", "Tout Canal+", "Canal+ Box", "Réabonnement"] else 0)
                    new_prix = st.number_input("Prix (FCFA)", value=float(row['prix_total'] or 0), step=500.0)

                if st.button("💾 Sauvegarder les modifications"):
                    conn = db()
                    c = conn.cursor()
                    # Enregistrer dans historique
                    for champ, old, new in [("client_nom", row['client_nom'], new_nom), ("client_tel", row['client_tel'], new_tel), ("formule", row['formule'], new_formule), ("prix_total", row['prix_total'], new_prix)]:
                        if str(old) != str(new):
                            c.execute("INSERT INTO historique_modifications (decodeur_numero, champ_modifie, ancienne_valeur, nouvelle_valeur, modifie_par, date_modification) VALUES (?,?,?,?,?,?)",
                                      (num_sel, champ, str(old), str(new), st.session_state.user, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    c.execute("UPDATE decodeurs SET client_nom=?, client_tel=?, formule=?, prix_total=? WHERE numero=?",
                              (new_nom, new_tel, new_formule, new_prix, num_sel))
                    conn.commit()
                    conn.close()
                    st.success("✅ Modifications enregistrées avec historique.")

    # ══ RÉABONNEMENTS ══════════════════════════════════════════
    elif "Réabonnements" in choix:
        st.markdown('<div class="page-title">Suivi Réabonnements</div>', unsafe_allow_html=True)

        alertes = get_alertes()
        expires = [a for a in alertes if a['statut'] == 'expiré']
        urgents = [a for a in alertes if a['statut'] == 'urgent']

        if not alertes:
            st.markdown('<div class="alerte vert">✅ Aucun réabonnement urgent en ce moment.</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if expires:
                st.markdown(f"#### 🔴 Expirés ({len(expires)})")
                for a in expires:
                    wa = wa_link(a['tel'], a['client'], a['jours'])
                    st.markdown(f'''<div class="alerte rouge"><b>{a["client"]}</b><br>📡 {a["numero"]} | 📞 {a["tel"]}<br>⏰ Expiré depuis {abs(a["jours"])} jour(s)<br><a href="{wa}" target="_blank" class="wa-btn">💬 WhatsApp</a></div>''', unsafe_allow_html=True)
        with c2:
            if urgents:
                st.markdown(f"#### 🟡 Expirent bientôt ({len(urgents)})")
                for a in urgents:
                    wa = wa_link(a['tel'], a['client'], a['jours'])
                    st.markdown(f'''<div class="alerte jaune"><b>{a["client"]}</b><br>📡 {a["numero"]} | 📞 {a["tel"]}<br>⏰ Expire dans {a["jours"]} jour(s)<br><a href="{wa}" target="_blank" class="wa-btn">💬 WhatsApp</a></div>''', unsafe_allow_html=True)

        st.markdown("#### 📋 Tous les abonnements actifs")
        conn = db()
        df_r = pd.read_sql_query("SELECT numero, client_nom, client_tel, formule, date_activation, date_expiration FROM decodeurs WHERE statut='vendu' ORDER BY date_expiration ASC", conn)
        conn.close()
        if not df_r.empty:
            df_r.columns = ["Numéro", "Client", "Téléphone", "Formule", "Activation", "Expiration"]
            st.dataframe(df_r, use_container_width=True, hide_index=True)
            excel_data = export_excel(df_r, "Réabonnements")
            st.download_button("📥 Exporter Excel", excel_data, "reabonnements.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ══ NOTIFICATIONS ══════════════════════════════════════════
    elif "Notifications" in choix:
        st.markdown('<div class="page-title">Notifications</div>', unsafe_allow_html=True)

        conn = db()
        c = conn.cursor()
        c.execute("SELECT message, type, date_creation, lu FROM notifications WHERE destinataire=? OR destinataire='tous' ORDER BY date_creation DESC LIMIT 60", (st.session_state.user,))
        notifs = c.fetchall()
        c.execute("UPDATE notifications SET lu=1 WHERE destinataire=? OR destinataire='tous'", (st.session_state.user,))
        conn.commit()
        conn.close()

        if not notifs:
            st.info("Aucune notification.")
        for msg, typ, date, lu in notifs:
            icons = {"vente": "🟢", "expiration_24h": "🔴", "expiration_7j": "🟡", "dormant": "📦"}
            icon = icons.get(typ, "🔵")
            bg = "var(--blanc)" if lu else "#f9f9f9"
            st.markdown(f'<div class="card" style="background:{bg}; border-left:3px solid {"#0a0a0a" if not lu else "#e8e8e8"};">{icon} {msg}<br><small style="color:var(--gris3);">🕐 {date}</small></div>', unsafe_allow_html=True)

    # ══ VENDEURS ═══════════════════════════════════════════════
    elif "Vendeurs" in choix and st.session_state.role == "admin":
        st.markdown('<div class="page-title">Gestion des Vendeurs</div>', unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["📋 Liste", "➕ Ajouter", "🔑 Token"])

        with tab1:
            conn = db()
            df_vend = pd.read_sql_query("""
                SELECT u.nom_complet, u.telephone, u.role, u.date_creation,
                       COUNT(d.id) as ventes,
                       COALESCE(SUM(d.prix_total),0) as ca
                FROM users u
                LEFT JOIN decodeurs d ON d.affecte_a=u.username AND d.statut='vendu'
                GROUP BY u.username
            """, conn)
            conn.close()
            if not df_vend.empty:
                df_vend.columns = ["Nom", "Téléphone", "Rôle", "Créé le", "Ventes", "CA (FCFA)"]
                st.dataframe(df_vend, use_container_width=True, hide_index=True)

        with tab2:
            c1, c2 = st.columns(2)
            with c1:
                nu = st.text_input("👤 Identifiant unique")
                nn = st.text_input("📝 Nom complet")
            with c2:
                nt = st.text_input("📞 Téléphone")
                np = st.text_input("🔑 Mot de passe initial", type="password")

            if st.button("➕ Créer le compte vendeur", use_container_width=True):
                if nu and nn and nt and np:
                    try:
                        h = bcrypt.hashpw(np.encode(), bcrypt.gensalt())
                        conn = db()
                        c = conn.cursor()
                        c.execute("INSERT INTO users (username, telephone, password, role, nom_complet, date_creation) VALUES (?,?,?,?,?,?)",
                                  (nu, nt, h.decode(), "vendeur", nn, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Compte créé pour {nn} — connexion via téléphone {nt}")
                    except sqlite3.IntegrityError:
                        st.error("❌ Identifiant ou téléphone déjà utilisé.")
                else:
                    st.error("❌ Remplissez tous les champs.")

        with tab3:
            st.markdown("#### 🔑 Générer un token de récupération")
            conn = db()
            df_users = pd.read_sql_query("SELECT username, nom_complet, telephone FROM users WHERE role='vendeur'", conn)
            conn.close()

            if df_users.empty:
                st.info("Aucun vendeur enregistré.")
            else:
                user_opts = [f"{r['nom_complet']} ({r['telephone']})" for _, r in df_users.iterrows()]
                user_sel = st.selectbox("Choisir le vendeur", user_opts)
                idx = user_opts.index(user_sel)
                username_sel = df_users.iloc[idx]['username']

                if st.button("🔑 Générer un token temporaire"):
                    token = secrets.token_hex(4).upper()
                    expiry = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
                    conn = db()
                    c = conn.cursor()
                    c.execute("UPDATE users SET token=?, token_expiry=? WHERE username=?", (token, expiry, username_sel))
                    conn.commit()
                    conn.close()
                    st.markdown(f'<div class="token-box">{token}</div>', unsafe_allow_html=True)
                    st.success(f"✅ Token valable 2 heures. Donnez-le au vendeur.")
                    st.info(f"Expiration : {expiry}")

    # ══ RAPPORTS ═══════════════════════════════════════════════
    elif "Rapport" in choix:
        st.markdown('<div class="page-title">Rapports</div>', unsafe_allow_html=True)

        conn = db()
        df_rap = pd.read_sql_query("""
            SELECT u.nom_complet, u.username,
                   COUNT(d.id) as ventes,
                   COALESCE(SUM(d.prix_total),0) as ca,
                   MAX(d.date_activation) as derniere_vente
            FROM users u
            LEFT JOIN decodeurs d ON d.affecte_a=u.username AND d.statut='vendu'
            GROUP BY u.username
            ORDER BY ca DESC
        """, conn)
        conn.close()

        if not df_rap.empty:
            # Podium
            st.markdown("#### 🏆 Classement Vendeurs")
            medals = ["🥇", "🥈", "🥉"]
            cols = st.columns(min(3, len(df_rap)))
            for i, (_, row) in enumerate(df_rap.head(3).iterrows()):
                with cols[i]:
                    st.markdown(f'''
                    <div class="podium-card">
                        <div class="podium-emoji">{medals[i]}</div>
                        <div class="podium-nom">{row["nom_complet"]}</div>
                        <div class="podium-stat">{int(row["ventes"])} ventes</div>
                        <div class="podium-stat"><b>{row["ca"]:,.0f} FCFA</b></div>
                    </div>''', unsafe_allow_html=True)

            st.markdown("#### 📊 Détail par vendeur")

            # Filtrer par vendeur si vendeur connecté
            if st.session_state.role == "vendeur":
                df_rap = df_rap[df_rap['username'] == st.session_state.user]

            for _, row in df_rap.iterrows():
                with st.expander(f"👤 {row['nom_complet']} — {int(row['ventes'])} vente(s) — {row['ca']:,.0f} FCFA"):
                    conn = db()
                    # Décodeurs affectés
                    df_dec = pd.read_sql_query(f"SELECT numero, statut, formule, prix_total, date_activation FROM decodeurs WHERE affecte_a='{row['username']}' ORDER BY date_activation DESC", conn)
                    # Réabonnements à venir
                    df_reabo = pd.read_sql_query(f"""
                        SELECT numero, client_nom, date_expiration FROM decodeurs 
                        WHERE affecte_a='{row['username']}' AND statut='vendu' 
                        AND date_expiration >= date('now') 
                        ORDER BY date_expiration ASC LIMIT 5
                    """, conn)
                    conn.close()

                    c1, c2, c3 = st.columns(3)
                    total = len(df_dec)
                    vendus_v = len(df_dec[df_dec['statut'] == 'vendu']) if not df_dec.empty else 0
                    dispo_v = len(df_dec[df_dec['statut'] == 'disponible']) if not df_dec.empty else 0
                    taux = round((vendus_v / total * 100) if total > 0 else 0)

                    with c1:
                        st.metric("Décodeurs affectés", total)
                        st.metric("Vendus", vendus_v)
                    with c2:
                        st.metric("Disponibles", dispo_v)
                        st.metric("Taux conversion", f"{taux}%")
                    with c3:
                        st.metric("CA total", f"{row['ca']:,.0f} FCFA")
                        if row['derniere_vente']:
                            st.metric("Dernière vente", str(row['derniere_vente'])[:10])

                    if not df_dec.empty:
                        st.markdown("**Historique ventes :**")
                        st.dataframe(df_dec, use_container_width=True, hide_index=True)
                        excel_data = export_excel(df_dec, "Rapport")
                        st.download_button(f"📥 Export Excel — {row['nom_complet']}", excel_data, f"rapport_{row['username']}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"exp_{row['username']}")

    # ══ PARAMÈTRES ═════════════════════════════════════════════
    elif "Paramètres" in choix and st.session_state.role == "admin":
        st.markdown('<div class="page-title">Paramètres</div>', unsafe_allow_html=True)

        st.markdown("#### 🔑 Changer le mot de passe")
        old = st.text_input("Ancien mot de passe", type="password")
        new1 = st.text_input("Nouveau mot de passe", type="password")
        new2 = st.text_input("Confirmer le nouveau mot de passe", type="password")

        if st.button("💾 Mettre à jour"):
            if new1 != new2:
                st.error("❌ Les mots de passe ne correspondent pas.")
            elif len(new1) < 6:
                st.error("❌ Le mot de passe doit faire au moins 6 caractères.")
            else:
                conn = db()
                c = conn.cursor()
                c.execute("SELECT password FROM users WHERE username=?", (st.session_state.user,))
                res = c.fetchone()
                if res and bcrypt.checkpw(old.encode(), res[0].encode()):
                    h = bcrypt.hashpw(new1.encode(), bcrypt.gensalt())
                    c.execute("UPDATE users SET password=? WHERE username=?", (h.decode(), st.session_state.user))
                    conn.commit()
                    st.success("✅ Mot de passe mis à jour.")
                else:
                    st.error("❌ Ancien mot de passe incorrect.")
                conn.close()

        st.divider()
        st.markdown("#### 📊 Historique des modifications")
        conn = db()
        df_hist = pd.read_sql_query("SELECT * FROM historique_modifications ORDER BY date_modification DESC LIMIT 50", conn)
        conn.close()
        if not df_hist.empty:
            df_hist.columns = ["ID", "Décodeur", "Champ", "Ancienne valeur", "Nouvelle valeur", "Modifié par", "Date"]
            st.dataframe(df_hist[["Décodeur", "Champ", "Ancienne valeur", "Nouvelle valeur", "Modifié par", "Date"]], use_container_width=True, hide_index=True)
        else:
            st.info("Aucune modification enregistrée.")
