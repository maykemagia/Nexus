import mysql.connector
from mysql.connector import Error
from getpass import getpass


# Tentando a conexão:
try:
    senha = getpass("Senha do MySQL: ")

    conexao = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="nexus_app",
        password=senha,
        database="Nexus_Agenda"
    )

    # Quando a conexão der certo:
    if conexao.is_connected():
        print("Conexão com o banco NEXUS Agenda realizada!")

        # Mostrando as tabelas do banco:
        cursor = conexao.cursor()
        cursor.execute("SHOW TABLES")

        tabelas = cursor.fetchall()

        print("\nTabelas do Banco de Dados Nexus Agenda: \n")

        if tabelas:
            for tabela in tabelas:
                print(tabela[0])
        else:
            print("Nenhuma tabela encontrada.")

        while True:
            print("\n===== NEXUS AGENDA ===== \n")
            print("1 - Cadastrar Cliente")
            print("2 - Cadastrar Serviço")
            print("3 - Cadastrar Agendamento")
            print("4 - Listar Clientes")
            print("5 - Listar Serviços")
            print("6 - Listar Agendamentos")
            print("7 - Cancelar Agendamento")
            print("8 - Alterar Agendamento")
            print("9 - Sair")

            opcao = input("\nEscolha uma Opção: ")


            ## CRIAR CLIENTE

            if opcao == "1":
                nome = input("Nome do Cliente: ")
                telefone = input("Telefone do Cliente: ")

                cursor.execute(
                    "INSERT INTO clientes(nome,telefone) VALUES(%s, %s)", 
                    (nome, telefone)
                )

                conexao.commit()

                print("\nCliente Cadastrado com Sucesso!!\n")

            ## CRIAR SERVIÇO

            elif opcao =="2":
                nome = input("Nome do Serviço: ")
                preco = input("Preço do Serviço: ")
                duracao = input("Duração do Serviço (em minutos): ")

                cursor.execute(
                    "INSERT INTO servicos(nome, preco, duracao_minutos) VALUES(%s, %s, %s)", 
                    (nome, preco, duracao)
                )

                conexao.commit()

                print("\nServiço Cadastrado com Sucesso!\n")

            ## CRIAR AGENDAMENTOS

            elif opcao =="3":
                cliente = input("ID do Cliente: ")
                servico = input("ID do Serviço: ")
                data = input("Data (AAAA-MM-DD): ")
                horario = input("Horário (HH:MM:SS): ")
                horario = horario.replace("-", ":")
                cursor.execute(
                    """
                    INSERT INTO agendamentos (id_cliente, id_servico, data_agendamento, horario, status_agendamento)
                    VALUES(%s, %s, %s, %s, %s)
                    """,
                    (cliente, servico, data, horario, "Agendado")
                )

                conexao.commit()
                print("Agendamento Criado com Sucesso!")


            ## LISTAR AGENDAMENTOS

            elif opcao =="6":
                cursor.execute("""
                SELECT
                a.id_agendamento,
                c.nome,
                s.nome,
                a.data_agendamento,
                a.horario,
                a.status_agendamento
                FROM agendamentos a 
                INNER JOIN clientes c ON a.id_cliente = c.id_cliente
                INNER JOIN servicos s ON a.id_servico = s.id_servico
                ORDER BY a.data_agendamento, a.horario
                
                """)

           
                agendamentos = cursor.fetchall()

                print("\n===== AGENDAMENTOS =====\n")

                if agendamentos:
                    for agendamento in agendamentos:
                        print(f"\nID: {agendamento[0]}")
                        print(f"\nCliente: {agendamento[1]}")
                        print(f"\nServiço: {agendamento[2]}")
                        print(f"\nData: {agendamento[3].strftime('%d/%m/%Y')}")
                        print(f"\nHorário: {agendamento[4]}")
                        print(f"\nStatus: {agendamento[5]}")
                        print("========================")
                else:
                    print("Nenhum agendamento cadastrado")

            ## LISTAR SERVIÇOS

            elif opcao =="5":
                cursor.execute("SELECT * FROM servicos")
                servicos = cursor.fetchall()

                print("\n===== SERVIÇOS CADASTRADOS =====\n")

                for servico in servicos:
                    print(servico)
            

            ## LISTAR CLIENTES

            elif opcao == "4":
                cursor.execute("SELECT * FROM clientes")
                clientes = cursor.fetchall()

                print("\n===== CLIENTES CADASTRADOS =====\n")

                for cliente in clientes:
                    print(cliente)

            ## CANCELAR UM AGENDAMENTO

            elif opcao == "7":
                id_agendamento = input("ID do agendamento que deseja cancelar: ")

                cursor.execute(
                    """ 
                    UPDATE agendamentos 
                    SET status_agendamento = %s 
                    WHERE id_agendamento = %s
                    """,
                    ("Cancelado", id_agendamento)
                )

                conexao.commit()

                if cursor.rowcount > 0:
                    print("Agendamento cancelado com sucesso")
                else:
                    print("Agendamento não encontrado")


            elif opcao == "8":
                id_agendamento = input("ID do Agendamento: ")
                nova_data = input("Nova Data (AAAA-MM-DD): ")
                novo_horario = input("Novo Horário (HH:MM:SS): ")


                cursor.execute(
                    """
                    UPDATE agendamentos
                    SET data_agendamento = %s,
                    horario = %s
                    WHERE id_agendamento = %s
                    AND status_agendamento = %s
                    """,
                    (nova_data,novo_horario,id_agendamento,"Agendado")
                )

                conexao.commit()

                if cursor.rowcount > 0:
                    print("Agendamento alterado com sucesso!")
                else:
                    print("Agendamento não encontrado ou não esta ativo.")

            ## SAIR DO SISTEMA

            elif opcao == "9":
                print("\nSaindo do Sistema Nexus Agenda...")
                break

            else:
                print("\nOpção Inválida. Tente Novamente.")

        cursor.close()



except Error as erro:
    print(f"Erro ao conectar ao MySQL: {erro}")

finally:
    # Fechando a conexão com o banco:
    if 'conexao' in locals() and conexao.is_connected():
        conexao.close()
