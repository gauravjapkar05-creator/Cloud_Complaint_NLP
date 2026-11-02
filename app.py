import hmac
from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    register_student,
    login_student,
    add_complaint,
    get_all_complaints,
    get_student_complaints,
    update_complaint_status,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Cloud-Based College Complaint Classification",
    page_icon="🎓",
    layout="wide"
)


BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "models" / "complaint_classifier.pkl"


# =========================================================
# ADMIN LOGIN
# =========================================================

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.main-title {
    text-align: center;
    font-size: 32px;
    font-weight: bold;
    color: #7b1746;
    margin-bottom: 5px;
}

.college-title {
    text-align: center;
    font-size: 22px;
    font-weight: bold;
    color: #182848;
}

.subtitle {
    text-align: center;
    font-size: 16px;
    color: #555;
    margin-bottom: 25px;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #dddddd;
    margin-bottom: 15px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="college-title">
    SHRI CHHATRAPATI SHIVAJI MAHARAJ COLLEGE OF ENGINEERING
    </div>

    <div class="college-title">
    NEPTI, AHILYANAGAR
    </div>

    <div class="main-title">
    ☁️ Cloud-Based College Complaint Classification System Using NLP
    </div>

    <div class="subtitle">
    NLP • Machine Learning • Streamlit • Cloud Computing
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# LOAD MODEL
# =========================================================

@st.cache_resource
def load_model():

    if not MODEL_PATH.exists():

        st.error(
            "Model file not found. "
            "Please run: python train_model.py"
        )

        st.stop()

    return joblib.load(MODEL_PATH)


model = load_model()


# =========================================================
# SESSION STATE
# =========================================================

if "student_logged_in" not in st.session_state:

    st.session_state.student_logged_in = False


if "student_data" not in st.session_state:

    st.session_state.student_data = None


if "admin_logged_in" not in st.session_state:

    st.session_state.admin_logged_in = False


# =========================================================
# CATEGORY → DEPARTMENT
# =========================================================

department_map = {

    "Transport":
        "Transport Department",

    "Hostel":
        "Hostel Department",

    "Library":
        "Library Department",

    "Academic":
        "Academic Department",

    "Canteen":
        "Canteen Department",

    "Infrastructure":
        "Infrastructure Department",

    "Administration":
        "Administration Department",

}


# =========================================================
# SENTIMENT
# =========================================================

def detect_sentiment(text):

    text = text.lower()

    negative_words = [
        "bad",
        "poor",
        "worst",
        "problem",
        "issue",
        "broken",
        "dirty",
        "late",
        "delay",
        "unsafe",
        "not working",
        "unavailable"
    ]

    positive_words = [
        "good",
        "great",
        "excellent",
        "happy",
        "helpful",
        "satisfied",
        "thanks",
        "thank you"
    ]

    negative_count = sum(
        word in text
        for word in negative_words
    )

    positive_count = sum(
        word in text
        for word in positive_words
    )

    if negative_count > positive_count:

        return "Negative"

    if positive_count > negative_count:

        return "Positive"

    return "Neutral"


# =========================================================
# PRIORITY
# =========================================================

def detect_priority(text):

    text = text.lower()

    high_words = [
        "urgent",
        "emergency",
        "danger",
        "unsafe",
        "fire",
        "accident",
        "harassment",
        "ragging"
    ]

    medium_words = [
        "problem",
        "issue",
        "delay",
        "broken",
        "not working",
        "unavailable"
    ]

    if any(
        word in text
        for word in high_words
    ):

        return "High"

    if any(
        word in text
        for word in medium_words
    ):

        return "Medium"

    return "Low"


# =========================================================
# LOGIN PAGE
# =========================================================

if (
    not st.session_state.student_logged_in
    and
    not st.session_state.admin_logged_in
):

    login_type = st.radio(
        "Select User Type",
        [
            "👨‍🎓 Student",
            "🔐 Admin"
        ],
        horizontal=True
    )


    # =====================================================
    # STUDENT
    # =====================================================

    if login_type == "👨‍🎓 Student":

        login_tab, register_tab = st.tabs(
            [
                "Student Login",
                "Student Registration"
            ]
        )


        # -------------------------------------------------
        # LOGIN
        # -------------------------------------------------

        with login_tab:

            st.subheader(
                "👨‍🎓 Student Login"
            )

            student_name = st.text_input(
                "Student Name"
            )

            password = st.text_input(
                "Password",
                type="password"
            )


            if st.button(
                "Login",
                type="primary"
            ):

                if not student_name or not password:

                    st.warning(
                        "Please enter name and password."
                    )

                else:

                    student = login_student(
                        student_name,
                        password
                    )

                    if student:

                        st.session_state.student_logged_in = True

                        st.session_state.student_data = student

                        st.rerun()

                    else:

                        st.error(
                            "Invalid student name or password."
                        )


        # -------------------------------------------------
        # REGISTRATION
        # -------------------------------------------------

        with register_tab:

            st.subheader(
                "📝 Student Registration"
            )

            name = st.text_input(
                "Full Name",
                key="register_name"
            )

            email = st.text_input(
                "Email",
                key="register_email"
            )

            new_password = st.text_input(
                "Create Password",
                type="password",
                key="register_password"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                key="confirm_password"
            )


            if st.button(
                "Create Account",
                type="primary"
            ):

                if not name or not new_password:

                    st.warning(
                        "Name and password are required."
                    )

                elif new_password != confirm_password:

                    st.error(
                        "Passwords do not match."
                    )

                else:

                    success, message = register_student(
                        name,
                        email,
                        new_password
                    )

                    if success:

                        st.success(
                            message
                        )

                    else:

                        st.error(
                            message
                        )


    # =====================================================
    # ADMIN
    # =====================================================

    else:

        st.subheader(
            "🔐 Administrator Login"
        )

        username = st.text_input(
            "Admin Username"
        )

        password = st.text_input(
            "Admin Password",
            type="password"
        )


        if st.button(
            "Admin Login",
            type="primary"
        ):

            if (
                hmac.compare_digest(
                    username,
                    ADMIN_USERNAME
                )
                and
                hmac.compare_digest(
                    password,
                    ADMIN_PASSWORD
                )
            ):

                st.session_state.admin_logged_in = True

                st.rerun()

            else:

                st.error(
                    "Invalid admin credentials."
                )


# =========================================================
# STUDENT PANEL
# =========================================================

elif st.session_state.student_logged_in:

    student_name = st.session_state.student_data[0]


    # -----------------------------------------------------
    # SIDEBAR
    # -----------------------------------------------------

    st.sidebar.success(
        f"Welcome, {student_name}"
    )

    student_page = st.sidebar.radio(
        "Student Menu",
        [
            "📝 Submit Complaint",
            "📍 Track Complaints"
        ]
    )


    if st.sidebar.button(
        "Logout"
    ):

        st.session_state.student_logged_in = False

        st.session_state.student_data = None

        st.rerun()


    # =====================================================
    # SUBMIT COMPLAINT
    # =====================================================

    if student_page == "📝 Submit Complaint":

        st.header(
            "📝 Submit College Complaint"
        )

        complaint = st.text_area(
            "Describe your complaint",
            height=180,
            placeholder=(
                "Example: The college bus is always late."
            )
        )


        if st.button(
            "🤖 Analyze & Submit Complaint",
            type="primary"
        ):

            if not complaint.strip():

                st.warning(
                    "Please enter a complaint."
                )

            else:

                text = complaint.strip()


                # -----------------------------------------
                # NLP CLASSIFICATION
                # -----------------------------------------

                category = model.predict(
                    [text]
                )[0]


                # -----------------------------------------
                # SENTIMENT
                # -----------------------------------------

                sentiment = detect_sentiment(
                    text
                )


                # -----------------------------------------
                # PRIORITY
                # -----------------------------------------

                priority = detect_priority(
                    text
                )


                # -----------------------------------------
                # DEPARTMENT
                # -----------------------------------------

                department = department_map.get(
                    category,
                    "General Department"
                )


                # -----------------------------------------
                # CONFIDENCE
                # -----------------------------------------

                confidence = 0.0

                if hasattr(
                    model,
                    "decision_function"
                ):

                    scores = model.decision_function(
                        [text]
                    )

                    if scores.ndim == 1:

                        score = abs(
                            float(scores[0])
                        )

                    else:

                        score = abs(
                            float(scores.max())
                        )

                    confidence = min(
                        score * 25,
                        99.0
                    )


                # -----------------------------------------
                # SAVE COMPLAINT
                # -----------------------------------------

                complaint_id = add_complaint(

                    student_name=student_name,

                    complaint=text,

                    category=category,

                    sentiment=sentiment,

                    priority=priority,

                    department=department,

                    confidence=confidence

                )


                # -----------------------------------------
                # RESULT
                # -----------------------------------------

                st.success(
                    "Complaint submitted successfully!"
                )


                st.subheader(
                    f"Complaint ID: CMP-{complaint_id:04d}"
                )


                col1, col2, col3, col4 = st.columns(4)


                col1.metric(
                    "Category",
                    category
                )

                col2.metric(
                    "Sentiment",
                    sentiment
                )

                col3.metric(
                    "Priority",
                    priority
                )

                col4.metric(
                    "Confidence",
                    f"{confidence:.1f}%"
                )


                st.info(
                    f"Assigned Department: {department}"
                )


    # =====================================================
    # TRACK COMPLAINTS
    # =====================================================

    else:

        st.header(
            "📍 My Complaint Tracking"
        )


        complaints = get_student_complaints(
            student_name
        )


        if not complaints:

            st.info(
                "You have not submitted any complaints yet."
            )

        else:

            for row in complaints:

                (
                    complaint_id,
                    complaint,
                    category,
                    sentiment,
                    priority,
                    department,
                    confidence,
                    status,
                    duplicate_of,
                    similarity,
                    remarks,
                    created_at
                ) = row


                with st.container(
                    border=True
                ):

                    st.subheader(
                        f"CMP-{complaint_id:04d}"
                    )

                    st.write(
                        f"**Complaint:** {complaint}"
                    )

                    col1, col2, col3 = st.columns(3)

                    col1.write(
                        f"**Category:** {category}"
                    )

                    col2.write(
                        f"**Priority:** {priority}"
                    )

                    col3.write(
                        f"**Department:** {department}"
                    )

                    st.write(
                        f"**Status:** `{status}`"
                    )

                    st.caption(
                        f"Submitted: {created_at}"
                    )

                    if remarks:

                        st.info(
                            f"Admin Response: {remarks}"
                        )


# =========================================================
# ADMIN PANEL
# =========================================================

elif st.session_state.admin_logged_in:

    st.sidebar.success(
        "Administrator Logged In"
    )


    admin_page = st.sidebar.radio(
        "Admin Menu",
        [
            "📊 Dashboard",
            "🔄 Manage Complaints"
        ]
    )


    if st.sidebar.button(
        "Admin Logout"
    ):

        st.session_state.admin_logged_in = False

        st.rerun()


    records = get_all_complaints()


    columns = [
        "ID",
        "Student Name",
        "Complaint",
        "Category",
        "Sentiment",
        "Priority",
        "Department",
        "Confidence",
        "Status",
        "Duplicate Of",
        "Similarity",
        "Resolution Remarks",
        "Created At"
    ]


    df = pd.DataFrame(
        records,
        columns=columns
    )


    # =====================================================
    # DASHBOARD
    # =====================================================

    if admin_page == "📊 Dashboard":

        st.header(
            "📊 Administrator Dashboard"
        )


        if df.empty:

            st.info(
                "No complaints submitted yet."
            )

        else:

            total = len(df)

            pending = int(
                (df["Status"] == "Pending").sum()
            )

            in_progress = int(
                (df["Status"] == "In Progress").sum()
            )

            resolved = int(
                (df["Status"] == "Resolved").sum()
            )


            col1, col2, col3, col4 = st.columns(4)


            col1.metric(
                "Total Complaints",
                total
            )

            col2.metric(
                "Pending",
                pending
            )

            col3.metric(
                "In Progress",
                in_progress
            )

            col4.metric(
                "Resolved",
                resolved
            )


            # ---------------------------------------------
            # CATEGORY CHART
            # ---------------------------------------------

            category_counts = (
                df["Category"]
                .value_counts()
                .reset_index()
            )

            category_counts.columns = [
                "Category",
                "Count"
            ]


            fig1 = px.bar(
                category_counts,
                x="Category",
                y="Count",
                title="Complaints by Category"
            )


            st.plotly_chart(
                fig1,
                use_container_width=True
            )


            # ---------------------------------------------
            # STATUS CHART
            # ---------------------------------------------

            status_counts = (
                df["Status"]
                .value_counts()
                .reset_index()
            )

            status_counts.columns = [
                "Status",
                "Count"
            ]


            fig2 = px.pie(
                status_counts,
                names="Status",
                values="Count",
                title="Complaint Status"
            )


            st.plotly_chart(
                fig2,
                use_container_width=True
            )


            st.subheader(
                "All Complaints"
            )


            display_df = df.copy()


            display_df["Complaint ID"] = (
                display_df["ID"]
                .apply(
                    lambda x:
                    f"CMP-{int(x):04d}"
                )
            )


            st.dataframe(
                display_df[
                    [
                        "Complaint ID",
                        "Student Name",
                        "Complaint",
                        "Category",
                        "Priority",
                        "Department",
                        "Status",
                        "Created At"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )


    # =====================================================
    # MANAGE COMPLAINTS
    # =====================================================

    else:

        st.header(
            "🔄 Manage Complaints"
        )


        if df.empty:

            st.info(
                "No complaints available."
            )

        else:

            selected_id = st.selectbox(
                "Select Complaint",
                df["ID"].tolist(),
                format_func=lambda x:
                f"CMP-{int(x):04d}"
            )


            selected = df[
                df["ID"] == selected_id
            ].iloc[0]


            st.subheader(
                f"CMP-{int(selected_id):04d}"
            )


            st.write(
                f"**Student:** {selected['Student Name']}"
            )

            st.write(
                f"**Complaint:** {selected['Complaint']}"
            )

            st.write(
                f"**Category:** {selected['Category']}"
            )

            st.write(
                f"**Department:** {selected['Department']}"
            )

            st.write(
                f"**Priority:** {selected['Priority']}"
            )


            statuses = [
                "Pending",
                "In Progress",
                "Resolved"
            ]


            current_status = selected["Status"]


            status_index = (
                statuses.index(current_status)
                if current_status in statuses
                else 0
            )


            new_status = st.selectbox(
                "Update Status",
                statuses,
                index=status_index
            )


            existing_remarks = selected[
                "Resolution Remarks"
            ]


            if pd.isna(existing_remarks):

                existing_remarks = ""


            remarks = st.text_area(
                "Resolution Remarks",
                value=str(existing_remarks),
                height=120
            )


            if st.button(
                "💾 Save Update",
                type="primary"
            ):

                success = update_complaint_status(
                    selected_id,
                    new_status,
                    remarks
                )


                if success:

                    st.success(
                        "Complaint updated successfully!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Unable to update complaint."
                    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "Cloud-Based College Complaint Classification System "
    "| Python • NLP • Machine Learning • Streamlit"
)