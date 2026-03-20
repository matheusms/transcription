import os
import glob
from dotenv import load_dotenv

# Importando nossos modulos
from audio_extractor import AudioExtractor
from transcriber import Transcriber
from summarizer import Summarizer

def main():
    # Carregar variaveis do .env (como GEMINI_API_KEY)
    load_dotenv()
    
    videos_dir = "videos"
    output_dir = "output"
    
    # Criar pasta videos se nao existir
    if not os.path.exists(videos_dir):
        os.makedirs(videos_dir)
        print(f"Pasta '{videos_dir}' criada. Adicione seus vídeos lá e rode o script novamente.")
        return

    # Buscar vídeos na pasta (mp4, mkv)
    video_files = glob.glob(os.path.join(videos_dir, "*.mp4")) + glob.glob(os.path.join(videos_dir, "*.mkv"))
    if not video_files:
        print(f"Nenhum vídeo encontrado na pasta '{videos_dir}'.")
        return

    # Inicializar os módulos
    extractor = AudioExtractor(output_dir=output_dir)
    transcriber = Transcriber(model_size="small")  # Use "base", "small", ou "medium" dependendo do seu PC
    
    # Escolhe o tipo de sumarizador com base no .env (default: gemini)
    sum_type = os.getenv("SUMMARIZER_TYPE", "gemini")
    summarizer = Summarizer(summarizer_type=sum_type)

    for video_path in video_files:
        print("\n" + "="*50)
        print(f"Processando vídeo: {os.path.basename(video_path)}")
        print("="*50)
        
        # 1. Extração do Áudio
        audio_path = extractor.extract_audio(video_path)
        if not audio_path:
            continue
            
        # 2. Transcrição    
        text = transcriber.transcribe(audio_path)
        
        if not text:
            print("Nenhum texto pôde ser transcrito.")
            continue
            
        # 3. Resumo
        summary = summarizer.summarize(text)
        
        # 4. Salvar Resultados
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        result_path = os.path.join(output_dir, f"{base_name}_resultado.txt")
        
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(f"--- RESULTADO: {base_name} ---\n\n")
            f.write("=== RESUMO ===\n")
            f.write(summary + "\n\n")
            f.write("=== TRANSCRIÇÃO COMPLETA ===\n")
            f.write(text + "\n")
            
        print(f"\nConcluído! Processamento salvo em -> {result_path}")
        
    print("\nTodos os vídeos foram processados com sucesso.")

if __name__ == "__main__":
    main()
