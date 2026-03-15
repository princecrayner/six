from pymongo import MongoClient

import cloudinary
import cloudinary.uploader


client = MongoClient("mongodb+srv://princecrayner_db_user:JUNIOR80@cluster0.toxhpdn.mongodb.net/?appName=Cluster0")
db = client["six_app"]

videos_collection = db["videos"]
users_collection = db["users"]
comments_collection = db["comments"]

cloudinary.config(
  cloud_name="dq155p1ml",
  api_key="454437591454836",
  api_secret="GFqA3p4i03h-3QR1vRD509c8B_Y"
)

from flask import Flask, render_template, request, jsonify, session, send_from_directory
import sqlite3, os, hashlib

app = Flask(__name__)
app.secret_key = "six_secret"

UPLOAD_FOLDER = "uploads"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "database.db")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def db():
    return sqlite3.connect(DB)

# ---------- INIT DB ----------
with db() as con:
    con.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS videos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        owner TEXT,
        likes INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS comments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id INTEGER,
        user TEXT,
        text TEXT
    )""")

# ---------- AUTH ----------
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

@app.route("/register", methods=["POST"])
def register():
    u = request.json["username"]
    p = hash_pw(request.json["password"])

    if users_collection.find_one({"username": u}):
        return jsonify(ok=False)

    users_collection.insert_one({
        "username": u,
        "password": p
    })

    return jsonify(ok=True)

@app.route("/login", methods=["POST"])
def login():
    u = request.json["username"]
    p = hash_pw(request.json["password"])

    user = users_collection.find_one({
        "username": u,
        "password": p
    })

    if user:
        session["user"] = u
        return jsonify(ok=True)

    return jsonify(ok=False)

@app.route("/logout")
def logout():
    session.clear()
    return jsonify(ok=True)

# ---------- MAIN ----------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "user" not in session: return jsonify(error="login")
    f = request.files["video"]
    title = request.form["title"].replace(" ","_")
    name = f"{title}_{f.filename}"
    result = cloudinary.uploader.upload(
    f,
    resource_type="video"
    )

    video_url = result["secure_url"]
    with db() as con:
        videos_collection.insert_one({
    "file": video_url,
    "owner": session["user"],
    "likes": 0,
    "views": 0
    })
    return jsonify(ok=True)

@app.route("/videos")
def videos():
    with db() as con:
        videos = list(videos_collection.find().sort("_id",-1))

    return jsonify([{
    "id": str(v["_id"]),
    "file": v["file"],
    "owner": v["owner"],
    "likes": v["likes"],
    "views": v["views"]
    } for v in videos])

@app.route("/like/<id>", methods=["POST"])
def like(id):
    videos_collection.update_one(
        {"_id": ObjectId(id)},
        {"$inc": {"likes": 1}}
    )

    v = videos_collection.find_one({"_id": ObjectId(id)})
    return jsonify(likes=v["likes"])

@app.route("/view/<id>", methods=["POST"])
def view(id):
    videos_collection.update_one(
        {"_id": ObjectId(id)},
        {"$inc": {"views": 1}}
    )

    v = videos_collection.find_one({"_id": ObjectId(id)})
    return jsonify(views=v["views"])

@app.route("/delete/<int:i>", methods=["POST"])
def delete(i):
    if "user" not in session: return jsonify(error=True)
    with db() as con:
        v=con.execute("SELECT filename,owner FROM videos WHERE id=?",(i,)).fetchone()
        if v and v[1]==session["user"]:
            con.execute("DELETE FROM videos WHERE id=?",(i,))
    return jsonify(ok=True)

@app.route("/settings")
def settings():
    return render_template("settings.html")

# ---------- COMMENTS ----------
@app.route("/comment/<int:i>", methods=["POST"])
def comment(i):
    if "user" not in session: return jsonify(error=True)
    t=request.json["text"]
    with db() as con:
        con.execute("INSERT INTO comments VALUES(NULL,?,?,?)",(i,session["user"],t))
    return jsonify(ok=True)

@app.route("/comments/<int:i>")
def comments(i):
    with db() as con:
        c=con.execute("SELECT user,text FROM comments WHERE video_id=?",(i,)).fetchall()
    return jsonify(c)

@app.route("/uploads/<f>")
def up(f):
    return send_from_directory(UPLOAD_FOLDER,f)

if __name__=="__main__":
    app.run()
