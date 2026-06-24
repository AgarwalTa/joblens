"""
scraper.py — Phase 2
Fetches job listings from RemoteOK (JSON API) and Remotive (JSON API).
Parses experience requirements from description text using regex.
Extracts skills from a curated keyword list.
Stores results in job_posts + skills_extracted tables.
"""

import re
import json
import time
import sqlite3
import urllib.request
from datetime import datetime
from models import get_db

# ── Skill keyword list ─────────────────────────────────────────────────────────

SKILLS = {
    "language": ["python", "javascript", "typescript", "java", "go", "rust",
                 "c++", "c#", "ruby", "php", "swift", "kotlin", "scala", "r"],
    "framework": ["react", "vue", "angular", "django", "flask", "fastapi",
                  "express", "spring", "rails", "next.js", "nuxt", "svelte"],
    "tool":      ["docker", "kubernetes", "git", "linux", "aws", "gcp", "azure",
                  "terraform", "jenkins", "github actions", "postgres", "mysql",
                  "mongodb", "redis", "kafka", "elasticsearch", "sqlite"],
    "soft":      ["communication", "leadership", "problem solving", "teamwork",
                  "agile", "scrum", "kanban"],
}

SKILL_MAP = {}
for stype, slist in SKILLS.items():
    for s in slist:
        SKILL_MAP[s.lower()] = stype


# ── Experience parser ──────────────────────────────────────────────────────────

def parse_experience(text):
    if not text:
        return None, None, None
    text_lower = text.lower()

    m = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)\s*(?:years?|yrs?)', text_lower)
    if m:
        return int(m.group(1)), int(m.group(2)), m.group(0)

    m = re.search(r'(?:at least|minimum|min\.?|(\d+)\+)\s*(\d+)?\s*(?:years?|yrs?)', text_lower)
    if m:
        yr = int(m.group(1) or m.group(2) or 0)
        return yr, None, m.group(0)

    m = re.search(r'(\d+)\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)', text_lower)
    if m:
        yr = int(m.group(1))
        return yr, yr, m.group(0)

    return None, None, None


# ── Skill extractor ────────────────────────────────────────────────────────────

def extract_skills(text):
    if not text:
        return []
    text_lower = text.lower()
    found = []
    for skill, stype in SKILL_MAP.items():
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.append((skill, stype))
    return found


# ── Source: RemoteOK ───────────────────────────────────────────────────────────

def fetch_remoteok(limit=50):
    url = "https://remoteok.com/api"
    req = urllib.request.Request(url, headers={"User-Agent": "JobLens/1.0 (portfolio project)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    jobs = []
    for item in data[1:limit+1]:
        if not isinstance(item, dict):
            continue
        jobs.append({
            "title":       item.get("position", ""),
            "company":     item.get("company", ""),
            "location":    item.get("location", "Worldwide"),
            "job_type":    "full-time",
            "description": item.get("description", "") or str(item.get("tags", "")),
            "source_url":  item.get("url", ""),
            "source_site": "RemoteOK",
            "date_posted": item.get("date", ""),
            "is_remote":   1,
            "salary_raw":  item.get("salary", ""),
        })
    return jobs


# ── Source: Remotive ───────────────────────────────────────────────────────────

def fetch_remotive(limit=50):
    url = "https://remotive.com/api/remote-jobs?limit=" + str(limit)
    req = urllib.request.Request(url, headers={"User-Agent": "JobLens/1.0 (portfolio project)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    jobs = []
    for item in data.get("jobs", []):
        jobs.append({
            "title":       item.get("title", ""),
            "company":     item.get("company_name", ""),
            "location":    item.get("candidate_required_location", "Worldwide"),
            "job_type":    item.get("job_type", "full-time"),
            "description": item.get("description", ""),
            "source_url":  item.get("url", ""),
            "source_site": "Remotive",
            "date_posted": item.get("publication_date", "")[:10] if item.get("publication_date") else "",
            "is_remote":   1,
            "salary_raw":  item.get("salary", ""),
        })
    return jobs


# ── DB writer ──────────────────────────────────────────────────────────────────

def save_jobs(jobs):
    db = get_db()
    inserted = 0
    skipped = 0
    for job in jobs:
        exists = db.execute(
            "SELECT id FROM job_posts WHERE source_url = ?", (job["source_url"],)
        ).fetchone()
        if exists:
            skipped += 1
            continue
        exp_min, exp_max, exp_raw = parse_experience(job["description"])
        cursor = db.execute("""
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
        job_id = cursor.lastrowid
        for skill, stype in extract_skills(job["description"]):
            db.execute(
                "INSERT INTO skills_extracted (job_id, skill, skill_type) VALUES (?,?,?)",
                (job_id, skill, stype)
            )
        inserted += 1
    db.commit()
    db.close()
    return inserted, skipped


# ── Main ───────────────────────────────────────────────────────────────────────

def run_scraper():
    print(f"\n{'='*50}")
    print(f"JobLens Scraper — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")
    total_inserted = 0
    total_skipped = 0
    for name, fetcher in [("RemoteOK", fetch_remoteok), ("Remotive", fetch_remotive)]:
        print(f"\n[{name}] Fetching...")
        try:
            jobs = fetcher(limit=50)
            print(f"[{name}] Got {len(jobs)} listings")
            ins, skp = save_jobs(jobs)
            print(f"[{name}] Saved: {ins} new | Skipped (duplicate): {skp}")
            total_inserted += ins
            total_skipped += skp
        except Exception as e:
            print(f"[{name}] ERROR: {e}")
        time.sleep(1)
    print(f"\n{'='*50}")
    print(f"Done. Total new: {total_inserted} | Duplicates skipped: {total_skipped}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    run_scraper()