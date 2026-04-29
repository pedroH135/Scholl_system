from flask import Flask, render_template, request, redirect, session
import sqlite3
from models.aluno import Aluno
from models.professor import Professor
from models.notas import Nota
from models.visualizador_desempenho import DesempenhoAluno, DesempenhoProfessor
import os
import glob

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

        # Captura os dados preenchidos no formulário
        cpf = request.form["cpf"]
        senha = request.form["senha"]

        conn = conectar()
        cursor = conn.cursor()

        # Busca no banco de dados se existe um usuário com este CPF e senha
        cursor.execute("""
        SELECT * FROM usuarios
        WHERE cpf=? AND senha=?
        """,(cpf,senha))

        usuario_db = cursor.fetchone()

        conn.close()

        # Verifica se o usuário foi encontrado no banco
        # Verifica se o usuário foi encontrado no banco
        if usuario_db:
            
            # 1. Salva na sessão
            session["usuario_id"] = usuario_db[0]
            session["tipo"] = usuario_db[5]

            # 2. INSTANCIA O OBJETO (Transforma os dados do banco em POO)
            if usuario_db[5] == "aluno":
                usuario_logado = Aluno(
                    usuario_db[0],  # id
                    usuario_db[1],  # nome
                    usuario_db[3],  # email
                    usuario_db[6]   # ano_letivo
                )
            elif usuario_db[5] == "professor":
                usuario_logado = Professor(
                    usuario_db[0],  # id
                    usuario_db[1],  # nome
                    usuario_db[3]   # email
                )

            # 3. POLIMORFISMO EM AÇÃO
            # Agora o Python sabe quem é usuario_logado e vai chamar a URL certa!
            return redirect(usuario_logado.get_dashboard_url())

        else:
            return "CPF ou senha incorretos"

    # Se o método for GET, apenas renderiza a página de login
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

    # --- NOVIDADE: Busca a foto real na pasta ---
    padrao = f"static/img/aluno_{aluno_id}.*"
    fotos_encontradas = glob.glob(padrao)
    
    if fotos_encontradas:
        # Pega o caminho encontrado e ajusta para o navegador entender
        foto = "/" + fotos_encontradas[0].replace('\\', '/') 
    else:
        foto = "/static/img/aluno.jpg" # Foto padrão caso não tenha foto personalizada
    # --------------------------------------------

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

    # --- NOVIDADE: Busca a foto real na pasta ---
    padrao = f"static/img/professor_{professor_id}.*"
    fotos_encontradas = glob.glob(padrao)
    
    if fotos_encontradas:
        foto = "/" + fotos_encontradas[0].replace('\\', '/')
    else:
        foto = "/static/img/professor.png" # Foto padrão
    # --------------------------------------------

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
    campo = request.form.get("campo")
    valor = request.form.get("valor")
    valor = float(valor) if valor and valor != "-" else None

    nota = Nota()

    try:
        nota.atualizar(campo, valor)
    except ValueError as e:
        return jsonify({"status": "erro", "msg": str(e)})

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
            valor_validado = nota.get_valor(campo)
            query = f"""
            UPDATE notas
            SET {campo} = ?
            WHERE aluno_id=? AND materia_id=? AND ano_letivo=?
            """
            cursor.execute(query, (valor_validado, aluno_id, materia_id, ano))

        else:
            # INSERT se não existir ainda
            valor_validado = nota.get_valor(campo)

            cursor.execute(f"""
            INSERT INTO notas (aluno_id, materia_id, ano_letivo, {campo})
            VALUES (?, ?, ?, ?)
            """, (aluno_id, materia_id, ano, valor_validado))

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

@app.route("/materiais", methods=["GET", "POST"])
def materiais():
    if "usuario_id" not in session:
        return redirect("/")

    conn = conectar()
    cursor = conn.cursor()
    
    usuario_id = session["usuario_id"]
    cursor.execute("SELECT * FROM usuarios WHERE id=?", (usuario_id,))
    u_db = cursor.fetchone()
    
    # Instancia o objeto polimórfico
    if u_db[5] == "aluno":
        usuario_logado = Aluno(u_db[0], u_db[1], u_db[3], u_db[6])
    else:
        usuario_logado = Professor(u_db[0], u_db[1], u_db[3])

    # Se for POST (Professor enviando material)
    if request.method == "POST" and u_db[5] == "professor":
        titulo = request.form["titulo"]
        categoria = request.form["categoria"]
        link_externo = request.form.get("link_externo", "")
        
        # O value do select trará "materia_id-ano_letivo" juntos
        turma_selecionada = request.form["turma_selecionada"] 
        materia_id, ano_letivo = turma_selecionada.split("-")

        arquivo = request.files.get("arquivo")
        nome_arquivo = ""

        # Salva o arquivo na pasta se o professor tiver enviado um
        if arquivo and arquivo.filename:
            pasta = "static/uploads"
            os.makedirs(pasta, exist_ok=True)
            nome_arquivo = f"prof_{usuario_logado.id}_{arquivo.filename.replace(' ', '_')}"
            caminho_completo = os.path.join(pasta, nome_arquivo)
            arquivo.save(caminho_completo)

        # Salva no seu banco de dados
        cursor.execute("""
            INSERT INTO materiais (titulo, categoria, arquivo, link_externo, materia_id, ano_letivo, professor_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (titulo, categoria, nome_arquivo, link_externo, materia_id, ano_letivo, usuario_logado.id))
        conn.commit()
        return redirect("/materiais")

    # POLIMORFISMO: Pega os dados e renderiza
    dados = usuario_logado.obter_dados_materiais(cursor)
    conn.close()

    return render_template(dados["template"], **dados["contexto"])

@app.route('/calendario')
def calendario():
    return render_template("calendario.html")

@app.route("/presenca", methods=["GET", "POST"])
def presenca():
    # Iniciamos a conexão primeiro para poder buscar o usuário
    conn = conectar()
    cursor = conn.cursor()

    # 1. Pegar usuário (Simulação de sessão buscando o primeiro professor do banco)
    cursor.execute("SELECT id, nome, email FROM usuarios WHERE tipo='professor' LIMIT 1")
    dados_prof = cursor.fetchone()

    if not dados_prof:
        return "Erro: Nenhum professor encontrado no sistema para simular o acesso."

    # Criamos o objeto Professor usando os dados do banco
    usuario = Professor(id=dados_prof[0], nome=dados_prof[1], email=dados_prof[2])

    # 2. BLOQUEIO: Se não for professor, não entra
    if not usuario.eh_professor():
        conn.close()
        return redirect(usuario.get_dashboard_url())

    # 3. Se for POST (Professor salvando presença)
    if request.method == "POST":
        aluno_id = request.form["aluno_id"]
        # O campo turma_selecionada vem como "id-ano" (ex: "1-9")
        turma_info = request.form["turma_selecionada"].split("-")
        materia_id = turma_info[0]
        data = request.form["data"]
        status = request.form["status"]

        cursor.execute("""
            INSERT INTO presencas (aluno_id, materia_id, data, status)
            VALUES (?, ?, ?, ?)
        """, (aluno_id, materia_id, data, status))
        
        conn.commit()
        conn.close()
        return redirect("/presenca")

    # 4. Se for GET (Mostrar página de registro do Professor)
    # A função obter_dados_presenca já está definida dentro da sua classe Professor
    dados = usuario.obter_dados_presenca(cursor)
    
    # Extraímos os dados e fechamos a conexão antes de renderizar
    template = dados["template"]
    contexto = dados["contexto"]
    conn.close()

    return render_template(template, **contexto)


@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if "usuario_id" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()
    
    # 1. Recupera e instancia o usuário (Lógica que você já tem no Login)
    usuario_id = session["usuario_id"]
    cursor.execute("SELECT * FROM usuarios WHERE id=?", (usuario_id,))
    u_db = cursor.fetchone()
    
    if u_db[5] == "aluno":
        usuario_logado = Aluno(u_db[0], u_db[1], u_db[3], u_db[6])
    else:
        usuario_logado = Professor(u_db[0], u_db[1], u_db[3])

    # 2. Se for envio de mensagem (POST)
    if request.method == "POST":
        # Pega o ID do destinatário (seja professor_id ou aluno_id do formulário)
        destinatario_id = request.form.get("professor_id") or request.form.get("aluno_id")
        mensagem = request.form["mensagem"]
        
        cursor.execute("""
            INSERT INTO feedbacks (remetente_id, destinatario_id, mensagem) 
            VALUES (?, ?, ?)
        """, (usuario_logado.id, destinatario_id, mensagem))
        conn.commit()
        return redirect("/feedback")

    # 3. POLIMORFISMO: Uma única chamada para buscar os dados
    # O Python decidirá sozinho se chama a versão do Aluno ou do Professor
    dados = usuario_logado.obter_dados_feedback(cursor)
    
    conn.close()

    # Renderiza o template correto com o contexto correto
    return render_template(dados["template"], **dados["contexto"])

@app.route("/desempenho")
def desempenho():
    conn = conectar()
    cursor = conn.cursor()

    # -----------------------------
    # Professor (objeto)
    # -----------------------------
    cursor.execute("SELECT id, nome, email FROM usuarios WHERE tipo='professor' LIMIT 1")
    prof_db = cursor.fetchone()
    
    if not prof_db:
        return "Nenhum professor encontrado no sistema."

    prof_obj = Professor(prof_db[0], prof_db[1], prof_db[2])

    # -----------------------------
    # Usa classe abstrata (POO)
    # -----------------------------
    visualizador = DesempenhoProfessor(prof_obj)
    dados_brutos = visualizador.consultar_dados(cursor)

    # -----------------------------
    # Turmas e matérias (ESSENCIAL)
    # -----------------------------
    cursor.execute("SELECT DISTINCT ano_letivo FROM usuarios WHERE tipo='aluno'")
    turmas = [str(t[0]) for t in cursor.fetchall() if t[0] is not None]

    cursor.execute("SELECT nome FROM materias")
    materias = [m[0] for m in cursor.fetchall()]

    # -----------------------------
    # Estrutura dos dados
    # -----------------------------
    dados_formatados = {}

    if dados_brutos:
        for aluno, ano, materia, ab1_1, ab1_2, ab2_1, ab2_2 in dados_brutos:

            turma = str(ano)

            if turma not in dados_formatados:
                dados_formatados[turma] = {}

            if materia not in dados_formatados[turma]:
                dados_formatados[turma][materia] = {}

            notas = [n if n is not None else 0 for n in (ab1_1, ab1_2, ab2_1, ab2_2)]

            dados_formatados[turma][materia][aluno] = notas

    conn.close()

    return render_template(
        "desempenho.html",
        dados=dados_formatados,
        turmas=turmas,
        materias=materias
    )

@app.route("/meu_desempenho")
def meu_desempenho():

    aluno_id = session.get("usuario_id")
    if not aluno_id:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    # 🔥 CORREÇÃO: agora pega o ano_letivo também
    cursor.execute("""
        SELECT id, nome, email, ano_letivo
        FROM usuarios
        WHERE id=?
    """, (aluno_id,))
    
    aluno_db = cursor.fetchone()

    if not aluno_db:
        return "Aluno não encontrado"

    # 🔥 CORREÇÃO: passa o ano corretamente
    aluno_obj = Aluno(
        aluno_db[0],  # id
        aluno_db[1],  # nome
        aluno_db[2],  # email
        aluno_db[3]   # ano
    )

    # 🔥 POLIMORFISMO
    visualizador = DesempenhoAluno(aluno_obj)
    dados_brutos = visualizador.consultar_dados(cursor)

    dados_formatados = {}

    for materia, ab1_1, ab1_2, ab2_1, ab2_2 in dados_brutos:
        notas = [n if n is not None else 0 for n in (ab1_1, ab1_2, ab2_1, ab2_2)]
        dados_formatados[materia] = notas

    conn.close()

    return render_template(
        "meu_desempenho.html",
        dados_notas=dados_formatados,
        nome=aluno_obj.nome,   # 🔥 necessário para o HTML
        ano=aluno_obj.ano      # 🔥 necessário para o HTML
    )

# OUTRAS FUNCIONALIDADES

import os

@app.route("/editar_foto", methods=["GET","POST"])
def editar_foto():
    if request.method == "POST":
        foto = request.files["foto"]
        
        if foto.filename == '':
            return "Nenhum arquivo selecionado"

        pasta = "static/img"
        os.makedirs(pasta, exist_ok=True)

        # Pega as informações de quem está logado
        usuario_id = session.get("usuario_id")
        tipo = session.get("tipo") # 'aluno' ou 'professor'

        if not usuario_id:
            return redirect("/login")

        # Pega a extensão original do arquivo (ex: .png, .jpg)
        extensao = os.path.splitext(foto.filename)[1]

        # Nomeia o arquivo corretamente: ex "aluno_1.jpg" ou "professor_2.png"
        nome_arquivo = f"{tipo}_{usuario_id}{extensao}"
        caminho = os.path.join(pasta, nome_arquivo)

        foto.save(caminho)

        return redirect(f"/dashboard_{tipo}")

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