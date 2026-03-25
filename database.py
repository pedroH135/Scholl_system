import sqlite3

def criar_banco():

    conn = sqlite3.connect("escola.db")
    cursor = conn.cursor()

    # usuários
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        cpf TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT,
        ano_letivo INTEGER
    )
    """)

    # materias
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT
    )
    """)

    # relação professor-materia
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

    # notas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        materia_id INTEGER,
        ano_letivo INTEGER,
        ab1_1 REAL,
        ab1_2 REAL,
        ab2_1 REAL,
        ab2_2 REAL,
        FOREIGN KEY (aluno_id) REFERENCES usuarios(id),
        FOREIGN KEY (materia_id) REFERENCES materias(id)
    )
    """)

    # inserir materias padrão
    materias = [
        "Matematica",
        "Lingua_Portuguesa",
        "Geografia",
        "Historia",
        "Ciencia",
        "Ingles",
        "Artes",
        "Ensino_Religioso"
    ]

    for m in materias:
        cursor.execute("INSERT INTO materias (nome) VALUES (?)", (m,))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    criar_banco()