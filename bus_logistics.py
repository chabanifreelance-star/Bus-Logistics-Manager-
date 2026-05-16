import streamlit as st
import pandas as pd
import json
import os
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

# ─── Constants ────────────────────────────────────────────────────────────────
DATA_FILE                 = "bus_data.json"
AUDIT_FILE                = "audit_log.json"
DEFAULT_CAPACITY          = 50
ADMIN_USERNAME            = "admin"
ADMIN_PASSWORD_HASH       = hashlib.sha256("Admin@2024!".encode()).hexdigest()
SESSION_TIMEOUT_MINUTES   = 30
MAX_LOGIN_ATTEMPTS        = 5
LOCKOUT_DURATION_MINUTES  = 15

# ─── Page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="Bus Logistics Manager | مدير النقل",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Translations ─────────────────────────────────────────────────────────────
T = {
    "en": {
        "app_title":        "Bus Logistics",
        "app_subtitle":     "Fleet management",
        "login_title":      "Admin Login",
        "login_subtitle":   "Secure access required",
        "username":         "Username",
        "password":         "Password",
        "login_btn":        "Sign In",
        "logout_btn":       "Sign Out",
        "wrong_creds":      "Invalid username or password.",
        "locked_out":       "Too many failed attempts. Try again in {m} minutes.",
        "session_expired":  "Session expired. Please sign in again.",
        "welcome":          "Welcome, Admin",
        "new_bus":          "New Bus",
        "bus_name":         "Bus name",
        "capacity":         "Capacity",
        "create_bus":       "Create Bus",
        "delete_bus":       "Delete Bus",
        "select_bus_delete":"Select bus to delete",
        "confirm_delete":   "Delete {b} and all its members?",
        "yes_delete":       "Yes, Delete",
        "cancel":           "Cancel",
        "move_member":      "Move Member",
        "from_bus":         "From bus",
        "to_bus":           "To bus",
        "member":           "Member",
        "move_btn":         "Move",
        "export":           "Export",
        "download_csv":     "⬇ Download CSV",
        "download_json":    "⬇ Download JSON",
        "total_buses":      "Buses",
        "total_members":    "Members",
        "seats_available":  "Seats Free",
        "full_buses":       "Full Buses",
        "search_placeholder":"Search by name…",
        "search_label":     "Search Member",
        "found_results":    "{n} result(s) found",
        "no_members_found": "No members found.",
        "duplicate_warning":"⚠️ Duplicate Names",
        "no_buses":         "No buses yet — create one in the sidebar.",
        "add_member":       "Add Member",
        "name_placeholder": "Full name",
        "role":             "Role",
        "roles":            ["Member", "Leader", "Driver", "Assistant", "Other"],
        "add_btn":          "Add ✚",
        "bus_full":         "Bus is full ({c} seats).",
        "enter_name":       "Enter a name.",
        "added_success":    "✅ Added {n}!",
        "edit_capacity":    "⚙️ Edit Capacity",
        "max_seats":        "Max seats",
        "update_capacity":  "Update",
        "cap_updated":      "Capacity updated.",
        "members_count":    "Members — {n} / {c}",
        "filter_bus":       "Filter",
        "search_in_bus":    "Search in this bus…",
        "no_members_yet":   "No members yet.",
        "all_members_title":"All Members",
        "total_label":      "Total: {n} members across {b} buses",
        "bus_created":      "Bus '{b}' created.",
        "bus_exists":       "Bus already exists.",
        "enter_bus_name":   "Enter a bus name.",
        "bus_deleted":      "Bus deleted.",
        "moved_success":    "Moved {m} → {b}.",
        "no_members_bus":   "No members in this bus.",
        "audit_log":        "Audit Log",
        "session_info":     "Session",
        "expires_in":       "Expires in {m} min",
        "full_badge":       "FULL",
        "ok_badge":         "OK",
        "name_col":         "Name",
        "role_col":         "Role",
        "bus_col":          "Bus",
        "added_col":        "Added",
        "appears_in":       "appears in",
        "toggle_lang":      "عربي",
        "seats_of":         "{c} seats",
        "page_dashboard":   "Dashboard",
        "page_buses":       "Bus Roster",
        "page_rollcall":    "Roll Call",
        "page_search":      "Search",
        "page_analytics":   "Analytics",
        "page_settings":    "Settings",
        "rollcall_title":   "Roll Call",
        "rollcall_subtitle":"Mark each person as boarded",
        "select_bus_rc":    "Select bus",
        "boarded":          "Boarded",
        "not_boarded":      "Not Boarded",
        "mark_all_boarded": "✅ Mark All Boarded",
        "reset_rollcall":   "🔄 Reset",
        "rollcall_progress":"{b} / {t} boarded",
        "rollcall_complete":"🎉 All aboard!",
        "rc_export":        "⬇ Export Roll Call CSV",
        "rc_search_label":  "Search members in this bus…",
        "rc_search_placeholder": "Type a name to filter…",
        "analytics_title":  "Fleet Analytics",
        "avg_occupancy":    "Avg Occupancy",
        "most_roles":       "Role Distribution",
        "timeline":         "Members Added Over Time",
        "settings_title":   "Settings",
        "change_password":  "Change Password",
        "current_password": "Current Password",
        "new_password":     "New Password",
        "confirm_password": "Confirm Password",
        "save_password":    "Save Password",
        "password_changed": "Password changed.",
        "password_mismatch":"Passwords do not match.",
        "password_wrong":   "Current password is incorrect.",
        "session_timeout":  "Session Timeout (minutes)",
        "data_management":  "Data Management",
        "clear_all_data":   "⚠️ Clear All Data",
        "confirm_clear":    "Type CONFIRM to wipe all data",
        "data_cleared":     "All data cleared.",
        "danger_zone":      "Danger Zone",
        "notes":            "Notes",
        "add_note":         "Add a note…",
        "save_note":        "Save",
        "note_saved":       "Note saved.",
        "phone":            "Phone",
        "add_phone":        "Phone number",
        "phone_saved":      "Phone saved.",
        "fleet_overview":   "Fleet Overview",
        "attempts_left":    "{n} attempt(s) left before lockout.",
        "lang_label":       "Language",
    },
    "ar": {
        "app_title":        "مدير النقل",
        "app_subtitle":     "إدارة الأسطول",
        "login_title":      "تسجيل دخول المدير",
        "login_subtitle":   "يُشترط الوصول الآمن",
        "username":         "اسم المستخدم",
        "password":         "كلمة المرور",
        "login_btn":        "تسجيل الدخول",
        "logout_btn":       "تسجيل الخروج",
        "wrong_creds":      "اسم المستخدم أو كلمة المرور غير صحيحة.",
        "locked_out":       "محاولات فاشلة كثيرة. أعد المحاولة بعد {m} دقيقة.",
        "session_expired":  "انتهت الجلسة. يرجى تسجيل الدخول مجدداً.",
        "welcome":          "أهلاً، المدير",
        "new_bus":          "حافلة جديدة",
        "bus_name":         "اسم الحافلة",
        "capacity":         "الطاقة",
        "create_bus":       "إنشاء",
        "delete_bus":       "حذف حافلة",
        "select_bus_delete":"اختر الحافلة للحذف",
        "confirm_delete":   "حذف {b} مع جميع أعضائها؟",
        "yes_delete":       "نعم، احذف",
        "cancel":           "إلغاء",
        "move_member":      "نقل عضو",
        "from_bus":         "من الحافلة",
        "to_bus":           "إلى الحافلة",
        "member":           "العضو",
        "move_btn":         "نقل",
        "export":           "تصدير",
        "download_csv":     "⬇ تحميل CSV",
        "download_json":    "⬇ تحميل JSON",
        "total_buses":      "الحافلات",
        "total_members":    "الأعضاء",
        "seats_available":  "مقاعد حرة",
        "full_buses":       "حافلات ممتلئة",
        "search_placeholder":"ابحث عن عضو…",
        "search_label":     "البحث عن عضو",
        "found_results":    "تم العثور على {n} نتيجة",
        "no_members_found": "لم يُعثر على أي عضو.",
        "duplicate_warning":"⚠️ أسماء مكررة",
        "no_buses":         "لا توجد حافلات بعد — أنشئ واحدة من الشريط الجانبي.",
        "add_member":       "إضافة عضو",
        "name_placeholder": "الاسم الكامل",
        "role":             "الدور",
        "roles":            ["عضو", "قائد", "سائق", "مساعد", "أخرى"],
        "add_btn":          "إضافة ✚",
        "bus_full":         "الحافلة ممتلئة ({c} مقعداً).",
        "enter_name":       "أدخل اسماً.",
        "added_success":    "✅ تمت إضافة {n}!",
        "edit_capacity":    "⚙️ تعديل الطاقة",
        "max_seats":        "الحد الأقصى",
        "update_capacity":  "تحديث",
        "cap_updated":      "تم تحديث الطاقة.",
        "members_count":    "الأعضاء — {n} / {c}",
        "filter_bus":       "تصفية",
        "search_in_bus":    "بحث في الحافلة…",
        "no_members_yet":   "لا يوجد أعضاء بعد.",
        "all_members_title":"جميع الأعضاء",
        "total_label":      "الإجمالي: {n} عضواً في {b} حافلات",
        "bus_created":      "تم إنشاء الحافلة '{b}'.",
        "bus_exists":       "الحافلة موجودة بالفعل.",
        "enter_bus_name":   "أدخل اسم الحافلة.",
        "bus_deleted":      "تم حذف الحافلة.",
        "moved_success":    "تم نقل {m} إلى {b}.",
        "no_members_bus":   "لا يوجد أعضاء في هذه الحافلة.",
        "audit_log":        "سجل المراجعة",
        "session_info":     "الجلسة",
        "expires_in":       "تنتهي بعد {m} دقيقة",
        "full_badge":       "ممتلئ",
        "ok_badge":         "متاح",
        "name_col":         "الاسم",
        "role_col":         "الدور",
        "bus_col":          "الحافلة",
        "added_col":        "تاريخ الإضافة",
        "appears_in":       "يظهر في",
        "toggle_lang":      "English",
        "seats_of":         "{c} مقعداً",
        "page_dashboard":   "لوحة التحكم",
        "page_buses":       "قوائم الحافلات",
        "page_rollcall":    "التحقق من الركاب",
        "page_search":      "بحث",
        "page_analytics":   "التحليلات",
        "page_settings":    "الإعدادات",
        "rollcall_title":   "التحقق من الصعود",
        "rollcall_subtitle":"حدد كل شخص صعد الحافلة",
        "select_bus_rc":    "اختر الحافلة",
        "boarded":          "صعد",
        "not_boarded":      "لم يصعد",
        "mark_all_boarded": "✅ تحديد الجميع",
        "reset_rollcall":   "🔄 إعادة تعيين",
        "rollcall_progress":"{b} / {t} صعدوا",
        "rollcall_complete":"🎉 الجميع على متن الحافلة!",
        "rc_export":        "⬇ تصدير CSV",
        "rc_search_label":  "ابحث عن الأعضاء في هذه الحافلة…",
        "rc_search_placeholder": "اكتب اسماً للتصفية…",
        "analytics_title":  "تحليلات الأسطول",
        "avg_occupancy":    "متوسط الإشغال",
        "most_roles":       "توزيع الأدوار",
        "timeline":         "الأعضاء المضافون بمرور الوقت",
        "settings_title":   "الإعدادات",
        "change_password":  "تغيير كلمة المرور",
        "current_password": "كلمة المرور الحالية",
        "new_password":     "كلمة مرور جديدة",
        "confirm_password": "تأكيد كلمة المرور",
        "save_password":    "حفظ",
        "password_changed": "تم تغيير كلمة المرور.",
        "password_mismatch":"كلمتا المرور غير متطابقتين.",
        "password_wrong":   "كلمة المرور الحالية غير صحيحة.",
        "session_timeout":  "مهلة الجلسة (دقائق)",
        "data_management":  "إدارة البيانات",
        "clear_all_data":   "⚠️ مسح جميع البيانات",
        "confirm_clear":    "اكتب CONFIRM لمسح البيانات",
        "data_cleared":     "تم مسح جميع البيانات.",
        "danger_zone":      "منطقة الخطر",
        "notes":            "ملاحظات",
        "add_note":         "أضف ملاحظة…",
        "save_note":        "حفظ",
        "note_saved":       "تم حفظ الملاحظة.",
        "phone":            "الهاتف",
        "add_phone":        "رقم الهاتف",
        "phone_saved":      "تم حفظ الهاتف.",
        "fleet_overview":   "نظرة عامة على الأسطول",
        "attempts_left":    "{n} محاولة متبقية قبل القفل.",
        "lang_label":       "اللغة",
    },
}

# ─── Global CSS ───────────────────────────────────────────────────────────────
# FIX: The sidebar ALWAYS stays LTR in layout/positioning (Streamlit hardcodes
# it to slide from the left). RTL direction is applied only to the main content
# area via the [data-testid="stMain"] selector and the .rtl-content wrapper.
def inject_css(is_rtl: bool):
    text_side = "right" if is_rtl else "left"
    content_dir = "rtl" if is_rtl else "ltr"
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&family=Barlow+Condensed:wght@400;500;600;700&display=swap');

:root {{
    --bg:         #0d0d0d;
    --surface:    #141414;
    --surface2:   #1c1c1c;
    --surface3:   #242424;
    --border:     #2c2c2c;
    --border2:    #383838;
    --red:        #d32f2f;
    --red-soft:   #e57373;
    --red-glow:   rgba(211,47,47,.25);
    --green:      #2e7d32;
    --green-soft: #66bb6a;
    --green-glow: rgba(46,125,50,.25);
    --gold:       #f9a825;
    --blue:       #1565c0;
    --blue-soft:  #64b5f6;
    --white:      #ede8dc;
    --muted:      #6b6b6b;
    --muted2:     #9a9a9a;
    --radius:     10px;
    --radius-sm:  6px;
}}

/* ── Base: font + background only (NO direction here — avoids flipping sidebar) */
html, body, [class*="css"] {{
    font-family: 'Tajawal', 'Barlow Condensed', sans-serif;
    background: var(--bg) !important;
    color: var(--white) !important;
}}
h1,h2,h3,h4,h5 {{
    font-family: 'Barlow Condensed', 'Tajawal', sans-serif;
    font-weight: 600;
    letter-spacing: .4px;
}}
.stApp {{ background: var(--bg) !important; }}

/* ── SIDEBAR: always LTR, always slides from left ── */
[data-testid="stSidebar"] {{
    direction: ltr !important;
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}}
[data-testid="stSidebar"] > div:first-child {{
    padding-top: 1rem;
    direction: ltr !important;
}}

/* ── MAIN CONTENT: RTL only here when Arabic is active ── */
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {{
    direction: {content_dir} !important;
}}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
[data-testid="stSidebarNav"] {{ display: none; }}
button[kind="header"] {{ color: var(--white) !important; }}

/* ── Custom scrollbar ── */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--red); border-radius: 2px; }}

/* ── Buttons ── */
.stButton > button {{
    background: var(--surface2) !important;
    color: var(--white) !important;
    border: 1px solid var(--border2) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Barlow Condensed', 'Tajawal', sans-serif !important;
    font-size: .88rem !important;
    font-weight: 500 !important;
    letter-spacing: .3px !important;
    transition: all .15s !important;
    padding: .38rem .9rem !important;
}}
.stButton > button:hover {{
    background: var(--surface3) !important;
    border-color: var(--red) !important;
    color: var(--white) !important;
}}
.stButton > button:active {{
    background: var(--red) !important;
    border-color: var(--red) !important;
}}

/* ── Nav buttons inside sidebar (always LTR layout) ── */
.nav-btn > button {{
    background: transparent !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    color: var(--muted2) !important;
    text-align: left !important;
    padding: .55rem 1rem !important;
    font-size: .95rem !important;
    transition: all .15s !important;
}}
.nav-btn > button:hover {{
    background: var(--surface2) !important;
    color: var(--white) !important;
    border-color: transparent !important;
}}
.nav-btn-active > button {{
    background: linear-gradient(90deg, rgba(211,47,47,.2), transparent) !important;
    border-left: 3px solid var(--red) !important;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0 !important;
    color: var(--white) !important;
    font-weight: 600 !important;
}}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {{
    background: var(--surface2) !important;
    color: var(--white) !important;
    border: 1px solid var(--border2) !important;
    border-radius: var(--radius-sm) !important;
}}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {{
    border-color: var(--red) !important;
    box-shadow: 0 0 0 2px var(--red-glow) !important;
}}
.stSelectbox > div > div:hover {{ border-color: var(--red) !important; }}
label {{ color: var(--muted2) !important; font-size: .8rem !important; }}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background: var(--surface) !important;
    border-radius: var(--radius) var(--radius) 0 0 !important;
    gap: 2px;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: var(--muted) !important;
    font-family: 'Barlow Condensed', 'Tajawal', sans-serif !important;
    font-size: .9rem !important;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
    padding: .5rem 1rem !important;
}}
.stTabs [aria-selected="true"] {{
    color: var(--white) !important;
    border-bottom: 2px solid var(--red) !important;
    background: var(--surface2) !important;
}}

/* ── Expander ── */
.streamlit-expanderHeader {{
    background: var(--surface2) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--muted2) !important;
    font-size: .9rem !important;
}}
.streamlit-expanderContent {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 var(--radius-sm) var(--radius-sm) !important;
}}

/* ── Progress ── */
.stProgress > div > div > div {{
    background: var(--surface2) !important;
    border-radius: 4px !important;
    height: 6px !important;
}}
.stProgress > div > div > div > div {{
    background: linear-gradient(90deg, var(--red), var(--green)) !important;
    border-radius: 4px !important;
}}

/* ── Dataframe ── */
.stDataFrame {{ border-radius: var(--radius) !important; overflow: hidden !important; }}
.stDataFrame iframe {{ border-radius: var(--radius) !important; }}

/* ── Alerts ── */
.stAlert {{ border-radius: var(--radius-sm) !important; }}

/* ── Divider ── */
hr {{ border-color: var(--border) !important; margin: 10px 0 !important; }}

/* ── Component: Stat card ── */
.stat-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 14px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: transform .15s, border-color .15s;
}}
.stat-card:hover {{ transform: translateY(-2px); border-color: var(--red); }}
.stat-card::after {{
    content:''; position:absolute; bottom:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg,var(--red),var(--green));
}}
.stat-num {{
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 2.4rem; font-weight: 700;
    color: var(--red); line-height: 1;
}}
.stat-label {{ font-size: .68rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; }}
.stat-green .stat-num {{ color: var(--green-soft) !important; }}
.stat-blue  .stat-num {{ color: var(--blue-soft)  !important; }}
.stat-gold  .stat-num {{ color: var(--gold)        !important; }}
.stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 1rem; }}

/* ── Component: Bus card ── */
.bus-card {{
    background: linear-gradient(135deg, var(--surface), var(--surface2));
    border: 1px solid var(--border);
    border-{text_side}: 4px solid var(--red);
    border-radius: var(--radius);
    padding: 16px;
    margin-bottom: 8px;
    transition: border-color .2s, box-shadow .2s;
}}
.bus-card:hover {{ box-shadow: 0 4px 20px var(--red-glow); }}
.bus-title {{
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.2rem; font-weight: 600;
    color: var(--white); text-transform: uppercase; letter-spacing: 1px;
}}
.bus-count {{ font-family: 'Barlow Condensed', sans-serif; font-size: 2.4rem; font-weight: 700; color: var(--red); line-height: 1; }}
.bus-sub   {{ font-size: .72rem; color: var(--muted); letter-spacing: 1px; }}

/* ── Component: Badges ── */
.badge {{
    display: inline-block; padding: 2px 8px;
    border-radius: 4px; font-size: .68rem;
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 600; letter-spacing: .8px; text-transform: uppercase;
}}
.badge-full  {{ background: rgba(211,47,47,.18); color: var(--red-soft); border: 1px solid var(--red); }}
.badge-ok    {{ background: rgba(46,125,50,.18); color: var(--green-soft); border: 1px solid var(--green); }}
.badge-warn  {{ background: rgba(249,168,37,.18); color: var(--gold); border: 1px solid var(--gold); }}

/* ── Component: Role tags ── */
.role-tag {{
    display: inline-block; padding: 1px 7px;
    border-radius: 3px; font-size: .7rem; font-weight: 600;
    background: var(--surface3); color: var(--muted2);
    border: 1px solid var(--border);
}}
.role-leader {{ background: rgba(249,168,37,.15); color: var(--gold);       border-color: var(--gold); }}
.role-driver {{ background: rgba(21,101,192,.15); color: var(--blue-soft); border-color: var(--blue); }}

/* ── Component: Member row ── */
.member-row {{
    display: flex; align-items: center; gap: 8px;
    padding: 8px 10px; border-radius: var(--radius-sm);
    border-bottom: 1px solid var(--border);
    transition: background .1s;
}}
.member-row:hover {{ background: var(--surface2); }}
.member-name {{ font-size: .92rem; font-weight: 500; }}
.member-phone {{ font-size: .72rem; color: var(--blue-soft); }}
.member-note  {{ font-size: .72rem; color: var(--muted); font-style: italic; }}

/* ── Component: Roll-call rows ── */
.rc-row {{
    display: flex; align-items: center; gap: 10px;
    padding: 9px 12px; border-radius: var(--radius-sm);
    border-bottom: 1px solid var(--border);
    transition: background .1s;
}}
.rc-boarded   {{ background: rgba(46,125,50,.08); }}
.rc-pending   {{ background: transparent; }}
.rc-name      {{ font-size: .95rem; font-weight: 500; flex: 1; }}
.rc-name.done {{ text-decoration: line-through; color: var(--muted); }}

/* ── Component: Roll Call search box ── */
.rc-search-wrap {{
    background: var(--surface);
    border: 1px solid var(--border2);
    border-radius: var(--radius);
    padding: 10px 14px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.rc-search-icon {{
    font-size: 1rem;
    color: var(--muted);
    flex-shrink: 0;
}}

/* ── Component: Analytics bar ── */
.a-bar-wrap {{ margin-bottom: 10px; }}
.a-bar-label {{ font-size: .82rem; color: var(--muted2); margin-bottom: 3px; }}
.a-bar-bg    {{ background: var(--surface2); border-radius: 4px; height: 8px; overflow: hidden; }}
.a-bar-fill  {{ height: 100%; border-radius: 4px; transition: width .4s; }}

/* ── Component: Progress section (roll call) ── */
.rc-progress {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 18px;
    margin-bottom: 14px;
}}
.rc-fraction {{ font-family: 'Barlow Condensed', sans-serif; font-size: 3rem; font-weight: 700; line-height: 1; }}

/* ── Component: Page header ── */
.page-header {{
    background: linear-gradient(135deg, var(--surface) 0%, #150103 60%, #001507 100%);
    border-bottom: 2px solid var(--red);
    padding: 16px 20px 12px;
    margin: -1rem -1rem 1.2rem -1rem;
    position: relative; overflow: hidden;
}}
.page-header::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg, var(--bg) 0%, var(--red) 33%, var(--white) 33%, var(--white) 66%, var(--green) 66%);
}}
.page-title {{
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.5rem; font-weight: 700;
    color: var(--white); text-transform: uppercase; letter-spacing: 2px;
    line-height: 1.1;
}}
.page-sub {{ font-size: .72rem; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; margin-top: 1px; }}
.page-badge {{
    position: absolute; top: 50%; right: 20px; transform: translateY(-50%);
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 20px; padding: 3px 14px;
    font-size: .68rem; color: var(--muted); letter-spacing: 1px; text-transform: uppercase;
}}

/* ── Component: Sidebar branding ── */
.sidebar-brand {{
    text-align: center;
    padding: 6px 0 16px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 12px;
}}
.sidebar-brand-icon {{ font-size: 2rem; }}
.sidebar-brand-name {{
    font-family: 'Barlow Condensed', 'Tajawal', sans-serif;
    font-size: 1.05rem; font-weight: 700;
    color: var(--white); text-transform: uppercase; letter-spacing: 2px;
    margin-top: 2px;
}}
.sidebar-brand-sub {{ font-size: .65rem; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; }}

/* ── Component: Sidebar section label ── */
.sidebar-section {{
    font-size: .65rem; color: var(--muted); text-transform: uppercase;
    letter-spacing: 1.5px; padding: 10px 0 4px; font-weight: 600;
}}

/* ── Component: Security notice ── */
.security-notice {{
    background: rgba(211,47,47,.07);
    border: 1px solid rgba(211,47,47,.2);
    border-radius: var(--radius-sm);
    padding: 6px 10px;
    font-size: .7rem; color: var(--muted2);
    text-align: center; margin-bottom: 12px;
}}

/* ── Component: Duplicate warning ── */
.dup-warn {{
    background: rgba(249,168,37,.08);
    border: 1px solid rgba(249,168,37,.3);
    border-radius: var(--radius-sm);
    padding: 8px 12px; margin: 4px 0;
    font-size: .82rem; color: var(--gold);
}}

/* ── Component: Audit row ── */
.audit-row {{
    padding: 6px 0;
    border-bottom: 1px solid var(--border);
    font-size: .78rem; line-height: 1.4;
}}

/* ── Component: Login card ── */
.login-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-top: 3px solid var(--red);
    border-radius: var(--radius);
    padding: 32px 28px 28px;
    box-shadow: 0 8px 32px rgba(0,0,0,.5);
}}
.login-title {{
    font-family: 'Barlow Condensed', 'Tajawal', sans-serif;
    font-size: 1.6rem; font-weight: 700;
    color: var(--white); text-transform: uppercase; letter-spacing: 2px;
    text-align: center; margin-bottom: 2px;
}}
.login-sub {{ font-size: .72rem; color: var(--muted); text-align: center; letter-spacing: 1px; margin-bottom: 20px; }}

/* ── Mobile tweaks ── */
@media (max-width: 768px) {{
    .page-title    {{ font-size: 1.15rem !important; letter-spacing: .5px !important; }}
    .page-sub      {{ display: none; }}
    .page-badge    {{ display: none; }}
    .page-header   {{ padding: 10px 14px 8px !important; margin-bottom: 8px !important; }}
    .stat-num      {{ font-size: 1.9rem !important; }}
    .bus-count     {{ font-size: 1.9rem !important; }}
    .rc-fraction   {{ font-size: 2.2rem !important; }}
}}
</style>
""", unsafe_allow_html=True)

# ─── Language helpers ─────────────────────────────────────────────────────────
def t(key: str, **kwargs) -> str:
    lang = st.session_state.get("lang", "en")
    text = T[lang].get(key, T["en"].get(key, key))
    for k, v in kwargs.items():
        text = text.replace("{" + k + "}", str(v))
    return text

def is_ar() -> bool:
    return st.session_state.get("lang", "en") == "ar"

# ─── Security helpers ─────────────────────────────────────────────────────────
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def verify_password(pw: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(pw), hashed)

def init_session():
    defaults = {
        "lang":               "en",
        "authenticated":      False,
        "login_attempts":     0,
        "lockout_until":      None,
        "session_start":      None,
        "session_token":      None,
        "admin_pw_hash":      ADMIN_PASSWORD_HASH,
        "active_page":        "dashboard",
        "rollcall_state":     {},
        "session_timeout_minutes": SESSION_TIMEOUT_MINUTES,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def check_session() -> bool:
    if not st.session_state.get("authenticated"):
        return False
    start = st.session_state.get("session_start")
    if not start:
        return False
    timeout = st.session_state.get("session_timeout_minutes", SESSION_TIMEOUT_MINUTES)
    if (datetime.now() - start).total_seconds() / 60 > timeout:
        _do_logout()
        return False
    return True

def session_mins_left() -> int:
    start = st.session_state.get("session_start")
    if not start:
        return 0
    timeout = st.session_state.get("session_timeout_minutes", SESSION_TIMEOUT_MINUTES)
    return max(0, int(timeout - (datetime.now() - start).total_seconds() / 60))

def _do_logout():
    log_audit("LOGOUT", "Admin logged out")
    st.session_state.authenticated = False
    st.session_state.session_start = None
    st.session_state.session_token = None

def do_login(username: str, password: str) -> bool:
    lockout = st.session_state.get("lockout_until")
    if lockout and datetime.now() < lockout:
        return False
    pw_hash = st.session_state.get("admin_pw_hash", ADMIN_PASSWORD_HASH)
    if username == ADMIN_USERNAME and verify_password(password, pw_hash):
        st.session_state.authenticated   = True
        st.session_state.login_attempts  = 0
        st.session_state.lockout_until   = None
        st.session_state.session_start   = datetime.now()
        st.session_state.session_token   = secrets.token_hex(32)
        log_audit("LOGIN", f"Successful login from '{username}'")
        return True
    st.session_state.login_attempts = st.session_state.get("login_attempts", 0) + 1
    log_audit("LOGIN_FAIL", f"Failed attempt #{st.session_state.login_attempts}")
    if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
        st.session_state.lockout_until = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        log_audit("LOCKOUT", "Account locked — too many failed attempts")
    return False

def is_locked_out():
    lockout = st.session_state.get("lockout_until")
    if lockout and datetime.now() < lockout:
        remaining = int((lockout - datetime.now()).total_seconds() / 60) + 1
        return True, remaining
    return False, 0

# ─── Audit log ────────────────────────────────────────────────────────────────
def log_audit(action: str, detail: str):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "detail": detail,
    }
    logs = []
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE) as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.insert(0, entry)
    with open(AUDIT_FILE, "w") as f:
        json.dump(logs[:200], f, indent=2)

def load_audit() -> list:
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []

# ─── Data persistence ─────────────────────────────────────────────────────────
def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"buses": {}, "capacity": {}}

def save_data(d: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

def all_members_flat(buses: dict) -> list:
    rows = []
    for bname, members in buses.items():
        for m in members:
            rows.append({
                t("bus_col"):   bname,
                t("name_col"):  m["name"],
                t("role_col"):  m.get("role", ""),
                t("phone"):     m.get("phone", ""),
                t("notes"):     m.get("note", ""),
                t("added_col"): m.get("added", ""),
            })
    return rows

# ─── Role badge helper ────────────────────────────────────────────────────────
def role_cls(role: str) -> str:
    r = (role or "").lower()
    if "leader" in r or "قائد" in r:
        return "role-tag role-leader"
    if "driver" in r or "سائق" in r:
        return "role-tag role-driver"
    return "role-tag"

# ═══════════════════════════════════════════════════════════════════════════════
# INITIALISE
# ═══════════════════════════════════════════════════════════════════════════════
init_session()
inject_css(is_ar())

if "data" not in st.session_state:
    st.session_state.data = load_data()

data     = st.session_state.data
buses    = data.setdefault("buses", {})
capacity = data.setdefault("capacity", {})

# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════
if not check_session():
    # Language toggle at top-right of login screen
    top_cols = st.columns([6, 1])
    with top_cols[1]:
        if st.button(t("toggle_lang"), key="lang_login"):
            st.session_state.lang = "ar" if st.session_state.lang == "en" else "en"
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        st.markdown(f"""
        <div class="login-card {'rtl' if is_ar() else ''}">
            <div style="text-align:center;font-size:2.6rem;margin-bottom:8px">🚌</div>
            <div class="login-title">{t('login_title')}</div>
            <div class="login-sub">{t('login_subtitle')}</div>
        </div>
        """, unsafe_allow_html=True)

        locked, lock_mins = is_locked_out()
        if locked:
            st.error(t("locked_out", m=lock_mins))
        else:
            username_in = st.text_input(t("username"), placeholder="admin", key="li_user")
            password_in = st.text_input(t("password"), type="password",    key="li_pass")
            if st.button(t("login_btn"), use_container_width=True, key="li_btn"):
                if do_login(username_in, password_in):
                    st.rerun()
                else:
                    locked2, lm2 = is_locked_out()
                    if locked2:
                        st.error(t("locked_out", m=lm2))
                    else:
                        st.error(t("wrong_creds"))
                        remaining = MAX_LOGIN_ATTEMPTS - st.session_state.get("login_attempts", 0)
                        if remaining <= 2:
                            st.warning(t("attempts_left", n=remaining))

        st.markdown('<div style="text-align:center;margin-top:18px;font-size:.68rem;color:#3a3a3a">🔒 Bus Logistics Manager — Secured</div>', unsafe_allow_html=True)
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATED — SIDEBAR
# Note: sidebar content is always rendered LTR (Streamlit slides from left).
# We do not apply `direction:rtl` inside the sidebar — only in the main area.
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:

    # ── Branding ──────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="sidebar-brand">
        <div class="sidebar-brand-icon">🚌</div>
        <div class="sidebar-brand-name">{t('app_title')}</div>
        <div class="sidebar-brand-sub">{t('app_subtitle')}</div>
    </div>""", unsafe_allow_html=True)

    # ── Language toggle ───────────────────────────────────────────────────────
    st.markdown(f'<div class="sidebar-section">{t("lang_label")}</div>', unsafe_allow_html=True)
    lc1, lc2 = st.columns(2)
    with lc1:
        if st.button("🇬🇧  EN", use_container_width=True, key="sb_lang_en"):
            st.session_state.lang = "en"
            st.rerun()
    with lc2:
        if st.button("🇩🇿  AR", use_container_width=True, key="sb_lang_ar"):
            st.session_state.lang = "ar"
            st.rerun()

    st.markdown('<div class="security-notice">🔐 Secured — All actions logged</div>', unsafe_allow_html=True)

    # ── Navigation ────────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">Navigation</div>', unsafe_allow_html=True)

    nav_pages = [
        ("dashboard", "📊", t("page_dashboard")),
        ("buses",     "🚌", t("page_buses")),
        ("rollcall",  "✅", t("page_rollcall")),
        ("search",    "🔍", t("page_search")),
        ("analytics", "📈", t("page_analytics")),
        ("settings",  "⚙️", t("page_settings")),
    ]
    current_page = st.session_state.get("active_page", "dashboard")

    for pid, picon, plabel in nav_pages:
        is_active = current_page == pid
        cls = "nav-btn nav-btn-active" if is_active else "nav-btn"
        st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
        if st.button(f"{picon}  {plabel}", key=f"nav_{pid}", use_container_width=True):
            st.session_state.active_page = pid
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Create New Bus ────────────────────────────────────────────────────────
    st.markdown(f'<div class="sidebar-section">➕ {t("new_bus")}</div>', unsafe_allow_html=True)
    nb_name = st.text_input(
        t("bus_name"),
        placeholder="Bus A" if not is_ar() else "حافلة أ",
        key="sb_new_bus_name",
        label_visibility="collapsed",
    )
    nb_cap = st.number_input(
        t("capacity"),
        min_value=1, max_value=200, value=DEFAULT_CAPACITY,
        key="sb_new_bus_cap",
        label_visibility="collapsed",
    )
    if st.button(t("create_bus"), use_container_width=True, key="sb_create_bus"):
        name = nb_name.strip()
        if not name:
            st.warning(t("enter_bus_name"))
        elif name in buses:
            st.error(t("bus_exists"))
        else:
            buses[name] = []
            capacity[name] = int(nb_cap)
            save_data(data)
            log_audit("CREATE_BUS", f"Created bus '{name}' cap={nb_cap}")
            st.success(t("bus_created", b=name))
            st.rerun()

    st.markdown("---")

    # ── Move Member ───────────────────────────────────────────────────────────
    if len(buses) >= 2:
        st.markdown(f'<div class="sidebar-section">🔄 {t("move_member")}</div>', unsafe_allow_html=True)
        from_b = st.selectbox(t("from_bus"), list(buses.keys()), key="sb_move_from", label_visibility="collapsed")
        if buses.get(from_b):
            move_sel = st.selectbox(
                t("member"), [m["name"] for m in buses[from_b]],
                key="sb_move_member", label_visibility="collapsed",
            )
            to_b = st.selectbox(
                t("to_bus"), [b for b in buses if b != from_b],
                key="sb_move_to", label_visibility="collapsed",
            )
            if st.button(t("move_btn"), use_container_width=True, key="sb_move_btn"):
                obj = next((m for m in buses[from_b] if m["name"] == move_sel), None)
                if obj:
                    buses[from_b] = [m for m in buses[from_b] if m["name"] != move_sel]
                    buses[to_b].append(obj)
                    save_data(data)
                    log_audit("MOVE_MEMBER", f"Moved '{move_sel}' {from_b} → {to_b}")
                    st.success(t("moved_success", m=move_sel, b=to_b))
                    st.rerun()
        else:
            st.caption(t("no_members_bus"))
        st.markdown("---")

    # ── Export ────────────────────────────────────────────────────────────────
    if buses:
        flat = all_members_flat(buses)
        if flat:
            st.markdown(f'<div class="sidebar-section">📤 {t("export")}</div>', unsafe_allow_html=True)
            df_exp   = pd.DataFrame(flat)
            csv_out  = df_exp.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            json_out = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
            st.download_button(
                t("download_csv"), data=csv_out,
                file_name=f"roster_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv", use_container_width=True, key="sb_dl_csv",
            )
            st.download_button(
                t("download_json"), data=json_out,
                file_name=f"data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json", use_container_width=True, key="sb_dl_json",
            )
            st.markdown("---")

    # ── Session & Logout ──────────────────────────────────────────────────────
    with st.expander(f"👤 {t('session_info')}", expanded=False):
        st.caption(t("welcome"))
        st.caption(t("expires_in", m=session_mins_left()))
        if st.button(t("logout_btn"), use_container_width=True, key="sb_logout"):
            _do_logout()
            st.rerun()

    # ── Audit log (last 20) ───────────────────────────────────────────────────
    with st.expander(f"📋 {t('audit_log')}", expanded=False):
        entries = load_audit()
        if entries:
            action_colors = {
                "LOGIN": "#4caf7a", "LOGOUT": "#9a9a9a",
                "LOGIN_FAIL": "#ef9a9a", "LOCKOUT": "#ef5350",
            }
            for e in entries[:20]:
                col = action_colors.get(e["action"], "#f9a825")
                st.markdown(f"""<div class="audit-row">
                    <span style="color:{col};font-weight:700">{e['action']}</span>
                    &nbsp;·&nbsp; <span style="color:#555">{e['timestamp']}</span><br>
                    <span style="color:#777">{e['detail']}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("No entries yet.")


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED COMPUTED VALUES
# ═══════════════════════════════════════════════════════════════════════════════
page           = st.session_state.get("active_page", "dashboard")
total_members  = sum(len(m) for m in buses.values())
total_buses_n  = len(buses)
total_cap      = sum(capacity.get(b, DEFAULT_CAPACITY) for b in buses)
full_buses_n   = sum(1 for b in buses if len(buses[b]) >= capacity.get(b, DEFAULT_CAPACITY))
seats_free     = max(0, total_cap - total_members)

# ── Page header ───────────────────────────────────────────────────────────────
_page_labels = {pid: lbl for pid, _, lbl in nav_pages}

st.markdown(f"""
<div class="page-header {'rtl' if is_ar() else ''}">
    <div class="page-title">🚌 {t('app_title')}</div>
    <div class="page-sub">{t('app_subtitle')}</div>
    <div class="page-badge">{_page_labels.get(page, '')}</div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "dashboard":

    stats = [
        (total_buses_n, t("total_buses"),   ""),
        (total_members, t("total_members"), ""),
        (seats_free,    t("seats_available"),"stat-green"),
        (full_buses_n,  t("full_buses"),    ""),
    ]
    html = '<div class="stat-grid">'
    for num, label, cls in stats:
        html += f'<div class="stat-card {cls}"><div class="stat-num">{num}</div><div class="stat-label">{label}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    st.markdown(f"### {t('fleet_overview')}")
    if buses:
        for bname, members in buses.items():
            cap   = capacity.get(bname, DEFAULT_CAPACITY)
            count = len(members)
            pct   = count / cap if cap > 0 else 0
            is_full = count >= cap
            badge_cls = "badge-full" if is_full else ("badge-warn" if pct >= 0.75 else "badge-ok")
            badge_txt = t("full_badge") if is_full else t("ok_badge")
            pct_int   = int(pct * 100)
            bar_color = "#d32f2f" if pct_int >= 90 else "#f9a825" if pct_int >= 70 else "#2e7d32"

            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"""
                <div style="margin-bottom:4px">
                    <span style="font-family:'Barlow Condensed',sans-serif;font-size:1rem;text-transform:uppercase;letter-spacing:.5px">{bname}</span>
                    &nbsp;<span class="badge {badge_cls}">{badge_txt}</span>
                    <span style="font-size:.78rem;color:#555;margin-left:8px">{count} / {cap}</span>
                </div>""", unsafe_allow_html=True)
                st.progress(min(pct, 1.0))
            with col_b:
                st.markdown(f'<div style="text-align:right;font-family:Barlow Condensed,sans-serif;font-size:1.6rem;font-weight:700;color:{bar_color};padding-top:4px">{pct_int}%</div>', unsafe_allow_html=True)
    else:
        st.info(t("no_buses"))

    # Duplicate names check
    all_names = [m["name"].lower() for mems in buses.values() for m in mems]
    dups = {n for n in all_names if all_names.count(n) > 1}
    if dups:
        st.markdown(f"### {t('duplicate_warning')}")
        for dup in dups:
            dup_buses = [b for b, mems in buses.items() if any(m["name"].lower() == dup for m in mems)]
            st.markdown(f'<div class="dup-warn">⚠️ <b>{dup.title()}</b> — {t("appears_in")}: {", ".join(dup_buses)}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: BUS ROSTER
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "buses":
    if not buses:
        st.info(t("no_buses"))
    else:
        with st.expander(f"🗑️ {t('delete_bus')}", expanded=False):
            del_sel = st.selectbox(t("select_bus_delete"), list(buses.keys()), key="del_bus_sel")
            if st.button(t("delete_bus"), key="del_bus_btn"):
                st.session_state["_confirm_delete"] = True
            if st.session_state.get("_confirm_delete"):
                st.warning(t("confirm_delete", b=del_sel))
                ca, cb = st.columns(2)
                with ca:
                    if st.button(t("yes_delete"), key="del_yes"):
                        log_audit("DELETE_BUS", f"Deleted '{del_sel}' ({len(buses[del_sel])} members)")
                        del buses[del_sel]
                        capacity.pop(del_sel, None)
                        save_data(data)
                        st.session_state["_confirm_delete"] = False
                        st.rerun()
                with cb:
                    if st.button(t("cancel"), key="del_no"):
                        st.session_state["_confirm_delete"] = False
                        st.rerun()

        tab_labels = list(buses.keys()) + [t("all_members_title")]
        tabs = st.tabs(tab_labels)

        for i, bname in enumerate(buses.keys()):
            with tabs[i]:
                members = buses[bname]
                cap     = capacity.get(bname, DEFAULT_CAPACITY)
                count   = len(members)
                pct     = count / cap if cap > 0 else 0
                is_full = count >= cap

                col_info, col_add = st.columns([1, 1])
                with col_info:
                    badge_cls = "badge-full" if is_full else "badge-ok"
                    badge_txt = t("full_badge") if is_full else t("ok_badge")
                    st.markdown(f"""
                    <div class="bus-card">
                        <div class="bus-title">{bname} <span class="badge {badge_cls}">{badge_txt}</span></div>
                        <div class="bus-count">{count}</div>
                        <div class="bus-sub">{t('seats_of', c=cap)}</div>
                    </div>""", unsafe_allow_html=True)
                    st.progress(min(pct, 1.0))

                with col_add:
                    st.markdown(f"#### ✚ {t('add_member')}")
                    new_name  = st.text_input(t("name_col"),  key=f"nm_{bname}",  placeholder=t("name_placeholder"))
                    new_role  = st.selectbox(t("role"),       t("roles"),          key=f"rl_{bname}")
                    new_phone = st.text_input(t("phone"),     key=f"ph_{bname}",  placeholder=t("add_phone"))
                    new_note  = st.text_input(t("notes"),     key=f"nt_{bname}",  placeholder=t("add_note"))
                    if st.button(t("add_btn"), key=f"add_{bname}", use_container_width=True):
                        name_clean = new_name.strip()
                        if not name_clean:
                            st.warning(t("enter_name"))
                        elif count >= cap:
                            st.error(t("bus_full", c=cap))
                        else:
                            buses[bname].append({
                                "name":  name_clean,
                                "role":  new_role,
                                "phone": new_phone.strip(),
                                "note":  new_note.strip(),
                                "added": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            })
                            save_data(data)
                            log_audit("ADD_MEMBER", f"Added '{name_clean}' role={new_role} to '{bname}'")
                            st.success(t("added_success", n=name_clean))
                            st.rerun()

                with st.expander(t("edit_capacity")):
                    new_cap_v = st.number_input(t("max_seats"), min_value=1, max_value=500, value=cap, key=f"cap_{bname}")
                    if st.button(t("update_capacity"), key=f"savecap_{bname}"):
                        old = capacity.get(bname, DEFAULT_CAPACITY)
                        capacity[bname] = int(new_cap_v)
                        save_data(data)
                        log_audit("EDIT_CAPACITY", f"'{bname}' cap {old} → {new_cap_v}")
                        st.success(t("cap_updated"))
                        st.rerun()

                st.markdown(f"#### 👥 {t('members_count', n=count, c=cap)}")
                if not members:
                    st.info(t("no_members_yet"))
                else:
                    bus_filter = st.text_input(
                        t("filter_bus"), placeholder=t("search_in_bus"),
                        key=f"bf_{bname}", label_visibility="collapsed",
                    )
                    filtered = [m for m in members if bus_filter.lower() in m["name"].lower()] if bus_filter else members

                    for j, m in enumerate(filtered):
                        mc1, mc2, mc3, mc4 = st.columns([3, 1.5, 1, 0.4])
                        with mc1:
                            ph_html = f'<div class="member-phone">📞 {m["phone"]}</div>' if m.get("phone") else ""
                            nt_html = f'<div class="member-note">📝 {m["note"]}</div>'  if m.get("note")  else ""
                            st.markdown(f'<div class="member-row"><div><span class="member-name">{m["name"]}</span>{ph_html}{nt_html}</div></div>', unsafe_allow_html=True)
                        with mc2:
                            st.markdown(f'<span class="{role_cls(m.get("role",""))}">{m.get("role","Member")}</span>', unsafe_allow_html=True)
                        with mc3:
                            st.markdown(f'<span style="font-size:.7rem;color:#555">{m.get("added","")[:10]}</span>', unsafe_allow_html=True)
                        with mc4:
                            orig_idx = next((idx for idx, om in enumerate(buses[bname]) if om["name"] == m["name"]), None)
                            if st.button("✕", key=f"rm_{bname}_{j}_{m['name']}"):
                                if orig_idx is not None:
                                    removed = buses[bname].pop(orig_idx)["name"]
                                    save_data(data)
                                    log_audit("REMOVE_MEMBER", f"Removed '{removed}' from '{bname}'")
                                    st.rerun()

        with tabs[-1]:
            st.markdown(f"#### 📋 {t('all_members_title')}")
            flat = all_members_flat(buses)
            if flat:
                st.dataframe(pd.DataFrame(flat), use_container_width=True, hide_index=True)
                st.caption(t("total_label", n=len(flat), b=len(buses)))
            else:
                st.info(t("no_members_yet"))


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ROLL CALL
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "rollcall":
    st.markdown(f"### ✅ {t('rollcall_title')}")
    st.markdown(f"<p style='color:#6b6b6b;font-size:.85rem'>{t('rollcall_subtitle')}</p>", unsafe_allow_html=True)

    if not buses:
        st.info(t("no_buses"))
    else:
        rc_bus = st.selectbox(t("select_bus_rc"), list(buses.keys()), key="rc_bus")
        members = buses.get(rc_bus, [])

        if rc_bus not in st.session_state.rollcall_state:
            st.session_state.rollcall_state[rc_bus] = {}
        rc = st.session_state.rollcall_state[rc_bus]
        for m in members:
            rc.setdefault(m["name"], False)

        total_rc   = len(members)
        boarded_n  = sum(1 for m in members if rc.get(m["name"]))
        pct_rc     = boarded_n / total_rc if total_rc else 0
        rc_color   = "#2e7d32" if pct_rc >= 1.0 else "#f9a825" if pct_rc >= 0.5 else "#d32f2f"

        # Progress block
        complete_html = f"<div style='margin-top:10px;font-size:1.1rem;color:#66bb6a;font-weight:700'>{t('rollcall_complete')}</div>" if pct_rc >= 1.0 and total_rc > 0 else ""
        st.markdown(f"""
        <div class="rc-progress">
            <div style="display:flex;align-items:baseline;gap:10px">
                <div class="rc-fraction" style="color:{rc_color}">{boarded_n}</div>
                <div style="font-family:'Barlow Condensed',sans-serif;font-size:1.8rem;color:#3a3a3a">/ {total_rc}</div>
                <div style="font-size:.8rem;color:#6b6b6b;text-transform:uppercase;letter-spacing:1px;margin-left:4px">{t('boarded')}</div>
            </div>
            <div style="background:var(--surface2);border-radius:4px;height:8px;margin-top:10px;overflow:hidden">
                <div style="height:100%;width:{int(pct_rc*100)}%;background:{rc_color};border-radius:4px;transition:width .4s"></div>
            </div>
            {complete_html}
        </div>""", unsafe_allow_html=True)

        # Controls row
        ca, cb, cc = st.columns([1, 1, 2])
        with ca:
            if st.button(t("mark_all_boarded"), use_container_width=True, key="rc_all"):
                for m in members:
                    rc[m["name"]] = True
                st.rerun()
        with cb:
            if st.button(t("reset_rollcall"), use_container_width=True, key="rc_reset"):
                for m in members:
                    rc[m["name"]] = False
                st.rerun()
        with cc:
            if members:
                rc_rows = [{
                    "Name": m["name"],
                    "Role": m.get("role", ""),
                    "Phone": m.get("phone", ""),
                    "Boarded": "✅" if rc.get(m["name"]) else "❌",
                } for m in members]
                rc_csv = pd.DataFrame(rc_rows).to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(
                    t("rc_export"), data=rc_csv,
                    file_name=f"rollcall_{rc_bus}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv", use_container_width=True, key="rc_dl",
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Search / filter bar ────────────────────────────────────────────────
        # Lets the admin quickly find a specific member during boarding
        rc_search = st.text_input(
            t("rc_search_label"),
            placeholder=t("rc_search_placeholder"),
            key="rc_search_input",
            label_visibility="collapsed",
        )
        st.markdown(
            f'<div style="font-size:.7rem;color:#555;margin:-8px 0 10px;padding-left:2px">🔍 {t("rc_search_label")}</div>',
            unsafe_allow_html=True,
        )

        def _rc_match(m: dict) -> bool:
            """Return True if this member matches the current search query."""
            if not rc_search:
                return True
            q = rc_search.strip().lower()
            return (
                q in m["name"].lower()
                or q in m.get("role", "").lower()
                or q in m.get("phone", "").lower()
            )

        # Split into pending / boarded, applying the search filter
        pending  = [m for m in members if not rc.get(m["name"]) and _rc_match(m)]
        boarded_ = [m for m in members if     rc.get(m["name"]) and _rc_match(m)]

        # If there is an active search, show counts relative to the filter
        if rc_search:
            total_shown = len(pending) + len(boarded_)
            st.caption(f"🔎 {total_shown} result(s) for "{rc_search.strip()}"")

        if pending:
            st.markdown(f"**⏳ {t('not_boarded')} ({len(pending)})**")
            for m in pending:
                chk_col, info_col = st.columns([0.07, 0.93])
                with chk_col:
                    if st.checkbox("", key=f"rck_{rc_bus}_{m['name']}", value=False, label_visibility="collapsed"):
                        rc[m["name"]] = True
                        log_audit("ROLL_CALL", f"'{m['name']}' boarded on '{rc_bus}'")
                        st.rerun()
                with info_col:
                    ph = f'<span style="font-size:.7rem;color:#64b5f6;margin-left:10px">📞 {m["phone"]}</span>' if m.get("phone") else ""
                    st.markdown(f"""<div class="rc-row rc-pending">
                        <span class="rc-name">{m['name']}</span>
                        <span class="{role_cls(m.get('role',''))}" style="margin-left:8px">{m.get('role','')}</span>
                        {ph}
                    </div>""", unsafe_allow_html=True)

        if boarded_:
            st.markdown(f"**✅ {t('boarded')} ({len(boarded_)})**")
            for m in boarded_:
                chk2, info2 = st.columns([0.07, 0.93])
                with chk2:
                    if not st.checkbox("", key=f"rck_{rc_bus}_{m['name']}", value=True, label_visibility="collapsed"):
                        rc[m["name"]] = False
                        st.rerun()
                with info2:
                    st.markdown(f"""<div class="rc-row rc-boarded">
                        <span class="rc-name done">{m['name']}</span>
                        <span style="font-size:.7rem;color:#66bb6a;margin-left:8px">{m.get('role','')}</span>
                    </div>""", unsafe_allow_html=True)

        if rc_search and not pending and not boarded_:
            st.info(t("no_members_found"))


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SEARCH
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "search":
    st.markdown(f"### 🔍 {t('search_label')}")
    query = st.text_input(
        t("search_label"), placeholder=t("search_placeholder"),
        key="gsearch", label_visibility="collapsed",
    )

    if query:
        results = []
        for bname, members in buses.items():
            for m in members:
                if query.lower() in m["name"].lower():
                    score = 2 if m["name"].lower().startswith(query.lower()) else 1
                    results.append({
                        "_s":            score,
                        t("bus_col"):    bname,
                        t("name_col"):   m["name"],
                        t("role_col"):   m.get("role", "—"),
                        t("phone"):      m.get("phone", ""),
                        t("notes"):      m.get("note", ""),
                        t("added_col"):  m.get("added", "—"),
                    })
        results.sort(key=lambda x: -x["_s"])
        results = [{k: v for k, v in r.items() if k != "_s"} for r in results]
        if results:
            st.success(t("found_results", n=len(results)))
            st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
        else:
            st.warning(t("no_members_found"))
    else:
        if buses:
            st.markdown("#### All Buses")
            for bname, members in buses.items():
                cap   = capacity.get(bname, DEFAULT_CAPACITY)
                count = len(members)
                pct   = count / cap if cap > 0 else 0
                bar_c = "#d32f2f" if pct >= 0.9 else "#f9a825" if pct >= 0.7 else "#2e7d32"
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #1c1c1c">
                    <span style="font-family:'Barlow Condensed',sans-serif;font-size:1rem;text-transform:uppercase;min-width:120px">{bname}</span>
                    <div style="flex:1;background:#1c1c1c;border-radius:3px;height:5px;overflow:hidden">
                        <div style="width:{int(min(pct,1)*100)}%;height:100%;background:{bar_c};border-radius:3px"></div>
                    </div>
                    <span style="font-size:.8rem;color:#6b6b6b;min-width:60px;text-align:right">{count}/{cap}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info(t("no_buses"))


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "analytics":
    st.markdown(f"### 📈 {t('analytics_title')}")

    if not buses or total_members == 0:
        st.info(t("no_buses"))
    else:
        avg_occ = int(total_members / total_cap * 100) if total_cap > 0 else 0

        kpi_html = '<div class="stat-grid">'
        for num, label, cls in [
            (f"{avg_occ}%", t("avg_occupancy"),    "stat-blue"),
            (total_cap,     "Total Capacity",       "stat-gold"),
            (total_members, t("total_members"),     "stat-green"),
            (total_buses_n, t("total_buses"),       ""),
        ]:
            kpi_html += f'<div class="stat-card {cls}"><div class="stat-num">{num}</div><div class="stat-label">{label}</div></div>'
        kpi_html += '</div>'
        st.markdown(kpi_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("#### Occupancy per Bus")
        for bname, members in buses.items():
            cap   = capacity.get(bname, DEFAULT_CAPACITY)
            count = len(members)
            pct   = count / cap if cap > 0 else 0
            c     = "#d32f2f" if pct >= 0.9 else "#f9a825" if pct >= 0.6 else "#2e7d32"
            st.markdown(f"""
            <div class="a-bar-wrap">
                <div class="a-bar-label">{bname} — {count}/{cap} ({int(pct*100)}%)</div>
                <div class="a-bar-bg"><div class="a-bar-fill" style="width:{int(min(pct,1)*100)}%;background:{c}"></div></div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(f"#### {t('most_roles')}")
        role_counts: dict = {}
        for mems in buses.values():
            for m in mems:
                r = m.get("role", "Member")
                role_counts[r] = role_counts.get(r, 0) + 1
        max_r = max(role_counts.values()) if role_counts else 1
        role_colors = {"Leader":"#f9a825","Driver":"#64b5f6","قائد":"#f9a825","سائق":"#64b5f6"}
        for role, cnt in sorted(role_counts.items(), key=lambda x: -x[1]):
            rc = cnt / max_r
            rc_color = role_colors.get(role, "#2e7d32")
            st.markdown(f"""
            <div class="a-bar-wrap">
                <div class="a-bar-label">{role} — {cnt}</div>
                <div class="a-bar-bg"><div class="a-bar-fill" style="width:{int(rc*100)}%;background:{rc_color}"></div></div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(f"#### {t('timeline')}")
        date_counts: dict = {}
        for mems in buses.values():
            for m in mems:
                d = m.get("added", "")[:10]
                if d:
                    date_counts[d] = date_counts.get(d, 0) + 1
        if date_counts:
            df_tl = pd.DataFrame(sorted(date_counts.items()), columns=["Date", "Members Added"])
            st.dataframe(df_tl, use_container_width=True, hide_index=True)
        else:
            st.info("No timeline data yet.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "settings":
    st.markdown(f"### ⚙️ {t('settings_title')}")

    with st.expander(f"🔑 {t('change_password')}", expanded=False):
        cur_pw  = st.text_input(t("current_password"), type="password", key="cp_cur")
        new_pw  = st.text_input(t("new_password"),     type="password", key="cp_new")
        conf_pw = st.text_input(t("confirm_password"), type="password", key="cp_conf")
        if st.button(t("save_password"), key="cp_save"):
            stored = st.session_state.get("admin_pw_hash", ADMIN_PASSWORD_HASH)
            if not verify_password(cur_pw, stored):
                st.error(t("password_wrong"))
            elif new_pw != conf_pw:
                st.error(t("password_mismatch"))
            elif len(new_pw) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                st.session_state.admin_pw_hash = hash_password(new_pw)
                log_audit("CHANGE_PASSWORD", "Admin changed password")
                st.success(t("password_changed"))

    with st.expander("⏱ Session Timeout", expanded=False):
        cur_to = st.session_state.get("session_timeout_minutes", SESSION_TIMEOUT_MINUTES)
        new_to = st.number_input(t("session_timeout"), min_value=5, max_value=240, value=cur_to, key="st_timeout")
        if st.button("Save", key="st_save"):
            st.session_state.session_timeout_minutes = int(new_to)
            st.success(f"Session timeout set to {new_to} minutes.")

    with st.expander(f"🗑️ {t('delete_bus')}", expanded=False):
        if buses:
            del_b = st.selectbox(t("select_bus_delete"), list(buses.keys()), key="st_del_sel")
            if st.button(t("delete_bus"), key="st_del_btn"):
                st.session_state["_st_confirm_delete"] = True
            if st.session_state.get("_st_confirm_delete"):
                st.warning(t("confirm_delete", b=del_b))
                d1, d2 = st.columns(2)
                with d1:
                    if st.button(t("yes_delete"), key="st_del_yes"):
                        log_audit("DELETE_BUS", f"Deleted '{del_b}'")
                        del buses[del_b]
                        capacity.pop(del_b, None)
                        save_data(data)
                        st.session_state["_st_confirm_delete"] = False
                        st.rerun()
                with d2:
                    if st.button(t("cancel"), key="st_del_no"):
                        st.session_state["_st_confirm_delete"] = False
                        st.rerun()
        else:
            st.info(t("no_buses"))

    st.markdown("---")
    st.markdown(f"### 📋 {t('audit_log')}")
    all_audit = load_audit()
    if all_audit:
        df_audit = pd.DataFrame(all_audit)
        st.dataframe(df_audit, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇ Download Audit Log",
            data=df_audit.to_csv(index=False).encode("utf-8"),
            file_name=f"audit_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.caption("No audit entries yet.")

    st.markdown("---")
    st.markdown(f"### ⚠️ {t('danger_zone')}")
    with st.expander(t("clear_all_data"), expanded=False):
        st.warning("This will permanently delete all buses and members. There is no undo.")
        confirm_txt = st.text_input(t("confirm_clear"), key="dz_confirm")
        if st.button(t("clear_all_data"), key="dz_btn"):
            if confirm_txt == "CONFIRM":
                data["buses"] = {}
                data["capacity"] = {}
                st.session_state.data = data
                st.session_state.rollcall_state = {}
                save_data(data)
                log_audit("CLEAR_ALL_DATA", "All data wiped by admin")
                st.success(t("data_cleared"))
                st.rerun()
            else:
                st.error("Type CONFIRM exactly to proceed.")
