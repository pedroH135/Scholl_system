class Usuario:
    def __init__(self, id, nome, email, tipo):
        self.id = id
        self.nome = nome
        self.email = email
        self.tipo = tipo

    def eh_aluno(self):
        return self.tipo == "aluno"

    def eh_professor(self):
        return self.tipo == "professor"
    
    #POLIMOFISMO com Contrato abstrato
    def get_dashboard_url(self):
        raise NotImplementedError("A subclasse deve implementar este método") #erro