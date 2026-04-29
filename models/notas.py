class Nota:
    CAMPOS_VALIDOS = {"ab1_1", "ab1_2", "ab2_1", "ab2_2"}

    def __init__(self):
        self.__dados = {
            "ab1_1": None,
            "ab1_2": None,
            "ab2_1": None,
            "ab2_2": None
        }

    #Encapsulamento
    def atualizar(self, campo, valor):
        # valida campo
        if campo not in self.CAMPOS_VALIDOS:
            raise ValueError("Campo inválido")

        # valida valor
        if valor is not None and (valor < 0 or valor > 10):
            raise ValueError("Nota deve estar entre 0 e 10")

        self.__dados[campo] = valor

    def get_valor(self, campo):
        return self.__dados.get(campo)