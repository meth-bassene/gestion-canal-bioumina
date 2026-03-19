import streamlit as st
import pandas as pd
import bcrypt
import os
import secrets
import io
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

try:
    from streamlit_cookies_manager import EncryptedCookieManager
    cookies = EncryptedCookieManager(prefix="appstock_", password="appstock_secret_key_2026")
    if not cookies.ready():
        st.stop()
    USE_COOKIES = True
except:
    USE_COOKIES = False

st.set_page_config(page_title="AppStock", page_icon="📡", layout="wide", initial_sidebar_state="expanded")

FAV_B64 = "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"
st.markdown(f'''<link rel="shortcut icon" href="data:image/png;base64,{FAV_B64}">''', unsafe_allow_html=True)

FORMULES = {"Access": 5500, "Access+": 16500, "Evasion": 11000, "Tout Canal+": 25000}
PRIX_DECODEUR_DEFAULT = 5000
PROMOS = {"Aucune promo": 0, "Promo -1000 FCFA": 1000, "Promo -3000 FCFA": 3000}

st.markdown("""
<style>
/* MOBILE FIRST — optimisé téléphone */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap');

* { font-family:'DM Sans',sans-serif; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }

/* APP */
.stApp { background:#f4f4f4 !important; }

/* SIDEBAR — grande et tactile */
[data-testid="stSidebar"] { background:#0a0a0a !important; }
[data-testid="stSidebar"] * { color:#ffffff !important; }
[data-testid="stSidebar"] .stRadio > div { gap:2px !important; }
[data-testid="stSidebar"] .stRadio label {
    padding:16px 20px !important;
    border-radius:10px !important;
    display:block !important;
    font-size:1.05rem !important;
    font-weight:500 !important;
    margin-bottom:2px !important;
    cursor:pointer !important;
    min-height:52px !important;
    display:flex !important;
    align-items:center !important;
    transition:background 0.1s !important;
}
[data-testid="stSidebar"] .stRadio label:hover,
[data-testid="stSidebar"] .stRadio label:active { background:#1f1f1f !important; }

/* BOUTONS — grands et tactiles */
.stButton > button {
    background:#0a0a0a !important;
    color:#ffffff !important;
    border:none !important;
    border-radius:10px !important;
    font-weight:600 !important;
    font-size:1rem !important;
    min-height:52px !important;
    padding:12px 20px !important;
    width:100% !important;
    cursor:pointer !important;
    transition:background 0.15s !important;
}
.stButton > button:hover { background:#333 !important; }
.stButton > button:active { background:#555 !important; }

/* INPUTS — grands et lisibles */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background:#ffffff !important;
    color:#0a0a0a !important;
    border:2px solid #e0e0e0 !important;
    border-radius:10px !important;
    font-size:1rem !important;
    padding:12px 14px !important;
    min-height:50px !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color:#0a0a0a !important;
    outline:none !important;
}
.stSelectbox > div > div {
    background:#ffffff !important;
    color:#0a0a0a !important;
    border:2px solid #e0e0e0 !important;
    border-radius:10px !important;
    font-size:1rem !important;
    min-height:50px !important;
}

/* LABELS — noir sauf dans sidebar et éléments blancs sur fond noir */
div[data-testid="stWidgetLabel"] p { color:#0a0a0a !important; font-weight:500 !important; font-size:0.95rem !important; }
div[data-testid="stMarkdownContainer"] p { color:#0a0a0a !important; }
div[data-testid="stMarkdownContainer"] h4 { color:#0a0a0a !important; }
/* Garder blanc dans sidebar */
[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p { color:#ffffff !important; }
[data-testid="stSidebar"] div[data-testid="stWidgetLabel"] p { color:#ffffff !important; }
/* Garder blanc dans boutons */
.stButton > button p, .stButton > button span, .stButton > button div { color:#ffffff !important; }
/* Garder blanc dans prix-box et total-box */
.prix-box p, .prix-box span, .prix-box div { color:#ffffff !important; }
.total-box p, .total-box span, .total-box div { color:#ffffff !important; }
/* Garder blanc dans token-box */
.token-box { color:#ffffff !important; }

/* CARDS */
.card { background:#ffffff; border-radius:12px; padding:18px 20px; box-shadow:0 1px 4px rgba(0,0,0,0.06); margin-bottom:14px; border:1px solid #e8e8e8; }
.card * { color:#0a0a0a !important; }

/* STAT CARDS */
.stat-card { background:#ffffff; border-radius:12px; padding:18px; border:1px solid #e8e8e8; margin-bottom:8px; }
.stat-label { font-size:0.72rem; color:#666; font-weight:500; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:6px; }
.stat-value { font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#0a0a0a; }
.stat-sub { font-size:0.78rem; color:#666; margin-top:2px; }
.stat-vert .stat-value { color:#00b341; }
.stat-rouge .stat-value { color:#e50000; }

/* PAGE TITLE */
.page-title { font-family:'Syne',sans-serif; font-size:1.4rem; font-weight:800; color:#0a0a0a; margin-bottom:20px; padding-bottom:10px; border-bottom:2px solid #0a0a0a; }

/* PRIX/TOTAL */
.prix-box { background:#0a0a0a; color:#ffffff; border-radius:12px; padding:18px; text-align:center; margin:10px 0; }
.prix-box .plabel { font-size:0.75rem; color:#cccccc; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px; }
.prix-box .pmontant { font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#ffffff; }
.total-box { background:#00b341; color:#ffffff; border-radius:12px; padding:18px; text-align:center; margin:10px 0; }
.total-box .plabel { font-size:0.75rem; color:#ffffff; text-transform:uppercase; margin-bottom:4px; }
.total-box .pmontant { font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; color:#ffffff; }
.total-box div { color:#ffffff !important; }

/* ALERTES */
.alerte { border-radius:10px; padding:14px 16px; margin:8px 0; font-size:0.9rem; }
.alerte.rouge { background:#fff0f0; border-left:4px solid #e50000; color:#333; }
.alerte.jaune { background:#fffbf0; border-left:4px solid #f5a623; color:#333; }
.alerte.vert { background:#f0fff5; border-left:4px solid #00b341; color:#333; }
.alerte * { color:#333 !important; }

/* WHATSAPP */
.wa-btn { display:inline-block; background:#25D366; color:#ffffff !important; padding:8px 16px; border-radius:8px; font-size:0.9rem; font-weight:600; text-decoration:none; margin-top:6px; }

/* TOKEN */
.token-box { background:#0a0a0a; color:#ffffff; border-radius:10px; padding:18px; font-family:monospace; font-size:1.4rem; letter-spacing:4px; text-align:center; margin:12px 0; }

/* PODIUM */
.podium-card { background:#ffffff; border-radius:12px; padding:16px; border:1px solid #e8e8e8; text-align:center; }
.podium-nom { font-family:'Syne',sans-serif; font-weight:700; font-size:1rem; color:#0a0a0a; margin:6px 0 2px; }
.podium-stat { font-size:0.85rem; color:#666; }

/* SCANNER */
.scanner-box { background:#f9f9f9; border:2px dashed #cccccc; border-radius:12px; padding:24px; text-align:center; color:#0a0a0a; }

/* LOGIN */
.login-card { background:#ffffff; border-radius:16px; padding:36px 28px; border:1px solid #e0e0e0; box-shadow:0 4px 20px rgba(0,0,0,0.08); margin-top:30px; }
.login-logo { font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#0a0a0a; letter-spacing:-1px; }
.login-sub { color:#666; font-size:0.85rem; margin-bottom:20px; }

/* TABS */
.stTabs [data-baseweb="tab-list"] { background:#ffffff !important; border-radius:10px; padding:4px; border:1px solid #e8e8e8; gap:4px; }
.stTabs [data-baseweb="tab"] { 
    color:#666 !important; font-weight:600; border-radius:8px; 
    min-height:44px !important; font-size:0.9rem !important; 
    background:#ffffff !important;
}
.stTabs [data-baseweb="tab"]:hover { 
    background:#f0f0f0 !important; 
    color:#0a0a0a !important; 
}
.stTabs [aria-selected="true"] { 
    background:#0a0a0a !important; 
    color:#ffffff !important; 
}
.stTabs [aria-selected="true"]:hover { 
    background:#222222 !important; 
    color:#ffffff !important; 
}
.stTabs [aria-selected="true"] p,
.stTabs [aria-selected="true"] span { color:#ffffff !important; }
.stTabs [aria-selected="false"] p,
.stTabs [aria-selected="false"] span { color:#666666 !important; }

/* DATAFRAME */
[data-testid="stDataFrame"] { border-radius:10px; overflow:hidden; }

/* MOBILE RESPONSIVE */
@media (max-width: 768px) {
    .stat-value { font-size:1.5rem !important; }
    .page-title { font-size:1.2rem !important; }
    .stButton > button { min-height:56px !important; font-size:1.05rem !important; }
    .stTextInput input, .stNumberInput input { min-height:54px !important; font-size:1.05rem !important; }
    [data-testid="stSidebar"] .stRadio label { min-height:58px !important; font-size:1.1rem !important; }
}
</style>
""", unsafe_allow_html=True)

def db():
    DATABASE_URL = st.secrets["DATABASE_URL"]
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY, username TEXT UNIQUE, telephone TEXT UNIQUE,
        password TEXT, role TEXT DEFAULT 'vendeur', nom_complet TEXT, date_creation TEXT,
        token TEXT, token_expiry TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS decodeurs (
        id SERIAL PRIMARY KEY, numero TEXT UNIQUE, partenaire TEXT DEFAULT 'Canal+',
        statut TEXT DEFAULT 'disponible', affecte_a TEXT, client_nom TEXT, client_tel TEXT,
        formule TEXT, prix_formule REAL DEFAULT 0, prix_decodeur REAL DEFAULT 0,
        promo REAL DEFAULT 0, prix_total REAL, date_ajout TEXT, date_activation TEXT, date_expiration TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS historique_modifications (
        id SERIAL PRIMARY KEY, decodeur_numero TEXT, champ_modifie TEXT,
        ancienne_valeur TEXT, nouvelle_valeur TEXT, modifie_par TEXT, date_modification TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id SERIAL PRIMARY KEY, message TEXT, type TEXT,
        destinataire TEXT DEFAULT 'tous', lu INTEGER DEFAULT 0, date_creation TEXT)''')
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        h = bcrypt.hashpw("Madinatou1432".encode(), bcrypt.gensalt())
        c.execute("INSERT INTO users (username,telephone,password,role,nom_complet,date_creation) VALUES (%s,%s,%s,%s,%s,%s)",
                  ("admin","000000000",h.decode(),"admin","Administrateur",datetime.now().strftime("%Y-%m-%d")))
    else:
        h = bcrypt.hashpw("Madinatou1432".encode(), bcrypt.gensalt())
        c.execute("UPDATE users SET password=%s WHERE username='admin'", (h.decode(),))
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
    c.execute("SELECT COUNT(*) FROM decodeurs WHERE statut='vendu' AND date_activation LIKE %s", (f"{today}%",))
    vj = c.fetchone()[0]
    conn.close()
    return dispo, vendus, ca, vj

def get_ventes_jour():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = db()
    df = pd.read_sql(f"""
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
    c.execute("SELECT numero,affecte_a,date_ajout FROM decodeurs WHERE statut='disponible' AND date_ajout<=%s", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def notif_count(user):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM notifications WHERE lu=0 AND (destinataire=%s OR destinataire='tous')", (user,))
    n = c.fetchone()[0]
    conn.close()
    return n

def push_notif(message, type_n, destinataire="tous"):
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO notifications (message,type,destinataire,date_creation) VALUES (%s,%s,%s,%s)",
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


LOGO_B64 = "iVBORw0KGgoAAAANSUhEUgAAAqgAAAEsCAIAAACAE9ZYAAAfP0lEQVR4nO3de1xUdf7H8RkYkIsioFmC5AVCSlaT8LZtIuT22LKsyCxNWbQePbb7ulmm7pbdH9ta28VsH6XlJa+pWWHZWg+1JNe84AUNU1ARxAtiYAIDw8zvj3n8ZmeZOV/OOXNmzsB5Pf8qzvfyOceB95y72eFwmAAAgDGE6F0AAAAIHIIfAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA0hwOh94lAEAbQvQuAOggnKlP9gMIcgQ/AAAGQvADGnDf0WenH0AwI/gBX3kmPdkPIGhZ9C4AgPZc3zzMZrO+lQAINuzxAz6R2rlnpx9AcCL4AfXE6U72AwhCBD+gkpxcJ/sBBBuCHwAAAyH4ATXk78qz0w8gqBD8gGJKs5zsBxA8CH4AAAyE4AeUUbf7zk4/gCBB8AMK+JLfZD+AYEDwAwBgIAQ/IJfvu+zs9APQHcEPyKJVZpP9APRF8ANt0zatyX4AOiL4AQAwEIIfaIM/dtDZ6QegF4IfEPFfQpP9AHRB8AMAYCAEPyDJ3zvl7PQDCDyL3gUAwctsNnv+0D2tvTYAgGDGHj+gAKkPoL0j+AG5ODIPoAMg+AFZWqU+u/sA2imCH1CM1AfQfhH8QNs4tQ+gwyD4gTZwah9AR0LwAwqwuw+gvSP4AREO8gPoYAh+QBIH+QF0PAQ/IAu7+wA6Bh7ZC4NSujfvtT3fBgC0O+zxAwBgIAQ/AAAGQvADAGAgnOMHAD317NkzJycnMzPzuuuuu+KKK7p27RobG2s2m+vr6xsaGmpqaiorKysqKk6cOHHw4MHi4uIjR460tLToXbViqampWVlZQ4YMueqqq3r37h0fHx8VFWU2mxsaGmpra8vLy8vKynbt2lVYWLh7927/3VBjNpszMjJGjBhx3XXXJScnJyUlxcXFRUZGms3murq62traM2fOFBcX79+//8cff9y5cye39gAdh0MLeq+EJD9VaDabT5w40eZmSU5OVjH48OHDlW7/xsbG06dPHz58eNu2bW+//XZeXl6/fv2CecZWcnJy1q1b19zcrKiGhoaG77///tVXXx0zZkx4eLjnsFu2bFG6Xupce+21ba5jfHz8jBkzDh06JH/YysrK119/vW/fvqo3rFcDBgyYN2/eqVOn5FdSVVX1wQcfZGVlCYYVf4rmzp0rp7a4uLhdu3aJi5k1a5ZGWwIwKvm//AJ6r4QkP1WYk5MjZ7M8//zzKgZXEcNebd68eeLEiRZL24czAz+jS1xc3JIlS3yfOi0tzXPwIAn+qKio55577tKlS+oGb2lpWbBgweWXXy5/q0pJT08vKCjwZU337Nkzfvx4r4P7HvzdunXbs2ePuIAZM2b4vh0Ao/Plr4CL3ishyU8VLl68WM5mKSsrU3Gjo1Yx7LRr16709PRgm9EpISGhtLRUk0mDNvgzMzOPHDni+xQ1NTW5ublytqpXYWFhL730ks1m872SkpISr1P4GPzdu3fft2+feOonn3xS9RYA8F++/yFwGCz4o6OjL168KHPLjBw5Uun42saww+GwWq0TJkwIqhlNJlNcXFxxcbFWMwZn8I8fP95qtWo40Zw5c+R+jNx07969sLBQqxr8Efw9evQ4cOCAeN4///nPKtYdgBea/C3QeyUk+aPCvLw8+Vtm4cKFSsfXPIYdDkdzc/PYsWODZ0aTyfTuu+9qOF0QBv/kyZNbWlo0n+u1115T9HFKSEjQ5JCDi+bBf8UVV7R56cOjjz6qaK0BiGjyt0DvlZDkjwq//fZb+VumtrY2MjJS0fj+iGGHw/Hrr78mJiYGyYz9+/dXeimfWLAFf3Z2dlNTk5+me+SRR2R+lmJjY9vck1ZK2+BPSEgoKSkRdLTb7Q8//LDM9VWK+/gBtC0pKWnUqFHy28fExNx5551+K0eB6OjoV155JUhmzM/PF1wDWFFR8cILL2RnZyclJUVHR1sslu7du6empt54441PPfXUypUrT5065beqNdCtW7dly5aFhYWJm23atGnq1KkDBgyIi4vr3Llzampqbm7uqlWrrFaruOMbb7wxaNAgOZUsWrRIzvUWe/bsef7552+44Ya+fftGRUXFxMSkpKT89re/nTZt2pdffvnrr7/KmUuFxMTELVu29O/fX6qBw+H405/+NH/+fD8VABiUJjsBeq+EJM0rnDVrltKNs3HjRkVTKN1zioyMTElJeeCBB/bv3y+uxG639+rVKxhmFFzGtXLlyoiICPEmMpvNQ4cOfeWVV44dO+bs5XWPX460tDRB/YsWLVIx5qJFi8Sbpby8/KabbpLqfs011+zYsUM8wp49e9q8bvSBBx4QD+JwOEpKSm699VbxOFFRUQ888IDrfIFWe/xJSUlHjx4VdLHb7ffff7+4NgBqtPmnQQ69V0KS5hUKDkva7XavP7fZbAkJCfKnUH2uNCwsbOHCheJ/qQcffFD3Gbt06SLV+OzZs22mvruQkJCxY8f++9//Tk1Nld/LnebBP3DgQPGp/fLycq9fhtxFRERs3bpVvGHvu+8+wQhdu3Y9e/aseIQNGzbIPw9lsVgeffTRX375RZPg7927d1lZmaB9S0tLfn6+zNoAKCP+0yCT3ishSdsKhw0bJrUFzp49u3r1aqmlTz31lPxZfLk6OjQ0dO/evYLu69at033GlJQUqcarVq2Sv6E0oXnwL126VDCg1WodMGCAnHG6du16/PhxwVD79u0TdJ89e7agr8PhKCgoaPNkhKdevXq99957XhfJ/xT17dtXvGo2m23SpElKa1OBc/wA2vDHP/5RatGaNWuWLVumoqO2Wlpa5s2bJ2jgy/P1tJrxsssuk2rc2NioTVk6iYuLu/vuuwUN3nrrrYMHD8oZqra29umnnxY0GDhw4IgRI7wuslgs4gsAz5w5k5+f39zcLKcSdxUVFQ899JDSXu6Sk5O3bt3au3dvqQYtLS15eXkff/yxL7PIRPADEAkPD7/nnnuklq5YsWLjxo21tbVelw4YMCAjI8Nvpf2PHTt2CJb26NFD9xlDQiT/3o4cOVLRg/+Cza233tqpUyeppQ0NDS+//LL80VavXi3erb/rrru8/jw7O7tnz56CjtOmTauurpZfiVZSU1O3bt2alJQk1cBms02cOHH58uWBqYfghz6ch7Z0nF2vqdud2267LT4+3uuiioqKbdu2Wa3W9evXS3UP2E7/L7/8IlgaGxur+4yCyOnTp8/777+v9AbI4HHLLbcIlm7YsEHqq6EUwWEkk8l08803e/35HXfcIehVWVn5ySefKCpDE2lpaVu2bJG6w9NkMtlstgkTJqxevTpgJRH80IErd3WJf1JfEUFyO8/um0ymlStXSrWZMGGCilOqKsTFxQmWXrhwQfcZT548KTjIPGXKlNLS0pdeeikzM1NwbCA4DRs2TLB0zZo1SgcUd7n66qtjYmI8f37DDTcIei1cuNBmsymtxEfO1Bcch2hubh4/fryKTeSLdvbxQgfgmbuua1t0mR0Cl1122R/+8Aeppa68/+abb86fPy81gtT+mbakzvs6nT17VvcZ6+vrd+7cKejSs2fP2bNn79y588KFC5s2bXr11Vdzc3MFx4eDRNeuXcVv0tu9e7fSMY8dO1ZTUyO11Gw2ez47KCoq6pprrhGMuXnzZqVl+G7MmDGC9ww1NTWNGzfu008/DWRJJoIf+mp1S66+x//haeLEiVL766Wlpa4Ys9lsa9eulRokLy/PL8W5cd5zJWhw7NixYJhR5uHcmJiY0aNHP/PMM2vXri0vLy8vL1+yZMnUqVP9caWC78Spf+nSpdLSUhXDHjhwQNGkffv2DQ0NlWrf0tIi/tYVeFarNTc39/PPPw/81AQ/Aso9152pb/5/7m38FP98q1BKcJy/1R1oghvSBFcJaCIsLGzBggXiJ7UpfZqQn2b84IMPzp07p3S6pKSkyZMnL1y4sLKysqCg4Pbbb1c6gl+J784/ceKEut+7srIyRZNeeeWVgvbl5eWXLl1SUYafWK3WO++8c8OGDbrMTvAjcMS///6Of1JfqfT09MGDB0stXbFihfv/btmy5fTp015biu8LUC0iIsL5HL2ioiLxJYQOh+PLL78Mhhnr6+unTJmi+qNosVjGjBmzfv36H3/88frrr1c3iOa6du0qWFpXV6du2IsXLwqWep7jF19yIThxEHiNjY1jx4796quv9CqA4EeAtPpjJ/XcTa/xr3lmq3hbvAEJsu3gwYPFxcXuP7Hb7YJLpn2/tv/JJ59s9bSThoaGI0eOfPDBB20+GWbp0qUVFRVBMuOGDRueeOIJu92utB53Q4YM2bp161/+8hdfBtGK+GYEcX4LiL8xeE4qLkN8C0aA6X5Ok+CHDtrM3Vbxb/L5V8XzFAPEQkNDBc9G9XoZv+Bo/7BhwwSvJPGr+vr6WbNmBdWM77zzzu23337mzBlfZgkNDX399dcff/xxXwYJZm0eINRwtACLjIz8/PPPBa8t8DeCH4GgLne1Ov0fVL/z7cXvf/97wT1IXoP/hx9+KC8vl+oSgEv8PLW0tEyaNKmysjLYZiwoKEhNTf373/+u9Ab3Vl5//XXP69sDrKGhQbC0S5cu6oYVn0Gor69XVIb4REDgRUREfPbZZ4JbZvyK4Iff+Z67Gh7/Z3dfJsHB+d27dx89etTz5w6HQ3DV+uTJkwO88Zubm/Pz8wN5r5SiGevq6p555pmEhISpU6d+9dVX6i49s1gszz77rIqOGhIfk/d6w70c4m8MnpOKD+YHW/CbTKaIiIj169cH5mZXIKBanSXVfMA2x5Rq6TmOCr6vjp/4WGFMTEx9fb3UWk+fPl2qY2ZmpmBz5eTkCCYVv+xEqaKiojZ3hQM/o0B4eHhWVtbf/vY35yOQ5c9rt9u7deumdDoNX9IzePBgwVAXL15U94Vv8+bNgmE9v5imp6cL2jc3N0dFRakoo00+fooaGxvFzz0E2plWH/HADy5o48vvqp/WSEM+Vih4o7ndbhc/Usb1/nJPixcvFnTUKoa/++67yZMny3n0feBnlCkkJGTQoEHTpk3btGmTzWZrs4Dc3FylU2gY/LGxseLykpOTlZZnMpmqq6sFY2ZlZbVqHx0dLX4vsGcXTYg/RatWrSotLRVvH6vVeuutt/qjNkAH7h/uAEzhEEa7uKM6flop3/lY4ffff6/J9mnl4sWL0dHRUpOqiGGr1Xr27NkjR44UFhbOmzcvPz9fUcYEfkYVEhMT33vvPbvdLqjqueeeUzqstq/lPXbsmGC08ePHKy2vT58+ggHtdrvXKwAOHDgg6DVnzhylZcjR5mt5e/XqdfToUUEbh8NhtVpvu+02f5QHBJT7xzqQc7lmFBcg/j2Uyd/rpZovFfbr108cM74QXOIn/73mWgn8jKrNmjVLUOrbb7+tdEBtg3/lypWC0VS8fmb69OmCAQ8dOuS11/z58wW9Tp48KXi0n2pyPkWJiYmCI2FOVqt17NixmpfnFRf3wS8cgQ1Fr7f/uS8NZDHtXV5env+2mC7X9ncAc+fO/fXXX6WWdu7cOZDFeBI/H2nMmDFKL/ET3EpqMpmkHn0jeEukyWTq1avXuHHjFJWhlcrKyqysrJ9//lnQJjw8fM2aNeIXDGqF4If2WqW+uhQRfzv2SqPyDc1sNk+ePNl/42dnZwf/W2eCUFNTk9c7KZz88e5BRQoKCqxWq9TSqKiomTNnyh/trrvuEl8mKfViiM2bN1dVVQk6/vOf/1RxIaQmTp06lZ2dffjwYUGbsLCw1atX33nnnf4uhuCHxjRJfQ3pXkD78rvf/a5fv37+Gz8kJGTSpEn+Gz/Ibdy4ccyYMer6xsbGSi2qrq5WWZBGampqxC+WnTZtWlpampyhYmJi/vGPfwgaHDhw4IcffvC6qLm5+b333hP07dmz54cffqjiMszExMT58+cr7dWKM/tLSkoEbZzZf9ddd/k4lxjBDz/SPXR1L6Dd8f3ZusEwRdAaPnx4QUHBnj17xo0bJ/XaQ6+GDh3ap08fqaUnT57UoDjfzJ07V3DUrVOnThs3bkxISBAP0qlTp88++0z8uj/x14J33nlH/DVo7Nix69ati4iIEFfiEhoa+vDDDx88eFB8M6pMVVVV2dnZP/30k6CNxWJZuXKlXmclAMU0PPCu4lC/ooP//h5fX+oqjIyMVHQHuWpDhw71nN0IF/f98ssvrvHPnTv3zjvvDBkypM1eqamp4svCExMTlVai7cV9TkuWLBGM6XA4jh8/Pnr0aEFJ27dvF49QVFQUEtLG/uqDDz4oHsThcBw6dKjNu+cjIiLy8/MPHz7s7CK1p67iU3T55ZcfPHhQXGFzc7OKuyGAQGv1wdV2NHV0HF9f6iqcMGGCYGUVHX6Mj49vamqSGurdd9/17GK04Hepqqpau3bt9OnTs7Ozr7nmmh49elgslsjIyD59+owdO3bBggWNjY2COg8ePKiiEn8Ef/fu3U+fPi0Y1unrr7/Oz89PS0uLiYmJiopKTk6+4447li9fLl5Nh8PR1NQkeF2kuy+++KLNMhwOx65du5599tnrr7++d+/ekZGRnTt37tu37/Dhwx977LHPPvus1ZdgDYPfZDL16NGjuLhYXJ7NZvPHay0BzbT6yGo+oDo6jq8vdRVu3LhRak3r6urkHx112rBhg9Ro58+fDw8Pb9XesMHvo0ceeURFJf4IfpPJNHr06ObmZs3X0Un+G4ni4+MPHTqk7ezaBr/JZLrsssv2798vntRms02YMEHNv4QQ5/ihPc6st0c9e/YUHIZdv359Y2OjogEFL+uLj4/nUWWaKCsre//99/Wu4r+++eYb55F2zUd+88035T+uoKam5qabbiorK9O8DA2dO3cuJydn//79gjahoaFLly6dOHGitlMT/NCAg5vm279JkyYJHm+yYsUKpQOuX79ecIsXN/T7rqGhIT8/v7m5We9C/sdHH300adIkbat65ZVXpk2bpqhLRUXFiBEjduzYoWEZmquurs7Jydm3b5+gTWho6JIlS7S9F4bgh6/88e0egSdI4vPnz2/atEnpgHV1dVIPWjGZTLfcckv37t2VjgkX58Vf33//vd6FeLF8+fIbbrhBkx3u2tra8ePHz549W0Xfs2fPjhw58rXXXrPb7b5X4ifnz5/PyckpKioStAkNDV28eLGGD9gg+OETR5DdtQ91MjIy0tPTpZauWbPGZrOpGHblypVSi8LCwvxx8jLIPffcc//5z398/668e/fuzMzMgoICTaryhx07dgwcOPCll15qaGhQN4Ldbl+8ePHVV1/9ySefqC6jqalpxowZGRkZGzduVD2IyWQqKipS8UIEmWpqakaPHr1nzx5Bm5CQkEWLFhn5VlgEi1bXofh1cHV0HF9fSit86623BKs5atQodWVER0dfunRJathdu3a5NzbCxX1OCQkJDz/88Jo1a6qqqgQFeLLb7Zs3b87Ly/P9mfN+urjPU7du3WbOnFlSUiJ/NU+dOvXGG29o/vajgQMHzp8/X859By5VVVULFiwQv9ZPq09RXFzcrl27xPW0tLRMmTLF903B/hnUc/jz1L5Di1gVVOXv8fXlWrugrRBOKSkpQ4YMueqqq1JSUpKTky+//PLOnTt37tw5MjKyoaGhrq6urq6usrJy7969RUVF3333XXl5ud4lq9S/f/9Ro0ZlZmampqZeeeWV8fHxUVFRZrO5oaGhtrb25MmTpaWlu3fvLiws3Llzpya/nl6ZzeYhQ4aMGDEiIyMjOTk5KSkpNjY2MjLSZDJdvHixtrb2zJkzxcXF+/fv37Fjh18r0RF/FKCSX1PfRPD7huAHIIVz/FCjQ34LBgAjIPihmIML+gCg3SL4oQypDwDtGsEP9Uh9AGh3CH4o4O8L+gAA/kbwQy4u6AOADoDghyyc2geAjoHgh2KkPgC0XwQ/2sapfQDoMAh+tIFT+wDQkRD8aIP7Lj67+wDQ3hH8aJsz70l9dABhYWFz5swpLS21Wq2HDx9++eWXO3fu7FxUXV3t/ia0tLS0iRMn/vTTT5cuXSosLMzKyoqIiPB8YdqWLVucfZ3vNe7UqdNrr71WWVlptVr3799/9913u6aurq7evXu36/fo9OnTaWlprcpz1mCz2aqqqtauXZuZmSlVW6uOMksVlBcWFvbCCy8cO3asoaFh7969kyZNck3tXLWoqKivv/56wYIFISH/ExxSHbt162a1Wt98881WKyi1EaTaC14YDaBDEb+eUiYdx9dX8Feol48//njHjh3Dhw+Pjo5OSUmZOXPmfffd51zUKmP69OlTX19/8803R0ZGDhs2bOnSpa5F11577enTp92HdfVdvnz59u3bBw4c2KVLl3Hjxl24cCE3N9fV5vjx4/fcc4/zf6WCPz093WKx9OvX78UXX6yvrx84cKBnba3IL1VQnnPLDB06NDo6Oj09fcmSJd26dXNN3bVr123btr3xxhueOwBSHZ944olPP/20qqoqPDzcfQWlNoJUe6kVLykpiY2NldomANoffwezv8fXV/BXqIurrrrKarX26tXL69JWGTN8+PDjx497bSkV/CkpKa3Gf+KJJ4qKilxt8vLyfv75Z4vFYhIGv+t/ly1b9tFHH3n+vBWZpQrKE2yZ6urqnJycoqKiOXPmeC4VdNy7d++IESO++OKLcePGuY8mtRGk2hP8muNQPwCjGDx4cGlpaUVFhVSDAwcOOL8w2Wy2nTt3Hjhw4Ntvv50xY0ZWVlZoaGib42dkZBw9etR9/M2bNw8aNMjV97vvvjt69Oj9998vs+CtW7cOGDDAs7ZWzWSWKihv8ODBrRa5W7169eeff+41+KU6ZmRkREREbN++fdGiRVOnTnVf5HUjCNpDcwQ/VOrYe8zoqFyfuuHDhzs/hIsWLXIt/c1vfmM2m81ms8ViaWlpue222x577LFz585NmzatsLAwMjLS9wJmzpz517/+VeZQ7sfV3Wtr1cz3UsVX8Hz55Zf33ntvz5495XecMmWKc8N+8cUXmZmZiYmJ7ks9N4K4vbvi4mLnP1z//v0vXLjg/G/XhRoA/Mjfwd/ex9dX8FeoC+dxafdQmT59uiv4xYfTDx06dPvttzv/W+pQv+f4jz/+uPuh/j59+phMpmXLlj399NNyDvUvX778ww8/bLM2maUKyvNc1KqkmTNnlpSUeGa/146dOnU6f/68+2/KrFmzBBtB3J5D/UCw8Hdwtvfx9RX8FerFeXXbsGHDoqKi4uLi5s2b5zyJbvLImOuvv/7NN99MS0uLiIgYPXr0pUuXhg0b5lwkuLhv1apV27ZtS09P79KlS25ubk1NjeuMtSvz+vXrd/r06draWsHFfX379n3hhRfq6+sHDRrkWVsr8ksVlLdixYrt27dnZmZGRUWlp6cvXrzY/eI+k8k0a9askpKSK664otXsnh3vv//+wsJCV4ORI0ceOXJEsBHGjx8vaE/wA8HC38HZ3sfXV/BXqJfw8PAXX3zx2LFjVqu1rKzsX//6l2svttUtczfeeONjjz126NChhoaGn3/++fHHH3cNIgj+iIiIuXPnnjp1qqmpqbi4+N5773Vv48w8k8k0b948h7e78ly38505c2bdunVSt/ONGjXKvZfFYpFZqqC88PDwl19++cSJE42Njfv27Zs8eXKrVTOZTLNnz/7pp59aZb9nx6+++uqhhx5yNTCbzWVlZSNHjpTaCOL27ivunvQEv2rcmQ2VNAkVwZnF9j6+vlxrF7QVAtALF/cBAGAgBD8AAAZC8AMAYCAEPwAABkLwAwBgIAQ/AAAGQvADAGAgBD8AAAZC8AMAYCAEPwAABkLwAwBgIAQ/AAAGQvADAGAgBD8AAAZC8AMAYCAEPwAABkLwAwBgIAQ/AAAGQvADAGAgBD8AAAZC8AMAYCAEPwAABkLwAwBgIAQ/AAAGQvADAGAgBD8AAAZC8AMAYCAEPwAABkLwAwBgIAQ/AAAGQvADAGAgBD8AAAZC8AMAYCAEPwAABkLwAwBgIAQ/AAAGQvADAGAgBD8AAAZC8AMAYCAEPwAABkLwAwBgIAQ/AAAGQvADAGAgBD8AAAZC8AMAYCAEPwAABmLRuwAA2jObzXqXACBIsccPAICBEPwAABgIwQ8AgIEQ/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUMDscDr1rAAAAARKidwEAACBw/g9gV9FZ0FhHegAAAABJRU5ErkJggg=="

for k,v in [('connecte',False),('mode_token',False),('confirmer_vente',False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# Toujours forcer mode_token à False au démarrage
st.session_state.mode_token = False

# Restaurer session depuis cookies si disponible
if USE_COOKIES and not st.session_state.connecte:
    try:
        if cookies.get("user") and cookies.get("user") != "":
            st.session_state.connecte = True
            st.session_state.user = cookies["user"]
            st.session_state.role = cookies["role"]
            st.session_state.nom = cookies["nom"]
            st.session_state.mode_token = False
    except:
        pass

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
                    cur.execute("SELECT password,role,nom_complet,username FROM users WHERE telephone=%s OR username=%s", (tel,tel))
                    res = cur.fetchone()
                    conn.close()
                    if res:
                        p = res[0].encode() if isinstance(res[0],str) else res[0]
                        if bcrypt.checkpw(pwd.encode(),p):
                            st.session_state.connecte = True
                            st.session_state.user = res[3]
                            st.session_state.role = res[1]
                            st.session_state.nom = res[2]
                            if USE_COOKIES:
                                cookies["user"] = res[3]
                                cookies["role"] = res[1]
                                cookies["nom"] = res[2]
                                cookies.save()
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
                cur.execute("SELECT username FROM users WHERE token=%s AND token_expiry>=%s", (tok.strip().upper(),now))
                res = cur.fetchone()
                if res:
                    h = bcrypt.hashpw(new_p.encode(),bcrypt.gensalt())
                    cur.execute("UPDATE users SET password=%s,token=NULL,token_expiry=NULL WHERE username=%s", (h.decode(),res[0]))
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
        choix = st.radio("", opts, label_visibility="collapsed", key="menu_choix")
        st.markdown("<hr style='border-color:#1a1a1a;'>", unsafe_allow_html=True)
        if st.button("Deconnexion", use_container_width=True):
            st.session_state.connecte = False
            if USE_COOKIES:
                try:
                    cookies["user"] = ""
                    cookies["role"] = ""
                    cookies["nom"] = ""
                    cookies.save()
                except:
                    pass
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
        df_v = pd.read_sql("SELECT numero, client_nom, formule, prix_formule, prix_decodeur, promo, prix_total, date_activation FROM decodeurs WHERE statut='vendu' ORDER BY date_activation DESC LIMIT 8", conn)
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
        df_dispo = pd.read_sql("SELECT numero FROM decodeurs WHERE statut='disponible'", conn)
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
                        st.rerun()
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
            df_s = pd.read_sql("SELECT numero,statut,affecte_a,client_nom,formule,prix_total,date_ajout,date_expiration FROM decodeurs ORDER BY date_ajout DESC", conn)
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
                            cur.execute("INSERT OR IGNORE INTO decodeurs (numero,statut,affecte_a,date_ajout) VALUES (%s,'disponible',%s,%s)",
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
                                    cur.execute("INSERT OR IGNORE INTO decodeurs (numero,statut,affecte_a,date_ajout) VALUES (%s,'disponible',%s,%s)",
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
            df_mod = pd.read_sql("SELECT numero,client_nom,client_tel,formule,prix_total FROM decodeurs WHERE statut='vendu'", conn)
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
                            cur.execute("INSERT INTO historique_modifications VALUES (NULL,%s,%s,%s,%s,%s,%s)",
                                        (num_sel,champ,str(old),str(new),st.session_state.user,datetime.now().strftime("%Y-%m-%d %H:%M")))
                    cur.execute("UPDATE decodeurs SET client_nom=%s,client_tel=%s,formule=%s,prix_total=%s WHERE numero=%s",
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
        st.divider()
        st.markdown("#### Renouveler un abonnement")
        conn = db()
        df_renew = pd.read_sql("SELECT numero, client_nom, client_tel, formule, date_expiration FROM decodeurs WHERE statut='vendu' ORDER BY date_expiration ASC", conn)
        conn.close()
        if not df_renew.empty:
            renew_opts = [f"{r['client_nom']} — {r['numero']} (expire {r['date_expiration']})" for _,r in df_renew.iterrows()]
            renew_sel = st.selectbox("Choisir le client a renouveler", renew_opts)
            renew_idx = renew_opts.index(renew_sel)
            renew_row = df_renew.iloc[renew_idx]
            
            rc1, rc2 = st.columns(2)
            with rc1:
                flist = list(FORMULES.keys())
                fidx = flist.index(renew_row['formule']) if renew_row['formule'] in flist else 0
                new_formule_renew = st.selectbox("Nouvelle formule", flist, index=fidx, key="renew_formule")
                new_duree_renew = st.selectbox("Duree", ["1 mois","3 mois","6 mois","12 mois"], key="renew_duree")
            with rc2:
                prix_renew = FORMULES[new_formule_renew]
                new_date_exp = (datetime.now() + timedelta(days={"1 mois":30,"3 mois":90,"6 mois":180,"12 mois":365}[new_duree_renew])).strftime("%Y-%m-%d")
                st.markdown(f"""
                <div class="total-box">
                    <div class="plabel">Prix renouvellement</div>
                    <div class="pmontant">{prix_renew:,} FCFA</div>
                    <div style="color:#fff;font-size:0.8rem;margin-top:4px;">Nouvelle expiration : {new_date_exp}</div>
                </div>""", unsafe_allow_html=True)
            
            if st.button("Confirmer le renouvellement", use_container_width=True):
                conn = db()
                cur = conn.cursor()
                cur.execute("UPDATE decodeurs SET formule=%s, date_expiration=%s, date_activation=%s WHERE numero=%s",
                            (new_formule_renew, new_date_exp, datetime.now().strftime("%Y-%m-%d %H:%M"), renew_row['numero']))
                conn.commit()
                conn.close()
                push_notif(f"Renouvellement : {renew_row['numero']} — {renew_row['client_nom']} ({new_formule_renew} — {prix_renew:,} FCFA)", "vente", "admin")
                st.success(f"Renouvellement confirme ! Nouvelle expiration : {new_date_exp}")
                st.rerun()

        st.markdown("#### Tous les abonnements actifs")
        conn = db()
        df_r = pd.read_sql("SELECT numero,client_nom,client_tel,formule,date_activation,date_expiration FROM decodeurs WHERE statut='vendu' ORDER BY date_expiration ASC", conn)
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
        cur.execute("SELECT message,type,date_creation,lu FROM notifications WHERE destinataire=%s OR destinataire='tous' ORDER BY date_creation DESC LIMIT 60", (st.session_state.user,))
        notifs = cur.fetchall()
        cur.execute("UPDATE notifications SET lu=1 WHERE destinataire=%s OR destinataire='tous'", (st.session_state.user,))
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
        tab1,tab2,tab3,tab4 = st.tabs(["Liste des vendeurs","Ajouter un vendeur","Modifier/Supprimer","Token recuperation"])

        with tab1:
            conn = db()
            df_vend = pd.read_sql("""
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
                        cur.execute("INSERT INTO users (username,telephone,password,role,nom_complet,date_creation) VALUES (%s,%s,%s,%s,%s,%s)",
                                    (nu,nt,h.decode(),"vendeur",nn,datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        conn.close()
                        st.success(f"Compte cree pour {nn} — connexion avec le telephone {nt}")
                        # Vider les champs
                        for k in ['nu','nn','nt','np_v']:
                            if k in st.session_state:
                                del st.session_state[k]
                        st.rerun()
                    except psycopg2.errors.UniqueViolation:
                        st.error("Identifiant ou telephone deja utilise.")
                else:
                    st.error("Remplissez tous les champs.")

        with tab3:
            st.markdown("#### Modifier ou supprimer un vendeur")
            conn = db()
            df_edit = pd.read_sql("SELECT username, nom_complet, telephone FROM users WHERE role='vendeur'", conn)
            conn.close()
            if df_edit.empty:
                st.info("Aucun vendeur enregistre.")
            else:
                e_opts = [f"{r['nom_complet']} ({r['telephone']})" for _,r in df_edit.iterrows()]
                e_sel = st.selectbox("Choisir le vendeur", e_opts, key="edit_vendeur_sel")
                e_idx = e_opts.index(e_sel)
                e_row = df_edit.iloc[e_idx]

                st.markdown("**Modifier les informations**")
                ec1, ec2 = st.columns(2)
                with ec1:
                    new_nom = st.text_input("Nouveau nom complet", value=e_row['nom_complet'], key="edit_nom")
                    new_tel = st.text_input("Nouveau telephone", value=e_row['telephone'], key="edit_tel")
                with ec2:
                    new_pwd_edit = st.text_input("Nouveau mot de passe (laisser vide = pas de changement)", type="password", key="edit_pwd")

                if st.button("Sauvegarder les modifications", use_container_width=True, key="btn_save_vendeur"):
                    conn = db()
                    cur = conn.cursor()
                    cur.execute("UPDATE users SET nom_complet=%s, telephone=%s WHERE username=%s",
                                (new_nom, new_tel, e_row['username']))
                    if new_pwd_edit:
                        h = bcrypt.hashpw(new_pwd_edit.encode(), bcrypt.gensalt())
                        cur.execute("UPDATE users SET password=%s WHERE username=%s", (h.decode(), e_row['username']))
                    conn.commit()
                    conn.close()
                    st.success(f"Vendeur {new_nom} mis a jour.")
                    st.rerun()

                st.divider()
                st.markdown("**Supprimer ce vendeur**")
                if st.button("Supprimer ce vendeur", use_container_width=True, key="btn_del_vendeur"):
                    if 'confirm_delete' not in st.session_state:
                        st.session_state.confirm_delete = False
                    st.session_state.confirm_delete = True
                    st.rerun()

                if st.session_state.get('confirm_delete', False):
                    st.warning(f"Confirmer la suppression de {e_row['nom_complet']} ?")
                    cd1, cd2 = st.columns(2)
                    with cd1:
                        if st.button("Oui supprimer", use_container_width=True, key="btn_confirm_del"):
                            conn = db()
                            cur = conn.cursor()
                            cur.execute("DELETE FROM users WHERE username=%s", (e_row['username'],))
                            conn.commit()
                            conn.close()
                            st.session_state.confirm_delete = False
                            st.success("Vendeur supprime.")
                            st.rerun()
                    with cd2:
                        if st.button("Annuler", use_container_width=True, key="btn_cancel_del"):
                            st.session_state.confirm_delete = False
                            st.rerun()

        with tab4:
            st.markdown("#### Generer un token de recuperation")
            conn = db()
            df_u = pd.read_sql("SELECT username,nom_complet,telephone FROM users WHERE role='vendeur'", conn)
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
                    cur.execute("UPDATE users SET token=%s,token_expiry=%s WHERE username=%s", (token,expiry,u_name))
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
        df_rap = pd.read_sql(f"""
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
                    df_dec = pd.read_sql(f"SELECT numero,statut,formule,prix_total,date_activation FROM decodeurs WHERE affecte_a='{row['username']}' ORDER BY date_activation DESC", conn)
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
        # Bouton sauvegarde complète
        st.markdown("#### Sauvegarde des donnees")
        if st.button("Telecharger sauvegarde complete", use_container_width=True):
            conn = db()
            df_save_dec = pd.read_sql("SELECT * FROM decodeurs", conn)
            df_save_usr = pd.read_sql("SELECT username, nom_complet, telephone, role, date_creation FROM users", conn)
            df_save_notif = pd.read_sql("SELECT * FROM notifications", conn)
            conn.close()
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as w:
                df_save_dec.to_excel(w, index=False, sheet_name="Decodeurs")
                df_save_usr.to_excel(w, index=False, sheet_name="Vendeurs")
                df_save_notif.to_excel(w, index=False, sheet_name="Notifications")
            st.download_button(
                "Cliquez ici pour telecharger",
                out.getvalue(),
                f"sauvegarde_appstock_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_sauvegarde"
            )
            st.success("Sauvegarde prete ! Gardez ce fichier en lieu sur.")
        
        st.divider()
        st.markdown("#### Changer le mot de passe")
        ancien_pwd = st.text_input("Ancien mot de passe", type="password")
        nouveau_pwd1 = st.text_input("Nouveau mot de passe", type="password")
        nouveau_pwd2 = st.text_input("Confirmer le nouveau mot de passe", type="password")
        if st.button("Mettre a jour"):
            if nouveau_pwd1 != nouveau_pwd2:
                st.error("Les mots de passe ne correspondent pas.")
            elif len(nouveau_pwd1) < 6:
                st.error("Minimum 6 caracteres.")
            else:
                conn = db()
                cur = conn.cursor()
                cur.execute("SELECT password FROM users WHERE username=%s", (st.session_state.user,))
                res = cur.fetchone()
                if res:
                    pwd_stored = res[0].encode() if isinstance(res[0], str) else res[0]
                    if bcrypt.checkpw(ancien_pwd.encode(), pwd_stored):
                        h = bcrypt.hashpw(nouveau_pwd1.encode(), bcrypt.gensalt())
                        cur.execute("UPDATE users SET password=%s WHERE username=%s", (h.decode(), st.session_state.user))
                        conn.commit()
                        st.success("Mot de passe mis a jour.")
                    else:
                        st.error("Ancien mot de passe incorrect.")
                conn.close()
        st.divider()
        st.markdown("#### Historique des modifications")
        conn = db()
        df_hist = pd.read_sql("SELECT decodeur_numero,champ_modifie,ancienne_valeur,nouvelle_valeur,modifie_par,date_modification FROM historique_modifications ORDER BY date_modification DESC LIMIT 50", conn)
        conn.close()
        if not df_hist.empty:
            df_hist.columns = ["Decodeur","Champ modifie","Ancienne valeur","Nouvelle valeur","Modifie par","Date"]
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune modification enregistree.")
