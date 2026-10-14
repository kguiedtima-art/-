# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import json
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DATA_FILE = Path(__file__).with_name("personal_notes.json")
CATEGORIES = ["การเรียน", "งานที่ต้องทำ", "กิจกรรม", "ข้อมูลสำคัญ", "ส่วนตัว", "อื่น ๆ"]


def load_notes():
    if not DATA_FILE.exists():
        return []
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_notes(notes):
    DATA_FILE.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")


def next_id(notes):
    used = {note.get("id") for note in notes}
    n = 1
    while f"N{n:04d}" in used:
        n += 1
    return f"N{n:04d}"


@app.route("/", methods=["GET"])
def index():
    notes = load_notes()
    keyword = request.args.get("q", "").strip().casefold()
    category_filter = request.args.get("category", "").strip()
    sort = request.args.get("sort", "newest")

    filtered = []
    for note in notes:
        haystack = " ".join([
            note.get("title", ""), note.get("content", ""),
            note.get("category", ""), " ".join(note.get("tags", []))
        ]).casefold()
        if keyword and keyword not in haystack:
            continue
        if category_filter and note.get("category") != category_filter:
            continue
        filtered.append(note)

    if sort == "oldest":
        filtered.sort(key=lambda n: n.get("date", ""))
    elif sort == "title":
        filtered.sort(key=lambda n: n.get("title", "").casefold())
    else:
        filtered.sort(key=lambda n: n.get("date", ""), reverse=True)

    counts = {category: 0 for category in CATEGORIES}
    for note in notes:
        cat = note.get("category", "อื่น ๆ")
        counts[cat] = counts.get(cat, 0) + 1

    tag_counts = {}
    for note in notes:
        for tag in note.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    popular_tag = max(tag_counts, key=tag_counts.get) if tag_counts else "ยังไม่มี"
    popular_category = max(counts, key=counts.get) if notes else "ยังไม่มี"
    latest = max(notes, key=lambda n: n.get("date", "")) if notes else None

    return render_template(
        "index.html", notes=filtered, all_count=len(notes), categories=CATEGORIES,
        counts=counts, keyword=request.args.get("q", ""), category_filter=category_filter,
        sort=sort, popular_tag=popular_tag, popular_category=popular_category, latest=latest
    )


@app.route("/add", methods=["POST"])
def add_note():
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    category = request.form.get("category", "อื่น ๆ")
    date = request.form.get("date", datetime.now().strftime("%Y-%m-%d"))
    tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
    if not title or not content:
        flash("กรุณากรอกชื่อเรื่องและรายละเอียด", "error")
        return redirect(url_for("index"))
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        flash("รูปแบบวันที่ไม่ถูกต้อง", "error")
        return redirect(url_for("index"))
    if category not in CATEGORIES:
        category = "อื่น ๆ"
    notes = load_notes()
    notes.append({
        "id": next_id(notes), "title": title, "content": content,
        "category": category, "date": date, "tags": tags,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": ""
    })
    save_notes(notes)
    flash("เพิ่มบันทึกเรียบร้อยแล้ว", "success")
    return redirect(url_for("index"))


@app.route("/edit/<note_id>", methods=["POST"])
def edit_note(note_id):
    notes = load_notes()
    note = next((n for n in notes if n.get("id") == note_id), None)
    if not note:
        flash("ไม่พบบันทึกที่ต้องการแก้ไข", "error")
        return redirect(url_for("index"))
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    date = request.form.get("date", note.get("date", ""))
    category = request.form.get("category", note.get("category", "อื่น ๆ"))
    tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
    if not title or not content:
        flash("ชื่อเรื่องและรายละเอียดห้ามว่าง", "error")
        return redirect(url_for("index"))
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        flash("รูปแบบวันที่ไม่ถูกต้อง", "error")
        return redirect(url_for("index"))
    note.update(title=title, content=content, date=date,
                category=category if category in CATEGORIES else "อื่น ๆ",
                tags=tags, updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    save_notes(notes)
    flash("แก้ไขบันทึกเรียบร้อยแล้ว", "success")
    return redirect(url_for("index"))


@app.route("/delete/<note_id>", methods=["POST"])
def delete_note(note_id):
    notes = load_notes()
    remaining = [n for n in notes if n.get("id") != note_id]
    if len(remaining) == len(notes):
        flash("ไม่พบบันทึกที่ต้องการลบ", "error")
    else:
        save_notes(remaining)
        flash("ลบบันทึกเรียบร้อยแล้ว", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    print("เปิดเว็บไซต์ที่ http://127.0.0.1:5000")
    app.run(debug=True)
