
# Clínica Vida - Sistema de agendamentos

from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "clinica123"

# Usa o banco clinica.db que fica na mesma pasta deste arquivo
PASTA = os.path.dirname(os.path.abspath(__file__))
BANCO = os.path.join(PASTA, "clinica.db")


# Conecta ao banco de dados
def conectar():
    banco = sqlite3.connect(BANCO)
    banco.row_factory = sqlite3.Row
    banco.execute("PRAGMA foreign_keys = ON")
    return banco


# Confere se alguém está conectado
def esta_logado():
    return "id_usuario" in session


# Confere se o usuário conectado é administrador
def eh_admin():
    return session.get("perfil") == "admin"


# -------------------------
# LOGIN - QUESTÃO 4
# -------------------------

@app.route("/", methods=["GET", "POST"])
def login():
    erro = ""

    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        banco = conectar()

        usuario = banco.execute(
            "SELECT * FROM usuario WHERE email = ?",
            (email,)
        ).fetchone()

        banco.close()

        # Confere o e-mail e a senha cadastrados
        if usuario and senha == usuario["senha_hash"]:
            session["id_usuario"] = usuario["id_usuario"]
            session["nome"] = usuario["nome"]
            session["perfil"] = usuario["perfil"]

            return redirect("/painel")

        erro = "E-mail ou senha incorretos."

    return render_template("login.html", erro=erro)


# -------------------------
# PAINEL - QUESTÃO 5
# -------------------------

@app.route("/painel")
def painel():
    if not esta_logado():
        return redirect("/")

    return render_template("painel.html")


# Sai do sistema e encerra a sessão
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")


# -------------------------
# USUÁRIOS - QUESTÃO 6
# Apenas o administrador pode gerenciar usuários
# -------------------------

@app.route("/usuarios", methods=["GET", "POST"])
def usuarios():
    if not esta_logado():
        return redirect("/")

    if not eh_admin():
        return "Acesso permitido somente ao administrador.", 403

    banco = conectar()

    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

        # Cadastra o novo usuário como usuário comum
        banco.execute(
            """INSERT INTO usuario (nome, email, senha_hash, perfil)
               VALUES (?, ?, ?, ?)""",
            (nome, email, senha, "usuario")
        )

        banco.commit()
        banco.close()

        flash("Usuário cadastrado!")
        return redirect("/usuarios")

    lista = banco.execute(
        "SELECT * FROM usuario ORDER BY nome"
    ).fetchall()

    banco.close()

    return render_template("usuarios.html", usuarios=lista)


# Edita um usuário
@app.route("/usuarios/editar/<int:id>", methods=["GET", "POST"])
def editar_usuario(id):
    if not esta_logado():
        return redirect("/")

    if not eh_admin():
        return "Acesso permitido somente ao administrador.", 403

    banco = conectar()

    usuario = banco.execute(
        "SELECT * FROM usuario WHERE id_usuario = ?", (id,)
    ).fetchone()

    if usuario is None:
        banco.close()
        return "Usuário não encontrado.", 404

    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form.get("senha", "")
        perfil = request.form["perfil"]

        # Se a senha ficar vazia, mantém a senha atual
        if senha:
            banco.execute(
                """UPDATE usuario
                   SET nome = ?, email = ?, senha_hash = ?, perfil = ?
                   WHERE id_usuario = ?""",
                (nome, email, senha, perfil, id)
            )
        else:
            banco.execute(
                """UPDATE usuario
                   SET nome = ?, email = ?, perfil = ?
                   WHERE id_usuario = ?""",
                (nome, email, perfil, id)
            )

        banco.commit()
        banco.close()

        flash("Usuário atualizado!")
        return redirect("/usuarios")

    banco.close()
    return render_template("editar_usuario.html", usuario=usuario)


# Exclui um usuário
@app.route("/usuarios/excluir/<int:id>")
def excluir_usuario(id):
    if not esta_logado():
        return redirect("/")

    if not eh_admin():
        return "Acesso permitido somente ao administrador.", 403

    # Impede que o administrador exclua a própria conta
    if id == session["id_usuario"]:
        flash("Você não pode excluir sua própria conta.")
        return redirect("/usuarios")

    banco = conectar()

    banco.execute(
        "DELETE FROM usuario WHERE id_usuario = ?", (id,)
    )

    banco.commit()
    banco.close()

    flash("Usuário excluído!")
    return redirect("/usuarios")


# -------------------------
# MÉDICOS - QUESTÃO 7
# -------------------------

@app.route("/medicos", methods=["GET", "POST"])
def medicos():
    if not esta_logado():
        return redirect("/")

    banco = conectar()

    if request.method == "POST":
        nome = request.form["nome"]
        crm = request.form["crm"]
        especialidade = request.form["especialidade"]
        email = request.form.get("email", request.form.get("telefone", ""))

        banco.execute(
            """INSERT INTO medico (nome, crm, especialidade, email)
               VALUES (?, ?, ?, ?)""",
            (nome, crm, especialidade, email)
        )

        banco.commit()
        banco.close()

        flash("Médico cadastrado!")
        return redirect("/medicos")

    lista = banco.execute(
        "SELECT * FROM medico ORDER BY nome"
    ).fetchall()

    banco.close()

    return render_template("medicos.html", medicos=lista)


# Edita um médico
@app.route("/medicos/editar/<int:id>", methods=["GET", "POST"])
def editar_medico(id):
    if not esta_logado():
        return redirect("/")

    banco = conectar()

    medico = banco.execute(
        "SELECT * FROM medico WHERE id_medico = ?", (id,)
    ).fetchone()

    if medico is None:
        banco.close()
        return "Médico não encontrado.", 404

    if request.method == "POST":
        nome = request.form["nome"]
        crm = request.form["crm"]
        especialidade = request.form["especialidade"]
        email = request.form.get("email", request.form.get("telefone", ""))

        banco.execute(
            """UPDATE medico
               SET nome = ?, crm = ?, especialidade = ?, email = ?
               WHERE id_medico = ?""",
            (nome, crm, especialidade, email, id)
        )

        banco.commit()
        banco.close()

        flash("Médico atualizado!")
        return redirect("/medicos")

    banco.close()
    return render_template("editar_medico.html", medico=medico)


# Exclui um médico
@app.route("/medicos/excluir/<int:id>")
def excluir_medico(id):
    if not esta_logado():
        return redirect("/")

    banco = conectar()

    try:
        banco.execute(
            "DELETE FROM medico WHERE id_medico = ?", (id,)
        )
        banco.commit()
        flash("Médico excluído!")
    except sqlite3.IntegrityError:
        flash("Não é possível excluir: existem agendamentos deste médico.")
    finally:
        banco.close()

    return redirect("/medicos")


# -------------------------
# PACIENTES - QUESTÃO 8
# -------------------------

@app.route("/pacientes", methods=["GET", "POST"])
def pacientes():
    if not esta_logado():
        return redirect("/")

    banco = conectar()

    if request.method == "POST":
        nome = request.form["nome"]
        cpf = request.form["cpf"]
        data_nascimento = request.form["data_nascimento"]
        telefone = request.form["telefone"]
        email = request.form.get("email", request.form.get("endereco", ""))

        banco.execute(
            """INSERT INTO paciente
               (nome, cpf, data_nascimento, telefone, email)
               VALUES (?, ?, ?, ?, ?)""",
            (nome, cpf, data_nascimento, telefone, email)
        )

        banco.commit()
        banco.close()

        flash("Paciente cadastrado!")
        return redirect("/pacientes")

    lista = banco.execute(
        "SELECT * FROM paciente ORDER BY nome"
    ).fetchall()

    banco.close()

    return render_template("pacientes.html", pacientes=lista)


# Edita um paciente
@app.route("/pacientes/editar/<int:id>", methods=["GET", "POST"])
def editar_paciente(id):
    if not esta_logado():
        return redirect("/")

    banco = conectar()

    paciente = banco.execute(
        "SELECT * FROM paciente WHERE id_paciente = ?", (id,)
    ).fetchone()

    if paciente is None:
        banco.close()
        return "Paciente não encontrado.", 404

    if request.method == "POST":
        nome = request.form["nome"]
        cpf = request.form["cpf"]
        data_nascimento = request.form["data_nascimento"]
        telefone = request.form["telefone"]
        email = request.form.get("email", request.form.get("endereco", ""))

        banco.execute(
            """UPDATE paciente
               SET nome = ?, cpf = ?, data_nascimento = ?,
                   telefone = ?, email = ?
               WHERE id_paciente = ?""",
            (nome, cpf, data_nascimento, telefone, email, id)
        )

        banco.commit()
        banco.close()

        flash("Paciente atualizado!")
        return redirect("/pacientes")

    banco.close()
    return render_template("editar_paciente.html", paciente=paciente)


# Exclui um paciente
@app.route("/pacientes/excluir/<int:id>")
def excluir_paciente(id):
    if not esta_logado():
        return redirect("/")

    banco = conectar()

    try:
        banco.execute(
            "DELETE FROM paciente WHERE id_paciente = ?", (id,)
        )
        banco.commit()
        flash("Paciente excluído!")
    except sqlite3.IntegrityError:
        flash("Não é possível excluir: existem agendamentos deste paciente.")
    finally:
        banco.close()

    return redirect("/pacientes")


# -------------------------
# AGENDAMENTOS - QUESTÃO 9
# -------------------------

@app.route("/agendamentos", methods=["GET", "POST"])
def agendamentos():
    if not esta_logado():
        return redirect("/")

    banco = conectar()
    erro = ""

    if request.method == "POST":
        paciente = request.form["id_paciente"]
        medico = request.form["id_medico"]
        data = request.form["data_consulta"]
        hora = request.form["hora_consulta"]
        descricao = request.form.get("observacao", "")

        # Confere se o médico já tem consulta nesse horário
        ocupado = banco.execute(
            """SELECT * FROM agendamento
               WHERE id_medico = ?
               AND data_consulta = ?
               AND hora_consulta = ?""",
            (medico, data, hora)
        ).fetchone()

        if ocupado:
            erro = "Este médico já tem consulta nesse horário."
        else:
            banco.execute(
                """INSERT INTO agendamento
                   (id_paciente, id_medico, data_consulta,
                    hora_consulta, observacao)
                   VALUES (?, ?, ?, ?, ?)""",
                (paciente, medico, data, hora, descricao)
            )

            banco.commit()
            banco.close()

            flash("Agendamento realizado!")
            return redirect("/agendamentos")

    # Busca os pacientes para o menu de seleção
    pacientes_lista = banco.execute(
        "SELECT * FROM paciente ORDER BY nome"
    ).fetchall()

    # Busca os médicos para o menu de seleção
    medicos_lista = banco.execute(
        "SELECT * FROM medico ORDER BY nome"
    ).fetchall()

    # Busca todos os agendamentos e os nomes correspondentes
    # LEFT JOIN permite mostrar o agendamento mesmo se faltar
    # o registro correspondente de um paciente ou médico
    lista = banco.execute("""
        SELECT agendamento.*,
               paciente.nome AS nome_paciente,
               medico.nome AS nome_medico
        FROM agendamento
        LEFT JOIN paciente
            ON agendamento.id_paciente = paciente.id_paciente
        LEFT JOIN medico
            ON agendamento.id_medico = medico.id_medico
        ORDER BY agendamento.data_consulta,
                 agendamento.hora_consulta
    """).fetchall()

    banco.close()

    return render_template(
        "agendamentos.html",
        pacientes=pacientes_lista,
        medicos=medicos_lista,
        agendamentos=lista,
        erro=erro
    )


# Cancela um agendamento
@app.route("/agendamentos/excluir/<int:id>")
def excluir_agendamento(id):
    if not esta_logado():
        return redirect("/")

    banco = conectar()

    banco.execute(
        "DELETE FROM agendamento WHERE id_agendamento = ?", (id,)
    )

    banco.commit()
    banco.close()

    flash("Agendamento cancelado!")
    return redirect("/agendamentos")


# Inicia o sistema
if __name__ == "__main__":
    app.run(debug=True)
