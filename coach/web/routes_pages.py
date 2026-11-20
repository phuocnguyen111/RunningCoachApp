from datetime import date

from flask import abort, redirect, render_template, url_for

from ..ids import slugify
from ..summary import athlete_summary
from .common import services


def register_page_routes(app):
    @app.get("/")
    def index():
        s = services()
        docs = s.athletes.all()
        athletes = s.athletes.list(docs=docs)
        return render_template(
            "index.html",
            groups=s.groups.list(s.athletes.counts_by_group(docs)),
            athletes=athletes,
            plans=s.catalog.all(),
            plan_errors=s.catalog.errors,
            default_plan_id=s.catalog.default_id(),
            total_km=round(sum(a["total_km"] for a in athletes), 1),
        )

    @app.get("/athletes/<athlete_id>")
    def athlete_page(athlete_id):
        s = services()
        a = s.athletes.get(athlete_id)
        if not a:
            abort(404)
        group = s.groups.get(a.get("group_id"))
        activities = [{k: v for k, v in x.items() if k != "hr_data"} for x in reversed(a["activities"])]
        plan_names = {p["id"]: p["name"] for p in s.catalog.all()}
        latest_plan = next((x["plan_id"] for x in activities if x.get("plan_id")), None)
        ai_plan_id = latest_plan or (group or {}).get("plan_id")
        return render_template(
            "athlete.html",
            athlete=a, group=group, activities=activities, plan_names=plan_names,
            summary=athlete_summary(a, s.catalog, group, date.today()),
            ai_enabled=s.config.ai_enabled, ai_plan=s.catalog.get(ai_plan_id),
        )

    @app.get("/athlete/<path:name>")
    def legacy_athlete_page(name):
        s = services()
        a = s.athletes.find_by_name(name) or s.athletes.get(slugify(name))
        if not a:
            abort(404)
        return redirect(url_for("athlete_page", athlete_id=a["id"]), code=301)
