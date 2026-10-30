import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="سامانه حضور و غیاب مدرسه", page_icon="🏫")

st.markdown("<h2 style='text-align: center; color: #4F46E5;'>سامانه هوشمند حضور و غیاب و نمره‌دهی</h2>", unsafe_allow_html=True)
st.write("---")

if "submitted_records" not in st.session_state:
    st.session_state.submitted_records = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "started" not in st.session_state:
    st.session_state.started = False

teacher_name = st.text_input("نام و نام خانوادگی معلم")
subject_name = st.text_input("نام درس")

uploaded_file = st.file_uploader("بارگذاری فایل اکسل دانش‌آموزان (.xlsx یا .xls)", type=["xls", "xlsx"])

if uploaded_file is not None:
    try:
        # خواندن فایل با موتور سازگار با xls و xlsx
        df = pd.read_excel(uploaded_file, engine=None)
        st.success("✅ فایل اکسل با موفقیت بارگذاری شد!")
        
        # پاکسازی نام ستون‌ها از فاصله‌های اضافی
        df.columns = df.columns.str.strip()
        
        # پیدا کردن ستون ردیف یا کلاس
        class_col = None
        for col in df.columns:
            if 'ردیف' in str(col) or 'کلاس' in str(col):
                class_col = col
                break
        
        if class_col is None and len(df.columns) > 0:
            class_col = df.columns[0] # پیش‌فرض ستون اول

        if class_col is not None:
            class_list = df[class_col].dropna().unique().tolist()
            class_list = [str(c).strip() for c in class_list]
            
            selected_class = st.selectbox(f"انتخاب کلاس (بر اساس ستون {class_col}):", class_list)

            if st.button("شروع حضور و غیاب 🚀", use_container_width=True):
                if not teacher_name or not subject_name:
                    st.warning("⚠️ لطفاً مشخصات معلم و درس را کامل وارد کنید.")
                else:
                    class_df = df[df[class_col].astype(str).str.strip() == str(selected_class).strip()]
                    if class_df.empty:
                        st.error("❌ هیچ دانش‌آموزی برای این کلاس یافت نشد!")
                    else:
                        standard_students = []
                        for _, row in class_df.iterrows():
                            # پیدا کردن نام و نام خانوادگی به صورت هوشمند
                            name_val = str(row.get('نام', row.get(df.columns[3], ''))).strip()
                            family_val = str(row.get('نام خانوادگی', row.get(df.columns[4], ''))).strip()
                            full_name = f"{name_val} {family_val}"
                            
                            standard_students.append({
                                "نام و نام خانوادگی": full_name,
                                "اسم مدرسه": str(row.get('مدرسه', 'مدیربت مدرسه')),
                                "اسم کلاس": str(selected_class)
                            })
                        st.session_state.students = standard_students
                        st.session_state.current_index = 0
                        st.session_state.submitted_records = []
                        st.session_state.started = True
                        st.rerun()
        else:
            st.error("❌ ستون کلاس یا ردیف در فایل اکسل یافت نشد.")
    except Exception as e:
        st.error(f"❌ خطا در خواندن فایل اکسل: {e}")

# پنل ثبت حضور و غیاب هر دانش‌آموز
if st.session_state.get("started", False):
    students = st.session_state.students
    idx = st.session_state.current_index
    
    if idx < len(students):
        student = students[idx]
        st.info(f"📍 نفر {idx + 1} از {len(students)} | کلاس: {student.get('اسم کلاس', '')}")
        st.markdown(f"### 👤 نام دانش‌آموز: **{student.get('نام و نام خانوادگی', '')}**")
        
        with st.form(key=f"form_{idx}"):
            status = st.selectbox("وضعیت حضور", ["حاضر", "غایب", "تاخیر"])
            score = st.number_input("نمره (اختیاری)", min_value=0.0, max_value=20.0, step=0.5, value=0.0)
            note = st.text_area("یادداشت کوتاه (حداکثر ۱۰۰ حرف)", max_chars=100)
            
            submitted = st.form_submit_button("ثبت و نفر بعدی ➡️", use_container_width=True)
            
            if submitted:
                record = {
                    "تاریخ": datetime.now().strftime("%Y-%m-%d"),
                    "مدرسه": student.get("اسم مدرسه", "نامشخص"),
                    "کلاس": student.get("اسم کلاس", "نامشخص"),
                    "درس": subject_name,
                    "معلم": teacher_name,
                    "نام دانش‌آموز": student.get('نام و نام خانوادگی', 'نامشخص'),
                    "وضعیت": status,
                    "نمره": score if score > 0 else None,
                    "یادداشت": note
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
            
        st.download_button(
            label="📥 دانلود فایل دیتابیس مرکزی مدرسه (گزارش کامل)",
            data=open(db_file, "rb").read(),
            file_name="central_school_database.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        if st.button("شروع کلاس جدید 🔄", use_container_width=True):
            st.session_state.started = False
            st.session_state.current_index = 0
            st.rerun()
            
