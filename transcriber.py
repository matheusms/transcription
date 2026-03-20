from faster_whisper import WhisperModel

class Transcriber:
    def __init__(self, model_size="small"):
        """
        Inicializa o transcritor (Whisper local)
        model_size pode ser: tiny, base, small, medium, large-v3
        """
        print(f"Carregando modelo Whisper ({model_size})...")
        # Usar cpu por padrão, mas pode mudar para 'cuda' se tiver GPU NVIDIA
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio_path):
        """
        Realiza a transcrição do arquivo de áudio
        """
        print(f"Iniciando transcrição do áudio: {audio_path}")
        try:
            segments, info = self.model.transcribe(audio_path, beam_size=5)
            
            print(f"Idioma detectado: {info.language} (probabilidade: {info.language_probability:.2f})")
            
            def format_time(seconds):
                s = int(seconds)
                h = s // 3600
                m = (s % 3600) // 60
                sec = s % 60
                if h > 0:
                    return f"{h:02d}:{m:02d}:{sec:02d}"
                return f"{m:02d}:{sec:02d}"
                
            texto_completo = []
            for segment in segments:
                linha = f"[{format_time(segment.start)} -> {format_time(segment.end)}] {segment.text}"
                texto_completo.append(linha)
                print(linha)
                
            transcricao_final = "\n".join(texto_completo)
            print("Transcrição concluída com sucesso!")
            return transcricao_final
        except Exception as e:
            print(f"Erro ao transcrever {audio_path}: {str(e)}")
            return ""
