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

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("Admin@2024!".encode()).hexdigest()
SESSION_TIMEOUT_MINUTES = 30
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

st.set_page_config(
    page_title="Bus Logistics Manager | مدير النقل",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed",
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
        "download_csv": "⬇ Download CSV",
        "download_json": "⬇ Download JSON",
        "total_buses": "Total Buses",
        "total_members": "Total Members",
        "seats_available": "Seats Available",
        "full_buses": "Full Buses",
        "search_placeholder": "Search member by name...",
        "search_label": "Search Member",
        "found_results": "Found {n} result(s):",
        "no_members_found": "No members found.",
        "duplicate_warning": "⚠️ Duplicate Names",
        "no_buses": "No buses yet. Create one in the sidebar ➡️",
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
        "update_capacity": "Update",
        "cap_updated": "Capacity updated!",
        "members_count": "Members ({n}/{c})",
        "filter_bus": "Filter",
        "search_in_bus": "Search in this bus…",
        "no_members_yet": "No members yet.",
        "all_members_title": "All Members",
        "total_label": "Total: {n} members across {b} buses",
        "bus_created": "Bus '{b}' created!",
        "bus_exists": "Bus already exists.",
        "enter_bus_name": "Enter a bus name.",
        "bus_deleted": "Bus deleted.",
        "moved_success": "Moved {m} to {b}!",
        "no_members_bus": "No members in this bus.",
        "audit_log": "Audit Log",
        "session_info": "Session Info",
        "expires_in": "Expires in: {m} min",
        "full_badge": "FULL",
        "ok_badge": "OK",
        "name_col": "Name",
        "role_col": "Role",
        "bus_col": "Bus",
        "added_col": "Added",
        "appears_in": "appears in",
        "security_notice": "🔐 Secured — All actions logged",
        "toggle_lang": "العربية",
        "seats_of": "{c} seats",
        # Pages
        "page_dashboard": "📊 Dashboard",
        "page_buses": "🚌 Bus Roster",
        "page_rollcall": "✅ Roll Call",
        "page_search": "🔍 Search",
        "page_analytics": "📈 Analytics",
        "page_settings": "⚙️ Settings",
        # Roll call
        "rollcall_title": "Roll Call — Boarding Check",
        "rollcall_subtitle": "Mark each person as boarded",
        "select_bus_rc": "Select bus for roll call",
        "boarded": "Boarded",
        "not_boarded": "Not Boarded",
        "mark_all_boarded": "✅ Mark All Boarded",
        "reset_rollcall": "🔄 Reset Roll Call",
        "rollcall_progress": "{b} / {t} boarded",
        "rollcall_complete": "🎉 All aboard!",
        "print_report": "🖨️ Print Report",
        "rc_export": "⬇ Export Roll Call CSV",
        # Analytics
        "analytics_title": "Fleet Analytics",
        "occupancy_rate": "Occupancy Rate",
        "avg_occupancy": "Avg Occupancy",
        "most_roles": "Role Distribution",
        "timeline": "Members Added Over Time",
        # Settings
        "settings_title": "Settings",
        "change_password": "Change Password",
        "current_password": "Current Password",
        "new_password": "New Password",
        "confirm_password": "Confirm Password",
        "save_password": "Save Password",
        "password_changed": "Password changed successfully!",
        "password_mismatch": "Passwords do not match.",
        "password_wrong": "Current password is incorrect.",
        "session_timeout": "Session Timeout (minutes)",
        "appearance": "Appearance",
        "data_management": "Data Management",
        "clear_all_data": "⚠️ Clear All Data",
        "confirm_clear": "Type CONFIRM to wipe all bus data",
        "data_cleared": "All data cleared.",
        "danger_zone": "Danger Zone",
        "notes": "Notes",
        "add_note": "Add note for this member",
        "save_note": "Save",
        "note_saved": "Note saved!",
        "phone": "Phone",
        "add_phone": "Phone number",
        "phone_saved": "Phone saved!",
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
        "download_csv": "⬇ تحميل CSV",
        "download_json": "⬇ تحميل JSON",
        "total_buses": "إجمالي الحافلات",
        "total_members": "إجمالي الأعضاء",
        "seats_available": "المقاعد المتاحة",
        "full_buses": "الحافلات الممتلئة",
        "search_placeholder": "ابحث عن عضو باسمه...",
        "search_label": "البحث عن عضو",
        "found_results": "تم العثور على {n} نتيجة:",
        "no_members_found": "لم يُعثر على أي عضو.",
        "duplicate_warning": "⚠️ أسماء مكررة",
        "no_buses": "لا توجد حافلات بعد. أنشئ واحدة من الشريط الجانبي ➡️",
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
        "update_capacity": "تحديث",
        "cap_updated": "تم تحديث الطاقة!",
        "members_count": "الأعضاء ({n}/{c})",
        "filter_bus": "تصفية",
        "search_in_bus": "بحث في الحافلة…",
        "no_members_yet": "لا يوجد أعضاء بعد.",
        "all_members_title": "جميع الأعضاء",
        "total_label": "الإجمالي: {n} عضواً في {b} حافلات",
        "bus_created": "تم إنشاء الحافلة '{b}'!",
        "bus_exists": "الحافلة موجودة بالفعل.",
        "enter_bus_name": "أدخل اسم الحافلة.",
        "bus_deleted": "تم حذف الحافلة.",
        "moved_success": "تم نقل {m} إلى {b}!",
        "no_members_bus": "لا يوجد أعضاء في هذه الحافلة.",
        "audit_log": "سجل المراجعة",
        "session_info": "معلومات الجلسة",
        "expires_in": "تنتهي بعد: {m} دقيقة",
        "full_badge": "ممتلئ",
        "ok_badge": "متاح",
        "name_col": "الاسم",
        "role_col": "الدور",
        "bus_col": "الحافلة",
        "added_col": "تاريخ الإضافة",
        "appears_in": "يظهر في",
        "security_notice": "🔐 مؤمّن — جميع الإجراءات مسجّلة",
        "toggle_lang": "English",
        "seats_of": "{c} مقعداً",
        "page_dashboard": "📊 لوحة التحكم",
        "page_buses": "🚌 قوائم الحافلات",
        "page_rollcall": "✅ التحقق من الركاب",
        "page_search": "🔍 بحث",
        "page_analytics": "📈 التحليلات",
        "page_settings": "⚙️ الإعدادات",
        "rollcall_title": "التحقق من الصعود",
        "rollcall_subtitle": "تحديد كل شخص صعد الحافلة",
        "select_bus_rc": "اختر الحافلة",
        "boarded": "صعد",
        "not_boarded": "لم يصعد",
        "mark_all_boarded": "✅ تحديد الجميع",
        "reset_rollcall": "🔄 إعادة تعيين",
        "rollcall_progress": "{b} / {t} صعدوا",
        "rollcall_complete": "🎉 الجميع على متن الحافلة!",
        "print_report": "🖨️ طباعة التقرير",
        "rc_export": "⬇ تصدير CSV",
        "analytics_title": "تحليلات الأسطول",
        "occupancy_rate": "معدل الإشغال",
        "avg_occupancy": "متوسط الإشغال",
        "most_roles": "توزيع الأدوار",
        "timeline": "الأعضاء المضافون بمرور الوقت",
        "settings_title": "الإعدادات",
        "change_password": "تغيير كلمة المرور",
        "current_password": "كلمة المرور الحالية",
        "new_password": "كلمة مرور جديدة",
        "confirm_password": "تأكيد كلمة المرور",
        "save_password": "حفظ",
        "password_changed": "تم تغيير كلمة المرور!",
        "password_mismatch": "كلمتا المرور غير متطابقتين.",
        "password_wrong": "كلمة المرور الحالية غير صحيحة.",
        "session_timeout": "مهلة الجلسة (دقائق)",
        "appearance": "المظهر",
        "data_management": "إدارة البيانات",
        "clear_all_data": "⚠️ مسح جميع البيانات",
        "confirm_clear": "اكتب CONFIRM لمسح البيانات",
        "data_cleared": "تم مسح جميع البيانات.",
        "danger_zone": "منطقة الخطر",
        "notes": "ملاحظات",
        "add_note": "أضف ملاحظة لهذا العضو",
        "save_note": "حفظ",
        "note_saved": "تم حفظ الملاحظة!",
        "phone": "الهاتف",
        "add_phone": "رقم الهاتف",
        "phone_saved": "تم حفظ الهاتف!",
    }
}

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&family=Oswald:wght@400;500;600;700&display=swap');

    :root {
        --black:   #0a0a0a;
        --white:   #f0ebe0;
        --red:     #ce1126;
        --red-dark:#a50e1e;
        --red-glow:rgba(206,17,38,0.30);
        --green:   #007a3d;
        --green-dark:#005a2d;
        --green-glow:rgba(0,122,61,0.30);
        --surface: #141414;
        --surface2:#1c1c1c;
        --surface3:#252525;
        --border:  #2a2a2a;
        --muted:   #777;
        --gold:    #c9a227;
        --blue:    #1565c0;
        --blue-glow: rgba(21,101,192,0.3);
    }

    html, body, [class*="css"] {
        font-family: 'Tajawal', 'Oswald', sans-serif;
        background: var(--black) !important;
        color: var(--white) !important;
    }
    h1,h2,h3,h4 { font-family: 'Oswald','Tajawal',sans-serif; letter-spacing:.5px; }
    .rtl { direction:rtl; text-align:right; font-family:'Tajawal',sans-serif!important; }
    .rtl * { font-family:'Tajawal',sans-serif!important; }
    .stApp { background: var(--black) !important; }

    /* ── Header ── */
    .app-header {
        background: linear-gradient(135deg,#0a0a0a 0%,#160204 40%,#001508 100%);
        border-bottom: 3px solid var(--red);
        padding: 20px 28px 14px;
        margin: -1rem -1rem 1.5rem -1rem;
        display: flex; align-items: center; gap: 16px;
        position: relative; overflow: hidden;
    }
    .app-header::before {
        content:''; position:absolute; top:0; left:0; right:0; height:4px;
        background: linear-gradient(90deg,var(--black) 0%,var(--red) 33%,var(--white) 33%,var(--white) 66%,var(--green) 66%);
    }
    .app-header::after {
        content:'🇵🇸'; position:absolute; right:28px; top:50%;
        transform:translateY(-50%); font-size:2.2rem; opacity:.12;
    }
    .header-icon { font-size:2.4rem; filter:drop-shadow(0 0 10px var(--red-glow)); }
    .header-title {
        font-family:'Oswald',sans-serif; font-size:1.75rem; font-weight:700;
        color:var(--white); line-height:1.1; text-transform:uppercase; letter-spacing:2px;
    }
    .header-subtitle { font-size:.78rem; color:var(--muted); letter-spacing:1px; text-transform:uppercase; }
    .header-page-badge {
        margin-left:auto; background:var(--surface2); border:1px solid var(--border);
        border-radius:20px; padding:4px 16px; font-size:.75rem; color:var(--muted);
        letter-spacing:1px; text-transform:uppercase;
    }

    /* ── Stat Cards ── */
    .stat-card {
        background:var(--surface); border:1px solid var(--border); border-radius:10px;
        padding:18px 14px; text-align:center; position:relative; overflow:hidden;
        transition:transform .15s, border-color .15s;
    }
    .stat-card:hover { transform:translateY(-2px); border-color:var(--red); }
    .stat-card::after {
        content:''; position:absolute; bottom:0; left:0; right:0; height:3px;
        background:linear-gradient(90deg,var(--red),var(--green));
    }
    .stat-num { font-family:'Oswald',sans-serif; font-size:2.4rem; font-weight:700; color:var(--red); line-height:1; }
    .stat-label { font-size:.68rem; color:var(--muted); text-transform:uppercase; letter-spacing:1.5px; margin-top:4px; }
    .stat-green .stat-num { color:var(--green)!important; }
    .stat-blue .stat-num { color:#42a5f5!important; }
    .stat-gold .stat-num { color:var(--gold)!important; }

    /* ── Bus Cards ── */
    .bus-card {
        background:linear-gradient(135deg,var(--surface) 0%,var(--surface2) 100%);
        border:1px solid var(--border); border-left:4px solid var(--red);
        border-radius:10px; padding:18px; margin-bottom:10px;
        transition:border-color .2s, box-shadow .2s;
    }
    .bus-card:hover { border-color:var(--red); box-shadow:0 4px 20px var(--red-glow); }
    .bus-title { font-family:'Oswald',sans-serif; font-size:1.3rem; font-weight:600; color:var(--white); text-transform:uppercase; letter-spacing:1px; }
    .bus-count { font-family:'Oswald',sans-serif; font-size:2.6rem; font-weight:700; color:var(--red); line-height:1; }
    .bus-label { font-size:.74rem; color:var(--muted); letter-spacing:1px; }

    /* ── Badges ── */
    .warning-badge { background:var(--red); color:white; font-size:.62rem; padding:3px 9px; border-radius:20px; font-weight:700; letter-spacing:1px; margin-left:8px; text-transform:uppercase; }
    .ok-badge { background:var(--green); color:white; font-size:.62rem; padding:3px 9px; border-radius:20px; font-weight:700; letter-spacing:1px; margin-left:8px; text-transform:uppercase; }

    /* ── Member rows ── */
    .member-row {
        background:var(--surface3); border-radius:8px; padding:10px 14px; margin:4px 0;
        display:flex; justify-content:space-between; align-items:center;
        border-left:3px solid var(--green); transition:border-color .15s;
    }
    .member-row:hover { border-left-color:var(--red); }

    /* ── Roll call rows ── */
    .rc-row-boarded {
        background:rgba(0,122,61,0.15); border:1px solid rgba(0,122,61,0.4);
        border-radius:8px; padding:12px 16px; margin:4px 0;
        display:flex; align-items:center; gap:12px; transition:all .2s;
    }
    .rc-row-pending {
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; padding:12px 16px; margin:4px 0;
        display:flex; align-items:center; gap:12px; transition:all .2s;
    }
    .rc-name-boarded { font-size:.95rem; color:#4caf7a; font-weight:600; text-decoration:line-through; opacity:.8; }
    .rc-name-pending { font-size:.95rem; color:var(--white); font-weight:500; }
    .rc-role { font-size:.72rem; color:var(--muted); margin-left:8px; }

    /* ── Roll call progress ── */
    .rc-progress-wrap {
        background:var(--surface); border:1px solid var(--border); border-radius:12px;
        padding:20px 24px; margin-bottom:20px;
    }
    .rc-fraction { font-family:'Oswald',sans-serif; font-size:3rem; font-weight:700; color:var(--green); line-height:1; }
    .rc-label { font-size:.78rem; color:var(--muted); text-transform:uppercase; letter-spacing:1px; }

    /* ── Role tag ── */
    .role-tag {
        background:var(--surface); border:1px solid var(--border); color:var(--muted);
        font-size:.68rem; padding:2px 9px; border-radius:20px; font-family:'Tajawal',sans-serif;
    }
    .role-leader { border-color:var(--gold); color:var(--gold); }
    .role-driver  { border-color:#42a5f5; color:#42a5f5; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background:var(--surface)!important;
        border-right:1px solid var(--border)!important;
    }
    [data-testid="stSidebar"] .stMarkdown h3 {
        color:var(--white); border-bottom:1px solid var(--border); padding-bottom:5px;
    }

    /* NAV menu items */
    .nav-item {
        display:flex; align-items:center; gap:10px; padding:10px 16px;
        border-radius:8px; margin:2px 0; cursor:pointer; transition:all .15s;
        font-family:'Oswald',sans-serif; font-size:.9rem; text-transform:uppercase;
        letter-spacing:.5px; color:var(--muted); border:1px solid transparent;
    }
    .nav-item:hover { background:var(--surface2); color:var(--white); border-color:var(--border); }
    .nav-item.active {
        background:linear-gradient(135deg,rgba(206,17,38,.15),rgba(0,122,61,.1));
        border-color:var(--red); color:var(--white);
        box-shadow:0 2px 12px var(--red-glow);
    }
    .nav-section { font-size:.65rem; color:var(--muted); letter-spacing:2px; text-transform:uppercase; padding:12px 16px 4px; }

    /* ── Buttons ── */
    .stButton > button {
        background:var(--red)!important; color:white!important; border:none!important;
        border-radius:6px!important; font-family:'Oswald',sans-serif!important;
        font-weight:500!important; letter-spacing:.5px!important; transition:all .2s!important;
    }
    .stButton > button:hover {
        background:var(--red-dark)!important; transform:translateY(-1px)!important;
        box-shadow:0 4px 12px var(--red-glow)!important;
    }
    .btn-green .stButton > button { background:var(--green)!important; }
    .btn-green .stButton > button:hover { background:var(--green-dark)!important; box-shadow:0 4px 12px var(--green-glow)!important; }
    .btn-ghost .stButton > button { background:transparent!important; border:1px solid var(--border)!important; color:var(--muted)!important; }
    .btn-blue .stButton > button { background:var(--blue)!important; }
    .btn-blue .stButton > button:hover { background:#0d47a1!important; box-shadow:0 4px 12px var(--blue-glow)!important; }

    /* ── Inputs ── */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
        background:var(--surface2)!important; border:1px solid var(--border)!important;
        color:var(--white)!important; border-radius:6px!important;
        font-family:'Tajawal',sans-serif!important;
    }
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border-color:var(--red)!important; box-shadow:0 0 0 2px var(--red-glow)!important;
    }
    .stSelectbox>div>div { background:var(--surface2)!important; border:1px solid var(--border)!important; border-radius:6px!important; color:var(--white)!important; }

    /* ── Progress ── */
    div[data-testid="stProgress"]>div>div { background:linear-gradient(90deg,var(--green),var(--red))!important; }

    /* ── Duplicate warning ── */
    .duplicate-warning {
        background:rgba(206,17,38,.1); border:1px solid var(--red); border-radius:6px;
        padding:7px 12px; color:#ff8a8a; font-size:.85rem; margin:4px 0;
    }

    /* ── Login ── */
    .login-container {
        max-width:420px; margin:0 auto; padding:44px 38px;
        background:var(--surface); border-radius:12px; border:1px solid var(--border);
        border-top:4px solid var(--red); box-shadow:0 24px 64px rgba(0,0,0,.6);
        position:relative; overflow:hidden;
    }
    .login-container::before {
        content:''; position:absolute; top:0; left:0; right:0; height:4px;
        background:linear-gradient(90deg,var(--black) 0%,var(--red) 33%,var(--white) 33%,var(--white) 66%,var(--green) 66%);
    }
    .login-title { font-family:'Oswald',sans-serif; font-size:1.7rem; font-weight:700; color:var(--white); text-align:center; text-transform:uppercase; letter-spacing:2px; margin-bottom:6px; }
    .login-subtitle { text-align:center; color:var(--muted); font-size:.78rem; letter-spacing:1px; margin-bottom:24px; text-transform:uppercase; }

    /* ── Audit ── */
    .audit-row {
        background:var(--surface3); border-radius:6px; padding:7px 11px; margin:3px 0;
        font-size:.79rem; color:#ccc; border-left:3px solid var(--green);
    }

    /* ── Security badge ── */
    .security-notice {
        background:rgba(0,122,61,.12); border:1px solid var(--green); border-radius:6px;
        padding:5px 12px; font-size:.74rem; color:#4caf7a; text-align:center;
        letter-spacing:.5px; margin-bottom:10px;
    }

    /* ── Analytics ── */
    .analytics-bar-wrap { margin:4px 0; }
    .analytics-bar-label { font-size:.8rem; color:var(--muted); margin-bottom:2px; }
    .analytics-bar-bg { background:var(--surface3); border-radius:4px; height:14px; overflow:hidden; }
    .analytics-bar-fill { height:100%; border-radius:4px; transition:width .4s; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab"] { font-family:'Oswald',sans-serif!important; letter-spacing:.5px!important; color:var(--muted)!important; }
    .stTabs [aria-selected="true"] { color:var(--red)!important; border-bottom-color:var(--red)!important; }

    /* ── Expander ── */
    .streamlit-expanderHeader { background:var(--surface2)!important; border-radius:6px!important; }

    /* ── Misc ── */
    #MainMenu, footer, header { visibility:hidden; }
    ::-webkit-scrollbar { width:5px; }
    ::-webkit-scrollbar-track { background:var(--black); }
    ::-webkit-scrollbar-thumb { background:var(--red); border-radius:3px; }
    .stAlert { border-radius:8px!important; }
    .stDataFrame { border-radius:8px!important; }
    hr { border-color:var(--border)!important; margin:10px 0!important; }

    /* Note / phone field */
    .member-note { font-size:.75rem; color:var(--muted); font-style:italic; margin-top:2px; }
    .member-phone { font-size:.75rem; color:#42a5f5; margin-top:2px; }

    /* Mobile Top Nav Bar */
    .mobile-nav {
        display: flex; gap: 0;
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 12px; overflow: hidden; margin-bottom: 16px; width: 100%;
    }
    .mobile-nav-item {
        flex: 1; text-align: center; padding: 9px 2px 7px;
        font-family: 'Oswald', sans-serif; font-size: .62rem; text-transform: uppercase;
        letter-spacing: .2px; color: var(--muted); cursor: pointer;
        border-right: 1px solid var(--border); transition: all .15s; line-height: 1.3;
    }
    .mobile-nav-item:last-child { border-right: none; }
    .mobile-nav-item:hover { background: var(--surface2); color: var(--white); }
    .mobile-nav-item.active {
        background: linear-gradient(180deg, rgba(206,17,38,.18) 0%, rgba(0,122,61,.10) 100%);
        color: var(--white); border-bottom: 2px solid var(--red);
    }
    .mobile-nav-icon { font-size: 1.05rem; display:block; margin-bottom:1px; }

    /* 2-col stat grid */
    .stat-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:16px; }

    /* Compact header on small screens */
    @media (max-width:768px) {
        .header-title { font-size:1.1rem!important; letter-spacing:.5px!important; }
        .header-subtitle { display:none; }
        .header-icon { font-size:1.6rem!important; }
        .app-header { padding:10px 14px 8px!important; margin-bottom:6px!important; }
    }
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
        "admin_pw_hash": ADMIN_PASSWORD_HASH,
        "active_page": "dashboard",
        "rollcall_state": {},   # {bus_name: {member_name: bool}}
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
    timeout = st.session_state.get("session_timeout_minutes", SESSION_TIMEOUT_MINUTES)
    elapsed = (datetime.now() - start).total_seconds() / 60
    if elapsed > timeout:
        logout()
        return False
    return True

def session_remaining_minutes():
    start = st.session_state.get("session_start")
    if not start:
        return 0
    timeout = st.session_state.get("session_timeout_minutes", SESSION_TIMEOUT_MINUTES)
    elapsed = (datetime.now() - start).total_seconds() / 60
    return max(0, int(timeout - elapsed))

def login(username: str, password: str) -> bool:
    lockout = st.session_state.get("lockout_until")
    if lockout and datetime.now() < lockout:
        return False
    pw_hash = st.session_state.get("admin_pw_hash", ADMIN_PASSWORD_HASH)
    if username == ADMIN_USERNAME and verify_password(password, pw_hash):
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
    entry = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": action, "detail": detail}
    logs = []
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.insert(0, entry)
    logs = logs[:200]
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

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

def get_all_members(buses):
    all_members = []
    for bus_name, members in buses.items():
        for m in members:
            all_members.append({
                t("bus_col"): bus_name,
                t("name_col"): m["name"],
                t("role_col"): m.get("role", ""),
                t("added_col"): m.get("added", ""),
                t("phone"): m.get("phone", ""),
                t("notes"): m.get("note", ""),
            })
    return all_members

# ─── Init ─────────────────────────────────────────────────────────────────────
init_security()

if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data
buses = data.setdefault("buses", {})
capacity = data.setdefault("capacity", {})

# ─── Role styling helper ───────────────────────────────────────────────────────
def role_class(role):
    r = role.lower() if role else ""
    if "leader" in r or "قائد" in r:
        return "role-tag role-leader"
    if "driver" in r or "سائق" in r:
        return "role-tag role-driver"
    return "role-tag"

# ─── LOGIN PAGE ───────────────────────────────────────────────────────────────
if not check_session_valid():
    col_lang_top = st.columns([8, 1])[1]
    with col_lang_top:
        if st.button(t("toggle_lang"), key="lang_toggle_login"):
            st.session_state.lang = "ar" if st.session_state.lang == "en" else "en"
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 1.4, 1])
    with center_col:
        st.markdown(f"""
        <div class="login-container {'rtl' if is_ar() else ''}">
            <div style="text-align:center;font-size:2.8rem;margin-bottom:10px;">🚌</div>
            <div class="login-title">{t('login_title')}</div>
            <div class="login-subtitle">{t('login_subtitle')}</div>
        </div>""", unsafe_allow_html=True)

    _, center_col2, _ = st.columns([1, 1.4, 1])
    with center_col2:
        locked, lock_mins = is_locked_out()
        if locked:
            st.error(t("locked_out", m=lock_mins))
        else:
            username_input = st.text_input(t("username"), placeholder="admin", key="login_user")
            password_input = st.text_input(t("password"), type="password", key="login_pass")
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
        st.markdown('<div style="text-align:center;margin-top:14px;font-size:.72rem;color:#444;">🔒 Bus Logistics Manager — Secured</div>', unsafe_allow_html=True)
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATED APP
# ═══════════════════════════════════════════════════════════════════════════════

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # Branding
    st.markdown("""
    <div style="text-align:center;padding:12px 0 8px;border-bottom:1px solid #2a2a2a;margin-bottom:10px;">
        <div style="font-size:2rem;">🚌</div>
        <div style="font-family:'Oswald',sans-serif;font-size:1rem;font-weight:700;color:#f0ebe0;text-transform:uppercase;letter-spacing:2px;">Bus Manager</div>
    </div>""", unsafe_allow_html=True)

    # Language toggle
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        if st.button("🇬🇧 EN", use_container_width=True, key="lang_en"):
            st.session_state.lang = "en"
            st.rerun()
    with col_l2:
        if st.button("🇩🇿 AR", use_container_width=True, key="lang_ar"):
            st.session_state.lang = "ar"
            st.rerun()

    st.markdown('<div class="security-notice">🔐 Secured — All actions logged</div>', unsafe_allow_html=True)

    # ── Navigation ──────────────────────────────────────────────────────────
    st.markdown('<div class="nav-section">Navigation</div>', unsafe_allow_html=True)

    pages = [
        ("dashboard", t("page_dashboard")),
        ("buses",     t("page_buses")),
        ("rollcall",  t("page_rollcall")),
        ("search",    t("page_search")),
        ("analytics", t("page_analytics")),
        ("settings",  t("page_settings")),
    ]
    for page_id, page_label in pages:
        is_active = st.session_state.active_page == page_id
        active_cls = "active" if is_active else ""
        if st.button(page_label, key=f"nav_{page_id}", use_container_width=True):
            st.session_state.active_page = page_id
            st.rerun()

    st.markdown("---")

    # ── Quick Add Bus ────────────────────────────────────────────────────────
    st.markdown(f"### ➕ {t('new_bus')}")
    new_bus_name = st.text_input(t("bus_name"), placeholder="Bus A" if not is_ar() else "حافلة أ", key="new_bus_input", label_visibility="collapsed")
    new_bus_cap  = st.number_input(t("capacity"), min_value=1, max_value=200, value=DEFAULT_CAPACITY, key="new_cap", label_visibility="collapsed")
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

    st.markdown("---")

    # ── Move Member ─────────────────────────────────────────────────────────
    if len(buses) >= 2:
        st.markdown(f"### 🔄 {t('move_member')}")
        from_bus = st.selectbox(t("from_bus"), list(buses.keys()), key="move_from", label_visibility="collapsed")
        if buses.get(from_bus):
            member_names = [m["name"] for m in buses[from_bus]]
            move_member_sel = st.selectbox(t("member"), member_names, key="move_member_sel", label_visibility="collapsed")
            to_bus_options = [b for b in buses if b != from_bus]
            to_bus = st.selectbox(t("to_bus"), to_bus_options, key="move_to", label_visibility="collapsed")
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
        st.markdown("---")

    # ── Export ───────────────────────────────────────────────────────────────
    st.markdown(f"### 📤 {t('export')}")
    if buses:
        all_m = get_all_members(buses)
        if all_m:
            df_export = pd.DataFrame(all_m)
            csv_bytes = df_export.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                t("download_csv"), data=csv_bytes,
                file_name=f"bus_roster_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv", use_container_width=True,
            )
            json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
            st.download_button(
                t("download_json"), data=json_bytes,
                file_name=f"bus_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json", use_container_width=True,
            )

    st.markdown("---")

    # ── Session / Logout ─────────────────────────────────────────────────────
    with st.expander(f"👤 {t('session_info')}", expanded=False):
        st.caption(t("welcome"))
        st.caption(t("expires_in", m=session_remaining_minutes()))
        if st.button(t("logout_btn"), use_container_width=True, key="logout_btn"):
            logout()
            st.rerun()

    # ── Audit Log ────────────────────────────────────────────────────────────
    with st.expander(f"📋 {t('audit_log')}", expanded=False):
        audit_entries = load_audit()
        if audit_entries:
            for entry in audit_entries[:20]:
                action_color = {"LOGIN":"#4caf7a","LOGOUT":"#aaa","LOGIN_FAIL":"#ff6b6b","LOCKOUT":"#ff0000"}.get(entry["action"],"#d4a843")
                st.markdown(f"""<div class="audit-row">
                    <span style="color:{action_color};font-weight:700">{entry['action']}</span>
                    &nbsp;·&nbsp; {entry['timestamp']}<br>
                    <span style="color:#999">{entry['detail']}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("No audit entries yet.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTING
# ═══════════════════════════════════════════════════════════════════════════════
page = st.session_state.get("active_page", "dashboard")

# Totals (used by multiple pages)
total_members   = sum(len(m) for m in buses.values())
total_buses_val = len(buses)
total_cap_val   = sum(capacity.get(b, DEFAULT_CAPACITY) for b in buses)
full_buses_val  = sum(1 for b in buses if len(buses[b]) >= capacity.get(b, DEFAULT_CAPACITY))
seats_avail     = max(0, total_cap_val - total_members)

# ── Header ───────────────────────────────────────────────────────────────────
page_label_map = {p[0]: p[1] for p in pages}
st.markdown(f"""
<div class="app-header {'rtl' if is_ar() else ''}">
    <div class="header-icon">🚌</div>
    <div>
        <div class="header-title">{t('app_title')}</div>
        <div class="header-subtitle">{t('app_subtitle')}</div>
    </div>
    <div class="header-page-badge">{page_label_map.get(page,'')}</div>
</div>""", unsafe_allow_html=True)

# ── Mobile-first Top Navigation Bar ──────────────────────────────────────────
# Rendered as real Streamlit columns so buttons actually work on mobile
nav_icons   = ["📊","🚌","✅","🔍","📈","⚙️"]
nav_ids     = ["dashboard","buses","rollcall","search","analytics","settings"]
nav_labels_short = ["Dash","Roster","Roll Call","Search","Stats","Settings"]
nav_cols = st.columns(len(nav_ids))
for col_n, (nid, nicon, nlabel) in zip(nav_cols, zip(nav_ids, nav_icons, nav_labels_short)):
    with col_n:
        is_active_nav = page == nid
        btn_style = "background:linear-gradient(180deg,rgba(206,17,38,.22),rgba(0,122,61,.12));border:1px solid #ce1126;color:#f0ebe0;" if is_active_nav else ""
        # We use a tiny markdown to set active style then a button
        if is_active_nav:
            st.markdown(f"""<div style="text-align:center;margin-bottom:-10px">
                <span style="font-size:.95rem">{nicon}</span><br>
                <span style="font-size:.58rem;color:#ce1126;font-family:'Oswald',sans-serif;text-transform:uppercase;letter-spacing:.3px">{nlabel}</span>
            </div>""", unsafe_allow_html=True)
        else:
            if st.button(f"{nicon}\n{nlabel}", key=f"mobnav_{nid}", use_container_width=True):
                st.session_state.active_page = nid
                st.rerun()

# thin separator
st.markdown('<hr style="margin:4px 0 14px;border-color:#2a2a2a">', unsafe_allow_html=True)


# ════════════════════════════════════════════════
# PAGE: DASHBOARD
# ════════════════════════════════════════════════
if page == "dashboard":
    # Stat cards — 2x2 HTML grid (mobile-friendly)
    stats_data = [
        (total_buses_val,  t("total_buses"),    ""),
        (total_members,    t("total_members"),  ""),
        (seats_avail,      t("seats_available"),"stat-green"),
        (full_buses_val,   t("full_buses"),     ""),
    ]
    cards_html = '<div class="stat-grid">'
    for num, label, cls in stats_data:
        cards_html += f'<div class="stat-card {cls}"><div class="stat-num">{num}</div><div class="stat-label">{label}</div></div>'
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Fleet occupancy overview
    if buses:
        st.markdown("### 🚌 Fleet Overview")
        for bname, members in buses.items():
            cap = capacity.get(bname, DEFAULT_CAPACITY)
            count = len(members)
            pct = count / cap if cap > 0 else 0
            is_full = count >= cap
            badge = f'<span class="{"warning-badge" if is_full else "ok-badge"}">{t("full_badge") if is_full else t("ok_badge")}</span>'
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"""<div style="margin-bottom:4px">
                    <span style="font-family:'Oswald',sans-serif;font-size:1rem;text-transform:uppercase;letter-spacing:.5px">{bname}</span>
                    {badge}
                    <span style="font-size:.8rem;color:#777;margin-left:10px">{count} / {cap}</span>
                </div>""", unsafe_allow_html=True)
                st.progress(min(pct, 1.0))
            with col_b:
                pct_val = int(pct * 100)
                color = "#ce1126" if pct_val >= 90 else "#d4a843" if pct_val >= 70 else "#007a3d"
                st.markdown(f'<div style="text-align:right;font-family:Oswald,sans-serif;font-size:1.6rem;font-weight:700;color:{color};line-height:1.2;padding-top:4px">{pct_val}%</div>', unsafe_allow_html=True)
    else:
        st.info(t("no_buses"))

    # Duplicate check
    all_names_list = [m["name"].lower() for members in buses.values() for m in members]
    duplicates = set(n for n in all_names_list if all_names_list.count(n) > 1)
    if duplicates:
        st.markdown(f"### {t('duplicate_warning')}")
        for dup in duplicates:
            dup_buses = [b for b, members in buses.items() if any(m["name"].lower() == dup for m in members)]
            st.markdown(f'<div class="duplicate-warning">⚠️ <b>{dup.title()}</b> {t("appears_in")}: {", ".join(dup_buses)}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════
# PAGE: BUS ROSTER
# ════════════════════════════════════════════════
elif page == "buses":
    if not buses:
        st.info(t("no_buses"))
    else:
        # Delete bus inline
        if buses:
            with st.expander(f"🗑️ {t('delete_bus')}", expanded=False):
                del_bus = st.selectbox(t("select_bus_delete"), list(buses.keys()), key="del_bus")
                if st.button(t("delete_bus"), key="del_bus_btn"):
                    st.session_state["confirm_delete"] = True
                if st.session_state.get("confirm_delete"):
                    st.warning(t("confirm_delete", b=del_bus))
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(t("yes_delete"), key="confirm_del_yes"):
                            log_audit("DELETE_BUS", f"Deleted bus '{del_bus}' with {len(buses[del_bus])} members")
                            del buses[del_bus]
                            capacity.pop(del_bus, None)
                            save_data(data)
                            st.session_state["confirm_delete"] = False
                            st.rerun()
                    with c2:
                        if st.button(t("cancel"), key="confirm_del_no"):
                            st.session_state["confirm_delete"] = False
                            st.rerun()

        tab_labels = list(buses.keys()) + [t("all_members_title")]
        tabs = st.tabs(tab_labels)

        for i, bname in enumerate(buses.keys()):
            with tabs[i]:
                members = buses[bname]
                cap = capacity.get(bname, DEFAULT_CAPACITY)
                count = len(members)
                pct = count / cap if cap > 0 else 0
                is_full = count >= cap

                col_info, col_add = st.columns([1, 1])

                with col_info:
                    badge_html = f'<span class="{"warning-badge" if is_full else "ok-badge"}">{t("full_badge") if is_full else t("ok_badge")}</span>'
                    st.markdown(f"""<div class="bus-card">
                        <div class="bus-title">{bname} {badge_html}</div>
                        <div class="bus-count">{count}</div>
                        <div class="bus-label">{t('seats_of', c=cap)}</div>
                    </div>""", unsafe_allow_html=True)
                    st.progress(min(pct, 1.0))

                with col_add:
                    st.markdown(f"#### ✚ {t('add_member')}")
                    new_name  = st.text_input(t("name_col"), key=f"name_{bname}", placeholder=t("name_placeholder"))
                    new_role  = st.selectbox(t("role"), t("roles"), key=f"role_{bname}")
                    new_phone = st.text_input(t("phone"), key=f"phone_{bname}", placeholder=t("add_phone"))
                    new_note  = st.text_input(t("notes"), key=f"note_{bname}", placeholder=t("add_note"))
                    if st.button(t("add_btn"), key=f"add_{bname}", use_container_width=True):
                        if new_name.strip():
                            if count >= cap:
                                st.error(t("bus_full", c=cap))
                            else:
                                buses[bname].append({
                                    "name":  new_name.strip(),
                                    "role":  new_role,
                                    "phone": new_phone.strip(),
                                    "note":  new_note.strip(),
                                    "added": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                })
                                save_data(data)
                                log_audit("ADD_MEMBER", f"Added '{new_name.strip()}' (role:{new_role}) to '{bname}'")
                                st.success(t("added_success", n=new_name.strip()))
                                st.rerun()
                        else:
                            st.warning(t("enter_name"))

                # Capacity edit
                with st.expander(t("edit_capacity")):
                    new_cap_val = st.number_input(t("max_seats"), min_value=1, max_value=500, value=cap, key=f"cap_{bname}")
                    if st.button(t("update_capacity"), key=f"savecap_{bname}"):
                        old_cap = capacity.get(bname, DEFAULT_CAPACITY)
                        capacity[bname] = int(new_cap_val)
                        save_data(data)
                        log_audit("EDIT_CAPACITY", f"Changed '{bname}' capacity from {old_cap} to {new_cap_val}")
                        st.success(t("cap_updated"))
                        st.rerun()

                st.markdown(f"#### 👥 {t('members_count', n=count, c=cap)}")
                if not members:
                    st.info(t("no_members_yet"))
                else:
                    bus_search = st.text_input(t("filter_bus"), placeholder=t("search_in_bus"), key=f"busfilter_{bname}")
                    filtered   = [m for m in members if bus_search.lower() in m["name"].lower()] if bus_search else members

                    for j, m in enumerate(filtered):
                        c1, c2, c3, c4 = st.columns([3, 1.5, 1, 0.5])
                        with c1:
                            phone_html = f'<div class="member-phone">📞 {m.get("phone","")}</div>' if m.get("phone") else ""
                            note_html  = f'<div class="member-note">📝 {m.get("note","")}</div>' if m.get("note") else ""
                            st.markdown(f'<b>{m["name"]}</b>{phone_html}{note_html}', unsafe_allow_html=True)
                        with c2:
                            rc = role_class(m.get("role", ""))
                            st.markdown(f'<span class="{rc}">{m.get("role","Member")}</span>', unsafe_allow_html=True)
                        with c3:
                            st.markdown(f'<span style="font-size:.72rem;color:#555">{m.get("added","")[:10]}</span>', unsafe_allow_html=True)
                        with c4:
                            orig_idx = next((idx for idx, om in enumerate(buses[bname]) if om["name"] == m["name"]), None)
                            if st.button("✕", key=f"del_{bname}_{j}_{m['name']}"):
                                if orig_idx is not None:
                                    removed_name = buses[bname][orig_idx]["name"]
                                    buses[bname].pop(orig_idx)
                                    save_data(data)
                                    log_audit("REMOVE_MEMBER", f"Removed '{removed_name}' from '{bname}'")
                                    st.rerun()

        # All Members tab
        with tabs[-1]:
            st.markdown(f"#### 📋 {t('all_members_title')}")
            all_m = get_all_members(buses)
            if all_m:
                df_all = pd.DataFrame(all_m)
                st.dataframe(df_all, use_container_width=True, hide_index=True)
                st.markdown(f"**{t('total_label', n=len(all_m), b=len(buses))}**")
            else:
                st.info(t("no_members_yet"))


# ════════════════════════════════════════════════
# PAGE: ROLL CALL
# ════════════════════════════════════════════════
elif page == "rollcall":
    st.markdown(f"### ✅ {t('rollcall_title')}")
    st.markdown(f"<p style='color:#777;font-size:.85rem'>{t('rollcall_subtitle')}</p>", unsafe_allow_html=True)

    if not buses:
        st.info(t("no_buses"))
    else:
        rc_bus = st.selectbox(t("select_bus_rc"), list(buses.keys()), key="rc_bus_sel")
        members = buses.get(rc_bus, [])

        # Init roll call state for this bus
        if rc_bus not in st.session_state.rollcall_state:
            st.session_state.rollcall_state[rc_bus] = {}
        rc_state = st.session_state.rollcall_state[rc_bus]

        # Ensure all members have an entry
        for m in members:
            if m["name"] not in rc_state:
                rc_state[m["name"]] = False

        total_rc = len(members)
        boarded_count = sum(1 for m in members if rc_state.get(m["name"], False))

        # Progress display
        pct_rc = boarded_count / total_rc if total_rc > 0 else 0
        color_rc = "#007a3d" if pct_rc >= 1.0 else "#d4a843" if pct_rc >= 0.5 else "#ce1126"
        st.markdown(f"""<div class="rc-progress-wrap">
            <div style="display:flex;align-items:baseline;gap:10px">
                <div class="rc-fraction" style="color:{color_rc}">{boarded_count}</div>
                <div style="font-family:'Oswald',sans-serif;font-size:1.8rem;color:#555">/ {total_rc}</div>
                <div class="rc-label" style="margin-left:8px">{t('boarded')}</div>
            </div>
            <div style="background:#252525;border-radius:4px;height:10px;margin-top:10px;overflow:hidden">
                <div style="height:100%;width:{int(pct_rc*100)}%;background:{color_rc};border-radius:4px;transition:width .4s"></div>
            </div>
            {"<div style='margin-top:10px;font-size:1.2rem;color:#4caf7a;font-weight:700'>" + t('rollcall_complete') + "</div>" if pct_rc >= 1.0 and total_rc > 0 else ""}
        </div>""", unsafe_allow_html=True)

        # Controls row
        col_a, col_b, col_c = st.columns([1, 1, 2])
        with col_a:
            st.markdown('<div class="btn-green">', unsafe_allow_html=True)
            if st.button(t("mark_all_boarded"), use_container_width=True, key="rc_all"):
                for m in members:
                    rc_state[m["name"]] = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_b:
            st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
            if st.button(t("reset_rollcall"), use_container_width=True, key="rc_reset"):
                for m in members:
                    rc_state[m["name"]] = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_c:
            # Export roll call
            if members:
                rc_export_data = []
                for m in members:
                    rc_export_data.append({
                        "Name": m["name"],
                        "Role": m.get("role", ""),
                        "Phone": m.get("phone", ""),
                        "Boarded": "✅" if rc_state.get(m["name"]) else "❌",
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
                rc_df = pd.DataFrame(rc_export_data)
                rc_csv = rc_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(
                    t("rc_export"), data=rc_csv,
                    file_name=f"rollcall_{rc_bus}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv", use_container_width=True, key="rc_download",
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # Filter pending first
        pending   = [m for m in members if not rc_state.get(m["name"], False)]
        boarded_l = [m for m in members if rc_state.get(m["name"], False)]

        if pending:
            st.markdown(f"**⏳ Not Yet Boarded ({len(pending)})**")
            for m in pending:
                col_check, col_info2 = st.columns([0.08, 0.92])
                with col_check:
                    checked = st.checkbox("", key=f"rc_chk_{rc_bus}_{m['name']}", value=False, label_visibility="collapsed")
                    if checked:
                        rc_state[m["name"]] = True
                        log_audit("ROLL_CALL", f"'{m['name']}' marked as boarded on '{rc_bus}'")
                        st.rerun()
                with col_info2:
                    rc_cls  = role_class(m.get("role", ""))
                    ph_html = f'<span style="font-size:.72rem;color:#42a5f5;margin-left:12px">📞 {m.get("phone","")}</span>' if m.get("phone") else ""
                    st.markdown(f"""<div class="rc-row-pending">
                        <span class="rc-name-pending">{m['name']}</span>
                        <span class="{rc_cls}" style="margin-left:10px">{m.get('role','')}</span>
                        {ph_html}
                    </div>""", unsafe_allow_html=True)

        if boarded_l:
            st.markdown(f"**✅ Boarded ({len(boarded_l)})**")
            for m in boarded_l:
                col_check2, col_info3 = st.columns([0.08, 0.92])
                with col_check2:
                    checked2 = st.checkbox("", key=f"rc_chk_{rc_bus}_{m['name']}", value=True, label_visibility="collapsed")
                    if not checked2:
                        rc_state[m["name"]] = False
                        st.rerun()
                with col_info3:
                    st.markdown(f"""<div class="rc-row-boarded">
                        <span class="rc-name-boarded">{m['name']}</span>
                        <span style="font-size:.72rem;color:#4caf7a;margin-left:10px">{m.get('role','')}</span>
                    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════
# PAGE: SEARCH
# ════════════════════════════════════════════════
elif page == "search":
    st.markdown(f"### 🔍 {t('search_label')}")
    search_query = st.text_input(
        t("search_label"), placeholder=t("search_placeholder"),
        key="global_search", label_visibility="collapsed"
    )
    if search_query:
        results = []
        for bname, members in buses.items():
            for m in members:
                score = 0
                if search_query.lower() in m["name"].lower():
                    score = 2 if m["name"].lower().startswith(search_query.lower()) else 1
                if score > 0:
                    results.append({
                        "_score": score,
                        t("bus_col"):   bname,
                        t("name_col"):  m["name"],
                        t("role_col"):  m.get("role", "—"),
                        t("phone"):     m.get("phone", ""),
                        t("notes"):     m.get("note", ""),
                        t("added_col"): m.get("added", "—"),
                    })
        results.sort(key=lambda x: -x["_score"])
        results = [{k: v for k, v in r.items() if k != "_score"} for r in results]

        if results:
            st.success(t("found_results", n=len(results)))
            st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
        else:
            st.warning(t("no_members_found"))
    else:
        # Show all buses overview while no search
        if buses:
            st.markdown("#### All Buses")
            for bname, members in buses.items():
                cap   = capacity.get(bname, DEFAULT_CAPACITY)
                count = len(members)
                st.markdown(f"**{bname}** — {count}/{cap} members")
        else:
            st.info(t("no_buses"))


# ════════════════════════════════════════════════
# PAGE: ANALYTICS
# ════════════════════════════════════════════════
elif page == "analytics":
    st.markdown(f"### 📈 {t('analytics_title')}")

    if not buses or total_members == 0:
        st.info(t("no_buses"))
    else:
        # KPI row
        avg_occ = int((total_members / total_cap_val * 100)) if total_cap_val > 0 else 0
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div class="stat-card stat-blue">
                <div class="stat-num">{avg_occ}%</div>
                <div class="stat-label">{t('avg_occupancy')}</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="stat-card stat-gold">
                <div class="stat-num">{total_cap_val}</div>
                <div class="stat-label">Total Capacity</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="stat-card stat-green">
                <div class="stat-num">{total_members}</div>
                <div class="stat-label">{t('total_members')}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Occupancy per bus
        st.markdown("#### Occupancy per Bus")
        for bname, members in buses.items():
            cap   = capacity.get(bname, DEFAULT_CAPACITY)
            count = len(members)
            pct   = count / cap if cap > 0 else 0
            color = "#ce1126" if pct >= 0.9 else "#d4a843" if pct >= 0.6 else "#007a3d"
            st.markdown(f"""<div class="analytics-bar-wrap">
                <div class="analytics-bar-label">{bname} — {count}/{cap} ({int(pct*100)}%)</div>
                <div class="analytics-bar-bg">
                    <div class="analytics-bar-fill" style="width:{int(min(pct,1.0)*100)}%;background:{color}"></div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Role distribution
        st.markdown(f"#### {t('most_roles')}")
        role_counts: dict = {}
        for members in buses.values():
            for m in members:
                r = m.get("role", "Member")
                role_counts[r] = role_counts.get(r, 0) + 1

        max_r = max(role_counts.values()) if role_counts else 1
        role_colors = {"Leader":"#d4a843","Driver":"#42a5f5","قائد":"#d4a843","سائق":"#42a5f5"}
        for role, cnt in sorted(role_counts.items(), key=lambda x: -x[1]):
            pct_r = cnt / max_r
            rc_color = role_colors.get(role, "#007a3d")
            st.markdown(f"""<div class="analytics-bar-wrap">
                <div class="analytics-bar-label">{role} — {cnt}</div>
                <div class="analytics-bar-bg">
                    <div class="analytics-bar-fill" style="width:{int(pct_r*100)}%;background:{rc_color}"></div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Members added over time (by date)
        st.markdown(f"#### {t('timeline')}")
        date_counts: dict = {}
        for members in buses.values():
            for m in members:
                added = m.get("added", "")[:10]
                if added:
                    date_counts[added] = date_counts.get(added, 0) + 1
        if date_counts:
            sorted_dates = sorted(date_counts.items())
            df_timeline = pd.DataFrame(sorted_dates, columns=["Date", "Members Added"])
            st.dataframe(df_timeline, use_container_width=True, hide_index=True)
        else:
            st.info("No timeline data yet.")


# ════════════════════════════════════════════════
# PAGE: SETTINGS
# ════════════════════════════════════════════════
elif page == "settings":
    st.markdown(f"### ⚙️ {t('settings_title')}")

    # ── Change Password ───────────────────────────────────────────────────────
    with st.expander(f"🔑 {t('change_password')}", expanded=False):
        cur_pw   = st.text_input(t("current_password"), type="password", key="cur_pw")
        new_pw   = st.text_input(t("new_password"),     type="password", key="new_pw")
        conf_pw  = st.text_input(t("confirm_password"), type="password", key="conf_pw")
        if st.button(t("save_password"), key="save_pw"):
            stored_hash = st.session_state.get("admin_pw_hash", ADMIN_PASSWORD_HASH)
            if not verify_password(cur_pw, stored_hash):
                st.error(t("password_wrong"))
            elif new_pw != conf_pw:
                st.error(t("password_mismatch"))
            elif len(new_pw) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                st.session_state.admin_pw_hash = hash_password(new_pw)
                log_audit("CHANGE_PASSWORD", "Admin changed their password")
                st.success(t("password_changed"))

    # ── Session timeout ───────────────────────────────────────────────────────
    with st.expander("⏱ Session Timeout", expanded=False):
        current_timeout = st.session_state.get("session_timeout_minutes", SESSION_TIMEOUT_MINUTES)
        new_timeout = st.number_input(t("session_timeout"), min_value=5, max_value=240, value=current_timeout, key="sess_timeout")
        if st.button("Save Timeout", key="save_timeout"):
            st.session_state.session_timeout_minutes = int(new_timeout)
            st.success(f"Session timeout set to {new_timeout} minutes.")

    # ── Delete specific bus ───────────────────────────────────────────────────
    with st.expander(f"🗑️ {t('delete_bus')}", expanded=False):
        if buses:
            del_bus_s = st.selectbox(t("select_bus_delete"), list(buses.keys()), key="del_bus_settings")
            if st.button(t("delete_bus"), key="del_bus_settings_btn"):
                st.session_state["confirm_delete_settings"] = True
            if st.session_state.get("confirm_delete_settings"):
                st.warning(t("confirm_delete", b=del_bus_s))
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(t("yes_delete"), key="confirm_del_settings_yes"):
                        log_audit("DELETE_BUS", f"Deleted bus '{del_bus_s}'")
                        del buses[del_bus_s]
                        capacity.pop(del_bus_s, None)
                        save_data(data)
                        st.session_state["confirm_delete_settings"] = False
                        st.rerun()
                with c2:
                    if st.button(t("cancel"), key="confirm_del_settings_no"):
                        st.session_state["confirm_delete_settings"] = False
                        st.rerun()
        else:
            st.info(t("no_buses"))

    # ── Danger zone ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### ⚠️ {t('danger_zone')}")
    with st.expander(t("clear_all_data"), expanded=False):
        st.warning("This will permanently delete all buses and members. There is no undo.")
        confirm_text = st.text_input(t("confirm_clear"), key="clear_confirm_input")
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button(t("clear_all_data"), key="clear_data_btn"):
            if confirm_text == "CONFIRM":
                data["buses"] = {}
                data["capacity"] = {}
                st.session_state.data = data
                st.session_state.rollcall_state = {}
                save_data(data)
                log_audit("CLEAR_ALL_DATA", "All bus data wiped by admin")
                st.success(t("data_cleared"))
                st.rerun()
            else:
                st.error("Type CONFIRM exactly to proceed.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Full Audit Log ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### 📋 {t('audit_log')} (Full)")
    audit_entries = load_audit()
    if audit_entries:
        df_audit = pd.DataFrame(audit_entries)
        st.dataframe(df_audit, use_container_width=True, hide_index=True)
        audit_csv = df_audit.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ Download Audit Log", data=audit_csv,
                           file_name=f"audit_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
    else:
        st.caption("No audit entries yet.")
