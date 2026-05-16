import streamlit as st
import pandas as pd
import json
import os
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta

# ─── Config ───────────────────────────────────────────────────────────────────
DATA_FILE = "bus_data.json"
AUDIT_FILE = "audit_log.json"
DEFAULT_CAPACITY = 50

# ─── Security Config ──────────────────────────────────────────────────────────
# Admin credentials (hashed) — change ADMIN_PASSWORD_HASH to sha256 of your real password
# Default password: "Admin@2024!" — CHANGE THIS IN PRODUCTION
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("Admin@2024!".encode()).hexdigest()
SESSION_TIMEOUT_MINUTES = 30
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

st.set_page_config(
    page_title="Bus Logistics Manager | مدير النقل بالحافلات",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Translations ─────────────────────────────────────────────────────────────
T = {
    "en": {
        "app_title": "Bus Logistics Manager",
        "app_subtitle": "Manage your fleet with precision",
        "login_title": "Admin Login",
        "login_subtitle": "Secure access required",
        "username": "Username",
        "password": "Password",
        "login_btn": "Login",
        "logout_btn": "Logout",
        "wrong_creds": "Invalid username or password.",
        "locked_out": "Too many failed attempts. Try again in {m} minutes.",
        "session_expired": "Session expired. Please log in again.",
        "welcome": "Welcome, Admin",
        "new_bus": "New Bus",
        "bus_name": "Bus name",
        "capacity": "Capacity",
        "create_bus": "Create Bus",
        "delete_bus": "Delete Bus",
        "select_bus_delete": "Select bus to delete",
        "confirm_delete": "Delete {b} and all its members?",
        "yes_delete": "Yes, Delete",
        "cancel": "Cancel",
        "move_member": "Move Member",
        "from_bus": "From bus",
        "to_bus": "To bus",
        "member": "Member",
        "move_btn": "Move Member",
        "export": "Export",
        "download_csv": "Download CSV",
        "total_buses": "Total Buses",
        "total_members": "Total Members",
        "seats_available": "Seats Available",
        "full_buses": "Full Buses",
        "search_placeholder": "Search member by name across all buses...",
        "search_label": "Search Member",
        "found_results": "Found {n} result(s):",
        "no_members_found": "No members found.",
        "duplicate_warning": "Duplicate Names Detected",
        "no_buses": "No buses yet. Create one in the sidebar ➡️",
        "all_members_tab": "📋 All Members",
        "add_member": "Add Member",
        "name_placeholder": "Full name",
        "role": "Role",
        "roles": ["Member", "Leader", "Driver", "Assistant", "Other"],
        "add_btn": "Add ✚",
        "bus_full": "Bus is full! ({c} seats)",
        "enter_name": "Enter a name.",
        "added_success": "Added {n}!",
        "edit_capacity": "⚙️ Edit Capacity",
        "max_seats": "Max seats",
        "update_capacity": "Update Capacity",
        "cap_updated": "Capacity updated!",
        "members_count": "Members ({n})",
        "filter_bus": "Filter this bus",
        "search_in_bus": "Search...",
        "no_members_yet": "No members yet.",
        "all_members_title": "All Members Across All Buses",
        "total_label": "Total: {n} members across {b} buses",
        "bus_created": "Bus '{b}' created!",
        "bus_exists": "Bus already exists.",
        "enter_bus_name": "Enter a bus name.",
        "bus_deleted": "Bus deleted.",
        "moved_success": "Moved {m} to {b}!",
        "no_members_bus": "No members in this bus.",
        "audit_log": "Audit Log",
        "view_audit": "View Audit Log",
        "session_info": "Session Info",
        "expires_in": "Session expires in: {m} min",
        "full_badge": "FULL",
        "ok_badge": "OK",
        "name_col": "Name",
        "role_col": "Role",
        "bus_col": "Bus",
        "added_col": "Added",
        "appears_in": "appears in",
        "security_notice": "🔐 Secured — All actions logged",
        "toggle_lang": "العربية",
        "seats_of": "of {c} seats",
    },
    "ar": {
        "app_title": "مدير النقل بالحافلات",
        "app_subtitle": "إدارة أسطولك بدقة واحترافية",
        "login_title": "تسجيل دخول المدير",
        "login_subtitle": "يُشترط الوصول الآمن",
        "username": "اسم المستخدم",
        "password": "كلمة المرور",
        "login_btn": "تسجيل الدخول",
        "logout_btn": "تسجيل الخروج",
        "wrong_creds": "اسم المستخدم أو كلمة المرور غير صحيحة.",
        "locked_out": "محاولات فاشلة كثيرة. أعد المحاولة خلال {m} دقيقة.",
        "session_expired": "انتهت الجلسة. يرجى تسجيل الدخول مجدداً.",
        "welcome": "أهلاً، المدير",
        "new_bus": "حافلة جديدة",
        "bus_name": "اسم الحافلة",
        "capacity": "الطاقة الاستيعابية",
        "create_bus": "إنشاء حافلة",
        "delete_bus": "حذف حافلة",
        "select_bus_delete": "اختر الحافلة للحذف",
        "confirm_delete": "حذف {b} مع جميع أعضائها؟",
        "yes_delete": "نعم، احذف",
        "cancel": "إلغاء",
        "move_member": "نقل عضو",
        "from_bus": "من الحافلة",
        "to_bus": "إلى الحافلة",
        "member": "العضو",
        "move_btn": "نقل العضو",
        "export": "تصدير",
        "download_csv": "تحميل CSV",
        "total_buses": "إجمالي الحافلات",
        "total_members": "إجمالي الأعضاء",
        "seats_available": "المقاعد المتاحة",
        "full_buses": "الحافلات الممتلئة",
        "search_placeholder": "ابحث عن عضو باسمه في جميع الحافلات...",
        "search_label": "البحث عن عضو",
        "found_results": "تم العثور على {n} نتيجة:",
        "no_members_found": "لم يُعثر على أي عضو.",
        "duplicate_warning": "أسماء مكررة مكتشفة",
        "no_buses": "لا توجد حافلات بعد. أنشئ واحدة من الشريط الجانبي ➡️",
        "all_members_tab": "📋 جميع الأعضاء",
        "add_member": "إضافة عضو",
        "name_placeholder": "الاسم الكامل",
        "role": "الدور",
        "roles": ["عضو", "قائد", "سائق", "مساعد", "أخرى"],
        "add_btn": "إضافة ✚",
        "bus_full": "الحافلة ممتلئة! ({c} مقعداً)",
        "enter_name": "أدخل اسماً.",
        "added_success": "تمت إضافة {n}!",
        "edit_capacity": "⚙️ تعديل الطاقة",
        "max_seats": "الحد الأقصى للمقاعد",
        "update_capacity": "تحديث الطاقة",
        "cap_updated": "تم تحديث الطاقة!",
        "members_count": "الأعضاء ({n})",
        "filter_bus": "تصفية هذه الحافلة",
        "search_in_bus": "بحث...",
        "no_members_yet": "لا يوجد أعضاء بعد.",
        "all_members_title": "جميع الأعضاء في كل الحافلات",
        "total_label": "الإجمالي: {n} عضواً في {b} حافلات",
        "bus_created": "تم إنشاء الحافلة '{b}'!",
        "bus_exists": "الحافلة موجودة بالفعل.",
        "enter_bus_name": "أدخل اسم الحافلة.",
        "bus_deleted": "تم حذف الحافلة.",
        "moved_success": "تم نقل {m} إلى {b}!",
        "no_members_bus": "لا يوجد أعضاء في هذه الحافلة.",
        "audit_log": "سجل المراجعة",
        "view_audit": "عرض سجل المراجعة",
        "session_info": "معلومات الجلسة",
        "expires_in": "تنتهي الجلسة بعد: {m} دقيقة",
        "full_badge": "ممتلئ",
        "ok_badge": "متاح",
        "name_col": "الاسم",
        "role_col": "الدور",
        "bus_col": "الحافلة",
        "added_col": "تاريخ الإضافة",
        "security_notice": "🔐 مؤمّن — جميع الإجراءات مسجّلة",
        "toggle_lang": "English",
        "seats_of": "من {c} مقعداً",
    }
}

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&family=Oswald:wght@400;500;600;700&display=swap');

    :root {
        --black:   #0d0d0d;
        --white:   #f5f0e8;
        --red:     #ce1126;
        --red-dark:#a50e1e;
        --red-glow:rgba(206,17,38,0.35);
        --green:   #007a3d;
        --green-dark:#005a2d;
        --green-glow:rgba(0,122,61,0.35);
        --surface: #161616;
        --surface2:#1f1f1f;
        --surface3:#2a2a2a;
        --border:  #2e2e2e;
        --muted:   #888;
        --gold:    #d4a843;
    }

    html, body, [class*="css"] {
        font-family: 'Tajawal', 'Oswald', sans-serif;
        background: var(--black) !important;
        color: var(--white) !important;
    }
    h1, h2, h3, h4 {
        font-family: 'Oswald', 'Tajawal', sans-serif;
        letter-spacing: 0.5px;
    }

    /* Arabic RTL direction when needed */
    .rtl { direction: rtl; text-align: right; font-family: 'Tajawal', sans-serif !important; }
    .rtl * { font-family: 'Tajawal', sans-serif !important; }

    .stApp { background: var(--black) !important; }

    /* ── Header Banner ── */
    .app-header {
        background: linear-gradient(135deg, #0d0d0d 0%, #1a0305 40%, #001a0a 100%);
        border-bottom: 3px solid var(--red);
        padding: 24px 32px 18px;
        margin: -1rem -1rem 2rem -1rem;
        display: flex;
        align-items: center;
        gap: 18px;
        position: relative;
        overflow: hidden;
    }
    .app-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--black) 0%, var(--red) 33%, var(--white) 33%, var(--white) 66%, var(--green) 66%);
    }
    .app-header::after {
        content: '🇵🇸';
        position: absolute;
        right: 32px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 2.5rem;
        opacity: 0.15;
    }
    .header-icon { font-size: 2.8rem; filter: drop-shadow(0 0 12px var(--red-glow)); }
    .header-title {
        font-family: 'Oswald', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: var(--white);
        line-height: 1.1;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .header-subtitle {
        font-size: 0.85rem;
        color: var(--muted);
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    /* ── Stat Cards ── */
    .stat-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 20px 16px;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: transform 0.15s, border-color 0.15s;
    }
    .stat-card:hover { transform: translateY(-2px); border-color: var(--red); }
    .stat-card::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--red), var(--green));
    }
    .stat-num {
        font-family: 'Oswald', sans-serif;
        font-size: 2.6rem;
        font-weight: 700;
        color: var(--red);
        line-height: 1;
    }
    .stat-label {
        font-size: 0.72rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: 4px;
    }
    .stat-green .stat-num { color: var(--green) !important; }

    /* ── Bus Cards ── */
    .bus-card {
        background: linear-gradient(135deg, var(--surface) 0%, var(--surface2) 100%);
        border: 1px solid var(--border);
        border-left: 4px solid var(--red);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 12px;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .bus-card:hover { border-color: var(--red); box-shadow: 0 4px 24px var(--red-glow); }
    .bus-title {
        font-family: 'Oswald', sans-serif;
        font-size: 1.4rem;
        font-weight: 600;
        color: var(--white);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .bus-count {
        font-family: 'Oswald', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        color: var(--red);
        line-height: 1;
    }
    .bus-label { font-size: 0.78rem; color: var(--muted); letter-spacing: 1px; }

    /* ── Badges ── */
    .warning-badge {
        background: var(--red);
        color: white;
        font-size: 0.65rem;
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-left: 8px;
        text-transform: uppercase;
    }
    .ok-badge {
        background: var(--green);
        color: white;
        font-size: 0.65rem;
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-left: 8px;
        text-transform: uppercase;
    }

    /* ── Member rows ── */
    .member-row {
        background: var(--surface3);
        border-radius: 8px;
        padding: 10px 14px;
        margin: 5px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 3px solid var(--green);
        transition: border-color 0.15s;
    }
    .member-row:hover { border-left-color: var(--red); }
    .role-tag {
        background: var(--surface);
        border: 1px solid var(--border);
        color: var(--muted);
        font-size: 0.72rem;
        padding: 2px 10px;
        border-radius: 20px;
        font-family: 'Tajawal', sans-serif;
    }

    /* ── Progress bar ── */
    div[data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, var(--green), var(--red)) !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: var(--red) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-family: 'Oswald', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        background: var(--red-dark) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px var(--red-glow) !important;
    }
    .btn-green .stButton > button {
        background: var(--green) !important;
    }
    .btn-green .stButton > button:hover {
        background: var(--green-dark) !important;
        box-shadow: 0 4px 12px var(--green-glow) !important;
    }
    .btn-ghost .stButton > button {
        background: transparent !important;
        border: 1px solid var(--border) !important;
        color: var(--muted) !important;
    }

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        color: var(--white) !important;
        border-radius: 6px !important;
        font-family: 'Tajawal', sans-serif !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--red) !important;
        box-shadow: 0 0 0 2px var(--red-glow) !important;
    }
    .stSelectbox > div > div {
        background: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
        color: var(--white) !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--surface) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--white);
        border-bottom: 1px solid var(--border);
        padding-bottom: 6px;
    }
    .sidebar-section {
        background: var(--surface2);
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
        border: 1px solid var(--border);
        border-top: 2px solid var(--red);
    }

    /* ── Duplicate warning ── */
    .duplicate-warning {
        background: rgba(206,17,38,0.12);
        border: 1px solid var(--red);
        border-radius: 6px;
        padding: 8px 14px;
        color: #ff8a8a;
        font-size: 0.88rem;
        margin: 4px 0;
        font-family: 'Tajawal', sans-serif;
    }

    /* ── Login page ── */
    .login-container {
        max-width: 420px;
        margin: 0 auto;
        padding: 48px 40px;
        background: var(--surface);
        border-radius: 12px;
        border: 1px solid var(--border);
        border-top: 4px solid var(--red);
        box-shadow: 0 24px 64px rgba(0,0,0,0.6);
        position: relative;
        overflow: hidden;
    }
    .login-container::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--black) 0%, var(--red) 33%, var(--white) 33%, var(--white) 66%, var(--green) 66%);
    }
    .login-title {
        font-family: 'Oswald', sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--white);
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 8px;
    }
    .login-subtitle {
        text-align: center;
        color: var(--muted);
        font-size: 0.82rem;
        letter-spacing: 1px;
        margin-bottom: 28px;
        text-transform: uppercase;
    }

    /* ── Audit log ── */
    .audit-row {
        background: var(--surface3);
        border-radius: 6px;
        padding: 8px 12px;
        margin: 4px 0;
        font-size: 0.82rem;
        color: #ccc;
        border-left: 3px solid var(--green);
        font-family: 'Tajawal', monospace;
    }

    /* ── Security badge ── */
    .security-notice {
        background: rgba(0,122,61,0.15);
        border: 1px solid var(--green);
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 0.78rem;
        color: #4caf7a;
        text-align: center;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab"] {
        font-family: 'Oswald', sans-serif !important;
        letter-spacing: 0.5px !important;
        color: var(--muted) !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--red) !important;
        border-bottom-color: var(--red) !important;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: var(--surface2) !important;
        border-radius: 6px !important;
        font-family: 'Tajawal', sans-serif !important;
    }

    /* ── Hide streamlit branding ── */
    #MainMenu, footer, header { visibility: hidden; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--black); }
    ::-webkit-scrollbar-thumb { background: var(--red); border-radius: 3px; }

    /* ── Alert colors ── */
    .stAlert { border-radius: 8px !important; }

    /* ── Dataframe ── */
    .stDataFrame { border-radius: 8px !important; }

    /* ── Divider ── */
    hr { border-color: var(--border) !important; margin: 12px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─── Language ─────────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "en"

def t(key, **kwargs):
    text = T[st.session_state.lang].get(key, T["en"].get(key, key))
    for k, v in kwargs.items():
        text = text.replace("{" + k + "}", str(v))
    return text

def is_ar():
    return st.session_state.lang == "ar"

# ─── Security Helpers ─────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(password), hashed)

def init_security():
    defaults = {
        "authenticated": False,
        "login_attempts": 0,
        "lockout_until": None,
        "session_start": None,
        "session_token": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def check_session_valid():
    if not st.session_state.get("authenticated"):
        return False
    start = st.session_state.get("session_start")
    if start is None:
        return False
    elapsed = (datetime.now() - start).total_seconds() / 60
    if elapsed > SESSION_TIMEOUT_MINUTES:
        logout()
        return False
    return True

def session_remaining_minutes():
    start = st.session_state.get("session_start")
    if not start:
        return 0
    elapsed = (datetime.now() - start).total_seconds() / 60
    return max(0, int(SESSION_TIMEOUT_MINUTES - elapsed))

def login(username: str, password: str) -> bool:
    # Check lockout
    lockout = st.session_state.get("lockout_until")
    if lockout and datetime.now() < lockout:
        return False

    if username == ADMIN_USERNAME and verify_password(password, ADMIN_PASSWORD_HASH):
        st.session_state.authenticated = True
        st.session_state.login_attempts = 0
        st.session_state.lockout_until = None
        st.session_state.session_start = datetime.now()
        st.session_state.session_token = secrets.token_hex(32)
        log_audit("LOGIN", f"Successful login from user '{username}'")
        return True
    else:
        st.session_state.login_attempts = st.session_state.get("login_attempts", 0) + 1
        log_audit("LOGIN_FAIL", f"Failed login attempt #{st.session_state.login_attempts}")
        if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
            st.session_state.lockout_until = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            log_audit("LOCKOUT", "Account locked due to too many failed attempts")
        return False

def logout():
    log_audit("LOGOUT", "Admin logged out")
    st.session_state.authenticated = False
    st.session_state.session_start = None
    st.session_state.session_token = None

def is_locked_out():
    lockout = st.session_state.get("lockout_until")
    if lockout and datetime.now() < lockout:
        remaining = int((lockout - datetime.now()).total_seconds() / 60) + 1
        return True, remaining
    return False, 0

# ─── Audit Log ────────────────────────────────────────────────────────────────
def log_audit(action: str, detail: str):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "detail": detail,
    }
    logs = []
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.insert(0, entry)
    logs = logs[:200]  # keep last 200 entries
    with open(AUDIT_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def load_audit():
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# ─── Data Persistence ─────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"buses": {}, "capacity": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_all_members(buses):
    all_members = []
    for bus_name, members in buses.items():
        for m in members:
            all_members.append({
                t("bus_col"): bus_name,
                t("name_col"): m["name"],
                t("role_col"): m.get("role", ""),
                t("added_col"): m.get("added", "")
            })
    return all_members

# ─── Init ─────────────────────────────────────────────────────────────────────
init_security()

if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data
buses = data.setdefault("buses", {})
capacity = data.setdefault("capacity", {})

# ─── LOGIN PAGE ───────────────────────────────────────────────────────────────
if not check_session_valid():
    # Language toggle on login page
    col_lang_top = st.columns([8, 1])[1]
    with col_lang_top:
        if st.button(t("toggle_lang"), key="lang_toggle_login"):
            st.session_state.lang = "ar" if st.session_state.lang == "en" else "en"
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Centered login card
    _, center_col, _ = st.columns([1, 1.4, 1])
    with center_col:
        st.markdown(f"""
        <div class="login-container {'rtl' if is_ar() else ''}">
            <div style="text-align:center;font-size:3rem;margin-bottom:12px;">🚌</div>
            <div class="login-title">{t('login_title')}</div>
            <div class="login-subtitle">{t('login_subtitle')}</div>
        </div>""", unsafe_allow_html=True)

    _, center_col2, _ = st.columns([1, 1.4, 1])
    with center_col2:
        locked, lock_mins = is_locked_out()
        if locked:
            st.error(t("locked_out", m=lock_mins))
        else:
            username_input = st.text_input(
                t("username"),
                placeholder="admin",
                key="login_user"
            )
            password_input = st.text_input(
                t("password"),
                type="password",
                key="login_pass"
            )
            attempts_left = MAX_LOGIN_ATTEMPTS - st.session_state.get("login_attempts", 0)

            if st.button(t("login_btn"), use_container_width=True, key="login_submit"):
                if login(username_input, password_input):
                    st.rerun()
                else:
                    locked2, lock_mins2 = is_locked_out()
                    if locked2:
                        st.error(t("locked_out", m=lock_mins2))
                    else:
                        st.error(t("wrong_creds"))
                        remaining = MAX_LOGIN_ATTEMPTS - st.session_state.get("login_attempts", 0)
                        if remaining <= 2:
                            st.warning(f"⚠️ {remaining} attempt(s) remaining before lockout")

        st.markdown(f'<div style="text-align:center;margin-top:16px;font-size:0.75rem;color:#555;">🔒 Bus Logistics Manager — Secured</div>', unsafe_allow_html=True)

    st.stop()

# ─── AUTHENTICATED APP ────────────────────────────────────────────────────────

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    dir_attr = 'dir="rtl"' if is_ar() else ''

    # Language toggle
    st.markdown(f'<div {"class=rtl" if is_ar() else ""} >', unsafe_allow_html=True)
    if st.button(f"🌐 {t('toggle_lang')}", use_container_width=True, key="lang_toggle_main"):
        st.session_state.lang = "ar" if st.session_state.lang == "en" else "en"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="security-notice">{t("security_notice")}</div>', unsafe_allow_html=True)

    # Session info
    with st.expander(f"👤 {t('session_info')}", expanded=False):
        st.markdown(f'<div {"class=rtl" if is_ar() else ""}>', unsafe_allow_html=True)
        st.caption(t("welcome"))
        st.caption(t("expires_in", m=session_remaining_minutes()))
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button(t("logout_btn"), use_container_width=True, key="logout_btn"):
            logout()
            st.rerun()

    st.markdown("---")

    # Add Bus
    st.markdown(f'<div {"class=rtl" if is_ar() else ""}>', unsafe_allow_html=True)
    st.markdown(f"### ➕ {t('new_bus')}")
    new_bus_name = st.text_input(t("bus_name"), placeholder="Bus A" if not is_ar() else "حافلة أ", key="new_bus_input")
    new_bus_cap = st.number_input(t("capacity"), min_value=1, max_value=200, value=DEFAULT_CAPACITY, key="new_cap")
    if st.button(t("create_bus"), use_container_width=True, key="create_bus_btn"):
        if new_bus_name.strip():
            bname = new_bus_name.strip()
            if bname not in buses:
                buses[bname] = []
                capacity[bname] = int(new_bus_cap)
                save_data(data)
                log_audit("CREATE_BUS", f"Created bus '{bname}' with capacity {new_bus_cap}")
                st.success(t("bus_created", b=bname))
                st.rerun()
            else:
                st.error(t("bus_exists"))
        else:
            st.warning(t("enter_bus_name"))
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Delete Bus
    if buses:
        st.markdown(f'<div {"class=rtl" if is_ar() else ""}>', unsafe_allow_html=True)
        st.markdown(f"### 🗑️ {t('delete_bus')}")
        del_bus = st.selectbox(t("select_bus_delete"), list(buses.keys()), key="del_bus")
        if st.button(t("delete_bus"), use_container_width=True, key="del_bus_btn"):
            st.session_state["confirm_delete"] = True
            st.rerun()
        if st.session_state.get("confirm_delete"):
            st.warning(t("confirm_delete", b=del_bus))
            col1, col2 = st.columns(2)
            with col1:
                if st.button(t("yes_delete"), use_container_width=True, key="confirm_del_yes"):
                    log_audit("DELETE_BUS", f"Deleted bus '{del_bus}' with {len(buses[del_bus])} members")
                    del buses[del_bus]
                    capacity.pop(del_bus, None)
                    save_data(data)
                    st.session_state["confirm_delete"] = False
                    st.rerun()
            with col2:
                if st.button(t("cancel"), use_container_width=True, key="confirm_del_no"):
                    st.session_state["confirm_delete"] = False
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Move Member
    if len(buses) >= 2:
        st.markdown(f'<div {"class=rtl" if is_ar() else ""}>', unsafe_allow_html=True)
        st.markdown(f"### 🔄 {t('move_member')}")
        from_bus = st.selectbox(t("from_bus"), list(buses.keys()), key="move_from")
        if buses.get(from_bus):
            member_names = [m["name"] for m in buses[from_bus]]
            move_member_sel = st.selectbox(t("member"), member_names, key="move_member")
            to_bus_options = [b for b in buses if b != from_bus]
            to_bus = st.selectbox(t("to_bus"), to_bus_options, key="move_to")
            if st.button(t("move_btn"), use_container_width=True, key="move_btn"):
                member_obj = next((m for m in buses[from_bus] if m["name"] == move_member_sel), None)
                if member_obj:
                    buses[from_bus] = [m for m in buses[from_bus] if m["name"] != move_member_sel]
                    buses[to_bus].append(member_obj)
                    save_data(data)
                    log_audit("MOVE_MEMBER", f"Moved '{move_member_sel}' from '{from_bus}' to '{to_bus}'")
                    st.success(t("moved_success", m=move_member_sel, b=to_bus))
                    st.rerun()
        else:
            st.info(t("no_members_bus"))
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Export
    st.markdown(f'<div {"class=rtl" if is_ar() else ""}>', unsafe_allow_html=True)
    st.markdown(f"### 📤 {t('export')}")
    if buses:
        all_m = get_all_members(buses)
        if all_m:
            df_export = pd.DataFrame(all_m)
            csv = df_export.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                t("download_csv"),
                data=csv,
                file_name=f"bus_roster_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Audit Log
    with st.expander(f"📋 {t('audit_log')}", expanded=False):
        audit_entries = load_audit()
        if audit_entries:
            for entry in audit_entries[:20]:
                action_color = {"LOGIN": "#4caf7a", "LOGOUT": "#aaa", "LOGIN_FAIL": "#ff6b6b", "LOCKOUT": "#ff0000"}.get(entry["action"], "#d4a843")
                st.markdown(f"""<div class="audit-row">
                    <span style="color:{action_color};font-weight:700">{entry['action']}</span>
                    &nbsp;·&nbsp; {entry['timestamp']}<br>
                    <span style="color:#999">{entry['detail']}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("No audit entries yet.")


# ─── Main Area ────────────────────────────────────────────────────────────────
# Header
st.markdown(f"""
<div class="app-header {'rtl' if is_ar() else ''}">
    <div class="header-icon">🚌</div>
    <div>
        <div class="header-title">{t('app_title')}</div>
        <div class="header-subtitle">{t('app_subtitle')}</div>
    </div>
</div>""", unsafe_allow_html=True)

# Stats row
total_members = sum(len(m) for m in buses.values())
total_buses = len(buses)
total_capacity_val = sum(capacity.get(b, DEFAULT_CAPACITY) for b in buses)
full_buses = sum(1 for b in buses if len(buses[b]) >= capacity.get(b, DEFAULT_CAPACITY))
seats_avail = max(0, total_capacity_val - total_members)

col1, col2, col3, col4 = st.columns(4)
stats_data = [
    (total_buses, t("total_buses"), ""),
    (total_members, t("total_members"), ""),
    (seats_avail, t("seats_available"), "stat-green"),
    (full_buses, t("full_buses"), ""),
]
for col, (num, label, cls) in zip([col1, col2, col3, col4], stats_data):
    with col:
        st.markdown(f"""
        <div class="stat-card {cls} {'rtl' if is_ar() else ''}">
            <div class="stat-num">{num}</div>
            <div class="stat-label">{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Search bar
dir_style = 'direction:rtl;text-align:right;' if is_ar() else ''
search_query = st.text_input(
    f"🔍 {t('search_label')}",
    placeholder=t("search_placeholder"),
    key="search"
)
if search_query:
    results = []
    for bname, members in buses.items():
        for m in members:
            if search_query.lower() in m["name"].lower():
                results.append({
                    t("bus_col"): bname,
                    t("name_col"): m["name"],
                    t("role_col"): m.get("role", "—"),
                    t("added_col"): m.get("added", "—")
                })
    if results:
        st.success(t("found_results", n=len(results)))
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
    else:
        st.warning(t("no_members_found"))
    st.markdown("---")

# Duplicate check
all_names_list = [m["name"].lower() for members in buses.values() for m in members]
duplicates = set(n for n in all_names_list if all_names_list.count(n) > 1)

if duplicates:
    st.markdown(f'<div {"class=rtl" if is_ar() else ""}>', unsafe_allow_html=True)
    st.markdown(f"### ⚠️ {t('duplicate_warning')}")
    for dup in duplicates:
        dup_buses = [b for b, members in buses.items() if any(m["name"].lower() == dup for m in members)]
        st.markdown(
            f'<div class="duplicate-warning {'rtl' if is_ar() else ''}">⚠️ <b>{dup.title()}</b> {t("appears_in")}: {", ".join(dup_buses)}</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("")

# ─── Bus Cards ────────────────────────────────────────────────────────────────
if not buses:
    st.info(t("no_buses"))
else:
    tab_labels = list(buses.keys()) + [t("all_members_tab")]
    tabs = st.tabs(tab_labels)

    for i, bname in enumerate(buses.keys()):
        with tabs[i]:
            members = buses[bname]
            cap = capacity.get(bname, DEFAULT_CAPACITY)
            count = len(members)
            pct = count / cap if cap > 0 else 0
            is_full = count >= cap
            badge_html = (
                f'<span class="warning-badge">{t("full_badge")}</span>'
                if is_full
                else f'<span class="ok-badge">{t("ok_badge")}</span>'
            )

            col_info, col_add = st.columns([1, 1])

            with col_info:
                st.markdown(f"""
                <div class="bus-card {'rtl' if is_ar() else ''}">
                    <div class="bus-title">{bname} {badge_html}</div>
                    <div class="bus-count">{count}</div>
                    <div class="bus-label">{t('seats_of', c=cap)}</div>
                </div>""", unsafe_allow_html=True)
                st.progress(min(pct, 1.0))

            with col_add:
                st.markdown(f'<div {"class=rtl" if is_ar() else ""}>', unsafe_allow_html=True)
                st.markdown(f"#### ✚ {t('add_member')}")
                new_name = st.text_input(
                    t("name_col"),
                    key=f"name_{bname}",
                    placeholder=t("name_placeholder")
                )
                roles = t("roles")
                new_role = st.selectbox(t("role"), roles, key=f"role_{bname}")
                if st.button(t("add_btn"), key=f"add_{bname}", use_container_width=True):
                    if new_name.strip():
                        if count >= cap:
                            st.error(t("bus_full", c=cap))
                        else:
                            buses[bname].append({
                                "name": new_name.strip(),
                                "role": new_role,
                                "added": datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            save_data(data)
                            log_audit("ADD_MEMBER", f"Added '{new_name.strip()}' (role: {new_role}) to bus '{bname}'")
                            st.success(t("added_success", n=new_name.strip()))
                            st.rerun()
                    else:
                        st.warning(t("enter_name"))
                st.markdown('</div>', unsafe_allow_html=True)

            # Capacity edit
            with st.expander(t("edit_capacity")):
                st.markdown(f'<div {"class=rtl" if is_ar() else ""}>', unsafe_allow_html=True)
                new_cap = st.number_input(
                    t("max_seats"),
                    min_value=1, max_value=500, value=cap,
                    key=f"cap_{bname}"
                )
                if st.button(t("update_capacity"), key=f"savecap_{bname}"):
                    old_cap = capacity.get(bname, DEFAULT_CAPACITY)
                    capacity[bname] = int(new_cap)
                    save_data(data)
                    log_audit("EDIT_CAPACITY", f"Changed '{bname}' capacity from {old_cap} to {new_cap}")
                    st.success(t("cap_updated"))
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(f'<div {"class=rtl" if is_ar() else ""}>', unsafe_allow_html=True)
            st.markdown(f"#### 👥 {t('members_count', n=count)}")
            st.markdown('</div>', unsafe_allow_html=True)

            if not members:
                st.info(t("no_members_yet"))
            else:
                bus_search = st.text_input(
                    t("filter_bus"),
                    placeholder=t("search_in_bus"),
                    key=f"busfilter_{bname}"
                )
                filtered = [m for m in members if bus_search.lower() in m["name"].lower()] if bus_search else members

                for j, m in enumerate(filtered):
                    c1, c2, c3 = st.columns([3, 2, 1])
                    with c1:
                        st.markdown(f'<div {"class=rtl" if is_ar() else ""}><b>{m["name"]}</b></div>', unsafe_allow_html=True)
                    with c2:
                        st.markdown(f'<div {"class=rtl" if is_ar() else ""}><span class="role-tag">{m.get("role", "Member")}</span></div>', unsafe_allow_html=True)
                    with c3:
                        orig_idx = next((idx for idx, om in enumerate(buses[bname]) if om["name"] == m["name"]), None)
                        if st.button("✕", key=f"del_{bname}_{j}_{m['name']}"):
                            if orig_idx is not None:
                                removed_name = buses[bname][orig_idx]["name"]
                                buses[bname].pop(orig_idx)
                                save_data(data)
                                log_audit("REMOVE_MEMBER", f"Removed '{removed_name}' from bus '{bname}'")
                                st.rerun()

    # All Members tab
    with tabs[-1]:
        st.markdown(f'<div {"class=rtl" if is_ar() else ""}>', unsafe_allow_html=True)
        st.markdown(f"#### 📋 {t('all_members_title')}")
        all_m = get_all_members(buses)
        if all_m:
            df_all = pd.DataFrame(all_m)
            st.dataframe(df_all, use_container_width=True, hide_index=True)
            st.markdown(f"**{t('total_label', n=len(all_m), b=len(buses))}**")
        else:
            st.info(t("no_members_yet"))
        st.markdown('</div>', unsafe_allow_html=True)
