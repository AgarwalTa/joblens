"""
analysis.py — Phase 4
All the number-crunching logic. Called by app.py routes.
Returns plain dicts/lists — no Flask dependency.
"""
from models import get_db


def experience_inflation_report():
    """
    For each job title keyword group, shows average min experience required.
    Flags roles where a 'junior'/'entry' title asks for 3+ years — that's inflation.
    """
    db = get_db()
    rows = db.execute("""
        SELECT title, experience_min, experience_max, company, source_site
        FROM job_posts
        WHERE experience_min IS NOT NULL
        ORDER BY experience_min DESC
    """).fetchall()
    db.close()

    results = []
    for r in rows:
        title_lower = r["title"].lower()
        is_junior = any(kw in title_lower for kw in
                        ["junior", "entry", "fresher", "associate", "jr", "trainee"])
        inflated = is_junior and r["experience_min"] >= 3

        results.append({
            "title":          r["title"],
            "company":        r["company"],
            "source_site":    r["source_site"],
            "exp_min":        r["experience_min"],
            "exp_max":        r["experience_max"],
            "is_junior_role": is_junior,
            "inflated":       inflated,
        })

    total       = len(results)
    n_inflated  = sum(1 for r in results if r["inflated"])
    n_junior    = sum(1 for r in results if r["is_junior_role"])

    return {
        "summary": {
            "total_jobs_with_exp":   total,
            "junior_roles":          n_junior,
            "inflated_junior_roles": n_inflated,
            "inflation_rate_pct":    round(n_inflated / n_junior * 100, 1) if n_junior else 0,
        },
        "jobs": results,
    }


def top_skills_report(limit=15):
    """
    Most demanded skills across all job posts, broken down by type.
    """
    db = get_db()
    rows = db.execute("""
        SELECT skill, skill_type, COUNT(*) as demand
        FROM skills_extracted
        GROUP BY skill
        ORDER BY demand DESC
        LIMIT ?
    """, (limit,)).fetchall()
    db.close()

    by_type = {}
    all_skills = []
    for r in rows:
        entry = {"skill": r["skill"], "skill_type": r["skill_type"], "demand": r["demand"]}
        all_skills.append(entry)
        by_type.setdefault(r["skill_type"], []).append(entry)

    return {"top_skills": all_skills, "by_type": by_type}


def experience_distribution():
    """
    Bucketed distribution of min experience requirements.
    Good for a bar chart: 0-1 yrs, 2-3 yrs, 4-5 yrs, 6+ yrs.
    """
    db = get_db()
    rows = db.execute("""
        SELECT experience_min FROM job_posts
        WHERE experience_min IS NOT NULL
    """).fetchall()
    db.close()

    buckets = {"0-1": 0, "2-3": 0, "4-5": 0, "6+": 0}
    for r in rows:
        yr = r["experience_min"]
        if yr <= 1:
            buckets["0-1"] += 1
        elif yr <= 3:
            buckets["2-3"] += 1
        elif yr <= 5:
            buckets["4-5"] += 1
        else:
            buckets["6+"] += 1

    return {"distribution": buckets}


def outcome_breakdown():
    """
    How user stories break down by outcome and story type.
    Powers the 'what actually happens' section of the dashboard.
    """
    db = get_db()

    by_outcome = db.execute("""
        SELECT outcome, COUNT(*) as count
        FROM user_stories
        GROUP BY outcome
        ORDER BY count DESC
    """).fetchall()

    by_type = db.execute("""
        SELECT story_type, COUNT(*) as count
        FROM user_stories
        GROUP BY story_type
        ORDER BY count DESC
    """).fetchall()

    avg_yoe = db.execute("""
        SELECT AVG(yoe) as avg_yoe FROM user_stories WHERE yoe IS NOT NULL
    """).fetchone()

    db.close()

    return {
        "by_outcome":  [dict(r) for r in by_outcome],
        "by_type":     [dict(r) for r in by_type],
        "avg_yoe_of_applicants": round(avg_yoe["avg_yoe"], 1) if avg_yoe["avg_yoe"] else None,
    }


def remote_vs_onsite():
    """Simple split of remote vs non-remote postings."""
    db = get_db()
    rows = db.execute("""
        SELECT is_remote, COUNT(*) as count
        FROM job_posts
        GROUP BY is_remote
    """).fetchall()
    db.close()

    result = {"remote": 0, "onsite": 0}
    for r in rows:
        if r["is_remote"]:
            result["remote"] = r["count"]
        else:
            result["onsite"] = r["count"]
    return result

def top_companies(limit=10):
    db = get_db()
    rows = db.execute("""
        SELECT company, COUNT(*) as count
        FROM job_posts
        WHERE company IS NOT NULL AND company != ''
        GROUP BY company
        ORDER BY count DESC
        LIMIT ?
    """, (limit,)).fetchall()
    db.close()
    return {"companies": [dict(r) for r in rows]}