import sqlite3

def criar_banco():
    # Conecta ao arquivo do banco. Se não existir, ele cria um novo.
    conn = sqlite3.connect("escola.db")
    cursor = conn.cursor()

    print("Iniciando a criação das tabelas...")

    # 1. TABELA DE USUÁRIOS
    # Armazena tanto alunos quanto professores. 
    # O campo 'tipo' define o que o usuário é.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cpf TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        tipo TEXT NOT NULL,      -- Define se é 'aluno' ou 'professor'
        ano_letivo INTEGER        -- Usado apenas para alunos (ex: 1, 2, 3)
    )
    """)

    # 2. TABELA DE MATÉRIAS
    # Lista simples das disciplinas oferecidas pela escola.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL
    )
    """)

    # 3. RELAÇÃO PROFESSOR-MATÉRIA
    # Crucial para saber qual professor dá qual aula e para qual ano/turma.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS professor_materias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        professor_id INTEGER,
        materia_id INTEGER,
        ano_letivo INTEGER,
        FOREIGN KEY (professor_id) REFERENCES usuarios(id),
        FOREIGN KEY (materia_id) REFERENCES materias(id)
    )
    """)

    # 4. TABELA DE MATERIAIS
    # Guarda os arquivos ou links que os professores postam para os alunos.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materiais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        categoria TEXT,           -- Ex: 'Apostila', 'Slide', 'Vídeo'
        arquivo TEXT,             -- Nome do arquivo salvo na pasta static/uploads
        link_externo TEXT,        -- Caso o professor poste um link do YouTube/Drive
        materia_id INTEGER,
        ano_letivo INTEGER,       -- Para qual série esse material se destina
        professor_id INTEGER,
        data_postagem DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (materia_id) REFERENCES materias(id),
        FOREIGN KEY (professor_id) REFERENCES usuarios(id)
    )
    """)

    # 5. TABELA DE FEEDBACKS
    # Sistema de mensagens diretas entre aluno e professor.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedbacks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        remetente_id INTEGER,     -- Quem enviou
        destinatario_id INTEGER,  -- Quem recebe
        mensagem TEXT NOT NULL,
        data_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (remetente_id) REFERENCES usuarios(id),
        FOREIGN KEY (destinatario_id) REFERENCES usuarios(id)
    )
    """)

    # 6. TABELA DE PRESENÇA (Nova!)
    # Registra a frequência diária dos alunos por disciplina.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS presenca (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        materia_id INTEGER,
        data TEXT NOT NULL,       -- Formato YYYY-MM-DD
        status TEXT NOT NULL,     -- 'Presente' ou 'Faltou'
        FOREIGN KEY (aluno_id) REFERENCES usuarios(id),
        FOREIGN KEY (materia_id) REFERENCES materias(id)
    )
    """)

    # 7. TABELA DE NOTAS
    # Armazena as avaliações AB1 e AB2 divididas em duas partes cada.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        materia_id INTEGER,
        ano_letivo INTEGER,
        ab1_1 REAL DEFAULT 0,
        ab1_2 REAL DEFAULT 0,
        ab2_1 REAL DEFAULT 0,
        ab2_2 REAL DEFAULT 0,
        FOREIGN KEY (aluno_id) REFERENCES usuarios(id),
        FOREIGN KEY (materia_id) REFERENCES materias(id)
    )
    """)

    # --- INSERÇÃO DE DADOS PADRÃO ---

    # Lista de matérias para popular o sistema inicialmente
    materias_padrao = [
        "Matematica", "Lingua_Portuguesa", "Geografia", 
        "Historia", "Ciencia", "Ingles", "Artes", "Ensino_Religioso"
    ]
    
    # Verifica se já existem matérias para não duplicar toda vez que rodar
    cursor.execute("SELECT COUNT(*) FROM materias")
    if cursor.fetchone()[0] == 0:
        for m in materias_padrao:
            cursor.execute("INSERT INTO materias (nome) VALUES (?)", (m,))
        print("Materiais padrão inseridos.")

    conn.commit()
    conn.close()
    print("✅ Banco de dados 'escola.db' reiniciado e atualizado com sucesso!")

if __name__ == "__main__":
    criar_banco()