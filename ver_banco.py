import sqlite3

conn = sqlite3.connect("escola.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM usuarios")

dados = cursor.fetchall()

for usuario in dados:
    print(usuario)

conn.close()