#Módulos do Flask para lidar com requisições HTTP, renderizar templates HTML, redirecionar URLs, e gerar URLs para rotas definidas. Gerencia a autenticação de usuários (login, logout, e controle de acesso). Integra MySQL com Flask

from flask import Flask, request, render_template, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mysqldb import MySQL

app = Flask(__name__)  



# Configurações de conexão com o banco de dados MySQL e gerenciar sessões e proteger cookies.
app.config['SECRET_KEY'] = '6ec9b3e17d7cfdb88d5a984e1cb2e4ef4c57aab88cf9402c'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345'
app.config['MYSQL_DB'] = 'cadastro'

mysql = MySQL(app) #inicializa a extensão MySQL com a aplicação Flask.

# Inicialização do LoginManager e gerencia sessões de login
login_manager = LoginManager()
login_manager.init_app(app)

# Criação das tabelas no banco de dados
with app.app_context():
    cursor = mysql.connection.cursor()

    # Criação da tabela de cursos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cursos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) UNIQUE
        )
    ''')

    # Criação da tabela de usuário com referência ao curso
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100),
            matricula VARCHAR(100) UNIQUE,
            tipo ENUM('aluno', 'professor') NOT NULL,
            curso_id INT,
            FOREIGN KEY (curso_id) REFERENCES cursos(id)
        )
    ''')

    # Criação da tabela disciplinas com referência ao curso
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disciplinas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100),
            professor_id INT,
            curso_id INT,
            FOREIGN KEY (professor_id) REFERENCES usuarios(id),
            FOREIGN KEY (curso_id) REFERENCES cursos(id)
        )
    ''')

    # Criação da tabela de matrículas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matriculas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            aluno_id INT,
            disciplina_id INT,
            FOREIGN KEY (aluno_id) REFERENCES usuarios(id),
            FOREIGN KEY (disciplina_id) REFERENCES disciplinas(id)
        )
    ''')

    mysql.connection.commit()
    cursor.close()


# Classe User para o Flask-Login
class User(UserMixin):
    def __init__(self, id, tipo):
        self.id = id
        self.tipo = tipo



#Função que carrega o usuário atual baseado no user_id para o Flask-Login, permitindo o controle de sessões.
@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, tipo FROM usuarios WHERE id = %s", (user_id,))
    usuario = cursor.fetchone()
    cursor.close()
    if usuario:
        return User(id=usuario[0], tipo=usuario[1])
    return None

# Rota de login
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        nome = request.form.get('nome')
        matricula = request.form.get('matricula')
       
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE nome=%s AND  matricula = %s", (nome, matricula,))
        usuario = cursor.fetchone()
        cursor.close()

        if usuario:
            user = User(id=usuario[0], tipo=usuario[3])
            login_user(user)
            return redirect(url_for('inside_home'))
    return render_template('login.html')


# Rota de logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('alo_mundo'))


# Rota de home page
@app.route("/")
def alo_mundo():
    nome = "Faça login e selecione a ação que deseja realizar!"
    teste = ['Cadastrar','Cadastrar_curso','Cad_disciplinas', 'Matricular', 'Listar_atualizar_usuario','Remover', 'Logout']
    return render_template('index.html', nome=nome, teste=teste)


# Rotas de menus
@app.route("/inside")
def inside_home():
    menu="Pagina de Menus. O que você deseja executar?"
    return render_template('inside.html', menu=menu)


 
# Rota para cadastrar usuários
@app.route("/variaveis", methods=["POST", "GET"])
@login_required
def usando_variaveis():
    cursor = mysql.connection.cursor()
    
    if request.method == "POST":
        nome = request.form.get('nome')
        matricula = request.form.get('matricula')
        tipo = request.form.get('tipo')
        curso_id = request.form.get('curso_id')
        cursor.execute(
            "INSERT INTO usuarios (nome, matricula, tipo, curso_id) VALUES (%s, %s, %s, %s)",
            (nome, matricula, tipo, curso_id)
        )
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('usando_variaveis'))
    

    # Obter lista de cursos para exibir no formulário
    cursor.execute("SELECT id, nome FROM cursos")
    cursos = cursor.fetchall()
    cursor.close()
    
    return render_template('variaveis.html', cursos=cursos)



# Rota para deletar
@app.route("/delete", methods=["POST", "GET"])
@login_required
def remove_aluno():
    if request.method == "POST":
        nome = request.form.get('nome')
        matricula = request.form.get('matricula')
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM usuarios WHERE nome=%s AND matricula = %s", (nome, matricula,))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('remove_aluno'))
    return render_template('delete.html')


# Rota para cadastrar cursos
@app.route("/cursos", methods=["POST", "GET"])
@login_required
def cadastrar_curso():
    if request.method == "POST" and current_user.tipo == 'professor':
        nome = request.form.get('nome')
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO cursos (nome) VALUES (%s)", (nome,))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('cadastrar_curso'))
    return render_template('cursos.html')


 #Rota para cadastrar disciplinas
@app.route("/disciplinas", methods=["POST", "GET"])
@login_required
def cadastrar_disciplina():
    cursor = mysql.connection.cursor()

    if request.method == "POST" and current_user.tipo == 'professor':
        nome = request.form.get('nome')
        curso_id = request.form.get('curso_id')
        cursor.execute(
            "INSERT INTO disciplinas (nome, professor_id, curso_id) VALUES (%s, %s, %s)",
            (nome, current_user.id, curso_id)
        )
        mysql.connection.commit()
        print(f"Disciplina cadastrada: {nome} no curso {curso_id} por professor {current_user.id}")

    # Obter lista de cursos para exibir no formulário
    cursor.execute("SELECT id, nome FROM cursos")
    cursos = cursor.fetchall()

    # Obter lista de disciplinas cadastradas
    cursor.execute('''
        SELECT d.nome, u.nome, c.nome
        FROM disciplinas d 
        JOIN usuarios u ON d.professor_id = u.id
        JOIN cursos c ON d.curso_id = c.id
    ''')
    disciplinas = cursor.fetchall()
    
    cursor.close()
    return render_template('disciplinas.html', disciplinas=disciplinas, cursos=cursos)



# Rota para matrícula
@app.route("/matricular", methods=["POST", "GET"])
@login_required
def matricular_disciplina():
    cursor = mysql.connection.cursor()

    if request.method == "POST" and current_user.tipo == 'aluno':
        disciplina_id = request.form.get("disciplina_id")
        cursor.execute(
            "INSERT INTO matriculas (aluno_id, disciplina_id) VALUES (%s, %s)",
            (current_user.id, disciplina_id)
        )
        mysql.connection.commit()

    # Obter lista de disciplinas cadastradas
    cursor.execute('''
        SELECT d.id, d.nome, u.nome 
        FROM disciplinas d 
        JOIN usuarios u ON d.professor_id = u.id
    ''')
    disciplinas = cursor.fetchall()

    # Obter lista de disciplinas em que o aluno está matriculado
    cursor.execute('''
        SELECT d.nome, u.nome 
        FROM matriculas m
        JOIN disciplinas d ON m.disciplina_id = d.id
        JOIN usuarios u ON d.professor_id = u.id
        WHERE m.aluno_id = %s
    ''', (current_user.id,))
    disciplinas_matriculadas = cursor.fetchall()

    cursor.close()

    return render_template('matriculas.html', disciplinas=disciplinas, disciplinas_matriculadas=disciplinas_matriculadas)


# rota de listar usuários 
@app.route("/usuarios", methods=["GET"])
@login_required
def listar_usuarios():
    cursor = mysql.connection.cursor()
    
    cursor.execute("SELECT id, nome, matricula, tipo FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()

    return render_template('listar_usuarios.html', usuarios=usuarios)

# Rota de atualizar usuários
@app.route("/usuarios/update/<int:usuario_id>", methods=["GET", "POST"])
@login_required
def atualizar_usuario(usuario_id):
    cursor = mysql.connection.cursor()

    if request.method == "POST":
        nome = request.form.get("nome")
        matricula = request.form.get("matricula")
        tipo = request.form.get("tipo")
        
        cursor.execute(
            "UPDATE usuarios SET nome = %s, matricula = %s, tipo = %s WHERE id = %s",
            (nome, matricula, tipo, usuario_id)
        )
        mysql.connection.commit()
        return redirect(url_for('listar_usuarios'))

    cursor.execute("SELECT nome, matricula, tipo FROM usuarios WHERE id = %s", (usuario_id,))
    usuario = cursor.fetchone()
    cursor.close()

    return render_template("atualizar_usuario.html", usuario=usuario)



if __name__ == "__main__":
    app.run(debug=True)
