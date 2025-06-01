from flask import Flask, request, redirect, url_for, session, abort, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from jinja2 import DictLoader
with app.app_context():
    db.create_all()

# --- 템플릿 문자열 정의 ---
base_html_template = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>밤톨 커뮤니티</title>
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans KR', sans-serif;
    max-width: 700px;
    margin: 40px auto;
    background: #ffffff;
    color: #222;
    line-height: 1.6;
  }

  nav {
    margin-bottom: 20px;
    border-bottom: 1px solid #ddd;
    padding-bottom: 10px;
  }

  nav a {
    margin-right: 20px;
    text-decoration: none;
    color: #555;
    font-weight: 500;
    font-size: 1rem;
  }

  nav a:hover {
    color: #007bff;
  }

  .post, .comment {
    background: #fafafa;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 15px 18px;
    margin-bottom: 15px;
  }

  h1, h2, h3, h4 {
    color: #111;
    margin-bottom: 12px;
    font-weight: 600;
  }

  .timestamp {
    color: #888;
    font-size: 0.85rem;
  }

  form.inline {
    display: inline;
  }

  button, input[type=submit] {
    cursor: pointer;
    background-color: transparent;
    border: 1.5px solid #007bff;
    color: #007bff;
    padding: 6px 14px;
    border-radius: 3px;
    font-size: 0.9rem;
    font-weight: 600;
    transition: background-color 0.2s ease, color 0.2s ease;
    margin-right: 6px;
  }

  button:hover, input[type=submit]:hover {
    background-color: #007bff;
    color: white;
  }

  button:disabled, a.disabled {
    border-color: #ccc !important;
    color: #ccc !important;
    cursor: default !important;
    background-color: transparent !important;
  }

  input[type=text], input[type=password], textarea {
    width: 100%;
    padding: 8px 12px;
    margin-top: 6px;
    margin-bottom: 14px;
    border: 1px solid #ccc;
    border-radius: 3px;
    font-size: 1rem;
    box-sizing: border-box;
    resize: vertical;
    transition: border-color 0.2s ease;
  }

  input[type=text]:focus, input[type=password]:focus, textarea:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 4px rgba(0, 123, 255, 0.3);
  }

  a {
    color: #007bff;
    text-decoration: none;
  }

  a:hover {
    text-decoration: underline;
  }

  hr {
    border: none;
    height: 1px;
    background: #eaeaea;
    margin: 30px 0;
  }
</style>
</head>
<body>
<nav>
  {% if user %}
    안녕, <b>{{ user.username }}</b>! 
    <a href="{{ url_for('index') }}">홈</a>
    <a href="{{ url_for('logout') }}">로그아웃</a>
    <a href="{{ url_for('create_post') }}">글쓰기</a>
  {% else %}
    <a href="{{ url_for('index') }}">홈</a>
    <a href="{{ url_for('login') }}">로그인</a>
    <a href="{{ url_for('register') }}">회원가입</a>
  {% endif %}
</nav>
<hr>
{% block content %}{% endblock %}
</body>
</html>
"""

index_page_template = """
{% extends "base.html" %}
{% block title %}게시판 - {{ super() }}{% endblock %}
{% block content %}
<h1>밤톨 커뮤니티 게시판</h1>
{% if posts %}
  {% for post in posts %}
    <div class="post">
      <h2><a href="{{ url_for('post_detail', post_id=post.id) }}">{{ post.title }}</a></h2>
      <p>작성자: <b>{{ post.author.username }}</b> | <span class="timestamp">{{ post.created_at.strftime('%Y-%m-%d %H:%M') }}</span></p>
      <p>👍 {{ post.likes|selectattr('is_like','equalto',True)|list|length }}
         | 👎 {{ post.likes|selectattr('is_like','equalto',False)|list|length }}</p>
      {% if user and user.id == post.author_id %}
        <a href="{{ url_for('edit_post', post_id=post.id) }}">수정</a> |
        <a href="{{ url_for('delete_post', post_id=post.id) }}" onclick="return confirm('삭제할까요?');">삭제</a>
      {% endif %}
    </div>
  {% endfor %}
{% else %}
  <p>아직 작성된 글이 없습니다.</p>
{% endif %}
{% endblock %}
"""

register_page_template = """
{% extends "base.html" %}
{% block title %}회원가입 - {{ super() }}{% endblock %}
{% block content %}
<h1>회원가입</h1>
<form method="post">
  <label>사용자명:</label>
  <input type="text" name="username" required>
  <label>비밀번호:</label>
  <input type="password" name="password" required>
  <button type="submit">가입하기</button>
</form>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
{% endblock %}
"""

login_page_template = """
{% extends "base.html" %}
{% block title %}로그인 - {{ super() }}{% endblock %}
{% block content %}
<h1>로그인</h1>
<form method="post">
  <label>사용자명:</label>
  <input type="text" name="username" required>
  <label>비밀번호:</label>
  <input type="password" name="password" required>
  <button type="submit">로그인</button>
</form>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
{% endblock %}
"""

create_post_page_template = """
{% extends "base.html" %}
{% block title %}글쓰기 - {{ super() }}{% endblock %}
{% block content %}
<h1>새 글 쓰기</h1>
<form method="post">
  <label>제목:</label>
  <input type="text" name="title" required>
  <label>내용:</label>
  <textarea name="body" rows="10" required></textarea>
  <button type="submit">등록</button>
</form>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
{% endblock %}
"""

post_detail_page_template = """
{% extends "base.html" %}
{% block title %}{{ post.title }} - {{ super() }}{% endblock %}
{% block content %}
<h1>{{ post.title }}</h1>
<p>작성자: <b>{{ post.author.username }}</b> | <span class="timestamp">{{ post.created_at.strftime('%Y-%m-%d %H:%M') }}</span></p>
<p style="white-space: pre-line;">{{ post.body }}</p>

<p>
  👍 {{ post.likes|selectattr('is_like','equalto',True)|list|length }}
  | 👎 {{ post.likes|selectattr('is_like','equalto',False)|list|length }}
</p>

{% if user %}
  <form action="{{ url_for('like_post', post_id=post.id) }}" method="post" class="inline">
    <input type="hidden" name="is_like" value="1">
    <button type="submit" {% if user_like == True %}disabled{% endif %}>좋아요</button>
  </form>
  <form action="{{ url_for('like_post', post_id=post.id) }}" method="post" class="inline">
    <input type="hidden" name="is_like" value="0">
    <button type="submit" {% if user_like == False %}disabled{% endif %}>싫어요</button>
  </form>
{% endif %}

{% if user and user.id == post.author_id %}
  <p>
    <a href="{{ url_for('edit_post', post_id=post.id) }}">글 수정</a> |
    <a href="{{ url_for('delete_post', post_id=post.id) }}" onclick="return confirm('삭제할까요?');">글 삭제</a>
  </p>
{% endif %}

<hr>
<h3>댓글 ({{ comments|length }})</h3>

{% if comments %}
  {% for comment in comments %}
    <div class="comment">
      <p><b>{{ comment.author.username }}</b> <span class="timestamp">{{ comment.created_at.strftime('%Y-%m-%d %H:%M') }}</span></p>
      <p style="white-space: pre-line;">{{ comment.body }}</p>
      {% if user and user.id == comment.author_id %}
        <a href="{{ url_for('edit_comment', comment_id=comment.id) }}">수정</a> |
        <a href="{{ url_for('delete_comment', comment_id=comment.id) }}" onclick="return confirm('댓글을 삭제할까요?');">삭제</a>
      {% endif %}
    </div>
  {% endfor %}
{% else %}
  <p>댓글이 없습니다.</p>
{% endif %}

{% if user %}
  <hr>
  <h4>댓글 작성</h4>
  <form method="post" action="{{ url_for('add_comment', post_id=post.id) }}">
    <textarea name="body" rows="3" required></textarea>
    <button type="submit">댓글 달기</button>
  </form>
{% else %}
  <p><a href="{{ url_for('login') }}">로그인</a> 해야 댓글 작성이 가능합니다.</p>
{% endif %}
{% endblock %}
"""

edit_post_page_template = """
{% extends "base.html" %}
{% block title %}글 수정 - {{ super() }}{% endblock %}
{% block content %}
<h1>글 수정</h1>
<form method="post">
  <label>제목:</label>
  <input type="text" name="title" value="{{ post.title }}" required>
  <label>내용:</label>
  <textarea name="body" rows="10" required>{{ post.body }}</textarea>
  <button type="submit">수정 완료</button>
</form>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
{% endblock %}
"""

edit_comment_page_template = """
{% extends "base.html" %}
{% block title %}댓글 수정 - {{ super() }}{% endblock %}
{% block content %}
<h1>댓글 수정</h1>
<form method="post">
  <textarea name="body" rows="5" required>{{ comment.body }}</textarea>
  <button type="submit">수정 완료</button>
</form>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
{% endblock %}
"""

# --- Flask 앱 설정 ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

# DictLoader로 템플릿 등록
app.jinja_loader = DictLoader({
    'base.html': base_html_template,
    'index_page.html': index_page_template,
    'register_page.html': register_page_template,
    'login_page.html': login_page_template,
    'create_post_page.html': create_post_page_template,
    'post_detail_page.html': post_detail_page_template,
    'edit_post_page.html': edit_post_page_template,
    'edit_comment_page.html': edit_comment_page_template
})

db = SQLAlchemy(app)

# --- 모델 정의 ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    posts = db.relationship('Post', backref='author', cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='author', cascade="all, delete-orphan")
    likes = db.relationship('Like', backref='user', cascade="all, delete-orphan")

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', cascade="all, delete-orphan")
    likes = db.relationship('Like', backref='post', cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    is_like = db.Column(db.Boolean, nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='user_post_unique'),)

def current_user():
    uid = session.get('user_id')
    if uid:
        return User.query.get(uid)
    return None

# --- 라우트 정의 ---
@app.route('/')
def index():
    user = current_user()
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index_page.html', posts=posts, user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user():
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            error = '모든 필드를 입력하세요.'
        elif User.query.filter_by(username=username).first():
            error = '이미 존재하는 사용자명입니다.'
        else:
            u = User(username=username)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            session['user_id'] = u.id
            return redirect(url_for('index'))
    return render_template('register_page.html', error=error, user=current_user())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user():
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        error = '사용자명 또는 비밀번호가 잘못되었습니다.'
    return render_template('login_page.html', error=error, user=current_user())

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/post/create', methods=['GET', 'POST'])
def create_post():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    error = None
    if request.method == 'POST':
        title = request.form['title'].strip()
        body = request.form['body'].strip()
        if not title or not body:
            error = '제목과 내용을 입력하세요.'
        else:
            post = Post(title=title, body=body, author=user)
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('post_detail', post_id=post.id))
    return render_template('create_post_page.html', error=error, user=user)

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    user = current_user()
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.created_at.desc()).all()
    user_like = None
    if user:
        like_obj = Like.query.filter_by(user_id=user.id, post_id=post.id).first()
        if like_obj:
            user_like = like_obj.is_like
    return render_template('post_detail_page.html', post=post, comments=comments, user=user, user_like=user_like)

@app.route('/post/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    user = current_user()
    if not user:
        abort(403)
    post = Post.query.get_or_404(post_id)
    is_like_str = request.form.get('is_like')
    if is_like_str not in ['0', '1']:
        return redirect(url_for('post_detail', post_id=post.id))
    is_like = True if is_like_str == '1' else False

    like_obj = Like.query.filter_by(user_id=user.id, post_id=post.id).first()
    if like_obj:
        if like_obj.is_like == is_like:
            db.session.delete(like_obj)
        else:
            like_obj.is_like = is_like
    else:
        new_like = Like(user_id=user.id, post_id=post.id, is_like=is_like)
        db.session.add(new_like)
    db.session.commit()
    return redirect(url_for('post_detail', post_id=post.id))

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    post = Post.query.get_or_404(post_id)
    if post.author_id != user.id:
        abort(403)
    error = None
    if request.method == 'POST':
        title = request.form['title'].strip()
        body = request.form['body'].strip()
        if not title or not body:
            error = '제목과 내용을 입력하세요.'
        else:
            post.title = title
            post.body = body
            db.session.commit()
            return redirect(url_for('post_detail', post_id=post.id))
    return render_template('edit_post_page.html', post=post, error=error, user=user)

@app.route('/post/<int:post_id>/delete')
def delete_post(post_id):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    post = Post.query.get_or_404(post_id)
    if post.author_id != user.id:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/post/<int:post_id>/comment/add', methods=['POST'])
def add_comment(post_id):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    post = Post.query.get_or_404(post_id)
    body = request.form.get('body', '').strip()
    if not body:
        return redirect(url_for('post_detail', post_id=post.id))
    comment = Comment(body=body, author=user, post=post)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('post_detail', post_id=post.id))

@app.route('/comment/<int:comment_id>/edit', methods=['GET', 'POST'])
def edit_comment(comment_id):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    comment = Comment.query.get_or_404(comment_id)
    if comment.author_id != user.id:
        abort(403)
    error = None
    if request.method == 'POST':
        body = request.form.get('body', '').strip()
        if not body:
            error = '댓글 내용을 입력하세요.'
        else:
            comment.body = body
            db.session.commit()
            return redirect(url_for('post_detail', post_id=comment.post_id))
    return render_template('edit_comment_page.html', comment=comment, error=error, user=user)

@app.route('/comment/<int:comment_id>/delete')
def delete_comment(comment_id):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    comment = Comment.query.get_or_404(comment_id)
    if comment.author_id != user.id:
        abort(403)
    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('post_detail', post_id=post_id))

# --- 애플리케이션 실행 ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
