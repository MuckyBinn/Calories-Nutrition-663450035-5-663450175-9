import streamlit as st
import numpy as np
import joblib
import sqlite3
import bcrypt

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="₊˚⊹♡🍰เเอพพลิเคชั่นคำนวนโภชนาการสารอาหาร🍓♡⊹˚₊", layout="centered")


DEFAULT_PROFILE = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_640.png"
# ===== SIDEBAR PASTEL PINK =====
st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background-color: #FFEAF4;
}
</style>
""", unsafe_allow_html=True)

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password BLOB,
    age INTEGER,
    weight REAL,
    height REAL,
    gender TEXT,
    profile_pic BLOB
)
""")
conn.commit()

# =========================
# SESSION
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_data" not in st.session_state:
    st.session_state.user_data = None
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# =========================
# AUTH FUNCTIONS
# =========================
def register_user(username, password, age, weight, height, gender, profile_pic):
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        c.execute("""
        INSERT INTO users (username, password, age, weight, height, gender, profile_pic)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, hashed_pw, age, weight, height, gender, profile_pic))
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    if user and bcrypt.checkpw(password.encode(), user[2]):
        return user
    return None

def update_profile(user_id, age, weight, height, gender, profile_pic):
    c.execute("""
    UPDATE users 
    SET age=?, weight=?, height=?, gender=?, profile_pic=?
    WHERE id=?
    """, (age, weight, height, gender, profile_pic, user_id))
    conn.commit()

def get_user_by_id(user_id):
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return c.fetchone()

# =========================
# SIDEBAR ACCOUNT
# =========================
with st.sidebar:
    st.title("👤 Account")

    if not st.session_state.logged_in:

        menu = st.radio("Select Option", ["Login", "Register"])

        if menu == "Register":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            age = st.number_input("Age", 10, 100)
            weight = st.number_input("Weight (kg)", 30.0, 200.0)
            height = st.number_input("Height (cm)", 100.0, 220.0)
            gender = st.selectbox("Gender", ["Male", "Female"])

            uploaded_file = st.file_uploader("Upload Profile Image", type=["png","jpg","jpeg"])

            profile_pic = uploaded_file.read() if uploaded_file else None

            if st.button("Register"):
                if register_user(username, password, age, weight, height, gender, profile_pic):
                    st.success("Registered successfully! Please login.")
                else:
                    st.error("Username already exists.")

        if menu == "Login":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login"):
                user = login_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    else:
        user = st.session_state.user_data

        # ป้องกัน user เป็น None
        if user is None:
            st.session_state.logged_in = False
            st.warning("Session expired. Please login again.")
            st.rerun()

        # ===== SHOW PROFILE =====
        if user[7]:
            st.image(user[7], width=100)
        else:
            st.image(DEFAULT_PROFILE, width=100)

        st.write(f"**{user[1]}**")
        st.write(f"Age: {user[3]}")
        st.write(f"Weight: {user[4]} kg")
        st.write(f"Height: {user[5]} cm")
        st.write(f"Gender: {user[6]}")

        # ===== BMR =====
        if user[6] == "Male":
            bmr = 10*user[4] + 6.25*user[5] - 5*user[3] + 5
        else:
            bmr = 10*user[4] + 6.25*user[5] - 5*user[3] - 161

        st.write(f"🔥 BMR: {bmr:.0f} kcal/day")

        # ===== EDIT PROFILE =====
        if st.button("Edit Profile"):
            st.session_state.edit_mode = True

        if st.session_state.edit_mode:
            st.subheader("✏️ Edit Profile")

            new_age = st.number_input("Age", 10, 100, value=user[3])
            new_weight = st.number_input("Weight (kg)", 30.0, 200.0, value=user[4])
            new_height = st.number_input("Height (cm)", 100.0, 220.0, value=user[5])
            new_gender = st.selectbox("Gender", ["Male","Female"], index=0 if user[6]=="Male" else 1)

            new_image = st.file_uploader("Upload New Profile Image", type=["png","jpg","jpeg"])

            if st.button("Save Changes"):
                profile_blob = new_image.read() if new_image else user[7]

                update_profile(user[0], new_age, new_weight, new_height, new_gender, profile_blob)

                # refresh user safely
                updated_user = get_user_by_id(user[0])
                if updated_user:
                    st.session_state.user_data = updated_user

                st.success("Profile Updated!")
                st.session_state.edit_mode = False
                st.rerun()

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_data = None
            st.session_state.edit_mode = False
            st.rerun()

# =========================
# MAIN APP
# =========================
st.title("₊˚⊹♡🍰เเอพพลิเคชั่นคำนวนโภชนาการสารอาหาร🍓♡⊹˚₊")

@st.cache_resource
def load_model():
    return joblib.load("calorie_model.pkl")

model = load_model()

st.subheader("ระบุสารอาหาร (ไม่เกิน 100g)")

# ====== FEATURES ที่โมเดลใช้จริง ======
FEATURES = ["protein", "fat", "carb", "fiber"]

for key in FEATURES:
    if key not in st.session_state:
        st.session_state[key] = 0.0

def validate_input(changed_key):
    total = (
        st.session_state.protein +
        st.session_state.fat +
        st.session_state.carb +
        st.session_state.fiber
    )
    if total > 100:
        excess = total - 100
        new_value = st.session_state[changed_key] - excess
        st.session_state[changed_key] = max(0.0, round(new_value, 4))
        st.warning("⚠️ Total macronutrients cannot exceed 100g!")

protein = st.slider("Protein", 0.0, 100.0, key="protein", step=0.1,
                    on_change=validate_input, args=("protein",))
fat = st.slider("Fat", 0.0, 100.0, key="fat", step=0.1,
                on_change=validate_input, args=("fat",))
carb = st.slider("Carbs", 0.0, 100.0, key="carb", step=0.1,
                 on_change=validate_input, args=("carb",))
fiber = st.slider("Fiber", 0.0, 100.0, key="fiber", step=0.1,
                  on_change=validate_input, args=("fiber",))


total_macro = protein + fat + carb + fiber
st.progress(total_macro / 100)

if st.button("คำนวนแคลอรี่ᕙ(  •̀ ᗜ •́  )ᕗ"):

    total_grams = total_macro  # ไม่รวม sodium เพราะเป็น mg

    if total_grams == 0:
        st.warning("ไม่มีสารอาหาร จึงไม่มีแคลอรี่ 🍓")
    else:
        # 🔥 ส่งเข้า model แค่ 4 features ตามที่ train ไว้
        input_data = np.array([[protein, fat, carb, fiber]])
        
        # เช็คความถูกต้องเพิ่มความปลอดภัย
        if input_data.shape[1] != model.n_features_in_:
            st.error(f"Model expects {model.n_features_in_} features")
        else:
            prediction = model.predict(input_data)[0]
            prediction = max(0, prediction)

            st.success(f"{prediction:.2f} แคลอรี่ ต่อ {total_grams:.2f} กรัม")

# =========================
# BMR SECTION (LEFT BOTTOM)
# =========================

st.markdown("---")
col_left, col_center = st.columns([1,2])

# ===== กรณียังไม่ Login =====
if not st.session_state.logged_in or not st.session_state.user_data:

    with col_left:
        st.subheader("📊 BMR Calculator")
        st.warning("กรุณาสมัครสมาชิกหรือเข้าสู่ระบบเพื่อใช้งาน")

# ===== กรณี Login แล้ว =====
else:

    with col_left:
        st.subheader("📊 BMR Calculator")

        user = st.session_state.user_data
        age = user[3]
        weight = user[4]
        height = user[5]
        gender = user[6]

        if gender == "Male":
            bmr_main = 10*weight + 6.25*height - 5*age + 5
        else:
            bmr_main = 10*weight + 6.25*height - 5*age - 161

        st.info(f"BMR ของคุณคือ {bmr_main:.0f} kcal/day")

    with col_center:
        st.subheader("🏃‍♂️ โปรแกรมคำนวณลดน้ำหนัก")

        # (ใส่โค้ดโปรแกรมลดน้ำหนักของคุณตรงนี้ต่อได้เลย)


    # -------- CENTER --------
    with col_center:

        st.subheader("🏃‍♂️ โปรแกรมคำนวณลดน้ำหนัก")

        target_weight = st.number_input(
            "น้ำหนักเป้าหมาย (kg)",
            30.0, 200.0,
            value=weight-5
        )

        days_plan = st.number_input(
            "จำนวนวันเป้าหมาย",
            30, 365, 60
        )

        activity = st.selectbox(
            "ระดับกิจกรรมประจำวัน",
            [
                "นั่งอยู่กับที่",
                "เบา 1-3 วัน/สัปดาห์",
                "ปานกลาง 3-5 วัน/สัปดาห์",
                "หนัก 6-7 วัน/สัปดาห์",
                "หนักมาก"
            ]
        )

        sport = st.selectbox(
            "เลือกชนิดกีฬา",
            ["เดินเร็ว", "วิ่ง", "ปั่นจักรยาน", "ว่ายน้ำ", "เวทเทรนนิ่ง"]
        )

        duration = st.slider("ออกกำลังกายกี่นาที/วัน", 10, 180, 45)
        days_per_week = st.slider("ออกกี่วัน/สัปดาห์", 1, 7, 4)

        act_map = {
            "นั่งอยู่กับที่": 1.2,
            "เบา 1-3 วัน/สัปดาห์": 1.375,
            "ปานกลาง 3-5 วัน/สัปดาห์": 1.55,
            "หนัก 6-7 วัน/สัปดาห์": 1.725,
            "หนักมาก": 1.9
        }

        met_values = {
            "เดินเร็ว": 4.3,
            "วิ่ง": 8.0,
            "ปั่นจักรยาน": 7.5,
            "ว่ายน้ำ": 6.0,
            "เวทเทรนนิ่ง": 5.0
        }

        if st.button("คำนวณแผนลดน้ำหนัก", use_container_width=True):

            TDEE = bmr_main * act_map[activity]

            MET = met_values[sport]
            calories_per_min = (MET * 3.5 * weight) / 200
            exercise_calories = calories_per_min * duration
            weekly_exercise = exercise_calories * days_per_week
            avg_daily_exercise = weekly_exercise / 7

            total_daily_burn = TDEE + avg_daily_exercise

            weight_loss = weight - target_weight

            if weight_loss <= 0:
                st.warning("น้ำหนักเป้าหมายต้องน้อยกว่าน้ำหนักปัจจุบัน")
            else:
                total_deficit = weight_loss * 7700
                daily_deficit_needed = total_deficit / days_plan
                recommended_calories = total_daily_burn - daily_deficit_needed

                st.write(f"**BMR:** {bmr_main:.0f} kcal")
                st.write(f"**TDEE:** {TDEE:.0f} kcal")
                st.write(f"**เผาผลาญจากกีฬาเฉลี่ย:** {avg_daily_exercise:.0f} kcal/วัน")
                st.success(f"เผาผลาญรวมต่อวัน: {total_daily_burn:.0f} kcal")

                st.warning(f"ต้องขาดดุล ~ {daily_deficit_needed:.0f} kcal/วัน")
                st.subheader(f"🔥 ควรบริโภค ~ {recommended_calories:.0f} kcal/วัน")




# =========================
# SIMPLE NOTEPAD (WORKING VERSION)
# =========================

st.markdown("---")
st.subheader("📝 Notepad")

if "note_text" not in st.session_state:
    st.session_state.note_text = ""

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

col1, col2, col3 = st.columns(3)

# ===== ล้าง =====
with col1:
    if st.button("ล้าง", use_container_width=True):
        st.session_state.note_text = ""
        st.rerun()

# ===== โหลดไฟล์ =====
with col2:
    uploaded_txt = st.file_uploader(
        "โหลด",
        type=["txt"],
        key=f"upload_{st.session_state.uploader_key}",
        label_visibility="collapsed"
    )

    if uploaded_txt is not None:
        st.session_state.note_text = uploaded_txt.read().decode("utf-8")
        st.session_state.uploader_key += 1  # รีเซ็ต uploader
        st.rerun()

# ===== บันทึก =====
with col3:
    st.download_button(
        label="บันทึก",
        data=st.session_state.note_text,
        file_name="note.txt",
        mime="text/plain",
        use_container_width=True
    )

# ===== Text Area =====
st.text_area(
    "เขียนบันทึกของคุณที่นี่...",
    key="note_text",
    height=250
)



