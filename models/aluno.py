from models.usuario import Usuario

class Aluno(Usuario):
    def __init__(self, id, nome, email, ano):
        super().__init__(id, nome, email, "aluno")
        self.ano = ano

    def calcular_ira(self, notas):
        notas_validas = [n for n in notas if n is not None]

        if notas_validas:
            return round(sum(notas_validas) / len(notas_validas), 1)
        return "-"
    
    def get_dashboard_url(self):
        return "/dashboard_aluno"
    
    def obter_dados_feedback(self, cursor):
        # Busca professores que dão aula no ano deste aluno
        cursor.execute("""
            SELECT DISTINCT u.id, u.nome 
            FROM usuarios u
            JOIN professor_materias pm ON u.id = pm.professor_id
            WHERE pm.ano_letivo = ?
        """, (self.ano,))
        professores = cursor.fetchall()

        # Feedbacks que o aluno recebeu
        cursor.execute("""
            SELECT u.nome, f.mensagem, f.data_envio
            FROM feedbacks f
            JOIN usuarios u ON f.remetente_id = u.id
            WHERE f.destinatario_id = ?
        """, (self.id,))
        recebidos = cursor.fetchall()
        
        return {
            "template": "feedback_aluno.html",
            "contexto": {"professores": professores, "recebidos": recebidos}
        }
    
    def obter_dados_materiais(self, cursor):
        # Aluno vê materiais do seu ano letivo, trazendo o nome do professor e da matéria
        cursor.execute("""
            SELECT m.titulo, m.categoria, m.arquivo, m.link_externo, m.data_postagem,
                   u.nome as professor_nome, mat.nome as materia_nome
            FROM materiais m
            JOIN usuarios u ON m.professor_id = u.id
            JOIN materias mat ON m.materia_id = mat.id
            WHERE m.ano_letivo = ?
            ORDER BY m.data_postagem DESC
        """, (self.ano,))
        arquivos = cursor.fetchall()
        
        return {
            "template": "materiais_aluno.html",
            "contexto": {"arquivos": arquivos}
        }