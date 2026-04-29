from models.usuario import Usuario

class Professor(Usuario):
    def __init__(self, id, nome, email):
        super().__init__(id, nome, email, "professor")

    def get_dashboard_url(self):
        return "/dashboard_professor"
    
    def obter_dados_feedback(self, cursor):
        # Busca alunos que pertencem aos anos que este professor leciona
        cursor.execute("""
            SELECT DISTINCT u.id, u.nome, u.ano_letivo
            FROM usuarios u
            JOIN professor_materias pm ON u.ano_letivo = pm.ano_letivo
            WHERE pm.professor_id = ? AND u.tipo = 'aluno'
        """, (self.id,))
        alunos = cursor.fetchall()

        # Feedbacks sobre a didática (enviados por alunos)
        cursor.execute("""
            SELECT u.nome, f.mensagem, f.data_envio
            FROM feedbacks f
            JOIN usuarios u ON f.remetente_id = u.id
            WHERE f.destinatario_id = ?
        """, (self.id,))
        recebidos = cursor.fetchall()

        return {
            "template": "feedback_professor.html",
            "contexto": {"alunos": alunos, "recebidos": recebidos}
        }
    
    def obter_dados_materiais(self, cursor):
        # 1. Busca histórico do que ele enviou
        cursor.execute("""
            SELECT m.titulo, m.categoria, m.arquivo, m.link_externo, m.ano_letivo, mat.nome, m.data_postagem
            FROM materiais m
            JOIN materias mat ON m.materia_id = mat.id
            WHERE m.professor_id = ?
            ORDER BY m.data_postagem DESC
        """, (self.id,))
        arquivos = cursor.fetchall()

        # 2. Busca as turmas que ele leciona (para preencher o <select> do formulário)
        cursor.execute("""
            SELECT pm.materia_id, mat.nome, pm.ano_letivo
            FROM professor_materias pm
            JOIN materias mat ON pm.materia_id = mat.id
            WHERE pm.professor_id = ?
        """, (self.id,))
        turmas = cursor.fetchall()

        return {
            "template": "materiais_professor.html",
            "contexto": {"arquivos": arquivos, "turmas": turmas}
        }
    
    def obter_dados_presenca(self, cursor):
        # 1. Busca todos os alunos para o Select do formulário
        cursor.execute("""
            SELECT id, nome, ano_letivo 
            FROM usuarios 
            WHERE tipo = 'aluno' 
            ORDER BY ano_letivo, nome
        """)
        alunos = cursor.fetchall()

        # 2. Busca as turmas que o professor ensina para o Select
        cursor.execute("""
            SELECT pm.materia_id, mat.nome, pm.ano_letivo
            FROM professor_materias pm
            JOIN materias mat ON pm.materia_id = mat.id
            WHERE pm.professor_id = ?
        """, (self.id,))
        turmas = cursor.fetchall()

        # 3. Busca os últimos lançamentos de presença feitos nas disciplinas deste professor
        cursor.execute("""
            SELECT a.nome, m.nome, p.data, p.status
            FROM presenca p
            JOIN usuarios a ON p.aluno_id = a.id
            JOIN materias m ON p.materia_id = m.id
            JOIN professor_materias pm ON pm.materia_id = m.id AND pm.ano_letivo = a.ano_letivo
            WHERE pm.professor_id = ?
            ORDER BY p.id DESC LIMIT 15
        """, (self.id,))
        historico = cursor.fetchall()

        return {
            "template": "presenca.html",
            "contexto": {"alunos": alunos, "turmas": turmas, "historico": historico}
        }