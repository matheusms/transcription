import os
import glob
import sys
import threading
import time
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
    
    # Menu lateral
    st.sidebar.header("⚙️ Configurações")
    
    # Caminho da pasta de vídeos
    videos_dir = st.sidebar.text_input(
        "📂 Caminho da pasta de vídeos", 
        value="videos",
        help="Insira o caminho onde os vídeos estão localizados (ex: C:/MeusVideos)."
    )
    
    # O output agora será guardado DENTRO da pasta de vídeos, para que os resumos acompanhem a pasta original
    output_dir = os.path.join(videos_dir, "output") if videos_dir.strip() else "output"
    
    # Garantir pastas
    try:
        os.makedirs(videos_dir, exist_ok=True)
    except Exception as e:
        st.sidebar.error(f"Não foi possível acessar a pasta de vídeos: {e}")
        
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception:
        pass
    
    # 1. Seleção de Vídeo
    video_files = []
    if os.path.exists(videos_dir):
        video_files = glob.glob(os.path.join(videos_dir, "*.mp4")) + glob.glob(os.path.join(videos_dir, "*.mkv"))
        
    video_names = [os.path.basename(v) for v in video_files]
    
    if not video_names:
        st.sidebar.warning(f"Nenhum vídeo (mp4/mkv) encontrado na pasta '{videos_dir}'.")
        video_selecionado = None
        modo_processamento = "Vídeo Individual"
        videos_para_processar = []
    else:
        modo_processamento = st.sidebar.radio("Modo de Processamento", ["Vídeo Individual", "Todos da Pasta"])
        if modo_processamento == "Vídeo Individual":
            video_selecionado = st.sidebar.selectbox("Escolha o vídeo", video_names)
            videos_para_processar = [video_selecionado]
        else:
            st.sidebar.info(f"O sistema irá processar os {len(video_names)} vídeos sequencialmente.")
            video_selecionado = video_names[-1] if video_names else None # O último ficará em destaque no cache
            videos_para_processar = video_names
        
    # 2. Seleção de Modelo
    modelo_selecionado = st.sidebar.radio("IA para o Resumo", ["Gemini (Nuvem/Rápido)", "Local (Transformers/Lento)"])
    model_type = "gemini" if "Gemini" in modelo_selecionado else "local"
    
    gemini_model_version = "gemini-2.5-flash"
    if model_type == "gemini":
        modelos_nuvem = {
            "Gemini 2.5 Flash": "gemini-2.5-flash",
            "Gemini 3 Flash": "gemini-3-flash-preview",
            "Gemini 3.1 Flash Lite": "gemini-3.1-flash-lite-preview",
            "Gemma 3 27B": "gemma-3-27b-it",
            "Gemma 3 12B": "gemma-3-12b-it",
            "Gemma 3 4B": "gemma-3-4b-it",
            "Gemma 3 2B": "gemma-3n-e2b-it",
            "Gemma 3 1B": "gemma-3-1b-it",
            "Gemma 4 31B": "gemma-4-31b-it",
            "Gemma 4 26B": "gemma-4-26b-a4b-it"
        }
        gemini_model_name = st.sidebar.selectbox("Versão do Modelo API", list(modelos_nuvem.keys()))
        gemini_model_version = modelos_nuvem[gemini_model_name]
    
    tamanho_whisper = st.sidebar.selectbox("Tamanho do Whisper (Transcrição)", ["tiny", "base", "small", "medium", "large-v3"], index=2)

    idioma_opcoes = {"Automático": "auto", "Português": "pt", "Inglês": "en", "Espanhol": "es"}
    idioma_selecionado = st.sidebar.selectbox("Idioma do Áudio", list(idioma_opcoes.keys()), index=1)
    idioma_whisper = idioma_opcoes[idioma_selecionado]

    # --- Auto-load cache logic ---
    if video_selecionado:
        video_full_path = os.path.join(videos_dir, video_selecionado)
        if st.session_state.get("current_video") != video_full_path:
            st.session_state["current_video"] = video_full_path
            st.session_state.pop("summary", None)
            st.session_state.pop("transcription", None)
            
            base_n = os.path.splitext(video_selecionado)[0]
            r_path = os.path.join(output_dir, f"{base_n}_resultado.txt")
            legacy_r_path = os.path.join("output", f"{base_n}_resultado.txt")
            
            path_to_load = r_path if os.path.exists(r_path) else (legacy_r_path if os.path.exists(legacy_r_path) else None)
            
            if path_to_load:
                try:
                    with open(path_to_load, "r", encoding="utf-8") as f:
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
        if st.button("▶️ Iniciar Processamento", type="primary", use_container_width=True, disabled=not videos_para_processar):
            
            # Area para os logs
            st.markdown("### 📜 Logs de Execução")
            log_container = st.empty()
            
            # Redirecionar stdout
            old_stdout = sys.stdout
            sys.stdout = StreamlitRedirect(log_container)
            
            try:
                extractor = None
                transcriber = None
                summarizer = None
                
                for idx, video_atual in enumerate(videos_para_processar):
                    if len(videos_para_processar) > 1:
                        print(f"\n==============================================")
                        print(f"🎬 [{idx+1}/{len(videos_para_processar)}] Processando: {video_atual}")
                        print(f"==============================================\n")
                    
                    video_path = os.path.join(videos_dir, video_atual)
                    base_name = os.path.splitext(video_atual)[0]
                    
                    result_path = os.path.join(output_dir, f"{base_name}_resultado.txt")
                    legacy_r_path = os.path.join("output", f"{base_name}_resultado.txt")
                    
                    path_to_load = result_path if os.path.exists(result_path) else (legacy_r_path if os.path.exists(legacy_r_path) else None)
                    
                    if path_to_load:
                        print(f"📁 Resultado já existe em {path_to_load}! Carregando do cache para economizar tempo...")
                        with open(path_to_load, "r", encoding="utf-8") as f:
                            content = f.read()
                            
                        parts = content.split("=== TRANSCRIÇÃO COMPLETA ===")
                        if len(parts) == 2:
                            summary_part = parts[0].split("=== RESUMO ===")[1].strip()
                            transcription_part = parts[1].strip()
                            st.session_state["summary"] = summary_part
                            st.session_state["transcription"] = transcription_part
                            print("✅ Resultados carregados com sucesso do cache!")
                        else:
                            print("⚠️ Arquivo de cache inválido. Por favor apague-o e tente novamente.")
                    
                    else:
                        if extractor is None:
                            print("⏳ Instanciando modelos IA (isso ocorrerá apenas uma vez)...")
                            extractor = AudioExtractor(output_dir=output_dir)
                            transcriber = Transcriber(model_size=tamanho_whisper)
                            summarizer = Summarizer(summarizer_type=model_type, gemini_model=gemini_model_version)
                            
                        print("\nIniciando fluxo...")
                        text = None
                        
                        # Cache intermediário de transcrição apenas
                        transcricao_path = os.path.join(output_dir, f"{base_name}_transcricao.txt")
                        
                        if os.path.exists(transcricao_path):
                            print("📁 Transcrição prévia encontrada no Cache! Pulando etapas do Áudio e do modelo Whisper...")
                            with open(transcricao_path, "r", encoding="utf-8") as f:
                                text = f.read()
                        else:
                            # Passo 1: Extrair Audio
                            audio_path = extractor.extract_audio(video_path)
                            
                            if audio_path:
                                # Passo 2: Transcrever
                                text = transcriber.transcribe(audio_path, language=idioma_whisper)
                                if text:
                                    # Salvar transcrição para não refazer do zero caso a API do Gemini dê erro de Tokens Limit
                                    with open(transcricao_path, "w", encoding="utf-8") as f:
                                        f.write(text)
                            else:
                                print(f"❌ Falha ao extrair o áudio de {video_atual}.")
                                
                        if text:
                            status_ui = st.empty()
                            summary = None
                            
                            for tentativa in range(3): # Tentará resumir até 3 vezes caso caia no Rate Limit
                                print(f"Chamando o modelo de resumo (Tentativa {tentativa+1}/3)...")
                                summary_temp = summarizer.summarize(text)
                                
                                # Verifica se retornou string de aviso de rate limit
                                if isinstance(summary_temp, str) and summary_temp.startswith("Erro") and ("Limite de cota" in summary_temp or "429" in summary_temp):
                                    if tentativa < 2:
                                        espera = 65
                                        print(f"⚠️ Limite da API (Tokens) atingido. Pausando por {espera} segundos...")
                                        for i in range(espera, 0, -1):
                                            status_ui.warning(f"⏳ Cota da API estourou! Aguardando reset... O processamento continuará em: {i}s")
                                            time.sleep(1)
                                        status_ui.empty()
                                    else:
                                        print("❌ Falha permanente: Limite da IA expirou repetidamente. O resumo não será salvo! Tente rotacionar o modelo na Sidebar.")
                                        summary = None
                                        break
                                # Verifica se retornou outro erro grave ("Erro Gemini:", "Erro Local:")
                                elif isinstance(summary_temp, str) and summary_temp.startswith("Erro"):
                                    print(f"❌ Falha na API durante a geração do resumo: {summary_temp}")
                                    print("O resultado não será salvo. Tente rotacionar o modelo na Sidebar.")
                                    summary = None
                                    break
                                # Se deu tudo certo
                                else:
                                    summary = summary_temp
                                    break
                                    
                            status_ui.empty()

                            if summary:
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
                                
                                if os.path.exists(transcricao_path):
                                    try:
                                        os.remove(transcricao_path)
                                        print("🗑️ Arquivo de transcrição intermediário excluído.")
                                    except Exception:
                                        pass
                                
                                print("✅ Fluxo finalizado com sucesso!")
                            
                print("\n🎉 Processamento concluído com sucesso!")
            
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
