import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from config import Config
from models import init_db, get_db

app = Flask(__name__)
app.config.from_object(Config)

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        role_applied  = request.form.get("role_applied", "").strip()
        company_name  = request.form.get("company_name", "").strip()
        yoe           = request.form.get("yoe", "").strip()
        outcome       = request.form.get("outcome", "").strip()
        story_type    = request.form.get("story_type", "").strip()
        story         = request.form.get("story", "").strip()
        submitter     = request.form.get("submitter_name", "").strip() or "Anonymous"

        # Basic validation
        errors = []
        if not role_applied:
            errors.append("Role applied is required.")
        if not story or len(story) < 30:
            errors.append("Story must be at least 30 characters.")
        if yoe and not yoe.isdigit():
            errors.append("Years of experience must be a number.")

        if errors:
            return render_template("submit.html", errors=errors, form=request.form)

        db = get_db()
        db.execute("""
            INSERT INTO user_stories
              (submitter_name, role_applied, company_name, yoe,
               outcome, story, story_type)
            VALUES (?,?,?,?,?,?,?)
        """, (
            submitter, role_applied, company_name,
            int(yoe) if yoe else None,
            outcome, story, story_type
        ))
        db.commit()
        db.close()

        return redirect(url_for("submit_success"))

    return render_template("submit.html", errors=[], form={})


@app.route("/submit/success")
def submit_success():
    return render_template("success.html")


@app.route("/api/status")
def status():
    db = get_db()
    counts = {
        "job_posts":        db.execute("SELECT COUNT(*) FROM job_posts").fetchone()[0],
        "skills_extracted": db.execute("SELECT COUNT(*) FROM skills_extracted").fetchone()[0],
        "user_stories":     db.execute("SELECT COUNT(*) FROM user_stories").fetchone()[0],
    }
    db.close()
    return jsonify({"status": "ok", "counts": counts})


@app.route("/api/stories")
def api_stories():
    """Returns approved stories as JSON."""
    db = get_db()
    rows = db.execute("""
        SELECT submitter_name, role_applied, company_name,
               yoe, outcome, story, story_type, submitted_at
        FROM user_stories
        WHERE is_approved = 1
        ORDER BY submitted_at DESC
        LIMIT 50
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# ── Analysis API ───────────────────────────────────────────────────────────────

from analysis import (
    experience_inflation_report,
    top_skills_report,
    experience_distribution,
    outcome_breakdown,
    remote_vs_onsite,
)

@app.route("/api/analysis/inflation")
def api_inflation():
    return jsonify(experience_inflation_report())

@app.route("/api/analysis/skills")
def api_skills():
    limit = request.args.get("limit", 15, type=int)
    return jsonify(top_skills_report(limit=limit))

@app.route("/api/analysis/exp-distribution")
def api_exp_dist():
    return jsonify(experience_distribution())

@app.route("/api/analysis/outcomes")
def api_outcomes():
    return jsonify(outcome_breakdown())

@app.route("/api/analysis/remote")
def api_remote():
    return jsonify(remote_vs_onsite())

@app.route("/api/analysis/summary")
def api_summary():
    """Single endpoint that returns everything — used by the dashboard."""
    return jsonify({
        "inflation":     experience_inflation_report(),
        "skills":        top_skills_report(limit=10),
        "exp_dist":      experience_distribution(),
        "outcomes":      outcome_breakdown(),
        "remote":        remote_vs_onsite(),
    })

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

from analysis import (
    experience_inflation_report,
    top_skills_report,
    experience_distribution,
    outcome_breakdown,
    remote_vs_onsite,
    top_companies,        # add this
)

@app.route("/api/analysis/companies")
def api_companies():
    return jsonify(top_companies())


# ── Bootstrap ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(os.path.dirname(Config.DATABASE), exist_ok=True)
    init_db()
    app.run(debug=Config.DEBUG, port=5000)