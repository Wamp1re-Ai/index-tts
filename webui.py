import os
import shutil
import sys
import threading
import time

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "indextts"))

import gradio as gr
from indextts.utils.webui_utils import next_page, prev_page

from indextts.infer import IndexTTS
from tools.i18n.i18n import I18nAuto

i18n = I18nAuto(language="en_US")
MODE = 'local'
tts = IndexTTS(model_dir="checkpoints",cfg_path="checkpoints/config.yaml")

os.makedirs("outputs/tasks",exist_ok=True)
os.makedirs("prompts",exist_ok=True)


def gen_single(prompt, text, infer_mode, progress=gr.Progress()):
    output_path = None
    if not output_path:
        output_path = os.path.join("outputs", f"spk_{int(time.time())}.wav")
    # set gradio progress
    tts.gr_progress = progress
    if infer_mode == "普通推理":
        output = tts.infer(prompt, text, output_path) # 普通推理
    else:
        output = tts.infer_fast(prompt, text, output_path) # 批次推理
    return gr.update(value=output,visible=True)

def update_prompt_audio():
    update_button = gr.update(interactive=True)
    return update_button


with gr.Blocks() as demo:
    mutex = threading.Lock()
    gr.HTML('''
    <h2><center>IndexTTS: An Industrial-Level Controllable and Efficient Zero-Shot Text-To-Speech System</h2>

<p align="center">
<a href='https://arxiv.org/abs/2502.05512'><img src='https://img.shields.io/badge/ArXiv-2502.05512-red'></a>
    ''')
    with gr.Tab(i18n("音频生成")):
        with gr.Row():
            os.makedirs("prompts",exist_ok=True)
            prompt_audio = gr.Audio(label=i18n("请上传参考音频"),key="prompt_audio",
                                    sources=["upload","microphone"],type="filepath")
            prompt_list = os.listdir("prompts")
            default = ''
            if prompt_list:
                default = prompt_list[0]
            with gr.Column():
                input_text_single = gr.TextArea(label=i18n("请输入目标文本"),key="input_text_single")
                infer_mode = gr.Radio(choices=[i18n("普通推理"), i18n("批次推理")], label=i18n("选择推理模式（批次推理：更适合长句，性能翻倍）"),value=i18n("普通推理"))
                gen_button = gr.Button(i18n("生成语音"),key="gen_button",interactive=True)
            output_audio = gr.Audio(label=i18n("生成结果"), visible=True,key="output_audio")

    prompt_audio.upload(update_prompt_audio,
                         inputs=[],
                         outputs=[gen_button])

    gen_button.click(gen_single,
                     inputs=[prompt_audio, input_text_single, infer_mode],
                     outputs=[output_audio])


def setup_cloudflare_tunnel():
    """Setup Cloudflare tunnel for public URL access"""
    try:
        import subprocess
        import threading
        import time

        print("🌐 Setting up Cloudflare tunnel for public access...")

        # Install cloudflared if not available
        try:
            subprocess.run(['cloudflared', '--version'], capture_output=True, check=True)
            print("✅ cloudflared is already installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("📦 Installing cloudflared...")
            # Install cloudflared
            subprocess.run([
                'wget', '-q',
                'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb'
            ], check=True)
            subprocess.run(['dpkg', '-i', 'cloudflared-linux-amd64.deb'], check=True)
            print("✅ cloudflared installed successfully")

        # Start tunnel in background
        def start_tunnel():
            try:
                process = subprocess.Popen([
                    'cloudflared', 'tunnel', '--url', 'http://localhost:7860'
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                # Wait for tunnel URL
                for line in process.stdout:
                    if 'trycloudflare.com' in line or 'cloudflare.com' in line:
                        url = line.strip().split()[-1]
                        if url.startswith('http'):
                            print(f"🔗 Public URL: {url}")
                            print(f"🌍 Your IndexTTS interface is now accessible at: {url}")
                            break

            except Exception as e:
                print(f"⚠️  Cloudflare tunnel setup failed: {e}")
                print("💡 Falling back to local access only")

        # Start tunnel in background thread
        tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
        tunnel_thread.start()

        # Give tunnel time to start
        time.sleep(3)
        return True

    except Exception as e:
        print(f"⚠️  Cloudflare tunnel setup failed: {e}")
        print("💡 Continuing with local access only")
        return False

if __name__ == "__main__":
    import sys

    # Detect environment
    IN_COLAB = 'google.colab' in sys.modules
    IN_KAGGLE = 'kaggle_secrets' in sys.modules or os.path.exists('/kaggle')

    # Setup Cloudflare tunnel for public access (except in Colab which has built-in sharing)
    use_cloudflare = False
    if not IN_COLAB:
        use_cloudflare = setup_cloudflare_tunnel()

    # Configure launch parameters based on environment
    if IN_COLAB:
        # Colab configuration - use built-in sharing
        print("🚀 Starting IndexTTS on Google Colab...")
        print("🔗 Public URL will be provided by Colab's built-in sharing")
        demo.queue(20)
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=True,  # Create public URL for Colab
            debug=False,
            quiet=False
        )
    elif IN_KAGGLE:
        # Kaggle configuration with Cloudflare tunnel
        print("🚀 Starting IndexTTS on Kaggle...")
        if use_cloudflare:
            print("🌐 Public URL will be provided by Cloudflare tunnel (see above)")
        else:
            print("🔗 Interface will be available in Kaggle's output panel")
        demo.queue(20)
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,  # Use Cloudflare tunnel instead
            debug=False,
            quiet=False
        )
    else:
        # Local development configuration with Cloudflare tunnel
        print("🚀 Starting IndexTTS locally...")
        if use_cloudflare:
            print("🌐 Public URL provided by Cloudflare tunnel (see above)")
            print("🏠 Local access: http://localhost:7860")
        else:
            print("🏠 Local access only: http://localhost:7860")
        demo.queue(20)
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,  # Use Cloudflare tunnel for public access
            debug=False,
            quiet=False
        )
