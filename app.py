from flask import Flask, render_template, request

app = Flask(__name__)

# AI 모델 (간단한 예시)
def simple_ai(input_text):
    # 텍스트 입력에 대한 간단한 응답
    if "안녕" in input_text:
        return "안녕하세요!"
    elif "잘 지내" in input_text:
        return "잘 지내고 있어요, 감사합니다!"
    else:
        return "무슨 말인지 잘 모르겠어요."

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        user_input = request.form["user_input"]  # 사용자가 입력한 텍스트
        ai_response = simple_ai(user_input)  # AI 응답
        return render_template("index.html", user_input=user_input, ai_response=ai_response)
    return render_template("index.html", user_input="", ai_response="")

if __name__ == "__main__":
    app.run(debug=True)
