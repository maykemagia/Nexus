from flask import Flask, request, redirect, render_template
from banco import conectar_banco


app = Flask(__name__)


def horario_tem_conflito(
    cursor,
    data_agendamento,
    horario,
    id_servico,
    ignorar_id=None
):
    # Descobre a duração do serviço solicitado.
    cursor.execute("""
        SELECT duracao_minutos
        FROM servicos
        WHERE id_servico = %s
    """, (id_servico,))

    servico = cursor.fetchone()

    if servico is None:
        return True

    duracao_nova = int(servico[0])

    # Converte os horários para minutos desde a meia-noite.
    hora, minuto = map(int, str(horario)[:5].split(":"))
    inicio_novo = hora * 60 + minuto
    fim_novo = inicio_novo + duracao_nova

    # Busca os agendamentos da mesma data.
    sql = """
        SELECT
            a.id_agendamento,
            a.horario,
            s.duracao_minutos
        FROM agendamentos AS a
        INNER JOIN servicos AS s
            ON a.id_servico = s.id_servico
        WHERE a.data_agendamento = %s
    """
    parametros = [data_agendamento]

    # Na edição, ignora o próprio agendamento.
    if ignorar_id is not None:
        sql += " AND a.id_agendamento != %s"
        parametros.append(ignorar_id)

    cursor.execute(sql, tuple(parametros))

    for _, horario_existente, duracao_existente in cursor.fetchall():
        hora_existente, minuto_existente = map(
            int, str(horario_existente)[:5].split(":")
        )

        inicio_existente = hora_existente * 60 + minuto_existente
        fim_existente = inicio_existente + int(duracao_existente)

        # Existe conflito se os intervalos se sobrepõem.
        if (
            inicio_novo < fim_existente
            and fim_novo > inicio_existente
        ):
            return True

    return False


@app.route("/")
def inicio():
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM servicos")
        total_servicos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM agendamentos")
        total_agendamentos = cursor.fetchone()[0]

        return render_template(
            "index.html",
            total_clientes=total_clientes,
            total_servicos=total_servicos,
            total_agendamentos=total_agendamentos
        )

    except Exception as erro:
        return f"Erro ao carregar o painel: {erro}", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None and conexao.is_connected():
            conexao.close()
@app.route("/clientes")
def clientes():
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT id_cliente, nome, telefone
            FROM clientes
            ORDER BY id_cliente
        """)

        lista_clientes = cursor.fetchall()

        return render_template(
            "clientes.html",
            clientes=lista_clientes
        )

    except Exception as erro:
        return f"Erro ao carregar clientes: {erro}", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None and conexao.is_connected():
            conexao.close()


@app.route("/clientes/cadastrar", methods=["GET", "POST"])
def cadastrar_cliente():
    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]

        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            INSERT INTO clientes (nome, telefone)
            VALUES (%s, %s)
        """, (nome, telefone))

        conexao.commit()
        cursor.close()
        conexao.close()

        return redirect("/clientes?sucesso=cadastrado")

    return render_template("cadastrar_cliente.html")


    
@app.route("/clientes/editar/<int:id_cliente>", methods=["GET", "POST"])
def editar_cliente(id_cliente):
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        if request.method == "POST":
            nome = request.form["nome"].strip()
            telefone = request.form["telefone"].strip()

            if not nome or not telefone:
                return "Preencha o nome e o telefone.", 400

            cursor.execute("""
                UPDATE clientes
                SET nome = %s, telefone = %s
                WHERE id_cliente = %s
            """, (nome, telefone, id_cliente))

            conexao.commit()
            return redirect("/clientes")

        cursor.execute("""
            SELECT id_cliente, nome, telefone
            FROM clientes
            WHERE id_cliente = %s
        """, (id_cliente,))

        cliente = cursor.fetchone()

        if cliente is None:
            return "Cliente não encontrado.", 404

        return render_template(
            "editar_cliente.html",
            cliente=cliente
        )

    except Exception as erro:
        if conexao is not None and conexao.is_connected():
            conexao.rollback()

        return f"Erro ao editar cliente: {erro}", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None and conexao.is_connected():
            conexao.close()

@app.route("/clientes/excluir/<int:id_cliente>", methods=["POST"])
def excluir_cliente(id_cliente):
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            DELETE FROM clientes
            WHERE id_cliente = %s
        """, (id_cliente,))

        if cursor.rowcount == 0:
            return redirect("/clientes?erro=nao_encontrado")

        conexao.commit()
        return redirect("/clientes?sucesso=excluido")

    except Exception:
        if conexao is not None and conexao.is_connected():
            conexao.rollback()

        return redirect("/clientes?erro=excluir")

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None and conexao.is_connected():
            conexao.close()

@app.route("/servicos", methods=["GET", "POST"])
def servicos():
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        if request.method == "POST":
            nome = request.form["nome"].strip()
            preco = request.form["preco"]
            duracao_minutos = request.form["duracao_minutos"]

            if not nome:
                return redirect("/servicos?erro=salvar")

            cursor.execute("""
                INSERT INTO servicos (nome, preco, duracao_minutos)
                VALUES (%s, %s, %s)
            """, (nome, preco, duracao_minutos))

            conexao.commit()
            return redirect("/servicos?sucesso=criado")

        cursor.execute("""
            SELECT id_servico, nome, preco, duracao_minutos
            FROM servicos
            ORDER BY id_servico
        """)

        lista_servicos = cursor.fetchall()

        return render_template(
            "servicos.html",
            servicos=lista_servicos
        )

    except Exception:
        if conexao is not None and conexao.is_connected():
            conexao.rollback()

        if request.method == "POST":
            return redirect("/servicos?erro=salvar")

        return "Não foi possível carregar os serviços. Verifique a conexão com o banco de dados.", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None and conexao.is_connected():
            conexao.close()


@app.route("/servicos/editar/<int:id_servico>", methods=["GET", "POST"])
def editar_servico(id_servico):
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        if request.method == "POST":
            nome = request.form["nome"].strip()
            preco = request.form["preco"]
            duracao_minutos = request.form["duracao_minutos"]

            if not nome:
                return redirect("/servicos?erro=editar")

            cursor.execute("""
                UPDATE servicos
                SET nome = %s,
                    preco = %s,
                    duracao_minutos = %s
                WHERE id_servico = %s
            """, (nome, preco, duracao_minutos, id_servico))

            conexao.commit()
            return redirect("/servicos?sucesso=editado")

        cursor.execute("""
            SELECT id_servico, nome, preco, duracao_minutos
            FROM servicos
            WHERE id_servico = %s
        """, (id_servico,))

        servico = cursor.fetchone()

        if servico is None:
            return redirect("/servicos?erro=nao_encontrado")

        return render_template("editar_servico.html", servico=servico)

    except Exception:
        if conexao is not None and conexao.is_connected():
            conexao.rollback()

        return redirect("/servicos?erro=editar")

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None and conexao.is_connected():
            conexao.close()


@app.route("/servicos/excluir/<int:id_servico>", methods=["POST"])
def excluir_servico(id_servico):
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            DELETE FROM servicos
            WHERE id_servico = %s
        """, (id_servico,))

        if cursor.rowcount == 0:
            return redirect("/servicos?erro=nao_encontrado")

        conexao.commit()
        return redirect("/servicos?sucesso=excluido")

    except Exception:
        if conexao is not None and conexao.is_connected():
            conexao.rollback()

        return redirect("/servicos?erro=excluir")

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None and conexao.is_connected():
            conexao.close()


@app.route("/agendamentos", methods=["GET", "POST"])
def agendamentos():
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        if request.method == "POST":
            id_cliente = request.form["id_cliente"]
            id_servico = request.form["id_servico"]
            data_agendamento = request.form["data_agendamento"]
            horario = request.form["horario"]
            status_agendamento = request.form["status_agendamento"]

            # Impede conflitos de horário.
            if horario_tem_conflito(
                cursor,
                data_agendamento,
                horario,
                id_servico
            ):
                return redirect("/agendamentos?erro=conflito")

            cursor.execute("""
                INSERT INTO agendamentos
                (
                    id_cliente,
                    id_servico,
                    data_agendamento,
                    horario,
                    status_agendamento
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                id_cliente,
                id_servico,
                data_agendamento,
                horario,
                status_agendamento
            ))

            conexao.commit()
            return redirect("/agendamentos?sucesso=criado")

        cursor.execute("""
            SELECT id_cliente, nome
            FROM clientes
            ORDER BY nome
        """)
        lista_clientes = cursor.fetchall()

        cursor.execute("""
            SELECT id_servico, nome
            FROM servicos
            ORDER BY nome
        """)
        lista_servicos = cursor.fetchall()

        cursor.execute("""
            SELECT
                a.id_agendamento,
                c.nome,
                s.nome,
                a.data_agendamento,
                a.horario,
                a.status_agendamento
            FROM agendamentos AS a
            INNER JOIN clientes AS c
                ON a.id_cliente = c.id_cliente
            INNER JOIN servicos AS s
                ON a.id_servico = s.id_servico
            ORDER BY a.data_agendamento, a.horario
        """)
        lista_agendamentos = cursor.fetchall()

        return render_template(
            "agendamentos.html",
            agendamentos=lista_agendamentos,
            clientes=lista_clientes,
            servicos=lista_servicos
        )

    except Exception:
        if conexao is not None and conexao.is_connected():
            conexao.rollback()

        if request.method == "POST":
            return redirect("/agendamentos?erro=salvar")

        return (
            "Não foi possível carregar os agendamentos. "
            "Verifique a conexão com o banco de dados.",
            500
        )

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None and conexao.is_connected():
            conexao.close()

@app.route("/agendamentos/editar/<int:id_agendamento>", methods=["GET", "POST"])
def editar_agendamento(id_agendamento):
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        if request.method == "POST":
            id_cliente = request.form["id_cliente"]
            id_servico = request.form["id_servico"]
            data_agendamento = request.form["data_agendamento"]
            horario = request.form["horario"]
            status_agendamento = request.form["status_agendamento"]

            # Confirma que o agendamento existe.
            cursor.execute("""
                SELECT id_agendamento
                FROM agendamentos
                WHERE id_agendamento = %s
            """, (id_agendamento,))

            if cursor.fetchone() is None:
                return redirect("/agendamentos?erro=nao_encontrado")

            # Verifica conflitos, ignorando o próprio agendamento.
            if horario_tem_conflito(
                cursor,
                data_agendamento,
                horario,
                id_servico,
                ignorar_id=id_agendamento
            ):
                return redirect("/agendamentos?erro=conflito")

            cursor.execute("""
                UPDATE agendamentos
                SET id_cliente = %s,
                    id_servico = %s,
                    data_agendamento = %s,
                    horario = %s,
                    status_agendamento = %s
                WHERE id_agendamento = %s
            """, (
                id_cliente,
                id_servico,
                data_agendamento,
                horario,
                status_agendamento,
                id_agendamento
            ))

            conexao.commit()
            return redirect("/agendamentos?sucesso=editado")

        cursor.execute("""
            SELECT
                id_agendamento,
                id_cliente,
                id_servico,
                DATE_FORMAT(data_agendamento, '%Y-%m-%d'),
                TIME_FORMAT(horario, '%H:%i'),
                status_agendamento
            FROM agendamentos
            WHERE id_agendamento = %s
        """, (id_agendamento,))

        agendamento = cursor.fetchone()

        if agendamento is None:
            return redirect("/agendamentos?erro=nao_encontrado")

        cursor.execute("""
            SELECT id_cliente, nome
            FROM clientes
            ORDER BY nome
        """)
        lista_clientes = cursor.fetchall()

        cursor.execute("""
            SELECT id_servico, nome
            FROM servicos
            ORDER BY nome
        """)
        lista_servicos = cursor.fetchall()

        return render_template(
            "editar_agendamento.html",
            agendamento=agendamento,
            clientes=lista_clientes,
            servicos=lista_servicos
        )

    except Exception:
        if conexao is not None and conexao.is_connected():
            conexao.rollback()

        return redirect("/agendamentos?erro=editar")

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None and conexao.is_connected():
            conexao.close()


@app.route("/agendamentos/excluir/<int:id_agendamento>", methods=["POST"])
def excluir_agendamento(id_agendamento):
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            DELETE FROM agendamentos
            WHERE id_agendamento = %s
        """, (id_agendamento,))

        if cursor.rowcount == 0:
            return redirect("/agendamentos?erro=nao_encontrado")

        conexao.commit()
        return redirect("/agendamentos?sucesso=excluido")

    except Exception:
        if conexao is not None and conexao.is_connected():
            conexao.rollback()

        return redirect("/agendamentos?erro=excluir")

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    app.run(debug=True)