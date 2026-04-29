from abc import ABC, abstractmethod

# Ao herdar de ABC, o Python proíbe que você faça "v = VisualizadorDesempenho()"
class VisualizadorDesempenho(ABC):
    def __init__(self, usuario):
        self.usuario = usuario

    @abstractmethod
    def consultar_dados(self, cursor):
        """
        Este é um MÉTODO ABSTRATO. 
        Ele não tem código aqui, serve apenas como uma regra:
        'Toda subclasse é OBRIGADA a implementar este método'.
        """
        pass

class DesempenhoAluno(VisualizadorDesempenho):
    def consultar_dados(self, cursor):
        cursor.execute("""
            SELECT m.nome, n.ab1_1, n.ab1_2, n.ab2_1, n.ab2_2
            FROM notas n
            JOIN materias m ON n.materia_id = m.id
            WHERE n.aluno_id = ?
        """, (self.usuario.id,))
        return cursor.fetchall()

class DesempenhoProfessor(VisualizadorDesempenho):
    def consultar_dados(self, cursor):
        cursor.execute("""
            SELECT 
                u.nome as aluno,
                u.ano_letivo,
                m.nome as materia,
                n.ab1_1, n.ab1_2, n.ab2_1, n.ab2_2
            FROM notas n
            JOIN usuarios u ON n.aluno_id = u.id
            JOIN materias m ON n.materia_id = m.id
        """)
        return cursor.fetchall()