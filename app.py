import streamlit as st
import pandas as pd
import io
from datetime import datetime
import os

st.set_page_config(page_title="سامانه حضور و غیاب مدرسه", page_icon="🏫", layout="centered")

st.markdown("<h2 style='text-align: center; color: #4F46E5;'>سامانه هوشمند حضور و غیاب و نمره‌دهی</h2>", unsafe_allow_html=True)
st.write("---")

if "submitted_records" not in st.session_state:
    st.session_state.submitted_records = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "started" not in st.session_state:
    st.session_state.started = False
if "selected_class_name" not in st.session_state:
    st.session_state.selected_class_name = ""

teacher_name = st.text_input("نام و نام خانوادگی معلم")
subject_name = st.text_input("نام درس")

uploaded_file = st.file_uploader("بارگذاری فایل دانش‌آموزان (فرمت .csv یا .xlsx یا .xls)", type=["csv", "xls", "xlsx"])

if uploaded_file is not None:
    try:
        bytes_data = uploaded_file.read()
        file_name = uploaded_file.name.lower()
        
        if file_name.endswith('.csv'):
            try:
                df = pd.read_csv(io.BytesIO(bytes_data), encoding='utf-8')
            except:
                try:
                    df = pd.read_csv(io.BytesIO(bytes_data), encoding='utf-8-sig')
                except:
                    df = pd.read_csv(io.BytesIO(bytes_data), encoding='latin1')
        else:
            df = pd.read_excel(io.BytesIO(bytes_data))
            
        st.success("✅ فایل با موفقیت بارگذاری شد!")
        
        df.columns = [str(col).strip() for col in df.columns]
        columns = list(df.columns)
        
        st.info("📌 لطفاً مشخص کنید کدام ستون‌ها مربوط به اطلاعات زیر هستند:")
        
        default_class_idx = columns.index('ردیف') if 'ردیف' in columns else (columns.index('کلاس') if 'کلاس' in columns else 0)
        default_name_idx = columns.index('نام') if 'نام' in columns else 0
        default_family_idx = columns.index('نام خانوادگی') if 'نام خانوادگی' in columns else (1 if len(columns) > 1 else 0)
        
        col_class = st.selectbox("ستون مربوط به کلاس / ردیف:", columns, index=default_class_idx)
        col_name = st.selectbox("ستون مربوط به نام:", columns, index=default_name_idx)
        col_family = st.selectbox("ستون مربوط به نام خانوادگی:", columns, index=default_family_idx)
        
        class_list = df[col_class].dropna().unique().tolist()
        class_list = [str(c).strip() for c in class_list]
        
        selected_class = st.selectbox("انتخاب کلاس مورد نظر برای حضور و غیاب:", class_list)

        if st.button("شروع حضور و غیاب 🚀", use_container_width=True):
            if not teacher_name or not subject_name:
                st.warning("⚠️ لطفاً نام معلم و نام درس را وارد کنید.")
            else:
                class_df = df[df[col_class].astype(str).str.strip() == str(selected_class).strip()]
                if class_df.empty:
                    st.error("❌ هیچ دانش‌آموزی در این کلاس یافت نشد!")
                else:
                    standard_students = []
                    for _, row in class_df.iterrows():
                        n = str(row.get(col_name, '')).strip()
                        f = str(row.get(col_family, '')).strip()
                        full_name = f"{n} {f}"
                        
                        standard_students.append({
                            "نام و نام خانوادگی": full_name,
                            "اسم مدرسه": "مدیریت مدرسه",
                            "اسم کلاس": str(selected_class)
                        })
                    st.session_state.students = standard_students
                    st.session_state.current_index = 0
                    st.session_state.submitted_records = []
                    st.session_state.started = True
                    st.session_state.selected_class_name = str(selected_class)
                    st.rerun()
    except Exception as e:
        st.error(f"❌ خطا در پردازش فایل: {e}")

# پنل ثبت حضور و غیاب کارت‌محور برای هر دانش‌آموز
if st.session_state.get("started", False):
    students = st.session_state.students
    idx = st.session_state.current_index
    
    db_file = "central_school_database.xlsx"
    history_df = pd.DataFrame()
    if os.path.exists(db_file):
        try:
            history_df = pd.read_excel(db_file)
        except:
            pass

    if idx < len(students):
        student = students[idx]
        student_name = student.get('نام و نام خانوادگی', '')
        
        student_history = pd.DataFrame()
        if not history_df.empty and 'نام دانش‌آموز' in history_df.columns:
            student_history = history_df[history_df['نام دانش‌آموز'].astype(str).str.strip() == student_name.strip()]

        avg_score = 0.0
        absences = 0
        lates = 0
        notes_list = []
        
        if not student_history.empty:
            valid_scores = student_history['نمره'].dropna()
            if not valid_scores.empty:
                avg_score = valid_scores.mean()
            
            if 'وضعیت' in student_history.columns:
                absences = len(student_history[student_history['وضعیت'] == 'غایب'])
                lates = len(student_history[student_history['وضعیت'] == 'تاخیر'])
                
            if 'یادداشت' in student_history.columns:
                notes_list = student_history['یادداشت'].dropna().tolist()
                notes_list = [str(n) for n in notes_list if str(n).strip() != "" and str(n).strip() != "nan"]

        st.info(f"📍 نفر {idx + 1} از {len(students)} | کلاس: {student.get('اسم کلاس', '')}")
        
        st.markdown(f"""
        <div style="background-color: #f8fafc; border: 2px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <h3 style="color: #1e293b; margin-top: 0; margin-bottom: 15px; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px;">👤 {student_name}</h3>
            <p style="margin: 6px 0; color: #475569;">📊 <b>میانگین نمرات قبلی:</b> {avg_score:.1f} از 20</p>
            <p style="margin: 6px 0; color: #475569;">❌ <b>تعداد غیبت‌ها:</b> {absences} &nbsp;&nbsp;|&nbsp;&nbsp; ⏰ <b>تاخیرها:</b> {lates}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if notes_list:
            with st.expander("📖 مشاهده یادداشت‌های ثبت شده‌ی قبلی"):
                for note_item in notes_list:
                    st.write(f"- {note_item}")

        with st.form(key=f"form_{idx}"):
            st.write("**ثبت وضعیت امروز:**")
            status = st.radio("وضعیت حضور", ["حاضر", "غایب", "تاخیر"], horizontal=True, label_visibility="collapsed")
            
            score = st.number_input("نمره جلسه (اختیاری)", min_value=0.0, max_value=20.0, step=0.5, value=0.0)
            note = st.text_area("یادداشت کوتاه جدید (حداکثر ۱۰۰ حرف)", max_chars=100)
            
            submitted = st.form_submit_button("ثبت و نفر بعدی ➡️", use_container_width=True)
            
            if submitted:
                record = {
                    "تاریخ": datetime.now().strftime("%Y-%m-%d"),
                    "مدرسه": student.get("اسم مدرسه", "نامشخص"),
                    "کلاس": student.get("اسم کلاس", "نامشخص"),
                    "درس": subject_name,
                    "معلم": teacher_name,
                    "نام دانش‌آموز": student_name,
                    "وضعیت": status,
                    "نمره": score if score > 0 else None,
                    "یادداشت": note if note.strip() != "" else None
                }
                st.session_state.submitted_records.append(record)
                st.session_state.current_index += 1
                st.rerun()
    else:
        st.success("✅ حضور و غیاب این کلاس به پایان رسید!")
        
        report_df = pd.DataFrame(st.session_state.submitted_records)
        db_file = "central_school_database.xlsx"
        
        if os.path.exists(db_file):
            existing_df = pd.read_excel(db_file)
            pd.concat([existing_df, report_df], ignore_index=True).to_excel(db_file, index=False)
        else:
            report_df.to_excel(db_file, index=False)
            
        absent_students = report_df[report_df['وضعیت'] == 'غایب']['نام دانش‌آموز'].tolist()
        late_students = report_df[report_df['وضعیت'] == 'تاخیر']['نام دانش‌آموز'].tolist()
        
        current_date_str = datetime.now().strftime("%Y/%m/%d")
        class_str = st.session_state.get('selected_class_name', 'نامشخص')
        
        report_text = f"📋 گزارش حضور و غیاب کلاس {class_str}\n"
        report_text += f"📚 درس: {subject_name} | 👨‍🏫 دبیر: {teacher_name}\n"
        report_text += f"📅 تاریخ: {current_date_str}\n\n"
        
        if absent_students:
            report_text += "❌ **دانش‌آموزان غایب:**\n"
            for i, name in enumerate(absent_students, 1):
                report_text += f"{i}. {name}\n"
        else:
            report_text += "❌ **دانش‌آموزان غایب:** موردی نداشت (کلاس کامل بود)\n"
            
        report_text += "\n"
        if late_students:
            report_text += "⏰ **دانش‌آموزان با تاخیر:**\n"
            for i, name in enumerate(late_students, 1):
                report_text += f"{i}. {name}\n"
        else:
            report_text += "⏰ **دانش‌آموزان با تاخیر:** موردی نداشت\n"

        st.markdown("### 📤 متن گزارش جهت ارسال به مدیر / معاون:")
        st.info("می‌توانید متن زیر را به راحتی کپی کرده و در پیام‌رسان‌ها ارسال کنید:")
        
        st.text_area("متن آماده گزارش:", value=report_text, height=200)
        
        st.download_button(
            label="📥 دانلود فایل دیتابیس مرکزی مدرسه (گزارش کامل اکسل)",
            data=open(db_file, "rb").read(),
            file_name="central_school_database.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        if st.button("شروع کلاس جدید 🔄", use_container_width=True):
            st.session_state.started = False
            st.session_state.current_index = 0
            st.session_state.submitted_records = []
            st.rerun()
