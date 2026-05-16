import streamlit as st
import pandas as pd
import json
import os
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

# ─── Constants ────────────────────────────────────────────────────────────────
DATA_FILE                = "bus_data.json"
AUDIT_FILE               = "audit_log.json"
DEFAULT_CAPACITY         = 50
SUPERADMIN_USERNAME      = "admin"
SESSION_TIMEOUT_MINUTES  = 30
MAX_LOGIN_ATTEMPTS       = 5
LOCKOUT_DURATION_MINUTES = 15

# ─── Incident / Status definitions ───────────────────────────────────────────
# Each status: (emoji, label_en, label_ar, css_class)
STATUSES = {
    "present":  ("🟢", "Present",  "حاضر",    "status-present"),
    "absent":   ("🔴", "Absent",   "غائب",    "status-absent"),
    "sick":     ("🟡", "Sick",     "مريض",    "status-sick"),
    "arrested": ("🟠", "Arrested", "موقوف",   "status-arrested"),
    "missing":  ("⚫", "Missing",  "مفقود",   "status-missing"),
}

def status_emoji(key):
    return STATUSES.get(key, STATUSES["absent"])[0]

def status_label(key, lang="en"):
    entry = STATUSES.get(key, STATUSES["absent"])
    return entry[1] if lang == "en" else entry[2]

def status_css(key):
    return STATUSES.get(key, STATUSES["absent"])[3]

# Map old boolean → new status for backwards-compat
def migrate_rc_state(rc_dict):
    """Convert {name: bool} → {name: 'present'|'absent'}"""
    out = {}
    for k, v in rc_dict.items():
        if isinstance(v, bool):
            out[k] = "present" if v else "absent"
        else:
            out[k] = v
    return out


st.set_page_config(
    page_title="Bus Logistics",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Translations ─────────────────────────────────────────────────────────────
T = {
    "en": {
        "app_title":         "Bus Logistics",
        "app_subtitle":      "Fleet management",
        "login_title":       "Admin Login",
        "login_subtitle":    "Secure access required",
        "first_run_title":   "First-Time Setup",
        "first_run_sub":     "Create your admin password to get started",
        "setup_new_pass":    "New Password",
        "setup_confirm":     "Confirm Password",
        "setup_btn":         "Create Account",
        "setup_done":        "Admin account created. Please sign in.",
        "setup_mismatch":    "Passwords do not match.",
        "setup_short":       "Password must be at least 8 characters.",
        "username":          "Username",
        "password":          "Password",
        "login_btn":         "Sign In",
        "logout_btn":        "Sign Out",
        "wrong_creds":       "Invalid username or password.",
        "locked_out":        "Too many failed attempts. Try again in {m} minutes.",
        "session_expired":   "Session expired. Please sign in again.",
        "welcome":           "Welcome, {u}",
        "new_bus":           "New Bus",
        "bus_name":          "Bus name",
        "capacity":          "Capacity",
        "create_bus":        "Create Bus",
        "delete_bus":        "Delete Bus",
        "select_bus_delete": "Select bus to delete",
        "confirm_delete":    "Delete {b} and all its members?",
        "yes_delete":        "Yes, Delete",
        "cancel":            "Cancel",
        "move_member":       "Move Member",
        "from_bus":          "From bus",
        "to_bus":            "To bus",
        "member":            "Member",
        "move_btn":          "Move",
        "export":            "Export",
        "download_csv":      "⬇ Download CSV",
        "download_json":     "⬇ Download JSON",
        "total_buses":       "Buses",
        "total_members":     "Members",
        "seats_available":   "Seats Free",
        "full_buses":        "Full Buses",
        "search_label":      "Search Member",
        "found_results":     "{n} result(s) found",
        "no_members_found":  "No members found.",
        "duplicate_warning": "⚠️ Duplicate Names",
        "no_buses":          "No buses yet — create one in the sidebar.",
        "add_member":        "Add Member",
        "name_placeholder":  "Full name",
        "role":              "Role",
        "roles":             ["Member", "Leader", "Driver", "Assistant", "Other"],
        "add_btn":           "Add ✚",
        "bus_full":          "Bus is full ({c} seats).",
        "enter_name":        "Enter a name.",
        "added_success":     "✅ Added {n}!",
        "edit_capacity":     "⚙️ Edit Capacity",
        "max_seats":         "Max seats",
        "update_capacity":   "Update",
        "cap_updated":       "Capacity updated.",
        "members_count":     "Members — {n} / {c}",
        "filter_bus":        "Filter",
        "no_members_yet":    "No members yet.",
        "all_members_title": "All Members",
        "total_label":       "Total: {n} members across {b} buses",
        "bus_created":       "Bus '{b}' created.",
        "bus_exists":        "Bus already exists.",
        "enter_bus_name":    "Enter a bus name.",
        "bus_deleted":       "Bus deleted.",
        "moved_success":     "Moved {m} → {b}.",
        "no_members_bus":    "No members in this bus.",
        "audit_log":         "Audit Log",
        "session_info":      "Session",
        "expires_in":        "Expires in {m} min",
        "full_badge":        "FULL",
        "ok_badge":          "OK",
        "name_col":          "Name",
        "role_col":          "Role",
        "bus_col":           "Bus",
        "added_col":         "Added",
        "appears_in":        "appears in",
        "toggle_lang":       "عربي",
        "seats_of":          "{c} seats",
        "page_dashboard":    "Dashboard",
        "page_buses":        "Bus Roster",
        "page_rollcall":     "Roll Call",
        "page_travel":       "Travel",
        "page_settings":     "Settings",
        "rollcall_title":    "Roll Call",
        "rollcall_subtitle": "Tap each person to set their status",
        "select_bus_rc":     "Select bus",
        "boarded":           "Present",
        "not_boarded":       "Not Marked",
        "mark_all_boarded":  "✅ Mark All Present",
        "reset_rollcall":    "🔄 Reset",
        "rollcall_progress": "{b} / {t} present",
        "rollcall_complete": "🎉 All accounted for!",
        "rc_export":         "⬇ Export CSV",
        "rc_search_label":   "Search members in this bus…",
        "settings_title":    "Settings",
        "change_password":   "Change Password",
        "current_password":  "Current Password",
        "new_password":      "New Password",
        "confirm_password":  "Confirm Password",
        "save_password":     "Save Password",
        "password_changed":  "Password changed.",
        "password_mismatch": "Passwords do not match.",
        "password_wrong":    "Current password is incorrect.",
        "session_timeout":   "Session Timeout (minutes)",
        "clear_all_data":    "⚠️ Clear All Data",
        "confirm_clear":     "Type CONFIRM to wipe all data",
        "data_cleared":      "All data cleared.",
        "danger_zone":       "Danger Zone",
        "notes":             "Notes",
        "phone":             "Phone",
        "fleet_overview":    "Fleet Overview",
        "attempts_left":     "{n} attempt(s) left before lockout.",
        "lang_label":        "Language",
        "admin_mgmt":        "Admin Management",
        "add_admin":         "Add Admin",
        "new_admin_user":    "New username",
        "new_admin_pass":    "Password",
        "admin_created":     "Admin '{u}' created.",
        "admin_exists":      "Username already exists.",
        "admin_removed":     "Admin '{u}' removed.",
        "remove_admin":      "Remove Admin",
        "select_admin":      "Select admin to remove",
        "cannot_remove_self":"You cannot remove yourself.",
        "admins_list":       "Admins",
        "superadmin_badge":  "SUPERADMIN",
        "travel_title":      "Travel Mode",
        "travel_subtitle":   "Pre-departure checklist & overview",
        "depart_summary":    "Departure Summary",
        "absent_members":    "Absent / Incidents",
        "checklist":         "Pre-Departure Checklist",
        "checklist_items":   [
            "Headcount confirmed",
            "Driver briefed",
            "Emergency contacts checked",
            "Bus documents ready",
            "First aid kit on board",
            "Departure time confirmed",
        ],
        "all_clear":         "✅ All checks passed — ready to depart!",
        "missing_checks":    "⚠️ {n} item(s) not checked",
        "trip_notes":        "Trip Notes",
        "save_trip_notes":   "Save",
        "trip_notes_saved":  "Notes saved.",
        "departure_time":    "Departure Time",
        "destination":       "Destination",
        "save_trip_info":    "Save Trip Info",
        "trip_info_saved":   "Trip info saved.",
        "absent_in":         "Absent in {b}",
        "incident_summary":  "Incident Summary",
        "tap_to_cycle":      "Tap to cycle status",
    },
    "ar": {
        "app_title":         "مدير النقل",
        "app_subtitle":      "إدارة الأسطول",
        "login_title":       "تسجيل دخول المدير",
        "login_subtitle":    "يُشترط الوصول الآمن",
        "first_run_title":   "الإعداد الأوّلي",
        "first_run_sub":     "أنشئ كلمة مرور المدير للبدء",
        "setup_new_pass":    "كلمة المرور الجديدة",
        "setup_confirm":     "تأكيد كلمة المرور",
        "setup_btn":         "إنشاء الحساب",
        "setup_done":        "تم إنشاء حساب المدير. يرجى تسجيل الدخول.",
        "setup_mismatch":    "كلمتا المرور غير متطابقتين.",
        "setup_short":       "يجب أن تتكون كلمة المرور من 8 أحرف على الأقل.",
        "username":          "اسم المستخدم",
        "password":          "كلمة المرور",
        "login_btn":         "تسجيل الدخول",
        "logout_btn":        "تسجيل الخروج",
        "wrong_creds":       "اسم المستخدم أو كلمة المرور غير صحيحة.",
        "locked_out":        "محاولات فاشلة كثيرة. أعد المحاولة بعد {m} دقيقة.",
        "session_expired":   "انتهت الجلسة. يرجى تسجيل الدخول مجدداً.",
        "welcome":           "أهلاً، {u}",
        "new_bus":           "حافلة جديدة",
        "bus_name":          "اسم الحافلة",
        "capacity":          "الطاقة",
        "create_bus":        "إنشاء",
        "delete_bus":        "حذف حافلة",
        "select_bus_delete": "اختر الحافلة للحذف",
        "confirm_delete":    "حذف {b} مع جميع أعضائها؟",
        "yes_delete":        "نعم، احذف",
        "cancel":            "إلغاء",
        "move_member":       "نقل عضو",
        "from_bus":          "من الحافلة",
        "to_bus":            "إلى الحافلة",
        "member":            "العضو",
        "move_btn":          "نقل",
        "export":            "تصدير",
        "download_csv":      "⬇ تحميل CSV",
        "download_json":     "⬇ تحميل JSON",
        "total_buses":       "الحافلات",
        "total_members":     "الأعضاء",
        "seats_available":   "مقاعد حرة",
        "full_buses":        "حافلات ممتلئة",
        "search_label":      "البحث عن عضو",
        "found_results":     "تم العثور على {n} نتيجة",
        "no_members_found":  "لم يُعثر على أي عضو.",
        "duplicate_warning": "⚠️ أسماء مكررة",
        "no_buses":          "لا توجد حافلات بعد — أنشئ واحدة من الشريط الجانبي.",
        "add_member":        "إضافة عضو",
        "name_placeholder":  "الاسم الكامل",
        "role":              "الدور",
        "roles":             ["عضو", "قائد", "سائق", "مساعد", "أخرى"],
        "add_btn":           "إضافة ✚",
        "bus_full":          "الحافلة ممتلئة ({c} مقعداً).",
        "enter_name":        "أدخل اسماً.",
        "added_success":     "✅ تمت إضافة {n}!",
        "edit_capacity":     "⚙️ تعديل الطاقة",
        "max_seats":         "الحد الأقصى",
        "update_capacity":   "تحديث",
        "cap_updated":       "تم تحديث الطاقة.",
        "members_count":     "الأعضاء — {n} / {c}",
        "filter_bus":        "تصفية",
        "no_members_yet":    "لا يوجد أعضاء بعد.",
        "all_members_title": "جميع الأعضاء",
        "total_label":       "الإجمالي: {n} عضواً في {b} حافلات",
        "bus_created":       "تم إنشاء الحافلة '{b}'.",
        "bus_exists":        "الحافلة موجودة بالفعل.",
        "enter_bus_name":    "أدخل اسم الحافلة.",
        "bus_deleted":       "تم حذف الحافلة.",
        "moved_success":     "تم نقل {m} إلى {b}.",
        "no_members_bus":    "لا يوجد أعضاء في هذه الحافلة.",
        "audit_log":         "سجل المراجعة",
        "session_info":      "الجلسة",
        "expires_in":        "تنتهي بعد {m} دقيقة",
        "full_badge":        "ممتلئ",
        "ok_badge":          "متاح",
        "name_col":          "الاسم",
        "role_col":          "الدور",
        "bus_col":           "الحافلة",
        "added_col":         "تاريخ الإضافة",
        "appears_in":        "يظهر في",
        "toggle_lang":       "English",
        "seats_of":          "{c} مقعداً",
        "page_dashboard":    "لوحة التحكم",
        "page_buses":        "قوائم الحافلات",
        "page_rollcall":     "التحقق من الركاب",
        "page_travel":       "السفر",
        "page_settings":     "الإعدادات",
        "rollcall_title":    "التحقق من الصعود",
        "rollcall_subtitle": "اضغط على كل شخص لتغيير حالته",
        "select_bus_rc":     "اختر الحافلة",
        "boarded":           "حاضر",
        "not_boarded":       "غير محدد",
        "mark_all_boarded":  "✅ تحديد الجميع حاضرين",
        "reset_rollcall":    "🔄 إعادة تعيين",
        "rollcall_progress": "{b} / {t} حاضر",
        "rollcall_complete": "🎉 الجميع محاسبون!",
        "rc_export":         "⬇ تصدير CSV",
        "rc_search_label":   "ابحث عن الأعضاء في هذه الحافلة…",
        "settings_title":    "الإعدادات",
        "change_password":   "تغيير كلمة المرور",
        "current_password":  "كلمة المرور الحالية",
        "new_password":      "كلمة مرور جديدة",
        "confirm_password":  "تأكيد كلمة المرور",
        "save_password":     "حفظ",
        "password_changed":  "تم تغيير كلمة المرور.",
        "password_mismatch": "كلمتا المرور غير متطابقتين.",
        "password_wrong":    "كلمة المرور الحالية غير صحيحة.",
        "session_timeout":   "مهلة الجلسة (دقائق)",
        "clear_all_data":    "⚠️ مسح جميع البيانات",
        "confirm_clear":     "اكتب CONFIRM لمسح البيانات",
        "data_cleared":      "تم مسح جميع البيانات.",
        "danger_zone":       "منطقة الخطر",
        "notes":             "ملاحظات",
        "phone":             "الهاتف",
        "fleet_overview":    "نظرة عامة على الأسطول",
        "attempts_left":     "{n} محاولة متبقية قبل القفل.",
        "lang_label":        "اللغة",
        "admin_mgmt":        "إدارة المديرين",
        "add_admin":         "إضافة مدير",
        "new_admin_user":    "اسم المستخدم الجديد",
        "new_admin_pass":    "كلمة المرور",
        "admin_created":     "تم إنشاء المدير '{u}'.",
        "admin_exists":      "اسم المستخدم موجود بالفعل.",
        "admin_removed":     "تم حذف المدير '{u}'.",
        "remove_admin":      "حذف مدير",
        "select_admin":      "اختر مديراً للحذف",
        "cannot_remove_self":"لا يمكنك حذف نفسك.",
        "admins_list":       "المديرون",
        "superadmin_badge":  "المدير الرئيسي",
        "travel_title":      "وضع السفر",
        "travel_subtitle":   "قائمة التحقق قبل المغادرة",
        "depart_summary":    "ملخص المغادرة",
        "absent_members":    "الغائبون / الحوادث",
        "checklist":         "قائمة التحقق قبل المغادرة",
        "checklist_items":   [
            "تم تأكيد العدد",
            "السائق جاهز",
            "جهات الاتصال الطارئة مراجعة",
            "وثائق الحافلة جاهزة",
            "حقيبة الإسعافات الأولية موجودة",
            "وقت المغادرة مؤكد",
        ],
        "all_clear":         "✅ جميع التحققات اجتازت — جاهز للمغادرة!",
        "missing_checks":    "⚠️ {n} عنصر لم يُؤكد",
        "trip_notes":        "ملاحظات الرحلة",
        "save_trip_notes":   "حفظ",
        "trip_notes_saved":  "تم حفظ الملاحظات.",
        "departure_time":    "وقت المغادرة",
        "destination":       "الوجهة",
        "save_trip_info":    "حفظ معلومات الرحلة",
        "trip_info_saved":   "تم حفظ معلومات الرحلة.",
        "absent_in":         "غائب في {b}",
        "incident_summary":  "ملخص الحوادث",
        "tap_to_cycle":      "اضغط للتغيير",
    },
}


# ─── Global CSS ───────────────────────────────────────────────────────────────
def inject_css(is_rtl: bool):
    text_side   = "right" if is_rtl else "left"
    content_dir = "rtl"   if is_rtl else "ltr"
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
    --orange:     #e65100;
    --orange-soft:#ff8a65;
    --blue:       #1565c0;
    --blue-soft:  #64b5f6;
    --white:      #ede8dc;
    --muted:      #6b6b6b;
    --muted2:     #9a9a9a;
    --radius:     10px;
    --radius-sm:  6px;
}}

html, body, [class*="css"] {{
    font-family: 'Tajawal', 'Barlow Condensed', sans-serif;
    background: var(--bg) !important;
    color: var(--white) !important;
}}
h1,h2,h3,h4,h5 {{
    font-family: 'Barlow Condensed', 'Tajawal', sans-serif;
    font-weight: 600; letter-spacing: .4px;
}}
.stApp {{ background: var(--bg) !important; }}

[data-testid="stSidebar"] {{
    direction: ltr !important;
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}}
[data-testid="stSidebar"] > div:first-child {{
    padding-top: 1rem; direction: ltr !important;
}}

[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {{
    direction: {content_dir} !important;
}}

#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
[data-testid="stSidebarNav"] {{ display: none; }}
button[kind="header"] {{ color: var(--white) !important; }}

::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--red); border-radius: 2px; }}

.stButton > button {{
    background: var(--surface2) !important;
    color: var(--white) !important;
    border: 1px solid var(--border2) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Barlow Condensed', 'Tajawal', sans-serif !important;
    font-size: .88rem !important; font-weight: 500 !important;
    letter-spacing: .3px !important; transition: all .15s !important;
    padding: .38rem .9rem !important;
}}
.stButton > button:hover {{
    background: var(--surface3) !important;
    border-color: var(--red) !important;
    color: var(--white) !important;
}}
.stButton > button:active {{
    background: var(--red) !important; border-color: var(--red) !important;
}}

.nav-btn > button {{
    background: transparent !important; border: none !important;
    border-radius: var(--radius-sm) !important;
    color: var(--muted2) !important;
    text-align: left !important; font-size: .88rem !important;
    padding: .45rem .75rem !important;
}}
.nav-btn > button:hover {{
    background: var(--surface2) !important; color: var(--white) !important;
    border: none !important;
}}
.nav-btn-active > button {{
    background: rgba(211,47,47,.12) !important;
    color: var(--red-soft) !important;
    border-left: 3px solid var(--red) !important;
    font-weight: 600 !important;
}}

.stTextInput > div > div > input,
.stNumberInput > div > div > input {{
    background: var(--surface2) !important; color: var(--white) !important;
    border: 1px solid var(--border2) !important;
    border-radius: var(--radius-sm) !important;
}}
.stSelectbox > div > div {{
    background: var(--surface2) !important; color: var(--white) !important;
    border: 1px solid var(--border2) !important;
    border-radius: var(--radius-sm) !important;
}}
.stTextArea textarea {{
    background: var(--surface2) !important; color: var(--white) !important;
    border: 1px solid var(--border2) !important;
    border-radius: var(--radius-sm) !important;
}}
.stTabs [data-baseweb="tab-list"] {{
    background: var(--surface) !important;
    border-bottom: 1px solid var(--border) !important;
    border-radius: var(--radius) var(--radius) 0 0 !important;
    gap: 2px !important;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important; color: var(--muted2) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Barlow Condensed', 'Tajawal', sans-serif !important;
    font-size: .85rem !important; font-weight: 500 !important;
    padding: .5rem 1rem !important;
}}
.stTabs [aria-selected="true"] {{
    background: var(--surface2) !important;
    color: var(--white) !important; border-bottom: 2px solid var(--red) !important;
}}
.stExpander {{
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}}
.stProgress > div > div > div > div {{
    background: linear-gradient(90deg, var(--red), var(--green)) !important;
}}
.stDataFrame {{ border-radius: var(--radius) !important; overflow: hidden !important; }}
.stAlert {{ border-radius: var(--radius-sm) !important; }}
hr {{ border-color: var(--border) !important; margin: 10px 0 !important; }}

/* ── Stat cards ── */
.stat-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 18px 14px;
    text-align: center; position: relative; overflow: hidden;
    transition: transform .15s, border-color .15s;
}}
.stat-card:hover {{ transform: translateY(-2px); border-color: var(--red); }}
.stat-card::after {{
    content:''; position:absolute; bottom:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg,var(--red),var(--green));
}}
.stat-num {{
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 2.4rem; font-weight: 700; color: var(--red); line-height: 1;
}}
.stat-label {{ font-size: .68rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; }}
.stat-green .stat-num {{ color: var(--green-soft) !important; }}
.stat-blue  .stat-num {{ color: var(--blue-soft)  !important; }}
.stat-gold  .stat-num {{ color: var(--gold)        !important; }}
.stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 1rem; }}

/* ── Bus card ── */
.bus-card {{
    background: linear-gradient(135deg, var(--surface), var(--surface2));
    border: 1px solid var(--border);
    border-{text_side}: 4px solid var(--red);
    border-radius: var(--radius); padding: 16px; margin-bottom: 8px;
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

/* ── Generic badge ── */
.badge {{
    display: inline-block; padding: 2px 8px;
    border-radius: 4px; font-size: .68rem;
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 600; letter-spacing: .8px; text-transform: uppercase;
}}
.badge-full {{ background: rgba(211,47,47,.18); color: var(--red-soft); border: 1px solid var(--red); }}
.badge-ok   {{ background: rgba(46,125,50,.18);  color: var(--green-soft); border: 1px solid var(--green); }}
.badge-warn {{ background: rgba(249,168,37,.18); color: var(--gold); border: 1px solid var(--gold); }}
.badge-gold {{ background: rgba(249,168,37,.18); color: var(--gold); border: 1px solid var(--gold); }}

/* ── Incident / status badges ── */
.status-present  {{ background:rgba(46,125,50,.18);  color:var(--green-soft);  border:1px solid var(--green);  }}
.status-absent   {{ background:rgba(211,47,47,.18);  color:var(--red-soft);    border:1px solid var(--red);    }}
.status-sick     {{ background:rgba(249,168,37,.18); color:var(--gold);        border:1px solid var(--gold);   }}
.status-arrested {{ background:rgba(230,81,0,.18);   color:var(--orange-soft); border:1px solid var(--orange); }}
.status-missing  {{ background:rgba(66,66,66,.3);    color:#aaa;               border:1px solid #555;          }}

/* ── Roll-call big tap button ── */
.rc-tap-btn {{
    width:100%; padding:14px 10px; border-radius:var(--radius-sm);
    border:1px solid var(--border2); background:var(--surface2);
    cursor:pointer; transition:all .15s; text-align:left;
    display:flex; align-items:center; gap:10px; margin-bottom:6px;
}}
.rc-tap-btn:hover {{ background:var(--surface3); border-color:var(--red); }}
.rc-tap-name  {{ font-size:.95rem; font-weight:500; flex:1; }}
.rc-tap-role  {{ font-size:.72rem; color:var(--muted2); }}
.rc-tap-phone {{ font-size:.72rem; color:var(--blue-soft); }}

.role-tag {{
    display: inline-block; padding: 1px 7px; border-radius: 3px;
    font-size: .7rem; font-weight: 600;
    background: var(--surface3); color: var(--muted2); border: 1px solid var(--border);
}}
.role-leader {{ background: rgba(249,168,37,.15); color: var(--gold);      border-color: var(--gold); }}
.role-driver {{ background: rgba(21,101,192,.15); color: var(--blue-soft); border-color: var(--blue); }}

.member-row {{
    display: flex; align-items: center; gap: 8px;
    padding: 8px 10px; border-radius: var(--radius-sm);
    border-bottom: 1px solid var(--border); transition: background .1s;
}}
.member-row:hover {{ background: var(--surface2); }}
.member-name  {{ font-size: .92rem; font-weight: 500; }}
.member-phone {{ font-size: .72rem; color: var(--blue-soft); }}
.member-note  {{ font-size: .72rem; color: var(--muted); font-style: italic; }}

.rc-progress {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 16px 18px; margin-bottom: 14px;
}}
.rc-fraction {{ font-family: 'Barlow Condensed', sans-serif; font-size: 3rem; font-weight: 700; line-height: 1; }}

.a-bar-wrap  {{ margin-bottom: 10px; }}
.a-bar-label {{ font-size: .82rem; color: var(--muted2); margin-bottom: 3px; }}
.a-bar-bg    {{ background: var(--surface2); border-radius: 4px; height: 8px; overflow: hidden; }}
.a-bar-fill  {{ height: 100%; border-radius: 4px; transition: width .4s; }}

.page-header {{
    background: linear-gradient(135deg, var(--surface) 0%, #150103 60%, #001507 100%);
    border-bottom: 2px solid var(--red);
    padding: 16px 20px 12px; margin: -1rem -1rem 1.2rem -1rem;
    position: relative; overflow: hidden;
}}
.page-header::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg, var(--bg) 0%, var(--red) 33%, var(--white) 33%, var(--white) 66%, var(--green) 66%);
}}
.page-title {{
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.5rem; font-weight: 700;
    color: var(--white); text-transform: uppercase; letter-spacing: 2px; line-height: 1.1;
}}
.page-sub   {{ font-size: .72rem; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; margin-top: 1px; }}
.page-badge {{
    position: absolute; top: 50%; right: 20px; transform: translateY(-50%);
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 20px; padding: 3px 14px;
    font-size: .68rem; color: var(--muted); letter-spacing: 1px; text-transform: uppercase;
}}

.sidebar-brand {{
    text-align: center; padding: 6px 0 16px;
    border-bottom: 1px solid var(--border); margin-bottom: 12px;
}}
.sidebar-brand-icon {{ font-size: 2rem; }}
.sidebar-brand-name {{
    font-family: 'Barlow Condensed', 'Tajawal', sans-serif;
    font-size: 1.05rem; font-weight: 700;
    color: var(--white); text-transform: uppercase; letter-spacing: 2px; margin-top: 2px;
}}
.sidebar-brand-sub {{ font-size: .65rem; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; }}

.sidebar-section {{
    font-size: .65rem; color: var(--muted); text-transform: uppercase;
    letter-spacing: 1.5px; padding: 10px 0 4px; font-weight: 600;
}}

.login-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-top: 3px solid var(--red); border-radius: var(--radius);
    padding: 32px 28px 28px; box-shadow: 0 8px 32px rgba(0,0,0,.5);
}}
.login-title {{
    font-family: 'Barlow Condensed', 'Tajawal', sans-serif;
    font-size: 1.6rem; font-weight: 700;
    color: var(--white); text-transform: uppercase; letter-spacing: 2px;
    text-align: center; margin-bottom: 2px;
}}
.login-sub {{ font-size: .72rem; color: var(--muted); text-align: center; letter-spacing: 1px; margin-bottom: 20px; }}

.dup-warn {{
    background: rgba(249,168,37,.08); border: 1px solid rgba(249,168,37,.3);
    border-radius: var(--radius-sm); padding: 8px 12px; margin: 4px 0;
    font-size: .82rem; color: var(--gold);
}}

.checklist-item {{
    display: flex; align-items: center; gap: 10px;
    padding: 10px 12px; border-radius: var(--radius-sm);
    border-bottom: 1px solid var(--border); transition: background .1s;
}}
.checklist-item:hover {{ background: var(--surface2); }}

.travel-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 16px; margin-bottom: 10px;
}}
.travel-card-title {{
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1rem; font-weight: 600; text-transform: uppercase;
    color: var(--muted2); letter-spacing: 1px; margin-bottom: 10px;
}}
.absent-row {{
    padding: 6px 10px; border-radius: var(--radius-sm);
    border-bottom: 1px solid var(--border);
    font-size: .88rem; color: var(--red-soft);
}}

.admin-row {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 12px; border-radius: var(--radius-sm);
    border-bottom: 1px solid var(--border);
    font-size: .88rem;
}}

/* incident summary strip */
.inc-strip {{
    display:flex; gap:6px; flex-wrap:wrap; margin:4px 0 8px;
}}
.inc-pill {{
    display:inline-flex; align-items:center; gap:4px;
    padding:3px 9px; border-radius:20px; font-size:.72rem;
    font-family:'Barlow Condensed',sans-serif; font-weight:600;
    border:1px solid var(--border2); background:var(--surface2);
    color:var(--muted2);
}}

@media (max-width: 768px) {{
    .page-title {{ font-size: 1.15rem !important; letter-spacing: .5px !important; }}
    .page-sub, .page-badge {{ display: none; }}
    .page-header {{ padding: 10px 14px 8px !important; margin-bottom: 8px !important; }}
    .stat-num {{ font-size: 1.9rem !important; }}
    .rc-fraction {{ font-size: 2.2rem !important; }}
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


# ─── Data persistence ─────────────────────────────────────────────────────────
def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"buses": {}, "capacity": {}, "admins": {}}

def save_data(d: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

def is_first_run(data: dict) -> bool:
    """True if no admin password has ever been set (fresh install)."""
    admins = data.get("admins", {})
    return SUPERADMIN_USERNAME not in admins


# ─── Admin helpers ────────────────────────────────────────────────────────────
def get_admins(data: dict) -> dict:
    return data.setdefault("admins", {})

def is_superadmin() -> bool:
    return st.session_state.get("current_user") == SUPERADMIN_USERNAME

def current_user() -> str:
    return st.session_state.get("current_user", SUPERADMIN_USERNAME)


# ─── Session ──────────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "lang":                    "en",
        "authenticated":           False,
        "current_user":            None,
        "login_attempts":          0,
        "lockout_until":           None,
        "session_start":           None,
        "session_token":           None,
        "active_page":             "dashboard",
        "rollcall_state":          {},
        "session_timeout_minutes": SESSION_TIMEOUT_MINUTES,
        "checklist_state":         {},
        "trip_info":               {},
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
    log_audit("LOGOUT", f"{current_user()} logged out")
    st.session_state.authenticated  = False
    st.session_state.current_user   = None
    st.session_state.session_start  = None
    st.session_state.session_token  = None

def do_login(username: str, password: str, data: dict) -> bool:
    lockout = st.session_state.get("lockout_until")
    if lockout and datetime.now() < lockout:
        return False
    admins = get_admins(data)
    if username in admins and verify_password(password, admins[username]):
        st.session_state.authenticated  = True
        st.session_state.current_user   = username
        st.session_state.login_attempts = 0
        st.session_state.lockout_until  = None
        st.session_state.session_start  = datetime.now()
        st.session_state.session_token  = secrets.token_hex(32)
        log_audit("LOGIN", f"Successful login: '{username}'")
        return True
    st.session_state.login_attempts = st.session_state.get("login_attempts", 0) + 1
    log_audit("LOGIN_FAIL", f"Failed attempt #{st.session_state.login_attempts} for '{username}'")
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
        "user":   st.session_state.get("current_user", "—"),
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
        json.dump(logs[:300], f, indent=2)

def load_audit() -> list:
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []


# ─── Misc helpers ─────────────────────────────────────────────────────────────
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

def role_cls(role: str) -> str:
    r = (role or "").lower()
    if "leader" in r or "قائد" in r:
        return "role-tag role-leader"
    if "driver" in r or "سائق" in r:
        return "role-tag role-driver"
    return "role-tag"

# Status cycle order: absent → present → sick → arrested → missing → absent
STATUS_CYCLE = ["absent", "present", "sick", "arrested", "missing"]

def next_status(current: str) -> str:
    try:
        idx = STATUS_CYCLE.index(current)
    except ValueError:
        idx = 0
    return STATUS_CYCLE[(idx + 1) % len(STATUS_CYCLE)]

def rc_bus_counts(members, rc):
    """Returns dict {status_key: count}."""
    counts = {k: 0 for k in STATUSES}
    for m in members:
        s = rc.get(m["name"], "absent")
        counts[s] = counts.get(s, 0) + 1
    return counts


# ═══════════════════════════════════════════════════════════════════════════════
# INITIALISE
# ═══════════════════════════════════════════════════════════════════════════════
init_session()

if "data" not in st.session_state:
    st.session_state.data = load_data()

data     = st.session_state.data
buses    = data.setdefault("buses", {})
capacity = data.setdefault("capacity", {})
admins   = get_admins(data)

inject_css(is_ar())

# ─── Migrate any old boolean rollcall values to status strings ────────────────
for bkey in list(st.session_state.rollcall_state.keys()):
    st.session_state.rollcall_state[bkey] = migrate_rc_state(
        st.session_state.rollcall_state[bkey]
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FIRST-RUN SETUP  (no admin password stored yet)
# ═══════════════════════════════════════════════════════════════════════════════
if is_first_run(data):
    top_cols = st.columns([6, 1])
    with top_cols[1]:
        if st.button(t("toggle_lang"), key="lang_setup"):
            st.session_state.lang = "ar" if st.session_state.lang == "en" else "en"
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        st.markdown(f"""
        <div class="login-card">
            <div style="text-align:center;font-size:2.6rem;margin-bottom:8px">🔐</div>
            <div class="login-title">{t('first_run_title')}</div>
            <div class="login-sub">{t('first_run_sub')}</div>
        </div>""", unsafe_allow_html=True)

        new_pw   = st.text_input(t("setup_new_pass"),  type="password", key="fr_new")
        conf_pw  = st.text_input(t("setup_confirm"),   type="password", key="fr_conf")

        if st.button(t("setup_btn"), use_container_width=True, key="fr_btn"):
            if len(new_pw) < 8:
                st.error(t("setup_short"))
            elif new_pw != conf_pw:
                st.error(t("setup_mismatch"))
            else:
                admins[SUPERADMIN_USERNAME] = hash_password(new_pw)
                save_data(data)
                log_audit("SETUP", "Superadmin password created on first run")
                st.success(t("setup_done"))
                st.rerun()

        st.markdown('<div style="text-align:center;margin-top:18px;font-size:.68rem;color:#3a3a3a">🔒 Bus Logistics — First-Run Setup</div>', unsafe_allow_html=True)
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
if not check_session():
    top_cols = st.columns([6, 1])
    with top_cols[1]:
        if st.button(t("toggle_lang"), key="lang_login"):
            st.session_state.lang = "ar" if st.session_state.lang == "en" else "en"
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        st.markdown(f"""
        <div class="login-card">
            <div style="text-align:center;font-size:2.6rem;margin-bottom:8px">🚌</div>
            <div class="login-title">{t('login_title')}</div>
            <div class="login-sub">{t('login_subtitle')}</div>
        </div>""", unsafe_allow_html=True)

        locked, lock_mins = is_locked_out()
        if locked:
            st.error(t("locked_out", m=lock_mins))
        else:
            username_in = st.text_input(t("username"), key="li_user")
            password_in = st.text_input(t("password"), type="password", key="li_pass")
            if st.button(t("login_btn"), use_container_width=True, key="li_btn"):
                if do_login(username_in, password_in, data):
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

        st.markdown('<div style="text-align:center;margin-top:18px;font-size:.68rem;color:#3a3a3a">🔒 Bus Logistics — Secured</div>', unsafe_allow_html=True)
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATED — SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand">
        <div class="sidebar-brand-icon">🚌</div>
        <div class="sidebar-brand-name">{t('app_title')}</div>
        <div class="sidebar-brand-sub">{t('app_subtitle')}</div>
    </div>""", unsafe_allow_html=True)

    # Language toggle
    st.markdown(f'<div class="sidebar-section">{t("lang_label")}</div>', unsafe_allow_html=True)
    lc1, lc2 = st.columns(2)
    with lc1:
        if st.button("🇬🇧 EN", use_container_width=True, key="sb_en"):
            st.session_state.lang = "en"; st.rerun()
    with lc2:
        if st.button("🇩🇿 AR", use_container_width=True, key="sb_ar"):
            st.session_state.lang = "ar"; st.rerun()

    # Navigation
    st.markdown('<div class="sidebar-section">Navigation</div>', unsafe_allow_html=True)
    nav_pages = [
        ("dashboard", "📊", t("page_dashboard")),
        ("buses",     "🚌", t("page_buses")),
        ("rollcall",  "✅", t("page_rollcall")),
        ("travel",    "✈️", t("page_travel")),
        ("settings",  "⚙️", t("page_settings")),
    ]
    current_page = st.session_state.get("active_page", "dashboard")
    for pid, picon, plabel in nav_pages:
        cls = "nav-btn nav-btn-active" if current_page == pid else "nav-btn"
        st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
        if st.button(f"{picon}  {plabel}", key=f"nav_{pid}", use_container_width=True):
            st.session_state.active_page = pid; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Create New Bus
    st.markdown(f'<div class="sidebar-section">➕ {t("new_bus")}</div>', unsafe_allow_html=True)
    nb_name = st.text_input(t("bus_name"), key="sb_new_bus_name", label_visibility="collapsed")
    nb_cap  = st.number_input(t("capacity"), min_value=1, max_value=200, value=DEFAULT_CAPACITY,
                               key="sb_new_bus_cap", label_visibility="collapsed")
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

    # Move Member (only if 2+ buses)
    if len(buses) >= 2:
        st.markdown(f'<div class="sidebar-section">🔄 {t("move_member")}</div>', unsafe_allow_html=True)
        from_b   = st.selectbox(t("from_bus"), list(buses.keys()), key="sb_move_from", label_visibility="collapsed")
        if buses.get(from_b):
            move_sel = st.selectbox(t("member"), [m["name"] for m in buses[from_b]],
                                     key="sb_move_member", label_visibility="collapsed")
            to_b = st.selectbox(t("to_bus"), [b for b in buses if b != from_b],
                                 key="sb_move_to", label_visibility="collapsed")
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

    # Export
    if buses:
        flat = all_members_flat(buses)
        if flat:
            st.markdown(f'<div class="sidebar-section">📤 {t("export")}</div>', unsafe_allow_html=True)
            df_exp  = pd.DataFrame(flat)
            csv_out = df_exp.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            json_out = json.dumps({"buses": buses, "capacity": capacity}, indent=2, ensure_ascii=False).encode("utf-8")
            st.download_button(t("download_csv"),  data=csv_out,
                               file_name=f"roster_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                               mime="text/csv", use_container_width=True, key="sb_dl_csv")
            st.download_button(t("download_json"), data=json_out,
                               file_name=f"data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                               mime="application/json", use_container_width=True, key="sb_dl_json")
            st.markdown("---")

    # Session / Logout
    user_badge = f'<span class="badge badge-gold">{t("superadmin_badge")}</span>' if is_superadmin() else ""
    with st.expander(f"👤 {current_user()}", expanded=False):
        st.caption(t("welcome", u=current_user()))
        st.caption(t("expires_in", m=session_mins_left()))
        if st.button(t("logout_btn"), use_container_width=True, key="sb_logout"):
            _do_logout(); st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED COMPUTED VALUES
# ═══════════════════════════════════════════════════════════════════════════════
page          = st.session_state.get("active_page", "dashboard")
total_members = sum(len(m) for m in buses.values())
total_buses_n = len(buses)
total_cap     = sum(capacity.get(b, DEFAULT_CAPACITY) for b in buses)
full_buses_n  = sum(1 for b in buses if len(buses[b]) >= capacity.get(b, DEFAULT_CAPACITY))
seats_free    = max(0, total_cap - total_members)

_page_labels = {pid: lbl for pid, _, lbl in nav_pages}
st.markdown(f"""
<div class="page-header">
    <div class="page-title">🚌 {t('app_title')}</div>
    <div class="page-sub">{t('app_subtitle')}</div>
    <div class="page-badge">{_page_labels.get(page, '')}</div>
</div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "dashboard":
    lang = st.session_state.get("lang", "en")

    # ── Global incident totals (across all buses) ─────────────────────────────
    global_cnts = {k: 0 for k in STATUSES}
    rc_state_all = st.session_state.get("rollcall_state", {})
    for bname, members in buses.items():
        rc = migrate_rc_state(rc_state_all.get(bname, {}))
        for m in members:
            s = rc.get(m["name"], "absent")
            global_cnts[s] = global_cnts.get(s, 0) + 1

    total_rc_marked = sum(global_cnts.values())
    total_present   = global_cnts.get("present", 0)
    total_absent    = global_cnts.get("absent",  0)
    total_sick      = global_cnts.get("sick",    0)
    total_arrested  = global_cnts.get("arrested",0)
    total_missing   = global_cnts.get("missing", 0)

    # ── Top stat grid ─────────────────────────────────────────────────────────
    # Row 1: fleet basics
    stats = [
        (total_buses_n, t("total_buses"),    ""),
        (total_members, t("total_members"),  ""),
        (seats_free,    t("seats_available"), "stat-green"),
        (full_buses_n,  t("full_buses"),     ""),
    ]
    html = '<div class="stat-grid">'
    for num, label, cls in stats:
        html += f'<div class="stat-card {cls}"><div class="stat-num">{num}</div><div class="stat-label">{label}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # Row 2: live incident bar (superadmin sees full breakdown, others see simplified)
    if is_superadmin() and total_members > 0:
        pct_present  = total_present  / total_members
        pct_absent   = total_absent   / total_members
        pct_sick     = total_sick     / total_members
        pct_arrested = total_arrested / total_members
        pct_missing  = total_missing  / total_members

        # Stacked bar segments
        seg_present  = f'<div style="flex:{pct_present:.3f};background:#2e7d32;height:100%"></div>'  if total_present  else ""
        seg_absent   = f'<div style="flex:{pct_absent:.3f};background:#d32f2f;height:100%"></div>'   if total_absent   else ""
        seg_sick     = f'<div style="flex:{pct_sick:.3f};background:#f9a825;height:100%"></div>'     if total_sick     else ""
        seg_arrested = f'<div style="flex:{pct_arrested:.3f};background:#e65100;height:100%"></div>' if total_arrested else ""
        seg_missing  = f'<div style="flex:{pct_missing:.3f};background:#555;height:100%"></div>'     if total_missing  else ""

        incident_pills = "".join(
            f'<span class="badge {status_css(sk)}">{status_emoji(sk)} {global_cnts[sk]}</span>'
            for sk in STATUSES if global_cnts[sk]
        )

        st.markdown(f"""
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px 16px;margin-bottom:12px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                <span style="font-family:'Barlow Condensed',sans-serif;font-size:.7rem;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted)">
                    🌐 Global Incident Overview
                </span>
                <div style="display:flex;gap:6px">{incident_pills}</div>
            </div>
            <div style="display:flex;height:10px;border-radius:4px;overflow:hidden;background:var(--surface2)">
                {seg_present}{seg_absent}{seg_sick}{seg_arrested}{seg_missing}
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:5px;font-size:.68rem;color:var(--muted)">
                <span>🟢 {total_present} Present &nbsp; 🔴 {total_absent} Absent &nbsp; 🟡 {total_sick} Sick</span>
                <span>🟠 {total_arrested} Arrested &nbsp; ⚫ {total_missing} Missing</span>
            </div>
        </div>""", unsafe_allow_html=True)

        # Alert banner for critical statuses
        alerts = []
        if total_missing  > 0: alerts.append(f"⚫ {total_missing} MISSING")
        if total_arrested > 0: alerts.append(f"🟠 {total_arrested} ARRESTED")
        if alerts:
            st.error(f"🚨 CRITICAL: {' · '.join(alerts)} — immediate attention required")

    # ── Fleet overview per bus ────────────────────────────────────────────────
    st.markdown(f"### {t('fleet_overview')}")
    if buses:
        for bname, members in buses.items():
            cap   = capacity.get(bname, DEFAULT_CAPACITY)
            count = len(members)
            pct   = count / cap if cap > 0 else 0
            is_full   = count >= cap
            badge_cls = "badge-full" if is_full else ("badge-warn" if pct >= 0.75 else "badge-ok")
            badge_txt = t("full_badge") if is_full else t("ok_badge")
            pct_int   = int(pct * 100)
            bar_color = "#d32f2f" if pct_int >= 90 else "#f9a825" if pct_int >= 70 else "#2e7d32"

            rc   = migrate_rc_state(rc_state_all.get(bname, {}))
            cnts = rc_bus_counts(members, rc)
            inc_pills = ""
            for sk, (emoji, lbl_en, lbl_ar, css) in STATUSES.items():
                n = cnts.get(sk, 0)
                if n:
                    lbl = lbl_ar if is_ar() else lbl_en
                    inc_pills += f'<span class="inc-pill badge {css}">{emoji} {n} {lbl}</span>'

            # Bus quick-note (superadmin can leave a short note per bus)
            if is_superadmin():
                bn_key = f"bus_note_{bname}"
                bus_notes = data.setdefault("bus_notes", {})
                note_val  = bus_notes.get(bname, "")

            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"""
                <div style="margin-bottom:4px">
                    <span style="font-family:'Barlow Condensed',sans-serif;font-size:1rem;text-transform:uppercase;letter-spacing:.5px">{bname}</span>
                    &nbsp;<span class="badge {badge_cls}">{badge_txt}</span>
                    <span style="font-size:.78rem;color:#555;margin-left:8px">{count} / {cap}</span>
                </div>
                <div class="inc-strip">{inc_pills}</div>""", unsafe_allow_html=True)
                st.progress(min(pct, 1.0))
                # Quick note per bus (superadmin only, inline under bar)
                if is_superadmin():
                    new_note = st.text_input("", value=note_val, key=f"dash_note_{bname}",
                                             placeholder=f"📝 Quick note for {bname}…",
                                             label_visibility="collapsed")
                    if new_note != note_val:
                        data["bus_notes"][bname] = new_note
                        save_data(data)
            with col_b:
                st.markdown(f'<div style="text-align:right;font-family:Barlow Condensed,sans-serif;font-size:1.6rem;font-weight:700;color:{bar_color};padding-top:4px">{pct_int}%</div>', unsafe_allow_html=True)
    else:
        st.info(t("no_buses"))

    # ── Superadmin: full incident table ───────────────────────────────────────
    if is_superadmin() and buses and total_members > 0:
        with st.expander("🗂️ Full Incident Table", expanded=False):
            rows = []
            for bname, members in buses.items():
                rc = migrate_rc_state(rc_state_all.get(bname, {}))
                for m in members:
                    s = rc.get(m["name"], "absent")
                    rows.append({
                        "Bus":    bname,
                        "Name":   m["name"],
                        "Role":   m.get("role", ""),
                        "Phone":  m.get("phone", ""),
                        "Status": f"{status_emoji(s)} {status_label(s, lang)}",
                    })
            if rows:
                df_inc = pd.DataFrame(rows)
                # Sort: missing/arrested first
                priority = {"missing": 0, "arrested": 1, "sick": 2, "absent": 3, "present": 4}
                def _sort_status(label_str):
                    for k, v in priority.items():
                        if status_label(k, lang) in label_str:
                            return v
                    return 99
                df_inc["_pri"] = df_inc["Status"].apply(_sort_status)
                df_inc = df_inc.sort_values("_pri").drop(columns=["_pri"])
                st.dataframe(df_inc, use_container_width=True, hide_index=True)
                inc_csv = df_inc.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button("⬇ Export Incident Report", data=inc_csv,
                                   file_name=f"incidents_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                   mime="text/csv")

    # ── Duplicate names warning ───────────────────────────────────────────────
    all_names = [m["name"].lower() for mems in buses.values() for m in mems]
    dups = {n for n in all_names if all_names.count(n) > 1}
    if dups:
        st.markdown(f"### {t('duplicate_warning')}")
        for dup in dups:
            dup_buses = [b for b, mems in buses.items() if any(m["name"].lower() == dup for m in mems)]
            st.markdown(f'<div class="dup-warn">⚠️ <b>{dup.title()}</b> — {t("appears_in")}: {", ".join(dup_buses)}</div>', unsafe_allow_html=True)

    # ── Event log (superadmin: last 10 actions at a glance) ───────────────────
    if is_superadmin():
        with st.expander("📡 Live Activity Log", expanded=False):
            recent = load_audit()[:15]
            if recent:
                for entry in recent:
                    action_icon = {
                        "LOGIN": "🔑", "LOGOUT": "🚪", "ROLL_CALL": "✅",
                        "ADD_MEMBER": "➕", "REMOVE_MEMBER": "✕",
                        "CREATE_BUS": "🚌", "DELETE_BUS": "🗑️",
                        "MOVE_MEMBER": "🔄", "CHANGE_PASSWORD": "🔐",
                        "TRIP_INFO": "✈️", "TRIP_NOTES": "📝",
                    }.get(entry.get("action",""), "•")
                    ts   = entry.get("timestamp","")[-8:]   # HH:MM:SS
                    user = entry.get("user","?")
                    det  = entry.get("detail","")
                    st.markdown(
                        f'<div style="display:flex;gap:8px;padding:5px 0;border-bottom:1px solid #1c1c1c;font-size:.8rem">'
                        f'<span style="color:#555;min-width:60px">{ts}</span>'
                        f'<span>{action_icon}</span>'
                        f'<span style="color:#9a9a9a;min-width:60px">{user}</span>'
                        f'<span style="color:#6b6b6b">{det}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No activity yet.")


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
                    new_name  = st.text_input(t("name_col"),  key=f"nm_{bname}")
                    new_role  = st.selectbox(t("role"),       t("roles"), key=f"rl_{bname}")
                    new_phone = st.text_input(t("phone"),     key=f"ph_{bname}")
                    new_note  = st.text_input(t("notes"),     key=f"nt_{bname}")
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
                            log_audit("ADD_MEMBER", f"Added '{name_clean}' to '{bname}'")
                            st.success(t("added_success", n=name_clean))
                            st.rerun()

                with st.expander(t("edit_capacity")):
                    new_cap_v = st.number_input(t("max_seats"), min_value=1, max_value=500, value=cap, key=f"cap_{bname}")
                    if st.button(t("update_capacity"), key=f"savecap_{bname}"):
                        capacity[bname] = int(new_cap_v)
                        save_data(data)
                        log_audit("EDIT_CAPACITY", f"'{bname}' cap → {new_cap_v}")
                        st.success(t("cap_updated"))
                        st.rerun()

                st.markdown(f"#### 👥 {t('members_count', n=count, c=cap)}")
                if not members:
                    st.info(t("no_members_yet"))
                else:
                    bus_filter = st.text_input(t("filter_bus"), key=f"bf_{bname}", label_visibility="collapsed")
                    filtered   = [m for m in members if bus_filter.lower() in m["name"].lower()] if bus_filter else members

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
# PAGE: ROLL CALL  — big-tap incident status per member
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "rollcall":
    lang = st.session_state.get("lang", "en")
    st.markdown(f"### ✅ {t('rollcall_title')}")
    st.markdown(f"<p style='color:#6b6b6b;font-size:.85rem'>{t('rollcall_subtitle')}</p>", unsafe_allow_html=True)

    if not buses:
        st.info(t("no_buses"))
    else:
        rc_bus  = st.selectbox(t("select_bus_rc"), list(buses.keys()), key="rc_bus")
        members = buses.get(rc_bus, [])

        # Ensure state exists and is migrated
        if rc_bus not in st.session_state.rollcall_state:
            st.session_state.rollcall_state[rc_bus] = {}
        rc = migrate_rc_state(st.session_state.rollcall_state[rc_bus])
        st.session_state.rollcall_state[rc_bus] = rc
        for m in members:
            rc.setdefault(m["name"], "absent")

        total_rc     = len(members)
        accounted_n  = sum(1 for m in members if rc.get(m["name"], "absent") != "absent")
        present_n    = sum(1 for m in members if rc.get(m["name"]) == "present")
        pct_rc       = present_n / total_rc if total_rc else 0
        pct_accounted= accounted_n / total_rc if total_rc else 0
        rc_color     = "#2e7d32" if pct_rc >= 1.0 else "#f9a825" if pct_rc >= 0.5 else "#d32f2f"
        cnts         = rc_bus_counts(members, rc)

        # ── Completion notification ───────────────────────────────────────────
        _notify_key   = f"rc_notified_{rc_bus}"
        all_accounted = (accounted_n == total_rc and total_rc > 0)
        all_present   = (present_n   == total_rc and total_rc > 0)
        was_notified  = st.session_state.get(_notify_key, False)

        if all_accounted and not was_notified:
            st.session_state[_notify_key] = True
            if all_present:
                st.balloons()
                st.success(f"🎉 All {total_rc} members of **{rc_bus}** confirmed PRESENT — bus ready!")
            else:
                non_p = total_rc - present_n
                st.warning(f"✅ All {total_rc} members of **{rc_bus}** accounted for — {present_n} present, {non_p} with incident status.")
        elif not all_accounted and was_notified:
            st.session_state[_notify_key] = False

        # Superadmin global fleet completion check
        if is_superadmin() and buses:
            _rc_all = st.session_state.rollcall_state
            all_buses_done = all(
                len(buses[bn]) > 0 and
                sum(1 for mm in buses[bn] if _rc_all.get(bn, {}).get(mm["name"], "absent") != "absent") == len(buses[bn])
                for bn in buses
            )
            _global_key = "rc_global_notified"
            if all_buses_done and not st.session_state.get(_global_key):
                st.session_state[_global_key] = True
                st.balloons()
                st.success(f"🚌💚 FLEET COMPLETE — All {total_members} members across all {total_buses_n} buses accounted for!")
            elif not all_buses_done:
                st.session_state[_global_key] = False

        # ── Progress block ────────────────────────────────────────────────────
        complete_html = (f"<div style='margin-top:10px;font-size:1.1rem;color:#66bb6a;font-weight:700'>"
                         f"{t('rollcall_complete')}</div>") if all_present and total_rc > 0 else ""

        accounted_html = ""
        if accounted_n > 0 and not all_accounted:
            accounted_html = f"<div style='font-size:.75rem;color:#9a9a9a;margin-top:4px'>{accounted_n}/{total_rc} accounted for (including incident statuses)</div>"

        # Incident summary pills
        inc_pills = ""
        for sk, (emoji, lbl_en, lbl_ar, css) in STATUSES.items():
            n = cnts.get(sk, 0)
            lbl = lbl_ar if lang == "ar" else lbl_en
            inc_pills += f'<span class="inc-pill badge {css}">{emoji} {n} {lbl}</span>'

        st.markdown(f"""
        <div class="rc-progress">
            <div style="display:flex;align-items:baseline;gap:10px">
                <div class="rc-fraction" style="color:{rc_color}">{present_n}</div>
                <div style="font-family:'Barlow Condensed',sans-serif;font-size:1.8rem;color:#3a3a3a">/ {total_rc}</div>
                <div style="font-size:.8rem;color:#6b6b6b;text-transform:uppercase;letter-spacing:1px;margin-left:4px">{t('boarded')}</div>
            </div>
            <div style="background:var(--surface2);border-radius:4px;height:8px;margin-top:10px;overflow:hidden">
                <div style="height:100%;width:{int(pct_rc*100)}%;background:{rc_color};border-radius:4px;transition:width .4s"></div>
            </div>
            <div class="inc-strip" style="margin-top:10px">{inc_pills}</div>
            {accounted_html}
            {complete_html}
        </div>""", unsafe_allow_html=True)

        # ── Action row ────────────────────────────────────────────────────────
        ca, cb, cc = st.columns([1, 1, 2])
        with ca:
            if st.button(t("mark_all_boarded"), use_container_width=True, key="rc_all"):
                for m in members:
                    rc[m["name"]] = "present"
                st.rerun()
        with cb:
            if st.button(t("reset_rollcall"), use_container_width=True, key="rc_reset"):
                for m in members:
                    rc[m["name"]] = "absent"
                st.rerun()
        with cc:
            if members:
                rc_rows = [
                    {
                        "Name":   m["name"],
                        "Role":   m.get("role", ""),
                        "Phone":  m.get("phone", ""),
                        "Status": rc.get(m["name"], "absent"),
                    }
                    for m in members
                ]
                rc_csv = pd.DataFrame(rc_rows).to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(t("rc_export"), data=rc_csv,
                                   file_name=f"rollcall_{rc_bus}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                   mime="text/csv", use_container_width=True, key="rc_dl")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Search ────────────────────────────────────────────────────────────
        rc_search = st.text_input("", key="rc_search_input",
                                   placeholder=f"🔍 {t('rc_search_label')}")

        def _rc_match(m: dict) -> bool:
            if not rc_search: return True
            q = rc_search.strip().lower()
            return q in m["name"].lower() or q in m.get("role","").lower() or q in m.get("phone","").lower()

        filtered_members = [m for m in members if _rc_match(m)]
        if rc_search:
            st.caption(f'🔎 {len(filtered_members)} result(s) for "{rc_search.strip()}"')

        # ── Legend ────────────────────────────────────────────────────────────
        legend_html = '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;font-size:.72rem;">'
        for sk, (emoji, lbl_en, lbl_ar, css) in STATUSES.items():
            lbl = lbl_ar if lang == "ar" else lbl_en
            legend_html += f'<span class="badge {css}">{emoji} {lbl}</span>'
        legend_html += f'<span style="color:var(--muted);font-size:.68rem;align-self:center">← {t("tap_to_cycle")}</span></div>'
        st.markdown(legend_html, unsafe_allow_html=True)

        # ── Member tap buttons ────────────────────────────────────────────────
        # Group by status for visual clarity: pending first, then others
        STATUS_ORDER = ["absent", "missing", "arrested", "sick", "present"]

        def sort_key(m):
            s = rc.get(m["name"], "absent")
            try:
                return STATUS_ORDER.index(s)
            except ValueError:
                return 99

        sorted_members = sorted(filtered_members, key=sort_key)

        for m in sorted_members:
            mname  = m["name"]
            cur_st = rc.get(mname, "absent")
            nxt_st = next_status(cur_st)
            emoji  = status_emoji(cur_st)
            lbl    = status_label(cur_st, lang)
            css    = status_css(cur_st)
            role_h = f'<span class="rc-tap-role">{m.get("role","")}</span>' if m.get("role") else ""
            phone_h= f'<span class="rc-tap-phone">📞 {m.get("phone","")}</span>' if m.get("phone") else ""

            # We render a native Streamlit button styled to look like a tap card.
            # The label encodes the full row so one tap = one action.
            col_btn, col_badge = st.columns([5, 1])
            with col_btn:
                btn_label = f"{emoji}  {mname}"
                if role_h or phone_h:
                    btn_label += f"  |  {m.get('role','')}  {m.get('phone','')}"
                if st.button(btn_label, key=f"rctap_{rc_bus}_{mname}", use_container_width=True):
                    rc[mname] = nxt_st
                    log_audit("ROLL_CALL", f"'{mname}' in '{rc_bus}': {cur_st} → {nxt_st}")
                    st.rerun()
            with col_badge:
                st.markdown(f'<div style="padding-top:6px"><span class="badge {css}">{lbl}</span></div>',
                            unsafe_allow_html=True)

        if rc_search and not filtered_members:
            st.info(t("no_members_found"))


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: TRAVEL
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "travel":
    lang = st.session_state.get("lang", "en")
    st.markdown(f"### ✈️ {t('travel_title')}")
    st.markdown(f"<p style='color:#6b6b6b;font-size:.85rem'>{t('travel_subtitle')}</p>", unsafe_allow_html=True)

    trip_info = st.session_state.get("trip_info", {})

    # ── Trip Info ─────────────────────────────────────────────────────────────
    st.markdown(f"#### 🗺️ {t('depart_summary')}")
    ti_col1, ti_col2 = st.columns(2)
    with ti_col1:
        dest = st.text_input(t("destination"), value=trip_info.get("destination",""), key="ti_dest")
    with ti_col2:
        dep_time = st.text_input(t("departure_time"), value=trip_info.get("departure_time",""),
                                  placeholder="e.g. 08:00", key="ti_dep")
    if st.button(t("save_trip_info"), key="ti_save"):
        st.session_state.trip_info = {"destination": dest.strip(), "departure_time": dep_time.strip()}
        log_audit("TRIP_INFO", f"Destination='{dest}' Departure='{dep_time}'")
        st.success(t("trip_info_saved"))

    st.markdown("---")

    # ── Pre-Departure Checklist ───────────────────────────────────────────────
    st.markdown(f"#### 📋 {t('checklist')}")
    checklist_items = t("checklist_items")
    cl_state = st.session_state.get("checklist_state", {})

    all_checked = True
    for item in checklist_items:
        checked = cl_state.get(item, False)
        if not checked:
            all_checked = False
        new_val = st.checkbox(item, value=checked, key=f"cl_{item}")
        if new_val != checked:
            cl_state[item] = new_val
            st.session_state.checklist_state = cl_state
            st.rerun()

    unchecked_n = sum(1 for item in checklist_items if not cl_state.get(item, False))
    _cl_key = "checklist_was_complete"
    if unchecked_n == 0 and checklist_items:
        if not st.session_state.get(_cl_key):
            st.session_state[_cl_key] = True
            st.balloons()
        st.success(t("all_clear"))
    else:
        if st.session_state.get(_cl_key):
            st.session_state[_cl_key] = False
        if unchecked_n < len(checklist_items):
            done_n = len(checklist_items) - unchecked_n
            st.info(f"✔️ {done_n} / {len(checklist_items)} checks done — {unchecked_n} remaining")
        st.warning(t("missing_checks", n=unchecked_n))

    reset_col, _ = st.columns([1, 3])
    with reset_col:
        if st.button("🔄 Reset Checklist", key="cl_reset"):
            st.session_state.checklist_state = {}
            st.rerun()

    st.markdown("---")

    # ── Incident Summary per Bus (replaces simple "Absent Members") ───────────
    st.markdown(f"#### ⚠️ {t('absent_members')}")
    rc_state = st.session_state.get("rollcall_state", {})

    if not buses:
        st.info(t("no_buses"))
    else:
        any_incident = False
        for bname, members in buses.items():
            rc = migrate_rc_state(rc_state.get(bname, {}))
            non_present = [m for m in members if rc.get(m["name"], "absent") != "present"]
            if non_present:
                any_incident = True
                cnts = rc_bus_counts(members, rc)
                pills = "".join(
                    f'<span class="badge {status_css(sk)}">{status_emoji(sk)} {cnts[sk]} {status_label(sk, lang)}</span> '
                    for sk in STATUSES if cnts.get(sk, 0) and sk != "present"
                )
                st.markdown(f'<div class="travel-card"><div class="travel-card-title">🚌 {bname} &nbsp; {pills}</div>', unsafe_allow_html=True)
                for m in non_present:
                    mst     = rc.get(m["name"], "absent")
                    emoji   = status_emoji(mst)
                    css     = status_css(mst)
                    lbl     = status_label(mst, lang)
                    phone_h = f' &nbsp; 📞 <span style="color:#64b5f6">{m["phone"]}</span>' if m.get("phone") else ""
                    st.markdown(
                        f'<div class="absent-row">'
                        f'{emoji} <b>{m["name"]}</b> '
                        f'<span class="badge {css}" style="margin-left:6px">{lbl}</span>'
                        f'<span style="color:#555;font-size:.78rem;margin-left:6px">[{m.get("role","Member")}]</span>'
                        f'{phone_h}</div>',
                        unsafe_allow_html=True
                    )
                st.markdown('</div>', unsafe_allow_html=True)

        if not any_incident:
            st.success(t("rollcall_complete"))
        else:
            st.caption("Run Roll Call first if counts look wrong.")

    st.markdown("---")

    # ── Fleet Ready Status ────────────────────────────────────────────────────
    st.markdown(f"#### 🚌 Fleet Ready Status")
    if buses:
        for bname, members in buses.items():
            cap    = capacity.get(bname, DEFAULT_CAPACITY)
            count  = len(members)
            rc     = migrate_rc_state(rc_state.get(bname, {}))
            present_n = sum(1 for m in members if rc.get(m["name"]) == "present")
            pct    = present_n / count if count else 0
            color  = "#2e7d32" if pct >= 1.0 else "#f9a825" if pct >= 0.5 else "#d32f2f"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #1c1c1c">
                <span style="font-family:'Barlow Condensed',sans-serif;font-size:1rem;text-transform:uppercase;min-width:130px">{bname}</span>
                <div style="flex:1;background:#1c1c1c;border-radius:3px;height:6px;overflow:hidden">
                    <div style="width:{int(min(pct,1)*100)}%;height:100%;background:{color};border-radius:3px"></div>
                </div>
                <span style="font-size:.82rem;color:#6b6b6b;min-width:80px;text-align:right">{present_n}/{count} present</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Trip Notes ────────────────────────────────────────────────────────────
    st.markdown(f"#### 📝 {t('trip_notes')}")
    trip_note_val = trip_info.get("notes", "")
    new_notes = st.text_area(t("trip_notes"), value=trip_note_val, height=100,
                              key="trip_notes_area", label_visibility="collapsed")
    if st.button(t("save_trip_notes"), key="tn_save"):
        st.session_state.trip_info["notes"] = new_notes
        log_audit("TRIP_NOTES", "Trip notes updated")
        st.success(t("trip_notes_saved"))


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "settings":
    st.markdown(f"### ⚙️ {t('settings_title')}")

    # ── Change MY Password ────────────────────────────────────────────────────
    with st.expander(f"🔑 {t('change_password')}", expanded=False):
        cur_pw  = st.text_input(t("current_password"), type="password", key="cp_cur")
        new_pw  = st.text_input(t("new_password"),     type="password", key="cp_new")
        conf_pw = st.text_input(t("confirm_password"), type="password", key="cp_conf")
        if st.button(t("save_password"), key="cp_save"):
            me = current_user()
            if not verify_password(cur_pw, admins[me]):
                st.error(t("password_wrong"))
            elif new_pw != conf_pw:
                st.error(t("password_mismatch"))
            elif len(new_pw) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                admins[me] = hash_password(new_pw)
                save_data(data)
                log_audit("CHANGE_PASSWORD", f"{me} changed their password")
                st.success(t("password_changed"))

    # ── Session Timeout ───────────────────────────────────────────────────────
    with st.expander("⏱ Session Timeout", expanded=False):
        cur_to = st.session_state.get("session_timeout_minutes", SESSION_TIMEOUT_MINUTES)
        new_to = st.number_input(t("session_timeout"), min_value=5, max_value=240, value=cur_to, key="st_timeout")
        if st.button("Save", key="st_save"):
            st.session_state.session_timeout_minutes = int(new_to)
            st.success(f"Session timeout set to {new_to} minutes.")

    # ── Admin Management (superadmin only) ────────────────────────────────────
    if is_superadmin():
        st.markdown("---")
        st.markdown(f"### 👥 {t('admin_mgmt')}")

        st.markdown(f"**{t('admins_list')}**")
        for uname in list(admins.keys()):
            badge = f'<span class="badge badge-gold">{t("superadmin_badge")}</span>' if uname == SUPERADMIN_USERNAME else ""
            st.markdown(f'<div class="admin-row"><span>👤 {uname} {badge}</span></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander(f"➕ {t('add_admin')}", expanded=False):
            na_user = st.text_input(t("new_admin_user"), key="na_user")
            na_pass = st.text_input(t("new_admin_pass"), type="password", key="na_pass")
            if st.button(t("add_admin"), key="na_create"):
                uname_clean = na_user.strip().lower()
                if not uname_clean or not na_pass:
                    st.warning("Enter both username and password.")
                elif uname_clean in admins:
                    st.error(t("admin_exists"))
                elif len(na_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    admins[uname_clean] = hash_password(na_pass)
                    save_data(data)
                    log_audit("ADD_ADMIN", f"Superadmin added '{uname_clean}'")
                    st.success(t("admin_created", u=uname_clean))
                    st.rerun()

        removable = [u for u in admins if u != SUPERADMIN_USERNAME]
        if removable:
            with st.expander(f"🗑️ {t('remove_admin')}", expanded=False):
                rem_sel = st.selectbox(t("select_admin"), removable, key="ra_sel")
                if st.button(t("remove_admin"), key="ra_btn"):
                    if rem_sel == current_user():
                        st.error(t("cannot_remove_self"))
                    else:
                        del admins[rem_sel]
                        save_data(data)
                        log_audit("REMOVE_ADMIN", f"Superadmin removed '{rem_sel}'")
                        st.success(t("admin_removed", u=rem_sel))
                        st.rerun()

    # ── Delete Bus ────────────────────────────────────────────────────────────
    st.markdown("---")
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

    # ── Audit Log ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### 📋 {t('audit_log')}")
    all_audit = load_audit()
    if all_audit:
        df_audit = pd.DataFrame(all_audit)
        st.dataframe(df_audit, use_container_width=True, hide_index=True)
        st.download_button("⬇ Download Audit Log",
                           data=df_audit.to_csv(index=False).encode("utf-8"),
                           file_name=f"audit_{datetime.now().strftime('%Y%m%d')}.csv",
                           mime="text/csv")
    else:
        st.caption("No audit entries yet.")

    # ── Danger Zone (superadmin only) ─────────────────────────────────────────
    if is_superadmin():
        st.markdown("---")
        st.markdown(f"### ⚠️ {t('danger_zone')}")
        with st.expander(t("clear_all_data"), expanded=False):
            st.warning("This will permanently delete all buses and members. There is no undo.")
            confirm_txt = st.text_input(t("confirm_clear"), key="dz_confirm")
            if st.button(t("clear_all_data"), key="dz_btn"):
                if confirm_txt == "CONFIRM":
                    data["buses"]    = {}
                    data["capacity"] = {}
                    st.session_state.data = data
                    st.session_state.rollcall_state  = {}
                    st.session_state.checklist_state = {}
                    st.session_state.trip_info       = {}
                    save_data(data)
                    log_audit("CLEAR_ALL_DATA", "All data wiped by superadmin")
                    st.success(t("data_cleared"))
                    st.rerun()
                else:
                    st.error("Type CONFIRM exactly to proceed.")
