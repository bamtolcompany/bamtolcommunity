from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os, sqlite3
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    with sqlite3.connect("db.sqlite3") as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
        c.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                title TEXT,
                content TEXT,
                image TEXT,
                created TEXT
            )
        """)
        c.execute("CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY, post_id INTEGER, user_id INTEGER, text TEXT, created TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS likes (id INTEGER PRIMARY KEY, post_id INTEGER, user_id INTEGER)")
        c.execute("CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY, post_id INTEGER, user_id INTEGER, reason TEXT)")
        conn.commit()

@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    with sqlite3.connect("db.sqlite3") as conn:
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (data["username"], data["password"]))
            conn.commit()
            return jsonify({"message": "가입 완료"}), 200
        except:
            return jsonify({"message": "이미 존재하는 사용자"}), 400

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    with sqlite3.connect("db.sqlite3") as conn:
        user = conn.execute("SELECT id FROM users WHERE username=? AND password=?", (data["username"], data["password"])).fetchone()
        if user:
            return jsonify({"message": "로그인 성공", "user_id": user[0]}), 200
        else:
            return jsonify({"message": "로그인 실패"}), 401

@app.route("/posts", methods=["GET", "POST"])
def posts():
    if request.method == "GET":
        with sqlite3.connect("db.sqlite3") as conn:
            rows = conn.execute(
                "SELECT posts.id, users.username, posts.content, posts.image, posts.created, "
                "(SELECT COUNT(*) FROM likes WHERE likes.post_id=posts.id) as like_count "
                "FROM posts JOIN users ON users.id=posts.user_id ORDER BY posts.id DESC").fetchall()
            return jsonify([
                {"id": r[0], "author": r[1], "content": r[2], "image": r[3], "created": r[4], "likes": r[5]} for r in rows
            ])
    else:
        user_id = request.form["user_id"]
        content = request.form["content"]
        image = None
        if "image" in request.files:
            file = request.files["image"]
            filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image = filename
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("INSERT INTO posts (user_id, content, image, created) VALUES (?, ?, ?, ?)", (user_id, content, image, datetime.now().isoformat()))
            conn.commit()
            return jsonify({"message": "작성 완료"})

@app.route("/posts/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    data = request.json
    user_id = data.get("user_id")
    with sqlite3.connect("db.sqlite3") as conn:
        existing = conn.execute("SELECT id FROM likes WHERE post_id=? AND user_id=?", (post_id, user_id)).fetchone()
        if existing:
            conn.execute("DELETE FROM likes WHERE id=?", (existing[0],))
            conn.commit()
            return jsonify({"message": "좋아요 취소"})
        else:
            conn.execute("INSERT INTO likes (post_id, user_id) VALUES (?, ?)", (post_id, user_id))
            conn.commit()
            return jsonify({"message": "좋아요"})
            @app.route('/write')
def write_page():
    return app.send_static_file('write.html')

@app.route("/comments/<int:post_id>", methods=["GET", "POST"])
def comments(post_id):
    if request.method == "GET":
        with sqlite3.connect("db.sqlite3") as conn:
            rows = conn.execute("SELECT comments.id, users.username, comments.text, comments.created FROM comments JOIN users ON users.id=comments.user_id WHERE post_id=?", (post_id,)).fetchall()
            return jsonify([
                {"id": r[0], "author": r[1], "text": r[2], "created": r[3]} for r in rows
            ])
    else:
        data = request.json
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("INSERT INTO comments (post_id, user_id, text, created) VALUES (?, ?, ?, ?)", (post_id, data["user_id"], data["text"], datetime.now().isoformat()))
            conn.commit()
            return jsonify({"message": "댓글 작성 완료"})

@app.route("/posts/<int:post_id>/report", methods=["POST"])
def report_post(post_id):
    data = request.json
    user_id = data.get("user_id")
    reason = data.get("reason", "")
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("INSERT INTO reports (post_id, user_id, reason) VALUES (?, ?, ?)", (post_id, user_id, reason))
        conn.commit()
    return jsonify({"message": "신고 완료"})

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
