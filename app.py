import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
import os
import secrets
import io
from datetime import datetime, timedelta

st.set_page_config(page_title="AppStock", page_icon="📡", layout="wide", initial_sidebar_state="expanded")

FORMULES = {"Access": 5500, "Access+": 16500, "Evasion": 11000, "Tout Canal+": 25000}
PRIX_DECODEUR_DEFAULT = 5000
PROMOS = {"Aucune promo": 0, "Promo -1000 FCFA": 1000, "Promo -3000 FCFA": 3000}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
:root { --noir:#0a0a0a; --blanc:#ffffff; --gris:#f4f4f4; --gris2:#e8e8e8; --gris3:#666; --rouge:#e50000; --vert:#00b341; --jaune:#f5a623; }
* { font-family:'DM Sans',sans-serif; box-sizing:border-box; color:#0a0a0a; }
h1,h2,h3 { font-family:'Syne',sans-serif; }
.stApp { background:var(--gris); }
/* Forcer texte visible partout sauf sidebar */
.stMarkdown, .stMarkdown p, .stMarkdown li,
p, span, div, h1, h2, h3, h4, h5,
label, .stRadio span, .stCheckbox span,
[data-testid="stMarkdownContainer"] p,
[data-testid="stText"] { color:#0a0a0a !important; }
/* Tabs texte visible */
.stTabs [data-baseweb="tab"] { color:#666666 !important; }
.stTabs [aria-selected="true"] { color:#ffffff !important; }
[data-testid="stSidebar"] { background:var(--noir) !important; border-right:1px solid #1a1a1a; }
[data-testid="stSidebar"] * { color:var(--blanc) !important; }
[data-testid="stSidebar"] .stRadio label { border-radius:8px; padding:10px 14px; cursor:pointer; transition:background 0.15s; font-size:0.9rem; display:block; }
[data-testid="stSidebar"] .stRadio label:hover { background:#1a1a1a; }
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background:#ffffff !important; color:#0a0a0a !important;
    border:1.5px solid #cccccc !important; border-radius:8px !important;
    font-family:'DM Sans',sans-serif !important; font-size:0.95rem !important; padding:10px 12px !important;
}
/* Labels visibles partout */
label, div[data-testid="stWidgetLabel"] p {
    color:#0a0a0a !important;
    font-family:'DM Sans',sans-serif !important;
    font-size:0.9rem !important;
    font-weight:500 !important;
}
.stTextInput input:focus, .stNumberInput input:focus { border-color:var(--noir) !important; box-shadow:0 0 0 3px rgba(0,0,0,0.1) !important; }
.stSelectbox > div > div { background:#ffffff !important; color:#0a0a0a !important; border:1.5px solid #cccccc !important; border-radius:8px !important; }
.stButton > button { background:var(--noir) !important; color:var(--blanc) !important; border:none !important; border-radius:8px !important; font-weight:600 !important; font-size:0.9rem !important; padding:10px 20px !important; transition:all 0.15s !important; }
.stButton > button:hover { background:#333 !important; transform:translateY(-1px); box-shadow:0 4px 12px rgba(0,0,0,0.2) !important; }
.card { background:var(--blanc); border-radius:12px; padding:20px 24px; box-shadow:0 1px 4px rgba(0,0,0,0.06); margin-bottom:16px; border:1px solid var(--gris2); }
.stat-card { background:var(--blanc); border-radius:12px; padding:20px; border:1px solid var(--gris2); box-shadow:0 1px 4px rgba(0,0,0,0.05); margin-bottom:8px; }
.stat-label { font-size:0.75rem; color:var(--gris3); font-weight:500; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:6px; }
.stat-value { font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:var(--noir); }
.stat-sub { font-size:0.78rem; color:var(--gris3); margin-top:2px; }
.stat-vert .stat-value { color:var(--vert); }
.stat-rouge .stat-value { color:var(--rouge); }
.page-title { font-family:'Syne',sans-serif; font-size:1.5rem; font-weight:800; color:var(--noir); margin-bottom:24px; padding-bottom:12px; border-bottom:2px solid var(--noir); letter-spacing:-0.5px; }
.prix-box { background:var(--noir); color:var(--blanc); border-radius:12px; padding:20px; text-align:center; margin:12px 0; }
.prix-box .plabel { font-size:0.78rem; opacity:0.6; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px; }
.prix-box .pmontant { font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; }
.total-box { background:var(--vert); color:var(--blanc); border-radius:12px; padding:20px; text-align:center; margin:12px 0; }
.total-box .plabel { font-size:0.78rem; opacity:0.8; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px; }
.total-box .pmontant { font-family:'Syne',sans-serif; font-size:2.2rem; font-weight:800; }
.alerte { border-radius:8px; padding:12px 16px; margin:6px 0; font-size:0.88rem; }
.alerte.rouge { background:#fff0f0; border-left:3px solid var(--rouge); color:#333; }
.alerte.jaune { background:#fffbf0; border-left:3px solid var(--jaune); color:#333; }
.alerte.vert { background:#f0fff5; border-left:3px solid var(--vert); color:#333; }
.wa-btn { display:inline-block; background:#25D366; color:white !important; padding:5px 12px; border-radius:6px; font-size:0.8rem; font-weight:600; text-decoration:none; margin-top:4px; }
.token-box { background:var(--noir); color:var(--blanc); border-radius:8px; padding:16px; font-family:monospace; font-size:1.4rem; letter-spacing:4px; text-align:center; margin:12px 0; }
.podium-card { background:var(--blanc); border-radius:12px; padding:16px; border:1px solid var(--gris2); text-align:center; }
.podium-emoji { font-size:2rem; }
.podium-nom { font-family:'Syne',sans-serif; font-weight:700; font-size:0.95rem; margin:6px 0 2px; }
.podium-stat { font-size:0.8rem; color:var(--gris3); }
.stTabs [data-baseweb="tab-list"] { background:var(--blanc); border-radius:10px; padding:4px; border:1px solid var(--gris2); }
.stTabs [aria-selected="true"] { background:var(--noir) !important; color:var(--blanc) !important; border-radius:8px !important; }
.scanner-box { background:var(--blanc); border:2px dashed var(--gris2); border-radius:12px; padding:24px; text-align:center; margin:12px 0; }
.login-card { background:var(--blanc); border-radius:16px; padding:40px 36px; border:1px solid var(--gris2); box-shadow:0 8px 32px rgba(0,0,0,0.08); margin-top:40px; }
.login-logo { font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; color:var(--noir); letter-spacing:-1px; }
.login-sub { color:var(--gris3); font-size:0.85rem; margin-bottom:24px; }
[data-testid="stDataFrame"] { border-radius:10px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'appstock.db')

def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, telephone TEXT UNIQUE,
        password TEXT, role TEXT DEFAULT "vendeur", nom_complet TEXT, date_creation TEXT,
        token TEXT, token_expiry TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS decodeurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT UNIQUE, partenaire TEXT DEFAULT "Canal+",
        statut TEXT DEFAULT "disponible", affecte_a TEXT, client_nom TEXT, client_tel TEXT,
        formule TEXT, prix_formule REAL DEFAULT 0, prix_decodeur REAL DEFAULT 0,
        promo REAL DEFAULT 0, prix_total REAL, date_ajout TEXT, date_activation TEXT, date_expiration TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS historique_modifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, decodeur_numero TEXT, champ_modifie TEXT,
        ancienne_valeur TEXT, nouvelle_valeur TEXT, modifie_par TEXT, date_modification TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, type TEXT,
        destinataire TEXT DEFAULT "tous", lu INTEGER DEFAULT 0, date_creation TEXT)''')
    for col, typ in [("prix_formule","REAL DEFAULT 0"),("prix_decodeur","REAL DEFAULT 0"),("promo","REAL DEFAULT 0")]:
        try:
            c.execute(f"ALTER TABLE decodeurs ADD COLUMN {col} {typ}")
        except: pass
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        h = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        c.execute("INSERT INTO users (username,telephone,password,role,nom_complet,date_creation) VALUES (?,?,?,?,?,?)",
                  ("admin","000000000",h.decode(),"admin","Administrateur",datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

init_db()

def get_stats():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM decodeurs WHERE statut='disponible'")
    dispo = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM decodeurs WHERE statut='vendu'")
    vendus = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(prix_total),0) FROM decodeurs WHERE statut='vendu'")
    ca = c.fetchone()[0]
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM decodeurs WHERE statut='vendu' AND date_activation LIKE ?", (f"{today}%",))
    vj = c.fetchone()[0]
    conn.close()
    return dispo, vendus, ca, vj

def get_ventes_jour():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = db()
    df = pd.read_sql_query(f"""
        SELECT u.nom_complet as Vendeur, COUNT(d.id) as Ventes_aujourd_hui,
               COALESCE(SUM(d.prix_total),0) as CA_aujourd_hui
        FROM users u LEFT JOIN decodeurs d ON d.affecte_a=u.username
            AND d.statut='vendu' AND d.date_activation LIKE '{today}%'
        GROUP BY u.username ORDER BY Ventes_aujourd_hui DESC
    """, conn)
    conn.close()
    return df

def get_alertes():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT numero,client_nom,client_tel,date_expiration,affecte_a FROM decodeurs WHERE statut='vendu' AND date_expiration IS NOT NULL AND date_expiration!=''")
    rows = c.fetchall()
    conn.close()
    today = datetime.now().date()
    alertes = []
    for num,nom,tel,exp,vendeur in rows:
        try:
            date_exp = datetime.strptime(exp,"%Y-%m-%d").date()
            jours = (date_exp - today).days
            if jours < 0:
                alertes.append({"numero":num,"client":nom,"tel":tel,"jours":jours,"statut":"expiré","vendeur":vendeur})
            elif jours <= 7:
                alertes.append({"numero":num,"client":nom,"tel":tel,"jours":jours,"statut":"urgent","vendeur":vendeur})
        except: pass
    return alertes

def get_dormants():
    conn = db()
    c = conn.cursor()
    limit = (datetime.now()-timedelta(days=30)).strftime("%Y-%m-%d")
    c.execute("SELECT numero,affecte_a,date_ajout FROM decodeurs WHERE statut='disponible' AND date_ajout<=?", (limit,))
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
    c.execute("INSERT INTO notifications (message,type,destinataire,date_creation) VALUES (?,?,?,?)",
              (message,type_n,destinataire,datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def auto_notifs():
    for a in get_alertes():
        if a['jours'] in [0,1]:
            push_notif(f"Abonnement expire dans 24h — {a['client']} ({a['numero']})", "expiration_24h", a['vendeur'] or "admin")
        elif 1 < a['jours'] <= 7:
            push_notif(f"Abonnement expire dans {a['jours']} jours — {a['client']} ({a['numero']})", "expiration_7j", a['vendeur'] or "admin")
    for num,vendeur,date_ajout in get_dormants():
        push_notif(f"Decodeur {num} en stock depuis plus d'1 mois sans vente", "dormant", vendeur or "admin")

def wa_link(tel, nom, jours):
    msg = f"Bonjour {nom}, votre abonnement Canal+ {'a expire' if jours<0 else f'expire dans {jours} jour(s)'}. Contactez-nous. — AppStock"
    tel_clean = tel.replace(" ","").replace("+","")
    if not tel_clean.startswith("221"):
        tel_clean = "221"+tel_clean
    import urllib.parse
    return f"https://wa.me/{tel_clean}?text={urllib.parse.quote(msg)}"

def export_excel(df, sheet="Data"):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name=sheet)
    return out.getvalue()

def get_vendeurs():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT username, nom_complet FROM users")
    rows = c.fetchall()
    conn.close()
    return rows if rows else [("admin","Administrateur")]

for k,v in [('connecte',False),('mode_token',False),('confirmer_vente',False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ═══ LOGIN ═══════════════════════════════════════════════════
if not st.session_state.connecte:
    col1,col2,col3 = st.columns([1,1.1,1])
    with col2:
        st.markdown('<div class="login-card"><div class="login-logo">AppStock</div><div class="login-sub">Gestion de stock Canal+ professionnelle</div></div>', unsafe_allow_html=True)
        if not st.session_state.mode_token:
            tel = st.text_input("Numero de telephone ou identifiant")
            pwd = st.text_input("Mot de passe", type="password")
            c1,c2 = st.columns(2)
            with c1:
                if st.button("Se connecter", use_container_width=True):
                    conn = db()
                    cur = conn.cursor()
                    cur.execute("SELECT password,role,nom_complet,username FROM users WHERE telephone=? OR username=?", (tel,tel))
                    res = cur.fetchone()
                    conn.close()
                    if res:
                        p = res[0].encode() if isinstance(res[0],str) else res[0]
                        if bcrypt.checkpw(pwd.encode(),p):
                            st.session_state.connecte = True
                            st.session_state.user = res[3]
                            st.session_state.role = res[1]
                            st.session_state.nom = res[2]
                            auto_notifs()
                            st.rerun()
                        else:
                            st.error("Mot de passe incorrect")
                    else:
                        st.error("Compte introuvable")
            with c2:
                if st.button("Mot de passe oublie", use_container_width=True):
                    st.session_state.mode_token = True
                    st.rerun()
        else:
            st.markdown("### Recuperation par token")
            st.info("Demandez un token a votre admin.")
            tok = st.text_input("Token recu")
            new_p = st.text_input("Nouveau mot de passe", type="password")
            if st.button("Valider", use_container_width=True):
                conn = db()
                cur = conn.cursor()
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                cur.execute("SELECT username FROM users WHERE token=? AND token_expiry>=?", (tok.strip().upper(),now))
                res = cur.fetchone()
                if res:
                    h = bcrypt.hashpw(new_p.encode(),bcrypt.gensalt())
                    cur.execute("UPDATE users SET password=?,token=NULL,token_expiry=NULL WHERE username=?", (h.decode(),res[0]))
                    conn.commit()
                    conn.close()
                    st.success("Mot de passe mis a jour !")
                    st.session_state.mode_token = False
                    st.rerun()
                else:
                    conn.close()
                    st.error("Token invalide ou expire.")
            if st.button("Retour"):
                st.session_state.mode_token = False
                st.rerun()

# ═══ APP ═════════════════════════════════════════════════════
else:
    nc = notif_count(st.session_state.user)
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:20px 0 16px;">
            <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;letter-spacing:-0.5px;">AppStock</div>
            <div style="font-size:0.75rem;opacity:0.4;margin-top:2px;">Canal+</div>
        </div>
        <hr style="border-color:#1a1a1a;margin:0 0 12px;">
        <div style="font-size:0.75rem;opacity:0.5;margin-bottom:2px;">{'ADMIN' if st.session_state.role=='admin' else 'VENDEUR'}</div>
        <div style="font-weight:600;font-size:0.9rem;margin-bottom:16px;">{st.session_state.nom}</div>
        """, unsafe_allow_html=True)
        notif_lbl = f"Notifications {'(!)' if nc>0 else ''}"
        if st.session_state.role=="admin":
            opts = ["Dashboard","Vente","Stock","Reabonnements",notif_lbl,"Vendeurs","Rapports","Parametres"]
        else:
            opts = ["Dashboard","Vente","Reabonnements",notif_lbl,"Mes Rapports"]
        choix = st.radio("", opts, label_visibility="collapsed")
        st.markdown("<hr style='border-color:#1a1a1a;'>", unsafe_allow_html=True)
        if st.button("Deconnexion", use_container_width=True):
            st.session_state.connecte = False
            st.rerun()

    # ══ DASHBOARD ════════════════════════════════════════════
    if choix == "Dashboard":
        st.markdown('<div class="page-title">Dashboard</div>', unsafe_allow_html=True)
        dispo,vendus,ca,vj = get_stats()
        alertes = get_alertes()
        dormants = get_dormants()
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="stat-card"><div class="stat-label">Stock disponible</div><div class="stat-value">{dispo}</div><div class="stat-sub">decodeurs</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-card stat-vert"><div class="stat-label">Total vendus</div><div class="stat-value">{vendus}</div><div class="stat-sub">decodeurs</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="stat-card"><div class="stat-label">Chiffre d affaires</div><div class="stat-value">{ca:,.0f}</div><div class="stat-sub">FCFA</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="stat-card stat-rouge"><div class="stat-label">Ventes aujourd hui</div><div class="stat-value">{vj}</div><div class="stat-sub">transactions</div></div>', unsafe_allow_html=True)

        st.markdown("#### Ventes du jour par vendeur")
        df_jour = get_ventes_jour()
        if not df_jour.empty and df_jour['Ventes_aujourd_hui'].sum() > 0:
            df_jour = df_jour[df_jour['Ventes_aujourd_hui'] > 0]
            st.dataframe(df_jour, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune vente aujourd'hui.")

        if alertes:
            st.markdown("#### Alertes Reabonnements")
            for a in alertes[:5]:
                wa = wa_link(a['tel'],a['client'],a['jours'])
                if a['statut']=='expiré':
                    st.markdown(f'<div class="alerte rouge"><b>{a["client"]}</b> — {a["numero"]} — Expire depuis {abs(a["jours"])} jours — Tel: {a["tel"]} <a href="{wa}" target="_blank" class="wa-btn">WhatsApp</a></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="alerte jaune"><b>{a["client"]}</b> — {a["numero"]} — Expire dans {a["jours"]} jours — Tel: {a["tel"]} <a href="{wa}" target="_blank" class="wa-btn">WhatsApp</a></div>', unsafe_allow_html=True)

        if dormants:
            st.markdown("#### Decodeurs Dormants (plus d'1 mois)")
            for num,vendeur,date_ajout in dormants[:4]:
                st.markdown(f'<div class="alerte jaune"><b>{num}</b> — {vendeur or "Non affecte"} — Ajoute le {date_ajout}</div>', unsafe_allow_html=True)

        st.markdown("#### Dernieres Ventes")
        conn = db()
        df_v = pd.read_sql_query("SELECT numero, client_nom, formule, prix_formule, prix_decodeur, promo, prix_total, date_activation FROM decodeurs WHERE statut='vendu' ORDER BY date_activation DESC LIMIT 8", conn)
        conn.close()
        if not df_v.empty:
            df_v.columns = ["Numero","Client","Formule","Prix Formule","Prix Decodeur","Promo","Total FCFA","Date"]
            st.dataframe(df_v, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune vente pour l'instant.")

    # ══ VENTE ════════════════════════════════════════════════
    elif choix == "Vente":
        st.markdown('<div class="page-title">Nouvelle Vente</div>', unsafe_allow_html=True)
        conn = db()
        df_dispo = pd.read_sql_query("SELECT numero FROM decodeurs WHERE statut='disponible'", conn)
        conn.close()

        if df_dispo.empty:
            st.warning("Aucun decodeur disponible en stock.")
        else:
            st.markdown(f'<div class="card"><b>{len(df_dispo)} decodeur(s) disponible(s)</b></div>', unsafe_allow_html=True)
            c1,c2 = st.columns(2)
            with c1:
                numero = st.selectbox("Numero du decodeur", df_dispo['numero'].tolist())
                client_nom = st.text_input("Nom du client")
                client_tel = st.text_input("Numero de telephone du client")
                duree = st.selectbox("Duree de l abonnement", ["1 mois","3 mois","6 mois","12 mois"])
            with c2:
                formule = st.selectbox("Formule Canal+", list(FORMULES.keys()))
                prix_formule = FORMULES[formule]
                prix_deco = st.number_input("Prix du decodeur (FCFA)", min_value=0, value=PRIX_DECODEUR_DEFAULT, step=500)
                prix_deco_final = prix_deco
                promo_val = 0
                total = prix_formule + prix_deco_final
                st.markdown(f"""
                <div class="prix-box">
                    <div class="plabel">Prix formule {formule}</div>
                    <div class="pmontant">{prix_formule:,} FCFA</div>
                </div>
                <div class="total-box">
                    <div class="plabel">Total a payer</div>
                    <div class="pmontant">{total:,} FCFA</div>
                    <div style="font-size:0.8rem;opacity:0.8;margin-top:4px;">Formule {prix_formule:,} + Decodeur {prix_deco_final:,} FCFA</div>
                </div>
                """, unsafe_allow_html=True)

            duree_map = {"1 mois":30,"3 mois":90,"6 mois":180,"12 mois":365}
            date_exp = (datetime.now()+timedelta(days=duree_map[duree])).strftime("%Y-%m-%d")
            st.info(f"Date d expiration : {date_exp}")

            if not st.session_state.confirmer_vente:
                if st.button("Confirmer la vente", use_container_width=True):
                    if client_nom and client_tel:
                        st.session_state.confirmer_vente = True
                        st.session_state.vente_data = {
                            "numero": numero, "client_nom": client_nom,
                            "client_tel": client_tel, "formule": formule,
                            "prix_formule": prix_formule, "prix_deco": prix_deco_final,
                            "promo": promo_val, "total": total,
                            "date_exp": date_exp, "vendeur": st.session_state.user
                        }
                        st.rerun()
                    else:
                        st.error("Remplissez le nom et le numero de telephone du client.")
            else:
                v = st.session_state.vente_data
                st.markdown(f"""
                <div class="card">
                    <b>Confirmation de vente</b><br><br>
                    Decodeur : {v['numero']}<br>
                    Client : {v['client_nom']} — Tel : {v['client_tel']}<br>
                    Formule : {v['formule']}<br>
                    Total : <b>{v['total']:,} FCFA</b><br>
                    Expiration : {v['date_exp']}
                </div>
                """, unsafe_allow_html=True)
                col_oui, col_non = st.columns(2)
                with col_oui:
                    if st.button("Oui confirmer", use_container_width=True):
                        conn = db()
                        cur = conn.cursor()
                        cur.execute("""UPDATE decodeurs SET statut='vendu', client_nom=?, client_tel=?,
                                       formule=?, prix_formule=?, prix_decodeur=?, promo=?, prix_total=?,
                                       date_activation=?, date_expiration=?, affecte_a=? WHERE numero=?""",
                                    (v['client_nom'],v['client_tel'],v['formule'],v['prix_formule'],
                                     v['prix_deco'],v['promo'],v['total'],
                                     datetime.now().strftime("%Y-%m-%d %H:%M"),
                                     v['date_exp'],v['vendeur'],v['numero']))
                        conn.commit()
                        conn.close()
                        push_notif(f"Vente : {v['numero']} vers {v['client_nom']} ({v['formule']} — {v['total']:,} FCFA)", "vente", "admin")
                        st.session_state.confirmer_vente = False
                        st.session_state.vente_data = {}
                        st.success(f"Vente confirmee ! {v['numero']} vendu a {v['client_nom']} pour {v['total']:,} FCFA")
                        st.balloons()
                with col_non:
                    if st.button("Annuler", use_container_width=True):
                        st.session_state.confirmer_vente = False
                        st.rerun()

    # ══ STOCK ════════════════════════════════════════════════
    elif choix == "Stock" and st.session_state.role == "admin":
        st.markdown('<div class="page-title">Gestion du Stock</div>', unsafe_allow_html=True)
        tab1,tab2,tab3 = st.tabs(["Stock actuel","Ajouter des decodeurs","Modifier une vente"])

        with tab1:
            conn = db()
            df_s = pd.read_sql_query("SELECT numero,statut,affecte_a,client_nom,formule,prix_total,date_ajout,date_expiration FROM decodeurs ORDER BY date_ajout DESC", conn)
            conn.close()
            if not df_s.empty:
                c1,c2 = st.columns([1,2])
                with c1:
                    filtre = st.selectbox("Filtrer par statut", ["Tous","disponible","vendu"])
                with c2:
                    rech = st.text_input("Rechercher un numero ou client")
                if filtre != "Tous":
                    df_s = df_s[df_s['statut']==filtre]
                if rech:
                    df_s = df_s[df_s.apply(lambda r: rech.lower() in str(r).lower(), axis=1)]
                df_s.columns = ["Numero","Statut","Vendeur","Client","Formule","Total FCFA","Date ajout","Expiration"]
                st.dataframe(df_s, use_container_width=True, hide_index=True)
                st.caption(f"{len(df_s)} resultat(s)")
                st.download_button("Exporter en Excel", export_excel(df_s,"Stock"), "stock.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.info("Stock vide.")

        with tab2:
            st.markdown('<div class="scanner-box">Ajouter des decodeurs — Saisie manuelle ou scanner — Maximum 20</div>', unsafe_allow_html=True)
            mode = st.radio("Mode d ajout", ["Saisie manuelle","Scanner"], horizontal=True)
            vendeurs = get_vendeurs()
            v_opts = [f"{v[1]} ({v[0]})" for v in vendeurs]
            v_sel = st.selectbox("Affecter au vendeur", v_opts)
            v_username = vendeurs[v_opts.index(v_sel)][0]

            if mode == "Saisie manuelle":
                nums_input = st.text_area("Numeros de decodeurs (un par ligne ou separes par virgule, maximum 20)", height=160)
                if st.button("Ajouter au stock", use_container_width=True):
                    raw = nums_input.replace('\n',',').replace(';',',')
                    nums = list(set([n.strip() for n in raw.split(',') if n.strip()]))[:20]
                    if nums:
                        conn = db()
                        cur = conn.cursor()
                        ok = doublons = 0
                        for num in nums:
                            cur.execute("INSERT OR IGNORE INTO decodeurs (numero,statut,affecte_a,date_ajout) VALUES (?,'disponible',?,?)",
                                        (num,v_username,datetime.now().strftime("%Y-%m-%d %H:%M")))
                            ok += cur.rowcount
                            doublons += 1-cur.rowcount
                        conn.commit()
                        conn.close()
                        st.success(f"{ok} decodeur(s) ajoute(s), {doublons} doublon(s) ignore(s).")
                    else:
                        st.error("Aucun numero valide.")
            else:
                try:
                    from streamlit_qrcode_scanner import qrcode_scanner
                    if 'scanned' not in st.session_state:
                        st.session_state.scanned = []
                    st.info("Pointez la camera vers le code-barres ou QR code du decodeur.")
                    qr_result = qrcode_scanner(key="qr_scanner")
                    if qr_result and qr_result.strip():
                        num_scanne = qr_result.strip()
                        if num_scanne not in st.session_state.scanned and len(st.session_state.scanned) < 20:
                            st.session_state.scanned.append(num_scanne)
                            st.success(f"Numero detecte : {num_scanne}")
                    if st.session_state.scanned:
                        st.markdown(f"**{len(st.session_state.scanned)} numero(s) scanne(s) :**")
                        for n in st.session_state.scanned:
                            st.markdown(f"- `{n}`")
                        ca_col, cb_col = st.columns(2)
                        with ca_col:
                            if st.button("Enregistrer tous les scans", use_container_width=True):
                                conn = db()
                                cur = conn.cursor()
                                ok = 0
                                for num in st.session_state.scanned:
                                    cur.execute("INSERT OR IGNORE INTO decodeurs (numero,statut,affecte_a,date_ajout) VALUES (?,'disponible',?,?)",
                                                (num,v_username,datetime.now().strftime("%Y-%m-%d %H:%M")))
                                    ok += cur.rowcount
                                conn.commit()
                                conn.close()
                                st.session_state.scanned = []
                                st.success(f"{ok} decodeur(s) enregistre(s).")
                        with cb_col:
                            if st.button("Vider la liste", use_container_width=True):
                                st.session_state.scanned = []
                                st.rerun()
                except Exception:
                    st.warning("Scanner non disponible. Utilisez la saisie manuelle.")

        with tab3:
            conn = db()
            df_mod = pd.read_sql_query("SELECT numero,client_nom,client_tel,formule,prix_total FROM decodeurs WHERE statut='vendu'", conn)
            conn.close()
            if df_mod.empty:
                st.info("Aucune vente a modifier.")
            else:
                num_sel = st.selectbox("Choisir le decodeur vendu", df_mod['numero'].tolist())
                row = df_mod[df_mod['numero']==num_sel].iloc[0]
                c1,c2 = st.columns(2)
                with c1:
                    new_nom = st.text_input("Nom du client", value=str(row['client_nom'] or ''))
                    new_tel = st.text_input("Numero de telephone", value=str(row['client_tel'] or ''))
                with c2:
                    flist = list(FORMULES.keys())
                    fidx = flist.index(row['formule']) if row['formule'] in flist else 0
                    new_formule = st.selectbox("Formule", flist, index=fidx)
                    new_prix = st.number_input("Prix total FCFA", value=float(row['prix_total'] or 0), step=500.0)
                if st.button("Sauvegarder les modifications"):
                    conn = db()
                    cur = conn.cursor()
                    for champ,old,new in [("client_nom",row['client_nom'],new_nom),("client_tel",row['client_tel'],new_tel),("formule",row['formule'],new_formule),("prix_total",row['prix_total'],new_prix)]:
                        if str(old) != str(new):
                            cur.execute("INSERT INTO historique_modifications VALUES (NULL,?,?,?,?,?,?)",
                                        (num_sel,champ,str(old),str(new),st.session_state.user,datetime.now().strftime("%Y-%m-%d %H:%M")))
                    cur.execute("UPDATE decodeurs SET client_nom=?,client_tel=?,formule=?,prix_total=? WHERE numero=?",
                                (new_nom,new_tel,new_formule,new_prix,num_sel))
                    conn.commit()
                    conn.close()
                    st.success("Modifications enregistrees.")

    # ══ REABONNEMENTS ════════════════════════════════════════
    elif choix == "Reabonnements":
        st.markdown('<div class="page-title">Suivi Reabonnements</div>', unsafe_allow_html=True)
        alertes = get_alertes()
        expires = [a for a in alertes if a['statut']=='expiré']
        urgents = [a for a in alertes if a['statut']=='urgent']
        if not alertes:
            st.markdown('<div class="alerte vert">Aucun reabonnement urgent en ce moment.</div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            if expires:
                st.markdown(f"#### Expires ({len(expires)})")
                for a in expires:
                    wa = wa_link(a['tel'],a['client'],a['jours'])
                    st.markdown(f'<div class="alerte rouge"><b>{a["client"]}</b><br>Decodeur {a["numero"]} — Tel {a["tel"]}<br>Expire depuis {abs(a["jours"])} jours<br><a href="{wa}" target="_blank" class="wa-btn">WhatsApp</a></div>', unsafe_allow_html=True)
        with c2:
            if urgents:
                st.markdown(f"#### Bientot expires ({len(urgents)})")
                for a in urgents:
                    wa = wa_link(a['tel'],a['client'],a['jours'])
                    st.markdown(f'<div class="alerte jaune"><b>{a["client"]}</b><br>Decodeur {a["numero"]} — Tel {a["tel"]}<br>Expire dans {a["jours"]} jours<br><a href="{wa}" target="_blank" class="wa-btn">WhatsApp</a></div>', unsafe_allow_html=True)
        st.markdown("#### Tous les abonnements actifs")
        conn = db()
        df_r = pd.read_sql_query("SELECT numero,client_nom,client_tel,formule,date_activation,date_expiration FROM decodeurs WHERE statut='vendu' ORDER BY date_expiration ASC", conn)
        conn.close()
        if not df_r.empty:
            df_r.columns = ["Numero","Client","Telephone","Formule","Date activation","Date expiration"]
            st.dataframe(df_r, use_container_width=True, hide_index=True)
            st.download_button("Exporter en Excel", export_excel(df_r,"Reabonnements"), "reabonnements.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ══ NOTIFICATIONS ════════════════════════════════════════
    elif "Notifications" in choix:
        st.markdown('<div class="page-title">Notifications</div>', unsafe_allow_html=True)
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT message,type,date_creation,lu FROM notifications WHERE destinataire=? OR destinataire='tous' ORDER BY date_creation DESC LIMIT 60", (st.session_state.user,))
        notifs = cur.fetchall()
        cur.execute("UPDATE notifications SET lu=1 WHERE destinataire=? OR destinataire='tous'", (st.session_state.user,))
        conn.commit()
        conn.close()
        if not notifs:
            st.info("Aucune notification.")
        for msg,typ,date,lu in notifs:
            icons = {"vente":"Vente","expiration_24h":"Urgent","expiration_7j":"Attention","dormant":"Stock"}
            label = icons.get(typ,"Info")
            bg = "#ffffff" if lu else "#f9f9f9"
            border = "#e8e8e8" if lu else "#0a0a0a"
            st.markdown(f'<div class="card" style="background:{bg};border-left:3px solid {border};"><b>{label}</b> — {msg}<br><small style="color:#999;">{date}</small></div>', unsafe_allow_html=True)

    # ══ VENDEURS ════════════════════════════════════════════
    elif choix == "Vendeurs" and st.session_state.role == "admin":
        st.markdown('<div class="page-title">Gestion des Vendeurs</div>', unsafe_allow_html=True)
        tab1,tab2,tab3 = st.tabs(["Liste des vendeurs","Ajouter un vendeur","Token recuperation"])

        with tab1:
            conn = db()
            df_vend = pd.read_sql_query("""
                SELECT u.nom_complet,u.telephone,u.role,u.date_creation,
                       COUNT(d.id) as ventes, COALESCE(SUM(d.prix_total),0) as ca
                FROM users u LEFT JOIN decodeurs d ON d.affecte_a=u.username AND d.statut='vendu'
                GROUP BY u.username ORDER BY ca DESC
            """, conn)
            conn.close()
            if not df_vend.empty:
                df_vend.columns = ["Nom complet","Telephone","Role","Date creation","Nombre ventes","Chiffre affaires FCFA"]
                st.dataframe(df_vend, use_container_width=True, hide_index=True)

        with tab2:
            c1,c2 = st.columns(2)
            with c1:
                nu = st.text_input("Identifiant du vendeur")
                nn = st.text_input("Nom complet")
            with c2:
                nt = st.text_input("Numero de telephone")
                np_v = st.text_input("Mot de passe initial", type="password")
            if st.button("Creer le compte vendeur", use_container_width=True):
                if nu and nn and nt and np_v:
                    try:
                        h = bcrypt.hashpw(np_v.encode(),bcrypt.gensalt())
                        conn = db()
                        cur = conn.cursor()
                        cur.execute("INSERT INTO users (username,telephone,password,role,nom_complet,date_creation) VALUES (?,?,?,?,?,?)",
                                    (nu,nt,h.decode(),"vendeur",nn,datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        conn.close()
                        st.success(f"Compte cree pour {nn} — connexion avec le telephone {nt}")
                    except sqlite3.IntegrityError:
                        st.error("Identifiant ou telephone deja utilise.")
                else:
                    st.error("Remplissez tous les champs.")

        with tab3:
            st.markdown("#### Generer un token de recuperation")
            conn = db()
            df_u = pd.read_sql_query("SELECT username,nom_complet,telephone FROM users WHERE role='vendeur'", conn)
            conn.close()
            if df_u.empty:
                st.info("Aucun vendeur enregistre.")
            else:
                u_opts = [f"{r['nom_complet']} ({r['telephone']})" for _,r in df_u.iterrows()]
                u_sel = st.selectbox("Choisir le vendeur", u_opts)
                u_name = df_u.iloc[u_opts.index(u_sel)]['username']
                if st.button("Generer le token"):
                    token = secrets.token_hex(4).upper()
                    expiry = (datetime.now()+timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
                    conn = db()
                    cur = conn.cursor()
                    cur.execute("UPDATE users SET token=?,token_expiry=? WHERE username=?", (token,expiry,u_name))
                    conn.commit()
                    conn.close()
                    st.markdown(f'<div class="token-box">{token}</div>', unsafe_allow_html=True)
                    st.success(f"Token valable 2 heures — expire a {expiry}")

    # ══ RAPPORTS ════════════════════════════════════════════
    elif "Rapport" in choix:
        st.markdown('<div class="page-title">Rapports</div>', unsafe_allow_html=True)
        col_p1,col_p2 = st.columns(2)
        with col_p1:
            date_debut = st.date_input("Du", value=datetime.now().replace(day=1).date())
        with col_p2:
            date_fin = st.date_input("Au", value=datetime.now().date())
        conn = db()
        df_rap = pd.read_sql_query(f"""
            SELECT u.nom_complet,u.username,
                   COUNT(d.id) as ventes, COALESCE(SUM(d.prix_total),0) as ca,
                   MAX(d.date_activation) as derniere_vente
            FROM users u LEFT JOIN decodeurs d ON d.affecte_a=u.username AND d.statut='vendu'
                AND d.date_activation>='{date_debut}' AND d.date_activation<='{date_fin} 23:59'
            GROUP BY u.username ORDER BY ca DESC
        """, conn)
        conn.close()
        if not df_rap.empty:
            st.markdown("#### Classement vendeurs")
            medals = ["1er","2eme","3eme"]
            top3 = df_rap.head(3)
            cols = st.columns(len(top3))
            for i,(_,row) in enumerate(top3.iterrows()):
                with cols[i]:
                    st.markdown(f'<div class="podium-card"><div class="podium-emoji">{"🥇" if i==0 else "🥈" if i==1 else "🥉"}</div><div class="podium-nom">{row["nom_complet"]}</div><div class="podium-stat">{int(row["ventes"])} ventes</div><div class="podium-stat"><b>{row["ca"]:,.0f} FCFA</b></div></div>', unsafe_allow_html=True)

            if st.session_state.role == "vendeur":
                df_rap = df_rap[df_rap['username']==st.session_state.user]

            st.markdown("#### Detail par vendeur")
            for _,row in df_rap.iterrows():
                with st.expander(f"{row['nom_complet']} — {int(row['ventes'])} vente(s) — {row['ca']:,.0f} FCFA"):
                    conn = db()
                    df_dec = pd.read_sql_query(f"SELECT numero,statut,formule,prix_total,date_activation FROM decodeurs WHERE affecte_a='{row['username']}' ORDER BY date_activation DESC", conn)
                    conn.close()
                    total = len(df_dec)
                    vendus_v = len(df_dec[df_dec['statut']=='vendu']) if not df_dec.empty else 0
                    dispo_v = total-vendus_v
                    taux = round((vendus_v/total*100) if total>0 else 0)
                    c1,c2,c3 = st.columns(3)
                    with c1:
                        st.metric("Decodeurs affectes",total)
                        st.metric("Vendus",vendus_v)
                    with c2:
                        st.metric("Disponibles",dispo_v)
                        st.metric("Taux de conversion",f"{taux}%")
                    with c3:
                        st.metric("Chiffre affaires",f"{row['ca']:,.0f} FCFA")
                        if row['derniere_vente']:
                            st.metric("Derniere vente",str(row['derniere_vente'])[:10])
                    if not df_dec.empty:
                        st.dataframe(df_dec, use_container_width=True, hide_index=True)
                        st.download_button(f"Exporter {row['nom_complet']}", export_excel(df_dec,"Rapport"), f"rapport_{row['username']}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"exp_{row['username']}")

    # ══ PARAMETRES ══════════════════════════════════════════
    elif choix == "Parametres" and st.session_state.role == "admin":
        st.markdown('<div class="page-title">Parametres</div>', unsafe_allow_html=True)
        st.markdown("#### Changer le mot de passe")
        old = st.text_input("Ancien mot de passe", type="password")
        new1 = st.text_input("Nouveau mot de passe", type="password")
        new2 = st.text_input("Confirmer le nouveau mot de passe", type="password")
        if st.button("Mettre a jour"):
            if new1 != new2:
                st.error("Les mots de passe ne correspondent pas.")
            elif len(new1) < 6:
                st.error("Minimum 6 caracteres.")
            else:
                conn = db()
                cur = conn.cursor()
                cur.execute("SELECT password FROM users WHERE username=?", (st.session_state.user,))
                res = cur.fetchone()
                if res and bcrypt.checkpw(old.encode(), res[0].encode()):
                    h = bcrypt.hashpw(new1.encode(),bcrypt.gensalt())
                    cur.execute("UPDATE users SET password=? WHERE username=?", (h.decode(),st.session_state.user))
                    conn.commit()
                    st.success("Mot de passe mis a jour.")
                else:
                    st.error("Ancien mot de passe incorrect.")
                conn.close()
        st.divider()
        st.markdown("#### Historique des modifications")
        conn = db()
        df_hist = pd.read_sql_query("SELECT decodeur_numero,champ_modifie,ancienne_valeur,nouvelle_valeur,modifie_par,date_modification FROM historique_modifications ORDER BY date_modification DESC LIMIT 50", conn)
        conn.close()
        if not df_hist.empty:
            df_hist.columns = ["Decodeur","Champ modifie","Ancienne valeur","Nouvelle valeur","Modifie par","Date"]
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune modification enregistree.")
