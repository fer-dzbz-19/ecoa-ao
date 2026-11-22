
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "ecoacao.db"


# Conexao com o banco de dados
def conectar_banco():
    conexao = sqlite3.connect(DATABASE)
    conexao.row_factory = sqlite3.Row
    return conexao


# Criacao da tabela de habitos
def criar_tabela():
    conexao = conectar_banco()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS habitos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            quantidade REAL NOT NULL,
            unidade TEXT NOT NULL,
            indicador TEXT NOT NULL,
            data_registro TEXT NOT NULL
        )
    """)

    conexao.commit()
    conexao.close()


# Pagina inicial
@app.route("/")
def inicio():
    return jsonify({
        "projeto": "EcoAcao",
        "mensagem": "Bem-vindo ao EcoAcao!",
        "status": "Sistema funcionando"
    })


# Registrar um novo habito
@app.route("/api/habitos", methods=["POST"])
def registrar_habito():

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({"erro": "Envie os dados em JSON."}), 400

    campos = ["nome", "categoria", "quantidade", "unidade", "indicador"]

    if any(campo not in dados for campo in campos):
        return jsonify({
            "erro": "Todos os campos sao obrigatorios."
        }), 400

    nome = dados["nome"]
    categoria = dados["categoria"]
    unidade = dados["unidade"]
    indicador = dados["indicador"]

    if not all(isinstance(valor, str) and valor.strip()
               for valor in [nome, categoria, unidade, indicador]):
        return jsonify({"erro": "Os campos de texto sao invalidos."}), 400

    try:
        quantidade = float(dados["quantidade"])
    except (ValueError, TypeError):
        return jsonify({"erro": "Quantidade invalida."}), 400

    if quantidade <= 0:
        return jsonify({"erro": "A quantidade deve ser positiva."}), 400

    indicadores_validos = {
        "agua_litros",
        "reciclagem_kg",
        "co2_kg"
    }

    if indicador not in indicadores_validos:
        return jsonify({"erro": "Indicador nao reconhecido."}), 400

    conexao = conectar_banco()

    conexao.execute("""
        INSERT INTO habitos
        (nome, categoria, quantidade, unidade, indicador, data_registro)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        nome.strip(),
        categoria.strip(),
        quantidade,
        unidade.strip(),
        indicador,
        datetime.now().isoformat(timespec="seconds")
    ))

    conexao.commit()
    conexao.close()

    return jsonify({
        "mensagem": "Habito registrado com sucesso!",
        "habito": nome
    }), 201


# Consultar historico de habitos
@app.route("/api/habitos", methods=["GET"])
def listar_habitos():

    conexao = conectar_banco()

    registros = conexao.execute("""
        SELECT * FROM habitos
        ORDER BY id DESC
    """).fetchall()

    conexao.close()

    habitos = [dict(registro) for registro in registros]

    return jsonify(habitos)


# Consultar indicadores do dashboard
@app.route("/api/dashboard", methods=["GET"])
def dashboard():

    conexao = conectar_banco()

    totais = conexao.execute("""
        SELECT indicador, SUM(quantidade) AS total
        FROM habitos
        GROUP BY indicador
    """).fetchall()

    quantidade_habitos = conexao.execute("""
        SELECT COUNT(*) AS total FROM habitos
    """).fetchone()

    conexao.close()

    indicadores = {
        registro["indicador"]: registro["total"]
        for registro in totais
    }

    return jsonify({
        "total_habitos": quantidade_habitos["total"],
        "agua_litros": indicadores.get("agua_litros", 0),
        "reciclagem_kg": indicadores.get("reciclagem_kg", 0),
        "co2_kg": indicadores.get("co2_kg", 0)
    })


# Inicializacao do sistema
if __name__ == "__main__":
    criar_tabela()
    app.run(debug=True)
