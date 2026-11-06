import sqlite3


def inicializar_banco():
  conexao = sqlite3.connect("leuqar_conhecimento.db")
  cursor = conexao.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS memorias (
            chave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS fatos_usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT,
            conteudo TEXT UNIQUE
        )
    """)
  conexao.commit()
  conexao.close()


def salvar_memoria(chave, valor):
  conexao = sqlite3.connect("leuqar_conhecimento.db")
  cursor = conexao.cursor()
  cursor.execute(
      "INSERT OR REPLACE INTO memorias (chave, valor) VALUES (?, ?)",
      (chave, valor),
  )
  conexao.commit()
  conexao.close()


def ler_memoria(chave):
  conexao = sqlite3.connect("leuqar_conhecimento.db")
  cursor = conexao.cursor()
  cursor.execute("SELECT valor FROM memorias WHERE chave = ?", (chave,))
  resultado = cursor.fetchone()
  conexao.close()
  return resultado[0] if resultado else None


def salvar_fato(categoria, conteudo):
  try:
    conexao = sqlite3.connect("leuqar_conhecimento.db")
    cursor = conexao.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO fatos_usuario (categoria, conteudo) VALUES (?,"
        " ?)",
        (categoria, conteudo),
    )
    conexao.commit()
    conexao.close()
    return True
  except Exception as e:
    print(f"[Erro ao salvar fato]: {e}")
    return False


def recuperar_todos_fatos():
  conexao = sqlite3.connect("leuqar_conhecimento.db")
  cursor = conexao.cursor()
  cursor.execute("SELECT id, categoria, conteudo FROM fatos_usuario")
  resultados = cursor.fetchall()
  conexao.close()
  return resultados


def apagar_ultimo_fato():
  """Apaga o fato mais recente inserido no banco de dados."""
  try:
    conexao = sqlite3.connect("leuqar_conhecimento.db")
    cursor = conexao.cursor()
    # Pega o último ID inserido
    cursor.execute("SELECT id, conteudo FROM fatos_usuario ORDER BY id DESC LIMIT 1")
    ultimo = cursor.fetchone()
    if ultimo:
      cursor.execute("DELETE FROM fatos_usuario WHERE id = ?", (ultimo[0],))
      conexao.commit()
      conexao.close()
      return ultimo[1]
    conexao.close()
    return None
  except Exception as e:
    print(f"[Erro ao apagar último fato]: {e}")
    return None


def apagar_fatos_por_termo(termo):
  """Apaga fatos que contenham um termo específico."""
  try:
    conexao = sqlite3.connect("leuqar_conhecimento.db")
    cursor = conexao.cursor()
    cursor.execute(
        "DELETE FROM fatos_usuario WHERE conteudo LIKE ?", (f"%{termo}%",)
    )
    linhas_afetadas = cursor.rowcount
    conexao.commit()
    conexao.close()
    return linhas_afetadas > 0
  except Exception as e:
    print(f"[Erro ao apagar fatos por termo]: {e}")
    return False


inicializar_banco()