import streamlit as st
import sqlite3
import pandas as pd
import json
import re
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="تطبيق إدخال البيانات والتطبيقات الذكية",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Professional UI Styling (CSS)
st.markdown("""
<style>
    /* Global Styles & Direction */
    .stApp {
        background-color: #f4f6f9;
        direction: rtl;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Login Card Styling */
    .login-container {
        max-width: 450px;
        margin: 40px auto;
        background: #ffffff;
        padding: 35px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        text-align: center;
        border: 1px solid #e1e8ed;
    }
    .login-header {
        color: #1a237e;
        font-size: 26px;
        font-weight: 800;
        margin-bottom: 10px;
    }
    .login-sub {
        color: #5c6bc0;
        font-size: 14px;
        margin-bottom: 25px;
    }

    /* App Hero Banner */
    .app-hero {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 28px 32px;
        border-radius: 20px;
        box-shadow: 0 8px 20px rgba(30, 60, 114, 0.2);
        margin-bottom: 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .app-hero h1 {
        color: #ffffff !important;
        font-size: 28px;
        font-weight: 800;
        margin: 0;
    }
    .app-hero p {
        color: #e0e7ff;
        font-size: 15px;
        margin: 6px 0 0 0;
    }
    .user-badge {
        background: rgba(255, 255, 255, 0.2);
        padding: 8px 16px;
        border-radius: 30px;
        font-size: 14px;
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }

    /* Metric Cards */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        border-right: 5px solid #2a5298;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-title {
        font-size: 14px;
        color: #64748b;
        font-weight: 600;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 800;
        color: #0f172a;
        margin-top: 5px;
    }

    /* Search Bar Styling */
    .search-box {
        background: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    /* Result Cards */
    .record-card {
        background: white;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        border: 1px solid #e2e8f0;
        border-right: 4px solid #3b82f6;
    }
    .record-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 8px;
    }
    .record-title {
        font-size: 18px;
        font-weight: 700;
        color: #1e293b;
    }
    .record-badge {
        background: #e0f2fe;
        color: #0369a1;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
    }
    
    /* Buttons Customization */
    .stButton>button {
        border-radius: 10px;
        font-weight: 700;
        height: 46px;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)

# Database Setup
DB_NAME = "app_database.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Table for registered users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Table for dynamic schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schema_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_name TEXT NOT NULL,
            field_type TEXT NOT NULL,
            options TEXT,
            is_required INTEGER DEFAULT 0
        )
    ''')
    # Table for actual data records
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_json TEXT NOT NULL
        )
    ''')

    # Seed default fields if empty
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
            
    # Seed sample record if empty
    cursor.execute("SELECT COUNT(*) FROM records")
    if cursor.fetchone()[0] == 0:
        sample_data = {
            "اسم العميل / المستفيد": "شركة الأمل للتجارة",
            "رقم الهاتف / التواصل": "0501234567",
            "تصنيف المعاملة": "طلب جديد",
            "حالة الطلب": "جديد",
            "المبلغ / القيمة": 1500,
            "تاريخ المعاملة": str(datetime.now().date()),
            "التفاصيل والملاحظات": "طلب توريد أجهزة ومستلزمات مكتبية"
        }
        cursor.execute("INSERT INTO records (user_email, data_json) VALUES (?, ?)", 
                       ("admin@app.com", json.dumps(sample_data, ensure_ascii=False)))

    conn.commit()
    conn.close()

init_db()

# Session State Initialization
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""

# EMAIL LOGIN SCREEN
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('''
        <div class="login-container">
            <div style="font-size: 50px; margin-bottom: 10px;">🔐</div>
            <div class="login-header">مرحباً بك في التطبيق الذكي</div>
            <div class="login-sub">أدخل بريدك الإلكتروني للدخول إلى واجهة إدخال وقاعدة البيانات</div>
        </div>
        ''', unsafe_allow_html=True)
        
        with st.form("login_form"):
            email_input = st.text_input("📧 البريد الإلكتروني:", placeholder="name@example.com")
            password_input = st.text_input("🔑 كلمة المرور (اختياري للتحقق):", type="password", placeholder="••••••••")
            submit_login = st.form_submit_button("🚀 دخول إلى التطبيق", use_container_width=True)
            
            if submit_login:
                email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
                if not email_input or not re.match(email_regex, email_input.strip()):
                    st.error("⚠️ يرجى إدخال بريد إلكتروني صحيح (مثل: user@example.com).")
                else:
                    # Save user to DB
                    conn = get_db()
                    conn.execute("INSERT OR IGNORE INTO users (email) VALUES (?)", (email_input.strip().lower(),))
                    conn.commit()
                    conn.close()
                    
                    st.session_state["logged_in"] = True
                    st.session_state["user_email"] = email_input.strip().lower()
                    st.success("تم تسجيل الدخول بنجاح!")
                    st.rerun()

# MAIN APPLICATION UI
else:
    # Top Hero Header
    st.markdown(f'''
    <div class="app-hero">
        <div>
            <h1>📱 منصة إدارة وتطبيق إدخال البيانات الذكية</h1>
            <p>واجهة متطورة، بحث فوري وقاعدة بيانات آمنة</p>
        </div>
        <div class="user-badge">
            👤 المستخدم الحالي: <b>{st.session_state["user_email"]}</b>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Sidebar Navigation & Logout
    with st.sidebar:
        st.image("https://img.icons8.com/isometric/100/database.png", width=70)
        st.title("القائمة الرئيسية")
        app_mode = st.radio(
            "اختر الشاشة:",
            ["🏠 الصفحة الرئيسية والدخول", "🔍 البحث والتفتيش الفوري", "📝 نموذج إدخال جديد", "📊 قاعدة البيانات الكاملة", "⚙️ إعدادات الحقول"],
            index=0
        )
        st.divider()
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["user_email"] = ""
            st.rerun()

    # Get DB data for metrics
    conn = get_db()
    total_records = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    total_fields = conn.execute("SELECT COUNT(*) FROM schema_fields").fetchone()[0]
    my_records = conn.execute("SELECT COUNT(*) FROM records WHERE user_email = ?", (st.session_state["user_email"],)).fetchone()[0]
    conn.close()

    # 1. LANDING DASHBOARD
    if app_mode == "🏠 الصفحة الرئيسية والدخول":
        st.subheader("📌 نظرة عامة وإحصائيات السجلات")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">📊 إجمالي السجلات بالمشروع</div>
                <div class="metric-value">{total_records}</div>
            </div>
            ''', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
            <div class="metric-card" style="border-right-color: #10b981;">
                <div class="metric-title">👤 سجلات أدخلتها ببريدك</div>
                <div class="metric-value">{my_records}</div>
            </div>
            ''', unsafe_allow_html=True)
        with col3:
            st.markdown(f'''
            <div class="metric-card" style="border-right-color: #8b5cf6;">
                <div class="metric-title">⚙️ عدد حقول الإدخال النشطة</div>
                <div class="metric-value">{total_fields}</div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Quick Action Buttons
        st.subheader("⚡ الإجراءات السريعة")
        qcol1, qcol2, qcol3 = st.columns(3)
        with qcol1:
            st.info("📝 **إدخال جديد**")
            st.caption("أضف سجل بيانات جديد مباشرة إلى قاعدة البيانات.")
        with qcol2:
            st.success("🔍 **البحث الفوري**")
            st.caption("ابحث برقم الهاتف أو الاسم أو التفاصيل بسرعة فائقة.")
        with qcol3:
            st.warning("⚙️ **تخصيص الواجهة**")
            st.caption("حدد الحقول والخيارات التي تظهر في النموذج بنفسك.")

    # 2. INSTANT SEARCH & FILTERING
    elif app_mode == "🔍 البحث والتفتيش الفوري":
        st.subheader("🔍 خانة البحث والتفتيش الذكي في السجلات")
        st.caption("قم بكتابة أي كلمة (اسم، رقم هاتف، حالة، أو تصنيف) للبحث الفوري عبر كافة البيانات.")

        search_query = st.text_input("🔎 اكتب كلمة البحث هنا:", placeholder="مثال: أحمد، 050، طلب جديد، شركة الأمل...")
        
        conn = get_db()
        all_recs = conn.execute("SELECT * FROM records ORDER BY id DESC").fetchall()
        conn.close()

        filtered_recs = []
        for r in all_recs:
            data_dict = json.loads(r["data_json"])
            # Flatten to text for easy regex/substring search
            full_text = f"{r['id']} {r['user_email']} {r['created_at']} " + " ".join([str(v) for v in data_dict.values()])
            if search_query.strip() == "" or search_query.strip().lower() in full_text.lower():
                filtered_recs.append((r, data_dict))

        st.write(f"🔍 عُثر على **{len(filtered_recs)}** سجل مطابق لـ '{search_query}'")
        
        if not filtered_recs:
            st.warning("لا توجد نتائج مطابقة للبحث.")
        else:
            for r, ddict in filtered_recs:
                first_key = list(ddict.keys())[0] if ddict else "سجل"
                first_val = ddict.get(first_key, "بدون عنوان")
                
                with st.container():
                    st.markdown(f'''
                    <div class="record-card">
                        <div class="record-header">
                            <span class="record-title">📌 #{r["id"]} - {first_val}</span>
                            <span class="record-badge">بواسطة: {r["user_email"]} | {r["created_at"][:10]}</span>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    # Display fields in clean 2-column layout
                    cols = st.columns(2)
                    idx = 0
                    for k, v in ddict.items():
                        with cols[idx % 2]:
                            st.write(f"• **{k}**: {v}")
                        idx += 1
                        
                    st.divider()

    # 3. DYNAMIC FORM ENTRY
    elif app_mode == "📝 نموذج إدخال جديد":
        st.subheader("📝 نموذج إدخال البيانات المطور")
        st.caption("أدخل البيانات في الحقول التالية وسوف تُحفظ فوراً في قاعدة البيانات.")

        conn = get_db()
        schema = conn.execute("SELECT * FROM schema_fields").fetchall()
        conn.close()

        if not schema:
            st.warning("لم يتم تعيين أي حقول بعد. انتقل إلى '⚙️ إعدادات الحقول' لإضافة حقولك.")
        else:
            with st.form("web_data_form", clear_on_submit=True):
                form_values = {}
                cols = st.columns(2)
                
                for i, field in enumerate(schema):
                    fname = field["field_name"]
                    ftype = field["field_type"]
                    fopts = [o.strip() for o in field["options"].split(",")] if field["options"] else []
                    freq = " *" if field["is_required"] else ""

                    with cols[i % 2]:
                        if ftype == "نص (Text)":
                            form_values[fname] = st.text_input(f"{fname}{freq}")
                        elif ftype == "رقم (Number)":
                            form_values[fname] = st.number_input(f"{fname}{freq}", value=0)
                        elif ftype == "قائمة خيارات (Dropdown)":
                            form_values[fname] = st.selectbox(f"{fname}{freq}", fopts if fopts else ["افتراضي"])
                        elif ftype == "تاريخ (Date)":
                            form_values[fname] = str(st.date_input(f"{fname}{freq}"))
                        elif ftype == "ملاحظات (Text Area)":
                            form_values[fname] = st.text_area(f"{fname}{freq}")

                btn_submit = st.form_submit_button("💾 حفظ البيانات وإضافتها لقاعدة البيانات", use_container_width=True)
                
                if btn_submit:
                    # Check required
                    missing_reqs = []
                    for field in schema:
                        if field["is_required"]:
                            v = form_values.get(field["field_name"])
                            if v is None or str(v).strip() == "":
                                missing_reqs.append(field["field_name"])
                    
                    if missing_reqs:
                        st.error(f"⚠️ يرجى ملء الحقول الإجبارية التالية: {', '.join(missing_reqs)}")
                    else:
                        conn = get_db()
                        conn.execute("INSERT INTO records (user_email, data_json) VALUES (?, ?)",
                                     (st.session_state["user_email"], json.dumps(form_values, ensure_ascii=False)))
                        conn.commit()
                        conn.close()
                        st.success("✅ تم حفظ السجل بنجاح في قاعدة البيانات!")

    # 4. MASTER DATABASE TABLE
    elif app_mode == "📊 قاعدة البيانات الكاملة":
        st.subheader("📊 قاعدة البيانات واستعراض السجلات")
        
        conn = get_db()
        recs = conn.execute("SELECT id, user_email, created_at, data_json FROM records ORDER BY id DESC").fetchall()
        conn.close()

        if not recs:
            st.info("لا توجد بيانات مسجلة في قاعدة البيانات حالياً.")
        else:
            table_data = []
            for r in recs:
                row_dict = {
                    "رقم السجل": r["id"],
                    "المُدخل (البريد)": r["user_email"],
                    "تاريخ الإدخال": r["created_at"]
                }
                row_dict.update(json.loads(r["data_json"]))
                table_data.append(row_dict)

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)

            csv_file = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تصدير السجلات كملف Excel / CSV",
                data=csv_file,
                file_name=f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv',
                use_container_width=True
            )

    # 5. SCHEMA SETTINGS
    elif app_mode == "⚙️ إعدادات الحقول":
        st.subheader("⚙️ تخصيص حقول واجهة التطبيق بنفسك")
        st.caption("يمكنك تحديد الحقول والأنواع والخيارات التي تظهر في الواجهة وتعديلها بسهولة.")

        with st.expander("➕ إضافة حقل جديد للنموذج", expanded=True):
            nf_name = st.text_input("اسم الحقل الجديد:")
            nf_type = st.selectbox("نوع الحقل:", ["نص (Text)", "رقم (Number)", "قائمة خيارات (Dropdown)", "تاريخ (Date)", "ملاحظات (Text Area)"])
            nf_opts = st.text_input("خيارات القائمة المنسدلة (فصل بالفاصلة):", placeholder="مثال: ممتاز, جيد, متوسط")
            nf_req = st.checkbox("حقل إجباري؟")

            if st.button("➕ حفظ وإضافة الحقل", use_container_width=True):
                if not nf_name.strip():
                    st.error("يرجى إدخال اسم الحقل.")
                else:
                    conn = get_db()
                    conn.execute("INSERT INTO schema_fields (field_name, field_type, options, is_required) VALUES (?, ?, ?, ?)",
                                 (nf_name.strip(), nf_type, nf_opts.strip(), 1 if nf_req else 0))
                    conn.commit()
                    conn.close()
                    st.success(f"تمت إضافة الحقل '{nf_name}' بنجاح!")
                    st.rerun()

        st.divider()
        st.write("📋 الحقول الحالية في تطبيقك:")
        conn = get_db()
        s_fields = conn.execute("SELECT * FROM schema_fields").fetchall()
        conn.close()

        for sf in s_fields:
            c1, c2 = st.columns([4, 1])
            with c1:
                req_badge = " [إجباري]" if sf["is_required"] else ""
                st.write(f"• **{sf['field_name']}** ({sf['field_type']}){req_badge}")
            with c2:
                if st.button("حذف 🗑️", key=f"del_sf_{sf['id']}"):
                    conn = get_db()
                    conn.execute("DELETE FROM schema_fields WHERE id = ?", (sf['id'],))
                    conn.commit()
                    conn.close()
                    st.success("تم الحذف.")
                    st.rerun()
