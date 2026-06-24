"""
seed.py — loads sample job data so you can test without the scraper.
Run once: python seed.py
"""
from models import get_db, init_db
from scraper import parse_experience, extract_skills
import os

SAMPLE_JOBS = [
    {
        "title": "Junior Python Developer",
        "company": "DataStack Inc.",
        "location": "Remote (India)",
        "job_type": "full-time",
        "description": "We are looking for a Python developer with 2-4 years of experience. Must know Django, Flask, PostgreSQL, Docker, and Git. Strong communication skills required. Experience with AWS is a plus.",
        "source_url": "https://example.com/job/1",
        "source_site": "seed",
        "date_posted": "2026-06-20",
        "is_remote": 1,
        "salary_raw": "6-10 LPA",
    },
    {
        "title": "Backend Engineer",
        "company": "CloudNine SaaS",
        "location": "Bangalore / Remote",
        "job_type": "full-time",
        "description": "Minimum 3 years of experience required. Stack: Node.js, TypeScript, MongoDB, Redis, Kubernetes. Agile team using Scrum. Problem solving and teamwork are essential.",
        "source_url": "https://example.com/job/2",
        "source_site": "seed",
        "date_posted": "2026-06-21",
        "is_remote": 1,
        "salary_raw": "12-18 LPA",
    },
    {
        "title": "Data Analyst",
        "company": "FinSight Analytics",
        "location": "Remote",
        "job_type": "full-time",
        "description": "5 years of experience in data analytics. Python, SQL, pandas, and Tableau required. Experience with Kafka and Elasticsearch is a plus. Must have strong communication.",
        "source_url": "https://example.com/job/3",
        "source_site": "seed",
        "date_posted": "2026-06-18",
        "is_remote": 1,
        "salary_raw": "",
    },
    {
        "title": "Frontend Developer",
        "company": "Pixel Labs",
        "location": "Mumbai / Remote",
        "job_type": "contract",
        "description": "2-3 years experience with React, Vue, or Angular. TypeScript required. Git, Linux basics needed. Good communication and agile mindset expected.",
        "source_url": "https://example.com/job/4",
        "source_site": "seed",
        "date_posted": "2026-06-22",
        "is_remote": 1,
        "salary_raw": "50-80k/month",
    },
    {
        "title": "DevOps Engineer",
        "company": "InfraCore",
        "location": "Pune / Remote",
        "job_type": "full-time",
        "description": "At least 4 years experience. Must know Docker, Kubernetes, AWS, Terraform, Jenkins, and GitHub Actions. Linux administration required. Elasticsearch monitoring experience a plus.",
        "source_url": "https://example.com/job/5",
        "source_site": "seed",
        "date_posted": "2026-06-19",
        "is_remote": 1,
        "salary_raw": "15-22 LPA",
    },
    {
        "title": "Full Stack Developer",
        "company": "StartupXYZ",
        "location": "Remote",
        "job_type": "full-time",
        "description": "0-2 years experience, freshers welcome! React, Python, Flask, PostgreSQL, Git. We value problem solving over years of experience. Agile team, fast learning environment.",
        "source_url": "https://example.com/job/6",
        "source_site": "seed",
        "date_posted": "2026-06-23",
        "is_remote": 1,
        "salary_raw": "4-7 LPA",
    },
]

def run_seed():
    os.makedirs("data", exist_ok=True)
    init_db()
    db = get_db()
    inserted = 0
    for job in SAMPLE_JOBS:
        exists = db.execute("SELECT id FROM job_posts WHERE source_url=?", (job["source_url"],)).fetchone()
        if exists:
            continue
        exp_min, exp_max, exp_raw = parse_experience(job["description"])
        cur = db.execute("""
            INSERT INTO job_posts
              (title, company, location, job_type,
               experience_min, experience_max, raw_experience,
               description, source_url, source_site,
               date_posted, is_remote, salary_raw)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            job["title"], job["company"], job["location"], job["job_type"],
            exp_min, exp_max, exp_raw,
            job["description"], job["source_url"], job["source_site"],
            job["date_posted"], job["is_remote"], job["salary_raw"],
        ))
        job_id = cur.lastrowid
        for skill, stype in extract_skills(job["description"]):
            db.execute(
                "INSERT INTO skills_extracted (job_id, skill, skill_type) VALUES (?,?,?)",
                (job_id, skill, stype)
            )
        inserted += 1
    db.commit()
    db.close()
    print(f"✅ Seeded {inserted} jobs")

if __name__ == "__main__":
    run_seed()