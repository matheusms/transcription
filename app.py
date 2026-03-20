import os
import glob
import sys
import threading
import streamlit as st
from dotenv import load_dotenv

# Imports do nosso backend
from audio_extractor import AudioExtractor
from transcriber import Transcriber
from summarizer import Summarizer

# --- Classe para redirecionar o PRINT (stdout) para a interface do Streamlit ---
class StreamlitRedirect(object):
    def __init__(self, text_area):
        self.text_area = text_area
        self.log_content = ""
        self.lock = threading.Lock()

    def write(self, text):
        with self.lock:
            self.log_content += text
            # Usando markdown ou code para atualizar o conteudo visual
            self.text_area.code(self.log_content, language="bash")
            
    def flush(self):
        pass

def main():
    st.set_page_config(page_title="Video Summarizer IA", layout="wide")
    st.title("🎙️ Transcrição e Resumo de Vídeos com IA")
    
    load_dotenv()
    videos_dir = "videos"
    output_dir = "output"
    
    # Garantir pastas
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Menu lateral
    st.sidebar.header("⚙️ Configurações")
    
    # 1. Seleção de Vídeo
    video_files = glob.glob(os.path.join(videos_dir, "*.mp4")) + glob.glob(os.path.join(videos_dir, "*.mkv"))
    video_names = [os.path.basename(v) for v in video_files]
    
    if not video_names:
        st.sidebar.warning("Nenhum vídeo encontrado. Coloque vídeos (mp4/mkv) na pasta 'videos'.")
        video_selecionado = None
    else:
        video_selecionado = st.sidebar.selectbox("Escolha o vídeo", video_names)
        
    # 2. Seleção de Modelo
    modelo_selecionado = st.sidebar.radio("IA para o Resumo", ["Gemini (Nuvem/Rápido)", "Local (Transformers/Lento)"])
    model_type = "gemini" if "Gemini" in modelo_selecionado else "local"
    
    tamanho_whisper = st.sidebar.selectbox("Tamanho do Whisper (Transcrição)", ["tiny", "base", "small", "medium", "large-v3"], index=2)

    # --- Auto-load cache logic ---
    if video_selecionado:
        if st.session_state.get("current_video") != video_selecionado:
            st.session_state["current_video"] = video_selecionado
            st.session_state.pop("summary", None)
            st.session_state.pop("transcription", None)
            
            base_n = os.path.splitext(video_selecionado)[0]
            r_path = os.path.join(output_dir, f"{base_n}_resultado.txt")
            if os.path.exists(r_path):
                try:
                    with open(r_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    parts = content.split("=== TRANSCRIÇÃO COMPLETA ===")
                    if len(parts) == 2:
                        st.session_state["summary"] = parts[0].split("=== RESUMO ===")[1].strip()
                        st.session_state["transcription"] = parts[1].strip()
                except Exception:
                    pass

    # Layout Principal
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Processamento")
        if st.button("▶️ Iniciar Processamento", type="primary", use_container_width=True, disabled=not video_selecionado):
            
            # Area para os logs
            st.markdown("### 📜 Logs de Execução")
            log_container = st.empty()
            
            # Redirecionar stdout
            old_stdout = sys.stdout
            sys.stdout = StreamlitRedirect(log_container)
            
            try:
                # Recuperar caminho absoluto do vídeo
                video_path = os.path.join(videos_dir, video_selecionado)
                base_name = os.path.splitext(video_selecionado)[0]
                
                result_path = os.path.join(output_dir, f"{base_name}_resultado.txt")
                
                if os.path.exists(result_path):
                    print("📁 Resultado já existe! Carregando do cache para economizar tempo...")
                    with open(result_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    parts = content.split("=== TRANSCRIÇÃO COMPLETA ===")
                    if len(parts) == 2:
                        summary_part = parts[0].split("=== RESUMO ===")[1].strip()
                        transcription_part = parts[1].strip()
                        st.session_state["summary"] = summary_part
                        st.session_state["transcription"] = transcription_part
                        print("\n✅ Resultados carregados com sucesso do cache!")
                    else:
                        print("⚠️ Arquivo de cache inválido. Por favor apague-o e tente novamente.")
                
                else:
                    print("Iniciando fluxo...")
                    # Instanciar os objetos
                    extractor = AudioExtractor(output_dir=output_dir)
                    transcriber = Transcriber(model_size=tamanho_whisper)
                    summarizer = Summarizer(summarizer_type=model_type)
                    
                    # Passo 1: Extrair Audio
                    audio_path = extractor.extract_audio(video_path)
                    
                    if audio_path:
                        # Passo 2: Transcrever
                        text = transcriber.transcribe(audio_path)
                        
                        if text:
                            # Passo 3: Resumir
                            print("Chamando o modelo de resumo...")
                            summary = summarizer.summarize(text)
                            
                            # Salvar texto fisicamente
                            with open(result_path, "w", encoding="utf-8") as f:
                                f.write(f"--- RESULTADO: {base_name} ---\n\n")
                                f.write("=== RESUMO ===\n")
                                f.write(summary + "\n\n")
                                f.write("=== TRANSCRIÇÃO COMPLETA ===\n")
                                f.write(text + "\n")
                                
                            # Salvar os resultados no session_state para exibir na coluna 2
                            st.session_state["summary"] = summary
                            st.session_state["transcription"] = text
                            
                            print("\n✅ Fluxo finalizado com sucesso!")
                        else:
                            print("❌ Falha na transcrição.")
                    else:
                        print("❌ Falha ao extrair o áudio.")
            
            except Exception as e:
                print(f"❌ Ocorreu um erro inesperado: {str(e)}")
            finally:
                # Restaurar stdout normal do Python
                sys.stdout = old_stdout

    with col2:
        st.subheader("Resultados")
        # Mostrar apenas se existir no estado da sessão
        if "summary" in st.session_state and "transcription" in st.session_state:
            st.success("Pronto! Veja o resultado final abaixo:")
            st.markdown("#### 📑 Resumo Executivo")
            st.info(st.session_state["summary"])
            
            with st.expander("Ver Transcrição Completa"):
                st.write(st.session_state["transcription"])
        else:
            st.warning("O resultado aparecerá aqui após o processamento.")

if __name__ == "__main__":
    main()
