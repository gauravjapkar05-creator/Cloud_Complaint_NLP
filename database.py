
import os
import streamlit as st
import psycopg2
import bcrypt


def get_connection():
    try:
        database_url = st.secrets.get("DATABASE_URL", "")
    except Exception:
        database_url = os.getenv("DATABASE_URL", "")

    if not database_url:
        raise Exception("DATABASE_URL is missing in Streamlit Secrets.")

    return psycopg2.connect(
        database_url,
        sslmode="require",
        connect_timeout=15
    )


def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id BIGSERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id BIGSERIAL PRIMARY KEY,
                student_id BIGINT REFERENCES students(id) ON DELETE CASCADE,
                complaint TEXT NOT NULL,
                category VARCHAR(100),
                sentiment VARCHAR(50),
                priority VARCHAR(50),
                department VARCHAR(100),
                status VARCHAR(50) DEFAULT 'Pending',
                remarks TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add columns required by the current app.
        cur.execute("""
            ALTER TABLE complaints
            ADD COLUMN IF NOT EXISTS student_name VARCHAR(100)
        """)
        cur.execute("""
            ALTER TABLE complaints
            ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION DEFAULT 0
        """)
        cur.execute("""
            ALTER TABLE complaints
            ADD COLUMN IF NOT EXISTS duplicate_of BIGINT
        """)
        cur.execute("""
            ALTER TABLE complaints
            ADD COLUMN IF NOT EXISTS similarity DOUBLE PRECISION DEFAULT 0
        """)

        # Keep older complaint records compatible.
        cur.execute("""
            UPDATE complaints c
            SET student_name = s.name
            FROM students s
            WHERE c.student_id = s.id
              AND (c.student_name IS NULL OR c.student_name = '')
        """)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


def register_student(name, email, password):
    name = name.strip()
    email = email.strip().lower()

    if not name or not email or not password:
        return False, "All fields are required."

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT id FROM students WHERE LOWER(email) = %s",
            (email,)
        )

        if cur.fetchone():
            return False, "Email already registered. Please log in."

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cur.execute("""
            INSERT INTO students (name, email, password)
            VALUES (%s, %s, %s)
        """, (name, email, hashed_password))

        conn.commit()
        return True, "Registration successful!"

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


def login_student(name, password):
    name = name.strip()

    if not name or not password:
        return None

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT id, name, email, password
            FROM students
            WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s))
            ORDER BY id DESC
            LIMIT 1
        """, (name,))

        student = cur.fetchone()

        if not student:
            return None

        stored_password = student[3]

        if isinstance(stored_password, str):
            stored_password = stored_password.encode("utf-8")

        if bcrypt.checkpw(
            password.encode("utf-8"),
            stored_password
        ):
            return (student[1], student[0], student[2])

        return None

    finally:
        cur.close()
        conn.close()


def add_complaint(
    student_name,
    complaint,
    category,
    sentiment,
    priority,
    department,
    confidence=0,
    status="Pending",
    duplicate_of=None,
    similarity=0
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT id FROM students
            WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s))
            ORDER BY id DESC
            LIMIT 1
        """, (student_name,))

        student = cur.fetchone()

        if not student:
            raise Exception("Student account not found.")

        cur.execute("""
            INSERT INTO complaints (
                student_id, student_name, complaint,
                category, sentiment, priority, department,
                confidence, status, duplicate_of, similarity
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            student[0], student_name, complaint,
            category, sentiment, priority, department,
            confidence, status, duplicate_of, similarity
        ))

        complaint_id = cur.fetchone()[0]
        conn.commit()
        return complaint_id

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


def get_student_complaints(student_name):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                id, complaint, category, sentiment, priority,
                department, confidence, status, duplicate_of,
                similarity, remarks, created_at
            FROM complaints
            WHERE LOWER(TRIM(student_name)) = LOWER(TRIM(%s))
            ORDER BY created_at DESC
        """, (student_name,))

        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def get_all_complaints():
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                id, student_name, complaint, category,
                sentiment, priority, department, confidence,
                status, duplicate_of, similarity, remarks,
                created_at
            FROM complaints
            ORDER BY created_at DESC
        """)

        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def update_complaint_status(complaint_id, status, remarks):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE complaints
            SET status = %s, remarks = %s
            WHERE id = %s
        """, (status, remarks, complaint_id))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


# Create / migrate tables when the app starts.
create_tables()
