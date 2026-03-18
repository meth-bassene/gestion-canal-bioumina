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
/* SIDEBAR */
[data-testid="stSidebar"] { background:#0a0a0a !important; }
[data-testid="stSidebar"] * { color:#ffffff !important; }
[data-testid="stSidebar"] .stRadio label { padding:8px 12px; border-radius:6px; display:block; }
[data-testid="stSidebar"] .stRadio label:hover { background:#1a1a1a; }
/* BOUTONS */
.stButton > button { background:#0a0a0a !important; color:#ffffff !important; border:none !important; border-radius:8px !important; font-weight:600 !important; }
.stButton > button:hover { background:#333 !important; }
/* CARDS CUSTOM */
.card { background:#ffffff; border-radius:10px; padding:16px 20px; border:1px solid #e0e0e0; margin-bottom:12px; color:#0a0a0a; }
.card b, .card strong { color:#0a0a0a; }
.stat-card { background:#ffffff; border-radius:10px; padding:16px; border:1px solid #e0e0e0; margin-bottom:8px; }
.stat-label { font-size:0.75rem; color:#666; text-transform:uppercase; margin-bottom:4px; }
.stat-value { font-size:1.8rem; font-weight:800; color:#0a0a0a; }
.stat-sub { font-size:0.78rem; color:#666; }
.stat-vert .stat-value { color:#00b341; }
.stat-rouge .stat-value { color:#e50000; }
.page-title { font-size:1.4rem; font-weight:800; color:#0a0a0a; margin-bottom:20px; padding-bottom:10px; border-bottom:2px solid #0a0a0a; }
.prix-box { background:#0a0a0a; color:#ffffff; border-radius:10px; padding:16px; text-align:center; margin:8px 0; }
.prix-box .plabel { font-size:0.75rem; color:#cccccc; text-transform:uppercase; margin-bottom:4px; }
.prix-box .pmontant { font-size:1.8rem; font-weight:800; color:#ffffff; }
.total-box { background:#00b341; color:#ffffff; border-radius:10px; padding:16px; text-align:center; margin:8px 0; }
.total-box .plabel { font-size:0.75rem; color:#ffffff; text-transform:uppercase; margin-bottom:4px; }
.total-box .pmontant { font-size:2rem; font-weight:800; color:#ffffff; }
.total-box div { color:#ffffff !important; }
.alerte { border-radius:8px; padding:12px 16px; margin:6px 0; font-size:0.88rem; }
.alerte.rouge { background:#fff0f0; border-left:3px solid #e50000; color:#333; }
.alerte.jaune { background:#fffbf0; border-left:3px solid #f5a623; color:#333; }
.alerte.vert { background:#f0fff5; border-left:3px solid #00b341; color:#333; }
.alerte b, .alerte strong { color:#0a0a0a !important; }
.wa-btn { display:inline-block; background:#25D366; color:#ffffff !important; padding:4px 10px; border-radius:6px; font-size:0.8rem; font-weight:600; text-decoration:none; }
.token-box { background:#0a0a0a; color:#ffffff; border-radius:8px; padding:16px; font-family:monospace; font-size:1.4rem; letter-spacing:4px; text-align:center; }
.podium-card { background:#ffffff; border-radius:10px; padding:14px; border:1px solid #e0e0e0; text-align:center; }
.podium-nom { font-weight:700; color:#0a0a0a; margin:4px 0 2px; }
.podium-stat { font-size:0.8rem; color:#666; }
.scanner-box { background:#f9f9f9; border:2px dashed #cccccc; border-radius:10px; padding:20px; text-align:center; color:#0a0a0a; }
.login-card { background:#ffffff; border-radius:14px; padding:36px; border:1px solid #e0e0e0; box-shadow:0 4px 20px rgba(0,0,0,0.08); margin-top:40px; }
.login-logo { font-size:1.8rem; font-weight:800; color:#0a0a0a; }
.login-sub { color:#666; font-size:0.85rem; margin-bottom:20px; }
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


LOGO_B64 = "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"

for k,v in [('connecte',False),('mode_token',False),('confirmer_vente',False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ═══ LOGIN ═══════════════════════════════════════════════════
if not st.session_state.connecte:
    col1,col2,col3 = st.columns([1,1.1,1])
    with col2:
        st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" style="width:100%;display:block;">', unsafe_allow_html=True)
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
        st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" style="width:100%;display:block;">', unsafe_allow_html=True)
        st.markdown(f"""
        <hr style="border-color:#1a1a1a;margin:8px 0 12px;">
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
