import os
from google import genai
from google.api_core import exceptions as google_exceptions
from transformers import pipeline

class Summarizer:
    def __init__(self, summarizer_type="gemini"):
        """
        Inicializa o módulo de resumo: pode ser 'gemini' (nuvem) ou 'local' (transformers)
        """
        self.summarizer_type = summarizer_type.lower()
        self.local_summarizer = None
        
        if self.summarizer_type == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                self.client = genai.Client(api_key=api_key)
                print("Summarizer configurado para API Gemini.")
            else:
                print("AVISO: Chave GEMINI_API_KEY não encontrada. Alternando para modelo local.")
                self.summarizer_type = "local"
                
        if self.summarizer_type == "local":
            print("Carregando modelo local de resumo (facebook/bart-large-cnn)... Isso pode demorar na primeira vez.")
            # max_length será ajustado na hora de fazer o resumo
            self.local_summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    def summarize(self, text):
        if not text or len(text.strip()) < 50:
            return "Texto muito curto para ser resumido."
            
        print(f"Gerando resumo usando modo: {self.summarizer_type}...")
        
        if self.summarizer_type == "gemini":
            try:
                prompt = (
                    "Faça um resumo executivo direto e claro da seguinte transcrição de reunião. "
                    "Destaque os pontos principais, decisões tomadas e próximos passos (se houver):\n\n"
                    f"{text}"
                )
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                # The google-genai SDK handles errors differently
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    print("ERRO DE RATE LIMIT: O limite de uso da API do Gemini foi excedido.")
                    return "Erro: Limite de cota da API Gemini atingido. Não foi possível gerar o resumo."
                print(f"Erro ao resumi-lo via API Gemini: {str(e)}")
                return f"Erro Gemini: {str(e)}"
                
        elif self.summarizer_type == "local":
            try:
                # Local HuggingFace Transformers
                # o tamanho máximo do resumo baseado no texto de entrada
                input_length = len(text.split())
                max_len = min(130, max(30, int(input_length * 0.5)))
                
                resumo = self.local_summarizer(text, max_length=max_len, min_length=30, do_sample=False)
                return resumo[0]['summary_text']
            except Exception as e:
                print(f"Erro no modelo local: {str(e)}")
                return f"Erro Local: {str(e)}"
