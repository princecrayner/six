from flask import Flask, render_template, request, jsonify, session, send_from_directory
import sqlite3, os, hashlib

app = Flask(__name__)
app.secret_key = "six_secret"

UPLOAD_FOLDER = "uploads"
DB = "database.db"
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
    try:
        with db() as con:
            con.execute("INSERT INTO users VALUES(NULL,?,?)",(u,p))
        return jsonify(ok=True)
    except:
        return jsonify(ok=False)

@app.route("/login", methods=["POST"])
def login():
    u = request.json["username"]
    p = hash_pw(request.json["password"])
    with db() as con:
        r = con.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p)).fetchone()
    if r:
        session["user"]=u
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
    f.save(os.path.join(UPLOAD_FOLDER,name))
    with db() as con:
        con.execute("INSERT INTO videos(filename,owner) VALUES(?,?)",(name,session["user"]))
    return jsonify(ok=True)

@app.route("/videos")
def videos():
    with db() as con:
        rows = con.execute("SELECT * FROM videos ORDER BY id DESC").fetchall()
    return jsonify([{
        "id":r[0],"file":r[1],"owner":r[2],"likes":r[3],"views":r[4]
    } for r in rows])

@app.route("/like/<int:i>", methods=["POST"])
def like(i):
    with db() as con:
        con.execute("UPDATE videos SET likes=likes+1 WHERE id=?",(i,))
        l=con.execute("SELECT likes FROM videos WHERE id=?",(i,)).fetchone()[0]
    return jsonify(likes=l)

@app.route("/view/<int:i>", methods=["POST"])
def view(i):
    with db() as con:
        con.execute("UPDATE videos SET views=views+1 WHERE id=?",(i,))
        v=con.execute("SELECT views FROM videos WHERE id=?",(i,)).fetchone()[0]
    return jsonify(views=v)

@app.route("/delete/<int:i>", methods=["POST"])
def delete(i):
    if "user" not in session: return jsonify(error=True)
    with db() as con:
        v=con.execute("SELECT filename,owner FROM videos WHERE id=?",(i,)).fetchone()
        if v and v[1]==session["user"]:
            os.remove(os.path.join(UPLOAD_FOLDER,v[0]))
            con.execute("DELETE FROM videos WHERE id=?",(i,))
    return jsonify(ok=True)

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
