# 🎓 Sistema de Gestão Escolar (SGE)

O SGE é uma plataforma focada na informatização acadêmica, inspirada em sistemas como SIGAA e SIGEDUC, com o objetivo de facilitar a interação entre alunos e professores através da gestão de notas, frequências e materiais.

---

## 🚀 As 10 Funcionalidades do Projeto (Escopo Original)

Com base no planejamento estratégico do projeto, o sistema contempla:

1.  **Gestão de Dados Pessoais**: Cadastro completo de alunos (Nome, CPF, E-mail, Nascimento, Endereço, Telefone, Filiação) e Professores.
2.  **Central de Notas**: Módulo para inserção, consulta e atualização de notas de provas e atividades.
3.  **Módulo de Feedback**: Canal bidirecional para comentários de desempenho (professores) e avaliação de metodologia (alunos).
4.  **Controle de Cadastro e Acessos**: Sistema de login com definição de permissões baseadas no perfil do usuário.
5.  **Registro de Presença**: Interface para professores controlarem a assiduidade e alunos acompanharem sua frequência.
6.  **Repositório de Materiais**: Upload e organização de apostilas, slides, vídeos e links educativos.
7.  **Calendário Acadêmico**: Cronograma de datas importantes, provas, feriados e eventos.
8.  **Histórico Acadêmico Automático**: Emissão de documentos com o resumo de disciplinas, notas e semestres concluídos.
9.  **Relatório de Frequência**: Detalhamento da participação do aluno por disciplina.
10. **Gráficos de Desempenho**: Visualização estatística e visual da evolução acadêmica.

---

## 🌟 Recursos Extras (Já Implementados no Código)

Recursos adicionados além do planejamento inicial para elevar a qualidade do software:

* **Planilha de Presença "Estilo Excel"**: Interface avançada que permite ao professor registrar a presença de até 20 aulas de uma só vez em uma tabela dinâmica.
* **Cálculo Automático de IRA**: Processamento em tempo real do Índice de Rendimento Acadêmico.
* **Gestão de Fotos de Perfil**: Módulo para upload e atualização de avatares dos usuários.
* **Segurança de Credenciais**: Funcionalidade de alteração de senha com verificação de segurança.

---

## ⏳ Roadmap (O que falta implementar)

Para atingir a conformidade total com o documento de planejamento de Pedro:

* **Cadastro e Login por CPF**: Adição de uma API que possa fazer com que o usuário entre no sistema apartir de um CPF válido.
* **Módulo de Calendário Visual**: Implementação da interface de cronograma e que essa interface tenha uma intima relação com a funcionalidade de presença(item 7).
* **Exportador de Histórico (PDF)**: Função para gerar o arquivo de histórico para download (item 8).

---

## 🧬 Sessão: Herança

### Motivação
A **Herança** foi a base da arquitetura de usuários do sistema. A motivação principal foi o reaproveitamento de código e a padronização. 

Tanto o `Aluno` quanto o `Professor` são, antes de tudo, um `Usuario`. Ao herdarem da classe pai `Usuario`, evitamos repetir campos como `nome`, `email` e `senha`. Isso garante que qualquer atualização na lógica de autenticação ou segurança na classe base seja refletida instantaneamente em todo o ecossistema do sistema (Princípio DRY - *Don't Repeat Yourself*).

---

## 🎭 Sessão: Polimorfismo

### Como foi feito
O Polimorfismo foi aplicado no sistema para permitir que a aplicação execute comportamentos diferentes usando o mesmo comando, dependendo de quem está logado.

No código, isso acontece principalmente nos métodos de "Obtenção de Dados" (obter_dados_feedback, obter_dados_materiais, obter_dados_presenca):

Quando o sistema chama usuario.obter_dados_presenca(), se o objeto for um Professor, ele abre a planilha de lançamento para a turma toda.

Se o objeto for um Aluno, o mesmo comando abre apenas o relatório individual de faltas.

Essa técnica deixa o código do app.py muito mais limpo, pois o servidor não precisa saber "quem" está pedindo a informação, ele apenas pede ao objeto para "mostrar seus dados".

---

## 🛠️ Tecnologias Utilizadas
* **Linguagem:** Python 3.x
* **Framework Web:** Flask
* **Banco de Dados:** SQLite3 (Relacional)
* **Frontend:** HTML5, CSS3 (Sticky tables) e Jinja2.
