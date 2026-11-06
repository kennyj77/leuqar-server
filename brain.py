from groq import Groq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from database import (
    ler_memoria,
    salvar_fato,
    recuperar_todos_fatos,
    apagar_ultimo_fato,
    apagar_fatos_por_termo,
)

GROQ_API_KEY = "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"
client_groq = Groq(api_key=GROQ_API_KEY)


class CérebroNeural:

  def __init__(self):
    self.treinar_rede_neural()

  def treinar_rede_neural(self):
    dados_treino = [
        "olá", "tudo bem", "oi leuqar", "bom dia", "boa tarde", "boa noite", "e aí", "como você está", "como vai",
        "obrigado", "valeu", "muito obrigado", "agradeço", "ótimo", "perfeito", "maravilhoso",
        "quem é você", "qual o seu nome", "como você se chama", "o que você é", "quem criou você", "léo car", "leo car", "léo", "leo",
        "ajuda", "o que você faz", "quais seus comandos", "socorro", "me ajude", "o que você sabe fazer",
        "você está me ouvindo", "esta me ouvindo", "consegue me ouvir"
    ]
    rotulos_treino = [
        "saudacao", "saudacao", "saudacao", "saudacao", "saudacao", "saudacao", "saudacao", "saudacao", "saudacao",
        "agradecimento", "agradecimento", "agradecimento", "agradecimento", "agradecimento", "agradecimento", "agradecimento",
        "identidade", "identidade", "identidade", "identidade", "identidade", "identidade", "identidade", "identidade", "identidade",
        "ajuda", "ajuda", "ajuda", "ajuda", "ajuda", "ajuda",
        "ouvindo", "ouvindo", "ouvindo"
    ]
    self.vetorizador = TfidfVectorizer()
    X_vetorizado = self.vetorizador.fit_transform(dados_treino)
    self.modelo_neural = MLPClassifier(
        hidden_layer_sizes=(12,), max_iter=1500, random_state=42
    )
    self.modelo_neural.fit(X_vetorizado, rotulos_treino)

  def classificar_intencao(self, texto):
    try:
      texto_vetorizado = self.vetorizador.transform([texto])
      probabilidades = self.modelo_neural.predict_proba(texto_vetorizado)[0]
      max_prob = max(probabilidades)
      if max_prob > 0.40:
        return self.modelo_neural.predict(texto_vetorizado)[0]
    except Exception as e:
      print(f"[Aviso Neural]: {e}")
    return "desconhecido"


cerebro_neural = CérebroNeural()


def consultar_groq_nuvem(pergunta_usuario, nome_usuario):
  try:
    fatos = recuperar_todos_fatos()
    contexto_fatos = ""
    if fatos:
      contexto_fatos = "\nO que você já sabe de importante sobre o Pedro:\n" + "\n".join(
          [f"- [{cat}] {cont}" for _, cat, cont in fatos]
      )

    print("--> Consultando a inteligência da Groq na nuvem...")
    chat_completion = client_groq.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    f"Você é a Leuqar, assistente virtual e amiga de {nome_usuario}."
                    " Responda sempre em português do Brasil de forma extremamente natural,"
                    " fluída e humana, exatamente como uma pessoa conversando por voz."
                    " NUNCA use estruturas de tópicos com marcadores ou listas numeradas."
                    f" {contexto_fatos}"
                ),
            },
            {"role": "user", "content": pergunta_usuario},
        ],
        model="openai/gpt-oss-20b",
        temperature=0.75,
        max_tokens=600,
    )
    return chat_completion.choices[0].message.content
  except Exception as e:
    print(f"[Erro na Groq]: {e}")
    return (
        f"Poxa, {nome_usuario}, deu uma falha aqui na nuvem e não consegui"
        " consultar os detalhes agora."
    )


def processar_resposta_livre(pergunta_usuario):
  nome_usuario = ler_memoria("nome_usuario") or "Pedro"
  texto_lc = pergunta_usuario.lower().strip()

  # --- DETECTOR DE EXCLUSÃO DE MEMÓRIA ---
  if any(
      termo in texto_lc
      for termo in [
          "apague essa memória",
          "esqueça sobre isso",
          "apague nosso último assunto",
          "esqueça isso",
          "não é mais necessário",
          "apague o último",
          "esqueca o ultimo",
      ]
  ):
    apagado = apagar_ultimo_fato()
    if apagado:
      return (
          f"Pronto, {nome_usuario}! Apaguei da minha memória o último assunto:"
            f" '{apagado}'. Não vou mais lembrar disso."
      )
    else:
      return (
          f"Olha, {nome_usuario}, tentei procurar o último assunto salvo, mas"
            " minha lista de memórias já está limpinha!"
      )

  # Detector se quiser apagar algo específico (ex: "esqueça sobre [assunto]")
  if "esqueça sobre" in texto_lc or "apague sobre" in texto_lc:
    termo_busca = (
        texto_lc.replace("esqueça sobre", "")
        .replace("apague sobre", "")
        .strip()
    )
    if termo_busca:
      sucesso = apagar_fatos_por_termo(termo_busca)
      if sucesso:
        return (
            f"Pronto, {nome_usuario}! Removi tudo o que encontrei relacionado"
            f" a '{termo_busca}' das minhas memórias."
        )
      else:
        return (
            f"Não encontrei nenhuma memória gravada com o termo"
            f" '{termo_busca}', {nome_usuario}."
        )

  # --- DETECTOR DE SALVAMENTO DE MEMÓRIA ---
  if any(
      termo in texto_lc
      for termo in [
          "anote aí que",
          "lembre-se que",
          "lembra que",
          "guarde que",
          "anota que",
          "meu projeto é",
          "eu gosto de",
      ]
  ):
    salvar_fato("Gosto/Projeto", pergunta_usuario)
    return (
        f"Pode deixar, {nome_usuario}! Já salvei isso na minha memória de longo"
        " prazo para não esquecer."
    )

  if texto_lc in ["o que é", "qual é", "o que e", "qual e"]:
    return f"Ah, sim! Sobre o que exatamente você quer saber, {nome_usuario}?"

  if any(
      nome in texto_lc
      for nome in ["léo car", "leo car", "leocar", "léo", "leo"]
  ) and len(texto_lc.split()) <= 4:
    return (
        f"Sim, {nome_usuario}? Sou eu, a Leuqar, sua assistente virtual!"
        " Como posso ajudar?"
    )

  if "mouse" in texto_lc and (
      "quebrou" in texto_lc or "parou" in texto_lc or "defeito" in texto_lc
  ):
    return (
        f"Nossa, que situação chata, {nome_usuario}! Mas olha, relaxa que dá"
        " para ir quebrando o galho com o teclado enquanto você não resolve"
        " isso."
    )

  gatilhos_groq = [
      "o que foi",
      "o que é",
      "quem foi",
      "explique",
      "me conte",
      "como funciona",
      "qual a história",
      "fale sobre",
      "curiosidade",
      "o que você sabe sobre mim",
      "quais são minhas memórias",
  ]
  for gatilho in gatilhos_groq:
    if gatilho in texto_lc:
      if "sobre mim" in texto_lc or "memórias" in texto_lc:
        fatos = recuperar_todos_fatos()
        if fatos:
          resumo = ", ".join([f for _, _, f in fatos])
          return (
              f"Olha, nas minhas memórias de longo prazo sobre você, eu lembro"
              f" de: {resumo}. Se quiser que eu apague alguma, é só falar"
              " 'esqueça sobre isso'!"
          )
        else:
          return (
              f"Ainda não salvei fatos específicos sobre você, {nome_usuario}."
              " É só me dizer 'anote aí que...' que eu guardo!"
          )
      return consultar_groq_nuvem(pergunta_usuario, nome_usuario)

  intencao = cerebro_neural.classificar_intencao(texto_lc)

  if intencao == "saudacao" and len(texto_lc.split()) <= 4:
    return (
        f"Tudo ótimo por aqui, {nome_usuario}! E com você? Do que precisa"
        " hoje?"
    )

  elif intencao == "agradecimento" and len(texto_lc.split()) <= 4:
    return (
        f"Imagina, {nome_usuario}! Sabe que tô sempre por aqui para o que"
        " precisar."
    )

  elif intencao == "identidade" and len(texto_lc.split()) <= 4:
    return (
        f"Eu sou a Leuqar, sua assistente virtual feita em Python, {nome_usuario}"
        " — embora você goste de me chamar de Léo Car de vez em quando!"
    )

  elif intencao == "ajuda" and len(texto_lc.split()) <= 4:
    return (
        "Olha, eu consigo abrir programas, gerenciar notas, mexer nas pastas"
        " do Windows e agora guardar ou apagar memórias sobre você quando"
        " mandar!"
    )

  elif intencao == "ouvindo" and len(texto_lc.split()) <= 4:
    return (
        f"Tô sim, {nome_usuario}! Com os microfones ligados e te ouvindo"
        " direitinho."
    )

  return consultar_groq_nuvem(pergunta_usuario, nome_usuario)