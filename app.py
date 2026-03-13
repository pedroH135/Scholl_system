from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/cadastro')
def cadastro():
    return render_template("cadastro.html")


@app.route('/dashboard_aluno')
def dashboard_aluno():
    return render_template("dashboard_aluno.html")


@app.route('/dashboard_professor')
def dashboard_professor():
    return render_template("dashboard_professor.html")


@app.route('/notas')
def notas():
    return render_template("notas.html")


@app.route('/materiais')
def materiais():
    return render_template("materiais.html")


@app.route('/presenca')
def presenca():
    return render_template("presenca.html")


@app.route('/feedback')
def feedback():
    return render_template("feedback.html")


@app.route('/desempenho')
def desempenho():
    return render_template("desempenho.html")


@app.route('/calendario')
def calendario():
    return render_template("calendario.html")


if __name__ == '__main__':
    app.run(debug=True)
