import os
import psycopg2
import bcrypt
import streamlit as st


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():
    """
    Connect to Supabase PostgreSQL database.
    """

    try:
        database_url = st.secrets["DATABASE_URL"]
    except Exception:
        database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise Exception(
            "DATABASE_URL not found. Please check .streamlit/secrets.toml"
        )

    return psycopg2.connect(database_url)


# ==========================================
# CREATE TABLES
# ==========================================

def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
            complaint TEXT NOT NULL,
            category VARCHAR(100),
            sentiment VARCHAR(50),
            priority VARCHAR(50),
            department VARCHAR(100),
            status VARCHAR(50) DEFAULT 'Pending',
            remarks TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()


# ==========================================
# STUDENT REGISTRATION
# ==========================================

def register_student(name, email, password):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute("""
            INSERT INTO students (name, email, password)
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (name, email, hashed_password))

        student_id = cursor.fetchone()[0]

        conn.commit()

        return True, student_id

    except psycopg2.errors.UniqueViolation:

        conn.rollback()

        return False, "Email already registered."

    except Exception as e:

        conn.rollback()

        return False, str(e)

    finally:

        cursor.close()
        conn.close()


# ==========================================
# STUDENT LOGIN
# ==========================================

def login_student(email, password):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT id, name, email, password
            FROM students
            WHERE email = %s;
        """, (email,))

        student = cursor.fetchone()

        if student is None:
            return None

        student_id, name, user_email, stored_password = student

        if bcrypt.checkpw(
            password.encode("utf-8"),
            stored_password.encode("utf-8")
        ):

            return {
                "id": student_id,
                "name": name,
                "email": user_email
            }

        return None

    finally:

        cursor.close()
        conn.close()


# ==========================================
# ADD COMPLAINT
# ==========================================

def add_complaint(
    student_id,
    complaint,
    category,
    sentiment,
    priority,
    department
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO complaints
            (
                student_id,
                complaint,
                category,
                sentiment,
                priority,
                department
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            student_id,
            complaint,
            category,
            sentiment,
            priority,
            department
        ))

        complaint_id = cursor.fetchone()[0]

        conn.commit()

        return complaint_id

    except Exception as e:

        conn.rollback()

        raise e

    finally:

        cursor.close()
        conn.close()


# ==========================================
# GET STUDENT COMPLAINTS
# ==========================================

def get_student_complaints(student_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            complaint,
            category,
            sentiment,
            priority,
            department,
            status,
            remarks,
            created_at
        FROM complaints
        WHERE student_id = %s
        ORDER BY created_at DESC;
    """, (student_id,))

    complaints = cursor.fetchall()

    cursor.close()
    conn.close()

    return complaints


# ==========================================
# GET ALL COMPLAINTS
# ==========================================

def get_all_complaints():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.id,
            s.name,
            s.email,
            c.complaint,
            c.category,
            c.sentiment,
            c.priority,
            c.department,
            c.status,
            c.remarks,
            c.created_at
        FROM complaints c
        JOIN students s
        ON c.student_id = s.id
        ORDER BY c.created_at DESC;
    """)

    complaints = cursor.fetchall()

    cursor.close()
    conn.close()

    return complaints


# ==========================================
# UPDATE COMPLAINT STATUS
# ==========================================

def update_complaint_status(
    complaint_id,
    status,
    remarks=""
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE complaints
            SET
                status = %s,
                remarks = %s
            WHERE id = %s;
        """, (
            status,
            remarks,
            complaint_id
        ))

        conn.commit()

        return True

    except Exception as e:

        conn.rollback()

        print("Error:", e)

        return False

    finally:

        cursor.close()
        conn.close()


# ==========================================
# INITIALIZE DATABASE
# ==========================================

try:
    create_tables()
except Exception as e:
    print("Database initialization error:", e)