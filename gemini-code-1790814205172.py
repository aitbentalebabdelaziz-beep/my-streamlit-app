import streamlit as st
import sqlite3
import pandas as pd
import json
import re
from datetime import datetime

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="منصة إدخال البيانات الذكية",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# RTL & Responsive CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }
    .block-container {
        padding: 1.5rem 1rem !important;
        max-width: 100% !important;
    }
    div.stButton > button, div.stDownloadButton > button {
        width: 100% !important;
        border-radius: 8px !important;
        height: 3rem !important;
        font-weight: bold !important;
        font-size: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE SETUP
# ==========================================
DB_NAME = "app_database.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schema_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_name TEXT NOT NULL,
            field_type TEXT NOT NULL,
            options TEXT,
            is_required INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_json TEXT NOT NULL
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM schema_fields")
    if cursor.fetchone()[0] == 0:
        default_schema = [
            ("اسم العميل / المستفيد", "نص (Text)", "", 1),
            ("رقم الهاتف / التواصل", "رقم (Number)", "", 1),
            ("تصنيف المعاملة", "قائمة خيارات (Dropdown)", "طلب جديد, استفسار, دعم فني, شكوى, صيانة", 1),
            ("حالة الطلب", "قائمة خيارات (Dropdown)", "جديد, قيد المتابعة, مكتمل, معلق", 1),
            ("المبلغ / القيمة", "رقم (Number)", "", 0),
            ("تاريخ المعاملة", "تاريخ (Date)", "", 1),
            ("التفاصيل والملاحظات", "ملاحظات (Text Area)", "", 0)
        ]
        for name, ftype, opts, req in default_schema:
            cursor.execute("INSERT INTO schema_fields (field_name, field_type, options, is_required) VALUES (?, ?, ?, ?)",
                           (name, ftype, opts, req))

    conn.commit()
    conn.close()

init_db()

def ai_extract_data(text_input, schema_fields):
    extracted = {}
    text = text_input.strip()
    phone_match = re.search(r'05\d{8}|\+?\d{10,12}', text)
    amount_match = re.search(r'(\d+)\s*(ريال|درهم|دولار|\$)?', text)

    for field in schema_fields:
        fname = field["field_name"]
        ftype = field["field_type"]

        if ("هاتف" in fname or "تواصل" in fname or "رقم" in fname) and ftype == "رقم (Number)":
            extracted[fname] = int(phone_match.group(0)) if phone_match else 0
        elif "مبلغ" in fname or "قيمة" in fname or "سعر" in fname:
            extracted[fname] = int(amount_match.group(1)) if amount_match else 0
        elif ftype == "تاريخ (Date)":
            extracted[fname] = str(datetime.now().date())
        elif ftype == "قائمة خيارات (Dropdown)":
            opts = [o.strip() for o in field["options"].split(",")] if field["options"] else []
            found_opt = opts[0] if opts else ""
            for o in opts:
                if o in text:
                    found_opt = o
                    break
            extracted[fname] = found_opt
        else:
            extracted[fname] = text

    return extracted

# ==========================================
# 3. SESSION STATE & LOGIN
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""
if "ai_prefilled" not in st.session_state:
    st.session_state["ai_prefilled"] = {}

if not st.session_state["logged_in"]:
    st.title("⚡ تسجيل الدخول")
    with st.form("login_form"):
        email_input = st.text_input("📧 البريد الإلكتروني:", placeholder="user@domain.com")
        submit_login = st.form_submit_button("🚀 دخول النظام", use_container_width=True)
        if submit_login:
            if "@" not in email_input:
                st.error("⚠️ يرجى إدخال بريد إلكتروني صحيح.")
            else:
                st.session_state["logged_in"] = True
                st.session_state["user_email"] = email_input.strip().lower()
                st.rerun()
else:
    st.title("⚡ منصة إدخال البيانات الذكية")
    st.caption(f"👤 المستخدم: **{st.session_state['user_email']}**")

    with st.sidebar:
        st.header("📌 القائمة")
        app_mode = st.radio("اختر الشاشة:", ["🏠 الرئيسية", "🤖 المساعد الذكي", "📝 نموذج إدخال", "📊 قاعدة البيانات"])
        if st.button("🚪 خروج", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    conn = get_db()
    schema_rows = conn.execute("SELECT * FROM schema_fields").fetchall()
    conn.close()

    if app_mode == "🏠 الرئيسية":
        st.subheader("📊 أهلاً بك في المنصة الذكية")
        st.info("التطبيق متوافق تماماً مع متصفحات جوجل وكافة الأجهزة المحمولة والحواسيب.")

    elif app_mode == "🤖 المساعد الذكي":
        st.subheader("🤖 تحليل النصوص وتعبئة الحقول")
        raw_text = st.text_area("ألصق نص المعاملة هنا:")
        if st.button("🪄 تحليل", use_container_width=True):
            if raw_text:
                st.session_state["ai_prefilled"] = ai_extract_data(raw_text, schema_rows)
                st.success("تم التفكيك بنجاح!")
                st.json(st.session_state["ai_prefilled"])

    elif app_mode == "📝 نموذج إدخال":
        st.subheader("📝 إدخال سجل جديد")
        with st.form("entry_form"):
            form_values = {}
            ai_data = st.session_state.get("ai_prefilled", {})
            for field in schema_rows:
                fname = field["field_name"]
                form_values[fname] = st.text_input(fname, value=str(ai_data.get(fname, "")))
            if st.form_submit_button("💾 حفظ", use_container_width=True):
                conn = get_db()
                conn.execute("INSERT INTO records (user_email, data_json) VALUES (?, ?)", 
                             (st.session_state["user_email"], json.dumps(form_values, ensure_ascii=False)))
                conn.commit()
                conn.close()
                st.success("✅ تم الحفظ بنجاح!")

    elif app_mode == "📊 قاعدة البيانات":
        st.subheader("📊 السجلات المسجلة")
        conn = get_db()
        recs = conn.execute("SELECT * FROM records ORDER BY id DESC").fetchall()
        conn.close()
        data = [json.loads(r["data_json"]) for r in recs]
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 تصدير CSV", df.to_csv(index=False).encode('utf-8-sig'), "data.csv", "text/csv")