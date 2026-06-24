import sqlite3
from config import Config

def get_db():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # --- job_posts ---
    # Core table: one row per scraped job listing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_posts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT NOT NULL,
            company         TEXT,
            location        TEXT,
            job_type        TEXT,           -- full-time, contract, internship, etc.
            experience_min  INTEGER,        -- min years required (parsed)
            experience_max  INTEGER,        -- max years required (parsed)
            raw_experience  TEXT,           -- original text e.g. "2-5 years"
            description     TEXT,
            source_url      TEXT,
            source_site     TEXT,           -- e.g. "LinkedIn", "Naukri", "Indeed"
            date_posted     TEXT,
            date_scraped    TEXT DEFAULT (datetime('now')),
            is_remote       INTEGER DEFAULT 0,  -- 0/1 boolean
            salary_raw      TEXT            -- raw salary string if present
        )
    """)

    # --- skills_extracted ---
    # Normalised skill tags linked to a job post
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills_extracted (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id      INTEGER NOT NULL,
            skill       TEXT NOT NULL,
            skill_type  TEXT,   -- 'language', 'framework', 'tool', 'soft', etc.
            FOREIGN KEY (job_id) REFERENCES job_posts(id) ON DELETE CASCADE
        )
    """)

    # --- user_stories ---
    # Community-submitted ATS / hiring experience stories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_stories (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            submitter_name  TEXT,           -- optional, can be anonymous
            role_applied    TEXT NOT NULL,
            company_name    TEXT,
            yoe             INTEGER,        -- submitter's years of experience
            outcome         TEXT,           -- 'rejected', 'ghosted', 'interviewed', 'hired'
            story           TEXT NOT NULL,
            story_type      TEXT,           -- 'experience_inflation', 'title_mismatch', 'ats_reject', 'other'
            submitted_at    TEXT DEFAULT (datetime('now')),
            is_approved     INTEGER DEFAULT 0   -- moderation flag
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialised — tables: job_posts, skills_extracted, user_stories")


if __name__ == "__main__":
    import os
    os.makedirs(os.path.dirname(Config.DATABASE), exist_ok=True)
    init_db()
