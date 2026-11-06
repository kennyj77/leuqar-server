import os
import tempfile
from elevenlabs.client import ElevenLabs
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Importa os módulos que já estruturamos
from brain import processar_resposta_livre
from database import inicializar_banco

# Inicializa o banco de dados SQLite no servidor
inicializar_banco()

app = FastAPI(
    title="Leuqar Cloud API",
    description="API para conectar a Leuqar de bolso ao celular via lapela/Bluetooth",
)

# Chave e cliente da ElevenLabs para síntese de voz na nuvem
API_KEY_ELEVEN = "sk_fc92184b5843aa04e6902b6410afc3bb0282d462e67ad532"
VOICE_ID = "Eo0ahm0OIs7wZBd0coK4"
client_eleven = ElevenLabs(api_key=API_KEY_ELEVEN)


class RequisiçãoComando(BaseModel):
  texto: str


@app.get("/")
def status():
  """Endpoint de checagem para ver se o servidor está online."""
  return {"status": "ok", "mensagem": "Cérebro da Leuqar funcionando na nuvem!"}


@app.post("/perguntar-texto")
def perguntar_texto(payload: RequisiçãoComando):
  """Recebe o texto reconhecido pelo celular e devolve apenas a resposta em texto.

  Ideal para conexões rápidas ou economizar dados móveis.
  """
  if not payload.texto.strip():
    raise HTTPException(status_code=400, detail="Texto vazio.")

  resposta_texto = processar_resposta_livre(payload.texto)
  return {"resposta": resposta_texto}


@app.post("/perguntar-audio")
def perguntar_audio(payload: RequisiçãoComando):
  """Recebe o texto do celular, processa na Groq e devolve o arquivo de áudio MP3.

  pronto para ser tocado direto no seu fone Bluetooth!
  """
  if not payload.texto.strip():
    raise HTTPException(status_code=400, detail="Texto vazio.")

  # 1. Processa a resposta usando o cérebro e memórias de longo prazo
  resposta_texto = processar_resposta_livre(payload.texto)
  print(f"[API Cloud - Leuqar]: {resposta_texto}")

  try:
    # 2. Sintetiza o áudio via ElevenLabs
    audio_stream = client_eleven.text_to_speech.convert(
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        text=resposta_texto,
        output_format="mp3_44100_128",
    )

    # 3. Salva em um arquivo temporário no servidor
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    with open(temp_file.name, "wb") as f:
      for chunk in audio_stream:
        if chunk:
          f.write(chunk)

    # 4. Envia o arquivo MP3 de volta para o smartphone
    return FileResponse(
        path=temp_file.name,
        media_type="audio/mpeg",
        filename="resposta_leuqar.mp3",
    )

  except Exception as e:
    print(f"[Erro no TTS Nuvem]: {e}")
    raise HTTPException(
        status_code=500, detail=f"Erro ao gerar sintese de voz: {e}"
    )


if __name__ == "__main__":
  import uvicorn

  uvicorn.run(app, host="0.0.0.0", port=8000)