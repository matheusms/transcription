import os
from moviepy import VideoFileClip

class AudioExtractor:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def extract_audio(self, video_path):
        """
        Extrai o áudio de um vídeo e salva como um arquivo .wav
        """
        print(f"Extraindo áudio de: {video_path}")
        try:
            video = VideoFileClip(video_path)
            
            # Gerar o nome do arquivo de áudio baseado no vídeo
            base_name = os.path.basename(video_path)
            name_without_ext = os.path.splitext(base_name)[0]
            audio_path = os.path.join(self.output_dir, f"{name_without_ext}.wav")
            
            # Extrair e salvar o áudio
            video.audio.write_audiofile(audio_path, logger=None)
            video.close()
            
            print(f"Áudio extraído com sucesso: {audio_path}")
            return audio_path
        except Exception as e:
            print(f"Erro ao extrair áudio de {video_path}: {str(e)}")
            return None
