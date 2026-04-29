import sqlite3

def ver_tabela(nome_tabela):
    conn = sqlite3.connect("escola.db")
    cursor = conn.cursor()

    print(f"\nTABELA: {nome_tabela.upper()}")
    print("-" * 40)

    try:
        cursor.execute(f"SELECT * FROM {nome_tabela}")
        dados = cursor.fetchall()

        if not dados:
            print("⚠️ Nenhum registro encontrado.")
        else:
            for linha in dados:
                print(linha)

    except Exception as e:
        print("Erro:", e)

    conn.close()


# 🔥 visualizar várias tabelas
ver_tabela("usuarios")
ver_tabela("materias")
ver_tabela("notas")
ver_tabela("professor_materias")
ver_tabela("feedbacks")
ver_tabela("presenca")