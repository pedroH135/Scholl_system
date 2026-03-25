from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)

app.secret_key = "sistema_escolar"


def conectar():
    return sqlite3.connect("escola.db")


@app.route('/')
def index():
    return render_template("index.html")


# LISTA DE ALUNOS (VISÃO DO PROFESSOR)

@app.route("/alunos")
def alunos():

    # conecta ao banco
    conn = conectar()
    cursor = conn.cursor()

    # ----------------------------------------------------
    # 1) pegar um professor (no futuro será o professor logado)
    # ----------------------------------------------------
    cursor.execute("""
    SELECT id FROM usuarios
    WHERE tipo='professor'
    LIMIT 1
    """)
    professor = cursor.fetchone()

    if not professor:
        return "Nenhum professor encontrado no sistema"

    professor_id = professor[0]

    # ----------------------------------------------------
    # 2) pegar as matérias e anos que ele leciona
    # ----------------------------------------------------
    cursor.execute("""
    SELECT m.nome, pm.ano_letivo
    FROM professor_materias pm
    JOIN materias m ON pm.materia_id = m.id
    WHERE pm.professor_id = ?
    """, (professor_id,))

    turmas_professor = cursor.fetchall()

    # estrutura que vamos mandar para o HTML
    turmas = []

    # ----------------------------------------------------
    # 3) para cada matéria + ano buscar os alunos
    # ----------------------------------------------------
    for materia_nome, ano in turmas_professor:

        cursor.execute("""
        SELECT id, nome, email
        FROM usuarios
        WHERE tipo='aluno'
        AND ano_letivo=?
        """, (ano,))

        alunos = cursor.fetchall()

        # buscar notas se existirem
        alunos_formatados = []

        for aluno in alunos:

            aluno_id = aluno[0]

            cursor.execute("""
            SELECT n.ab1_1, n.ab1_2, n.ab2_1, n.ab2_2
            FROM notas n
            JOIN materias m ON n.materia_id = m.id
            WHERE n.aluno_id=? AND m.nome=? AND n.ano_letivo=?
            """,(aluno_id, materia_nome, ano))

            notas = cursor.fetchone()

            if notas:
                ab1_1, ab1_2, ab2_1, ab2_2 = notas
            else:
                ab1_1 = ab1_2 = ab2_1 = ab2_2 = "-"

            alunos_formatados.append({
                "id": aluno_id,
                "nome": aluno[1],
                "email": aluno[2],
                "ab1_1": ab1_1,
                "ab1_2": ab1_2,
                "ab2_1": ab2_1,
                "ab2_2": ab2_2
            })

        turmas.append({
            "materia": materia_nome,
            "ano": ano,
            "alunos": alunos_formatados
        })

    conn.close()

    return render_template("alunos.html", turmas=turmas)


# LOGIN

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        cpf = request.form["cpf"]
        senha = request.form["senha"]

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM usuarios
        WHERE cpf=? AND senha=?
        """,(cpf,senha))

        usuario = cursor.fetchone()

        conn.close()

        if usuario:

            tipo = usuario[5]

            if tipo == "aluno":

                # salva ID do aluno na sessão
                session["usuario_id"] = usuario[0]

                return redirect("/dashboard_aluno")

            elif tipo == "professor":
                return redirect("/dashboard_professor")

        else:
            return "CPF ou senha incorretos"

    return render_template("login.html")


# CADASTRO

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form["nome"]
        cpf = request.form["cpf"]
        email = request.form["email"]
        senha = request.form["senha"]
        tipo = request.form["tipo"]

        conn = conectar()
        cursor = conn.cursor()

        # CADASTRO DE ALUNO
        if tipo == "aluno":

            ano = request.form.get("ano_letivo_aluno")

            cursor.execute("""
            INSERT INTO usuarios (nome, cpf, email, senha, tipo, ano_letivo)
            VALUES (?, ?, ?, ?, ?, ?)
            """,(nome, cpf, email, senha, tipo, ano))
        # CADASTRO DE PROFESSOR
        elif tipo == "professor":

            cursor.execute("""
            INSERT INTO usuarios (nome, cpf, email, senha, tipo)
            VALUES (?, ?, ?, ?, ?)
            """,(nome, cpf, email, senha, tipo))

            professor_id = cursor.lastrowid

            materias = request.form.getlist("materias")

            if materias:
                for materia in materias:
                    # Busca o ID da matéria no banco
                    cursor.execute("SELECT id FROM materias WHERE nome=?", (materia,))
                    resultado = cursor.fetchone()

                    if resultado:
                        materia_id = resultado[0]
                        
                        # Pega a lista de anos ESPECÍFICA para esta matéria selecionada
                        anos_da_materia = request.form.getlist(f"anos_{materia}")
                        
                        for ano in anos_da_materia:
                            cursor.execute("""
                            INSERT INTO professor_materias
                            (professor_id, materia_id, ano_letivo)
                            VALUES (?, ?, ?)
                            """,(professor_id, materia_id, ano))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("cadastro.html")


# DASHBOARDS

@app.route('/dashboard_aluno')
def dashboard_aluno():

    conn = conectar()
    cursor = conn.cursor()

    # -----------------------------------------
    # pegar aluno (depois será o aluno logado)
    # -----------------------------------------
    cursor.execute("""
    SELECT id, nome, email, ano_letivo
    FROM usuarios
    WHERE tipo='aluno'
    LIMIT 1
    """)

    aluno = cursor.fetchone()

    if not aluno:
        return "Aluno não encontrado"

    aluno_id = aluno[0]
    nome = aluno[1]
    email = aluno[2]
    ano_letivo = aluno[3]

    # -----------------------------------------
    # total de matérias
    # -----------------------------------------
    cursor.execute("SELECT COUNT(*) FROM materias")
    total_materias = cursor.fetchone()[0]

    # -----------------------------------------
    # buscar todas as notas do aluno
    # -----------------------------------------
    cursor.execute("""
    SELECT ab1_1, ab1_2, ab2_1, ab2_2
    FROM notas
    WHERE aluno_id=?
    """,(aluno_id,))

    notas = cursor.fetchall()

    notas_validas = []

    for linha in notas:
        for n in linha:
            if n is not None:
                notas_validas.append(n)

    # -----------------------------------------
    # calcular IRA
    # -----------------------------------------
    if notas_validas:
        ira = round(sum(notas_validas) / len(notas_validas),1)
    else:
        ira = "-"

    conn.close()

    foto = "/static/img/aluno.jpg"

    return render_template(
        "dashboard_aluno.html",
        nome=nome,
        email=email,
        foto=foto,
        total_materias=total_materias,
        ano_letivo=ano_letivo,
        ira=ira
    )


@app.route('/dashboard_professor')
def dashboard_professor():

    conn = conectar()
    cursor = conn.cursor()

    # pega professor (temporário)
    cursor.execute("""
    SELECT id, nome, email
    FROM usuarios
    WHERE tipo='professor'
    LIMIT 1
    """)

    professor = cursor.fetchone()

    professor_id = professor[0]
    nome = professor[1]
    email = professor[2]

    # contar turmas
    cursor.execute("""
    SELECT COUNT(*)
    FROM professor_materias
    WHERE professor_id=?
    """,(professor_id,))

    total_turmas = cursor.fetchone()[0]

    # contar matérias
    cursor.execute("""
    SELECT COUNT(DISTINCT materia_id)
    FROM professor_materias
    WHERE professor_id=?
    """,(professor_id,))

    total_materias = cursor.fetchone()[0]

    # contar alunos
    cursor.execute("""
    SELECT COUNT(*)
    FROM usuarios
    WHERE tipo='aluno'
    """)

    total_alunos = cursor.fetchone()[0]

    conn.close()

    # foto padrão
    foto = "/static/img/professor.png"

    return render_template(
        "dashboard_professor.html",
        nome=nome,
        email=email,
        foto=foto,
        total_turmas=total_turmas,
        total_alunos=total_alunos,
        total_materias=total_materias
    )


# PÁGINAS DO SISTEMA

# NOTAS

from flask import request, jsonify

@app.route("/atualizar_nota", methods=["POST"])
def atualizar_nota():

    aluno_id = request.form.get("aluno_id")
    materia_nome = request.form.get("materia")
    ano = request.form.get("ano")
    campo = request.form.get("campo")  # ab1_1, ab1_2...
    valor = request.form.get("valor")
    valor = float(valor) if valor and valor != "-" else None

    try:
        conn = conectar()
        cursor = conn.cursor()

        # pegar id da matéria
        cursor.execute("""
        SELECT id FROM materias WHERE nome=?
        """, (materia_nome,))
        materia = cursor.fetchone()

        if not materia:
            return jsonify({"status": "erro", "msg": "Matéria não encontrada"})

        materia_id = materia[0]

        # verifica se já existe registro
        cursor.execute("""
        SELECT id FROM notas
        WHERE aluno_id=? AND materia_id=? AND ano_letivo=?
        """, (aluno_id, materia_id, ano))

        existe = cursor.fetchone()

        if existe:
            # UPDATE dinâmico
            query = f"""
            UPDATE notas
            SET {campo} = ?
            WHERE aluno_id=? AND materia_id=? AND ano_letivo=?
            """
            cursor.execute(query, (valor, aluno_id, materia_id, ano))

        else:
            # INSERT se não existir ainda
            cursor.execute(f"""
            INSERT INTO notas (aluno_id, materia_id, ano_letivo, {campo})
            VALUES (?, ?, ?, ?)
            """, (aluno_id, materia_id, ano, valor))

        conn.commit()
        conn.close()

        return jsonify({"status": "sucesso"})

    except Exception as e:
        print("Erro:", e)
        return jsonify({"status": "erro"})

@app.route("/notas")
def notas():
    # Conecta ao banco
    conn = conectar()
    cursor = conn.cursor()

    # 1) Pegar o professor logado
    cursor.execute("SELECT id FROM usuarios WHERE tipo='professor' LIMIT 1")
    professor = cursor.fetchone()
    if not professor:
        return "Nenhum professor encontrado no sistema"
    professor_id = professor[0]

    # 2) Pegar matérias e anos
    cursor.execute("""
    SELECT m.nome, pm.ano_letivo
    FROM professor_materias pm
    JOIN materias m ON pm.materia_id = m.id
    WHERE pm.professor_id = ?
    """, (professor_id,))
    turmas_professor = cursor.fetchall()

    turmas = []

    # 3) Buscar alunos e notas
    for materia_nome, ano in turmas_professor:
        cursor.execute("SELECT id, nome, email FROM usuarios WHERE tipo='aluno' AND ano_letivo=?", (ano,))
        alunos = cursor.fetchall()
        
        alunos_formatados = []
        for aluno in alunos:
            aluno_id = aluno[0]
            cursor.execute("""
            SELECT n.ab1_1, n.ab1_2, n.ab2_1, n.ab2_2
            FROM notas n
            JOIN materias m ON n.materia_id = m.id
            WHERE n.aluno_id=? AND m.nome=? AND n.ano_letivo=?
            """,(aluno_id, materia_nome, ano))
            notas = cursor.fetchone()

            if notas:
                ab1_1, ab1_2, ab2_1, ab2_2 = notas
            else:
                ab1_1 = ab1_2 = ab2_1 = ab2_2 = "-"

            alunos_formatados.append({
                "id": aluno_id,
                "nome": aluno[1],
                "email": aluno[2],
                "ab1_1": ab1_1, "ab1_2": ab1_2, "ab2_1": ab2_1, "ab2_2": ab2_2
            })

        turmas.append({
            "materia": materia_nome,
            "ano": ano,
            "alunos": alunos_formatados
        })

    conn.close()

    # A GRANDE DIFERENÇA AQUI: Renderiza o seu arquivo de edição!
    return render_template("notas.html", turmas=turmas)

@app.route("/minhas_notas")
def minhas_notas():

    # verifica se aluno está logado
    if "usuario_id" not in session:
        return redirect("/login")

    aluno_id = session["usuario_id"]

    conn = conectar()
    cursor = conn.cursor()

    # ------------------------------------------------
    # descobrir o ano do aluno
    # ------------------------------------------------

    cursor.execute("""
    SELECT ano_letivo
    FROM usuarios
    WHERE id=?
    """,(aluno_id,))

    resultado = cursor.fetchone()

    if not resultado:
        return "Aluno não encontrado"

    ano = resultado[0]

    # ------------------------------------------------
    # pegar todas as matérias do ano
    # ------------------------------------------------

    cursor.execute("""
    SELECT id, nome
    FROM materias
    """)

    materias_db = cursor.fetchall()

    materias = []

    # ------------------------------------------------
    # para cada matéria buscar notas do aluno
    # ------------------------------------------------

    for materia in materias_db:

        materia_id = materia[0]
        materia_nome = materia[1]

        cursor.execute("""
        SELECT ab1_1, ab1_2, ab2_1, ab2_2
        FROM notas
        WHERE aluno_id=? AND materia_id=? AND ano_letivo=?
        """,(aluno_id, materia_id, ano))

        notas = cursor.fetchone()

        if notas:
            ab1_1, ab1_2, ab2_1, ab2_2 = notas
        else:
            ab1_1 = ab1_2 = ab2_1 = ab2_2 = "-"

        materias.append({

            "nome": materia_nome,
            "ab1_1": ab1_1,
            "ab1_2": ab1_2,
            "ab2_1": ab2_1,
            "ab2_2": ab2_2

        })

    conn.close()

    return render_template("minhas_notas.html", materias=materias)

@app.route('/materiais')
def materiais():
    return render_template("materiais.html")

@app.route('/calendario')
def calendario():
    return render_template("calendario.html")

@app.route('/presenca')
def presenca():
    return render_template("presenca.html")


@app.route('/feedback')
def feedback():
    return render_template("feedback.html")


@app.route('/desempenho')
def desempenho():
    conn = conectar()
    cursor = conn.cursor()

    # 1. Pegar anos letivos (que funcionam como turmas no seu banco)
    cursor.execute("SELECT DISTINCT ano_letivo FROM usuarios WHERE tipo='aluno'")
    turmas = [str(t[0]) for t in cursor.fetchall() if t[0] is not None]

    # 2. Pegar matérias
    cursor.execute("SELECT nome FROM materias")
    materias = [m[0] for m in cursor.fetchall()]

    dados = {}

    for turma in turmas:
        dados[turma] = {}
        for materia in materias:
            # Busca notas joinando usuarios(alunos) e materias
            cursor.execute("""
                SELECT u.nome, n.ab1_1, n.ab1_2, n.ab2_1, n.ab2_2
                FROM notas n
                JOIN usuarios u ON n.aluno_id = u.id
                JOIN materias m ON n.materia_id = m.id
                WHERE u.ano_letivo = ? AND m.nome = ?
            """, (turma, materia))
            
            resultados = cursor.fetchall()
            alunos_dict = {}

            for r in resultados:
                nome = r[0]
                # Converte None para 0 para o gráfico não quebrar
                notas = [r[1] or 0, r[2] or 0, r[3] or 0, r[4] or 0]
                alunos_dict[nome] = notas

            # Só adiciona se houver alunos com nota nessa matéria/turma
            if alunos_dict:
                dados[turma][materia] = alunos_dict
            else:
                # Evita erro de undefined no JS do HTML
                dados[turma][materia] = {}

    conn.close()
    return render_template("desempenho.html", turmas=turmas, materias=materias, dados=dados)

@app.route('/meu_desempenho')
def meu_desempenho():
    # Verifica se o aluno está logado (usando a chave definida no login)
    aluno_id = session.get("usuario_id")
    if not aluno_id:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    # 1. Pegar dados básicos do aluno
    cursor.execute("SELECT nome, ano_letivo FROM usuarios WHERE id = ?", (aluno_id,))
    aluno = cursor.fetchone()
    
    if not aluno:
        return "Aluno não encontrado"
    
    nome_aluno = aluno[0]
    ano_letivo = aluno[1]

    # 2. Buscar notas por matéria
    # Fazemos um JOIN com a tabela de materias para pegar os nomes
    cursor.execute("""
        SELECT m.nome, n.ab1_1, n.ab1_2, n.ab2_1, n.ab2_2
        FROM notas n
        JOIN materias m ON n.materia_id = m.id
        WHERE n.aluno_id = ? AND n.ano_letivo = ?
    """, (aluno_id, ano_letivo))

    resultados = cursor.fetchall()
    
    dados_notas = {}
    for r in resultados:
        materia_nome = r[0]
        # Converte None para 0 para o gráfico
        notas = [r[1] or 0, r[2] or 0, r[3] or 0, r[4] or 0]
        dados_notas[materia_nome] = notas

    conn.close()

    return render_template(
        "meu_desempenho.html",
        nome=nome_aluno,
        ano=ano_letivo,
        dados_notas=dados_notas
    )

# OUTRAS FUNCIONALIDADES

import os

@app.route("/editar_foto", methods=["GET","POST"])
def editar_foto():

    if request.method == "POST":

        foto = request.files["foto"]

        pasta = "static/img"

        # garante que a pasta existe
        os.makedirs(pasta, exist_ok=True)

        aluno_id = session.get("aluno_id")
        professor_id = session.get("professor_id")

        # define nome da foto dependendo do usuário
        if aluno_id:
            nome_arquivo = f"aluno_{aluno_id}.jpg"

        elif professor_id:
            nome_arquivo = f"professor_{professor_id}.jpg"

        else:
            nome_arquivo = "usuario.jpg"

        caminho = os.path.join(pasta, nome_arquivo)

        foto.save(caminho)

        return redirect(request.referrer)

    return render_template("editar_foto.html")

@app.route("/upload_foto", methods=["POST"])
def upload_foto():

    foto = request.files["foto"]

    caminho = "static/img/professor.jpg"

    foto.save(caminho)

    return redirect("/dashboard_professor")

@app.route("/alterar_senha", methods=["GET","POST"])
def alterar_senha():

    if request.method == "POST":

        senha_atual = request.form["senha_atual"]
        nova_senha = request.form["nova_senha"]

        conn = conectar()
        cursor = conn.cursor()

        # pega professor (temporário)
        cursor.execute("""
        SELECT id, senha
        FROM usuarios
        WHERE tipo='professor'
        LIMIT 1
        """)

        professor = cursor.fetchone()

        professor_id = professor[0]
        senha_banco = professor[1]

        # verifica senha atual
        if senha_atual != senha_banco:
            return "Senha atual incorreta"

        # atualiza senha
        cursor.execute("""
        UPDATE usuarios
        SET senha=?
        WHERE id=?
        """,(nova_senha, professor_id))

        conn.commit()
        conn.close()

        return redirect("/dashboard_professor")

    return render_template("alterar_senha.html")

if __name__ == '__main__':
    app.run(debug=True)