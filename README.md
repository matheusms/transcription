# Video Transcription & Summarization

Uma ferramenta em Python para processar vídeos (MP4, MKV), extrair seus áudios, obter a transcrição completa utilizando inteligência artificial local (Whisper), e gerar um resumo dos principais pontos da reunião (usando a API do Google Gemini ou um modelo local).

## 🚀 Funcionalidades

- **Extração de Áudio**: Lê arquivos de vídeo e extrai o áudio sem perda de qualidade.
- **Transcrição Local**: Utiliza a biblioteca `faster-whisper` rodando em seu computador, sem necessidade de enviar os áudios sensíveis para a nuvem.
- **Resumo Inteligente**: Suporta dois módulos - pode resumir via API do **Google Gemini** para maior inteligência analítica, ou via modelo **Local** (`transformers`) de forma 100% gratuita na sua máquina.
- **Tolerância a Limites**: Detecta limites de cota e falhas (Rate Limit) caso use o serviço em nuvem.

## 📋 Pré-requisitos

- Python 3.9+ instalado
- (Opcional, mas recomendado) Placa de vídeo dedicada capaz de rodar modelos IA.

## 🛠️ Instalação

Abra o terminal na pasta do projeto e execute os seguintes comandos:

1. **Crie um ambiente virtual:**
```bash
python -m venv .venv
```

2. **Ative o ambiente:**
- Em Windows (PowerShell):
  ```bash
  .\.venv\Scripts\Activate.ps1
  ```
- Em Linux/Mac:
  ```bash
  source .venv/bin/activate
  ```

3. **Instale as dependências:**
```bash
pip install moviepy faster-whisper transformers google-generativeai python-dotenv torch
```

## ⚙️ Configuração

Crie um arquivo `.env` na raiz do projeto (se já não existir) e adicione:

```ini
# Chave da API do Google Gemini (se for utilizar a nuvem para o resumo)
GEMINI_API_KEY="AIzaSyBN...suachaveaqui"

# Escolha o tipo de modelo para resumo: "gemini" ou "local"
SUMMARIZER_TYPE="gemini"
```

## 🌐 Interface Web (Streamlit)

Adicionamos uma interface gráfica interativa para facilitar o uso. Você pode escolher os vídeos, selecionar a IA de resumo de sua preferência, visualizar os logs em tempo real e ver os resultados diretamente no navegador.

Para rodar a interface web, use o comando:
```bash
streamlit run app.py
```

## ▶️ Como Usar (Modo Terminal)

Caso prefira o modo clássico sem interface gráfica:
1. Crie uma pasta chamada `videos` na raiz do projeto.
2. Coloque lá todos os seus vídeos de reuniões ou aulas (arquivos `.mp4` ou `.mkv`).
3. Com o ambiente virtual ativado, rode o script principal:

```bash
python main.py
```

4. Verifique a pasta `output/` gerada automaticamente. Você encontrará os áudios temporários extraídos (`.wav`) e os arquivos finais `.txt` contendo o resumo executivo e a transcrição completa.
