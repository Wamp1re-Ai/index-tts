import json
import os
import sys
import threading
import time

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "indextts"))

import argparse
parser = argparse.ArgumentParser(description="IndexTTS WebUI")
parser.add_argument("--verbose", action="store_true", default=False, help="Enable verbose mode")
parser.add_argument("--port", type=int, default=7860, help="Port to run the web UI on")
parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to run the web UI on")
parser.add_argument("--model_dir", type=str, default="checkpoints", help="Model checkpoints directory")
parser.add_argument("--language", type=str, default="auto", help="UI language (auto, en_US, zh_CN)")
cmd_args = parser.parse_args()

if not os.path.exists(cmd_args.model_dir):
    print(f"Model directory {cmd_args.model_dir} does not exist. Please download the model first.")
    sys.exit(1)

for file in [
    "bigvgan_generator.pth",
    "bpe.model",
    "gpt.pth",
    "config.yaml",
]:
    file_path = os.path.join(cmd_args.model_dir, file)
    if not os.path.exists(file_path):
        print(f"Required file {file_path} does not exist. Please download it.")
        sys.exit(1)

import gradio as gr
import pandas as pd

from indextts.infer import IndexTTS
from tools.i18n.i18n import I18nAuto

# Detect environment for automatic language selection
IN_COLAB = 'google.colab' in sys.modules
IN_KAGGLE = 'kaggle_secrets' in sys.modules or os.path.exists('/kaggle')

# Set language based on environment and arguments
if cmd_args.language == "auto":
    # Auto-detect: use English for cloud environments, Chinese for local
    language = "en_US" if (IN_COLAB or IN_KAGGLE) else "zh_CN"
else:
    language = cmd_args.language

i18n = I18nAuto(language=language)
MODE = 'local'
tts = IndexTTS(model_dir=cmd_args.model_dir, cfg_path=os.path.join(cmd_args.model_dir, "config.yaml"),)


os.makedirs("outputs/tasks",exist_ok=True)
os.makedirs("prompts",exist_ok=True)

# Load example cases if available
example_cases = []
if os.path.exists("tests/cases.jsonl"):
    with open("tests/cases.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            example = json.loads(line)
            example_cases.append([os.path.join("tests", example.get("prompt_audio", "sample_prompt.wav")),
                                  example.get("text"), [i18n("普通推理"), i18n("批次推理")][example.get("infer_mode", 0)]])

def gen_single(prompt, text, infer_mode, max_text_tokens_per_sentence=120, sentences_bucket_max_size=4,
                *args, progress=gr.Progress()):
    output_path = None
    if not output_path:
        output_path = os.path.join("outputs", f"spk_{int(time.time())}.wav")
    # set gradio progress
    tts.gr_progress = progress
    do_sample, top_p, top_k, temperature, \
        length_penalty, num_beams, repetition_penalty, max_mel_tokens = args
    kwargs = {
        "do_sample": bool(do_sample),
        "top_p": float(top_p),
        "top_k": int(top_k) if int(top_k) > 0 else None,
        "temperature": float(temperature),
        "length_penalty": float(length_penalty),
        "num_beams": num_beams,
        "repetition_penalty": float(repetition_penalty),
        "max_mel_tokens": int(max_mel_tokens),
        # "typical_sampling": bool(typical_sampling),
        # "typical_mass": float(typical_mass),
    }
    if infer_mode == i18n("普通推理"):
        output = tts.infer(prompt, text, output_path, verbose=cmd_args.verbose,
                           max_text_tokens_per_sentence=int(max_text_tokens_per_sentence),
                           **kwargs)
    else:
        # 批次推理
        output = tts.infer_fast(prompt, text, output_path, verbose=cmd_args.verbose,
            max_text_tokens_per_sentence=int(max_text_tokens_per_sentence),
            sentences_bucket_max_size=(sentences_bucket_max_size),
            **kwargs)
    return gr.update(value=output,visible=True)

def update_prompt_audio():
    update_button = gr.update(interactive=True)
    return update_button

with gr.Blocks(title="IndexTTS Demo") as demo:
    mutex = threading.Lock()
    # Dynamic header based on language
    if language == "en_US":
        header_html = '''
        <h2><center>IndexTTS: An Industrial-Level Controllable and Efficient Zero-Shot Text-To-Speech System</h2>
        <p align="center">
        <a href='https://arxiv.org/abs/2502.05512'><img src='https://img.shields.io/badge/ArXiv-2502.05512-red'></a>
        </p>
        '''
    else:
        header_html = '''
        <h2><center>IndexTTS: An Industrial-Level Controllable and Efficient Zero-Shot Text-To-Speech System</h2>
        <h2><center>(一款工业级可控且高效的零样本文本转语音系统)</h2>
        <p align="center">
        <a href='https://arxiv.org/abs/2502.05512'><img src='https://img.shields.io/badge/ArXiv-2502.05512-red'></a>
        </p>
        '''
    gr.HTML(header_html)
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
                input_text_single = gr.TextArea(
                    label=i18n("请输入目标文本"),
                    key="input_text_single",
                    placeholder=i18n("请输入目标文本"),
                    info=i18n("当前模型版本{}").format(tts.model_version or "1.0") if hasattr(tts, 'model_version') else ""
                )
                infer_mode = gr.Radio(
                    choices=[i18n("普通推理"), i18n("批次推理")],
                    label=i18n("选择推理模式（批次推理：更适合长句，性能翻倍）"),
                    value=i18n("普通推理")
                )
                gen_button = gr.Button(i18n("生成语音"), key="gen_button",interactive=True)
            output_audio = gr.Audio(label=i18n("生成结果"), visible=True,key="output_audio")
        with gr.Accordion(i18n("高级生成参数设置"), open=False):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown(i18n("**GPT2 采样设置** _参数会影响音频多样性和生成速度详见[Generation strategies](https://huggingface.co/docs/transformers/main/en/generation_strategies)_"))
                    with gr.Row():
                        do_sample = gr.Checkbox(label="do_sample", value=True, info=i18n("是否进行采样"))
                        temperature = gr.Slider(label="temperature", minimum=0.1, maximum=2.0, value=1.0, step=0.1)
                    with gr.Row():
                        top_p = gr.Slider(label="top_p", minimum=0.0, maximum=1.0, value=0.8, step=0.01)
                        top_k = gr.Slider(label="top_k", minimum=0, maximum=100, value=30, step=1)
                        num_beams = gr.Slider(label="num_beams", value=3, minimum=1, maximum=10, step=1)
                    with gr.Row():
                        repetition_penalty = gr.Number(label="repetition_penalty", precision=None, value=10.0, minimum=0.1, maximum=20.0, step=0.1)
                        length_penalty = gr.Number(label="length_penalty", precision=None, value=0.0, minimum=-2.0, maximum=2.0, step=0.1)
                    max_mel_tokens = gr.Slider(
                        label="max_mel_tokens",
                        value=600,
                        minimum=50,
                        maximum=tts.cfg.gpt.max_mel_tokens,
                        step=10,
                        info=i18n("生成Token最大数量，过小导致音频被截断"),
                        key="max_mel_tokens"
                    )
                with gr.Column(scale=2):
                    gr.Markdown(i18n("**分句设置** _参数会影响音频质量和生成速度_"))
                    with gr.Row():
                        max_text_tokens_per_sentence = gr.Slider(
                            label=i18n("分句最大Token数"),
                            value=120,
                            minimum=20,
                            maximum=tts.cfg.gpt.max_text_tokens,
                            step=2,
                            key="max_text_tokens_per_sentence",
                            info=i18n("建议80~200之间，值越大，分句越长；值越小，分句越碎；过小过大都可能导致音频质量不高"),
                        )
                        sentences_bucket_max_size = gr.Slider(
                            label=i18n("分句分桶的最大容量（批次推理生效）"),
                            value=4,
                            minimum=1,
                            maximum=16,
                            step=1,
                            key="sentences_bucket_max_size",
                            info=i18n("建议2-8之间，值越大，一批次推理包含的分句数越多，过大可能导致内存溢出"),
                        )
                    with gr.Accordion(i18n("预览分句结果"), open=True) as sentences_settings:
                        sentences_preview = gr.Dataframe(
                            headers=[i18n("序号"), i18n("分句内容"), i18n("Token数")],
                            key="sentences_preview",
                            wrap=True,
                        )
            advanced_params = [
                do_sample, top_p, top_k, temperature,
                length_penalty, num_beams, repetition_penalty, max_mel_tokens,
            ]

        if len(example_cases) > 0:
            gr.Examples(
                examples=example_cases,
                inputs=[prompt_audio, input_text_single, infer_mode],
            )

    def on_input_text_change(text, max_tokens_per_sentence):
        if text and len(text) > 0:
            text_tokens_list = tts.tokenizer.tokenize(text)

            sentences = tts.tokenizer.split_sentences(text_tokens_list, max_tokens_per_sentence=int(max_tokens_per_sentence))
            data = []
            for i, s in enumerate(sentences):
                sentence_str = ''.join(s)
                tokens_count = len(s)
                data.append([i, sentence_str, tokens_count])
            
            return {
                sentences_preview: gr.update(value=data, visible=True, type="array"),
            }
        else:
            df = pd.DataFrame([], columns=[i18n("序号"), i18n("分句内容"), i18n("Token数")])
            return {
                sentences_preview: gr.update(value=df)
            }

    input_text_single.change(
        on_input_text_change,
        inputs=[input_text_single, max_text_tokens_per_sentence],
        outputs=[sentences_preview]
    )
    max_text_tokens_per_sentence.change(
        on_input_text_change,
        inputs=[input_text_single, max_text_tokens_per_sentence],
        outputs=[sentences_preview]
    )
    prompt_audio.upload(update_prompt_audio,
                         inputs=[],
                         outputs=[gen_button])

    gen_button.click(gen_single,
                     inputs=[prompt_audio, input_text_single, infer_mode,
                             max_text_tokens_per_sentence, sentences_bucket_max_size,
                             *advanced_params,
                     ],
                     outputs=[output_audio])


def setup_ngrok_tunnel(port=7860):
    """Setup ngrok tunnel for public URL access (no signup required)"""
    try:
        import subprocess
        import threading
        import time
        import os
        import json

        print("🌐 Setting up ngrok tunnel for public access...")

        # Install ngrok if not available
        try:
            result = subprocess.run(['ngrok', 'version'], capture_output=True, check=True)
            print("✅ ngrok is already installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("📦 Installing ngrok...")
            try:
                # Download and install ngrok
                subprocess.run([
                    'wget', '-q',
                    'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz'
                ], check=True)
                subprocess.run(['tar', 'xzf', 'ngrok-v3-stable-linux-amd64.tgz'], check=True)
                subprocess.run(['mv', 'ngrok', '/usr/local/bin/ngrok'], check=True)
                subprocess.run(['chmod', '+x', '/usr/local/bin/ngrok'], check=True)
                print("✅ ngrok installed successfully")
            except Exception as install_error:
                print(f"❌ Failed to install ngrok: {install_error}")
                return False

        # Global variable to store the tunnel URL
        tunnel_url = [None]

        # Start tunnel in background
        def start_tunnel():
            try:
                print(f"🚀 Starting ngrok tunnel for port {port}...")
                print("⏳ This may take 10-30 seconds...")

                # Start ngrok tunnel
                process = subprocess.Popen([
                    'ngrok', 'http', str(port), '--log=stdout'
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

                # Monitor output for tunnel URL
                start_time = time.time()
                timeout = 45  # 45 seconds timeout

                while time.time() - start_time < timeout:
                    line = process.stdout.readline()
                    if line:
                        line = line.strip()
                        print(f"[ngrok] {line}")

                        # Look for tunnel URL in ngrok output
                        if 'url=' in line and 'ngrok' in line:
                            # Extract URL from ngrok log line
                            parts = line.split('url=')
                            if len(parts) > 1:
                                url = parts[1].split()[0]
                                if url.startswith('http') and 'ngrok' in url:
                                    tunnel_url[0] = url
                                    print(f"\n🎉 SUCCESS! ngrok tunnel is ready!")
                                    print(f"🔗 Public URL: {url}")
                                    print(f"🌍 Your IndexTTS interface is accessible at: {url}")
                                    print(f"📱 Share this URL with anyone!\n")
                                    return

                        # Alternative: look for forwarding info
                        if 'Forwarding' in line and 'ngrok' in line:
                            parts = line.split()
                            for part in parts:
                                if part.startswith('http') and 'ngrok' in part:
                                    tunnel_url[0] = part
                                    print(f"\n🎉 SUCCESS! ngrok tunnel is ready!")
                                    print(f"🔗 Public URL: {part}")
                                    print(f"🌍 Your IndexTTS interface is accessible at: {part}")
                                    print(f"📱 Share this URL with anyone!\n")
                                    return

                    # Check if process is still running
                    if process.poll() is not None:
                        break

                    time.sleep(0.5)

                print("⏰ Timeout waiting for ngrok tunnel URL")

            except Exception as e:
                print(f"⚠️  ngrok tunnel error: {e}")
                print("💡 Falling back to local access only")

        # Start tunnel in background thread
        tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
        tunnel_thread.start()

        # Give tunnel time to start
        print("⏳ Waiting for ngrok tunnel to establish...")
        time.sleep(10)

        if tunnel_url[0]:
            print(f"✅ Tunnel established: {tunnel_url[0]}")
            return True
        else:
            print("⏳ Tunnel is starting... URL will appear above when ready")
            return True

    except Exception as e:
        print(f"⚠️  ngrok tunnel setup failed: {e}")
        print("💡 Continuing with local access only")
        return False

def setup_cloudflare_tunnel(port=7860):
    """Setup Cloudflare tunnel as fallback option"""
    try:
        import subprocess
        import threading
        import time
        import os

        print("🌐 Setting up Cloudflare tunnel as fallback...")

        # Install cloudflared if not available
        try:
            result = subprocess.run(['cloudflared', '--version'], capture_output=True, check=True)
            print("✅ cloudflared is already installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("📦 Installing cloudflared...")
            try:
                subprocess.run([
                    'wget', '-q',
                    'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb'
                ], check=True)
                subprocess.run(['dpkg', '-i', 'cloudflared-linux-amd64.deb'], check=True)
                print("✅ cloudflared installed successfully")
            except Exception as install_error:
                print(f"❌ Failed to install cloudflared: {install_error}")
                return False

        # Start tunnel in background (simplified version)
        def start_tunnel():
            try:
                print(f"🚀 Starting Cloudflare tunnel for port {port}...")
                process = subprocess.Popen([
                    'cloudflared', 'tunnel', '--url', f'http://localhost:{port}'
                ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

                for line in iter(process.stdout.readline, ''):
                    line = line.strip()
                    if line:
                        print(f"[Cloudflare] {line}")
                        if 'trycloudflare.com' in line:
                            words = line.split()
                            for word in words:
                                if word.startswith('http') and 'trycloudflare.com' in word:
                                    print(f"\n🎉 Cloudflare tunnel ready!")
                                    print(f"🔗 Fallback URL: {word}")
                                    return

            except Exception as e:
                print(f"⚠️  Cloudflare tunnel error: {e}")

        tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
        tunnel_thread.start()
        return True

    except Exception as e:
        print(f"⚠️  Cloudflare tunnel setup failed: {e}")
        return False

def setup_public_tunnel(port=7860):
    """Setup public tunnel with ngrok as primary and Cloudflare as fallback"""
    print("🌐 Setting up public URL access...")
    print("🎯 Trying ngrok first (more reliable), Cloudflare as fallback")

    # Try ngrok first
    if setup_ngrok_tunnel(port):
        print("✅ ngrok tunnel setup initiated")
        # Also try Cloudflare as additional option
        print("\n🔄 Also setting up Cloudflare tunnel as backup...")
        setup_cloudflare_tunnel(port)
        return True
    else:
        print("❌ ngrok setup failed, trying Cloudflare...")
        return setup_cloudflare_tunnel(port)

if __name__ == "__main__":
    print(f"🚀 Starting IndexTTS...")
    print(f"🌐 Language: {language}")
    print(f"📍 Environment: {'Colab' if IN_COLAB else 'Kaggle' if IN_KAGGLE else 'Local'}")

    # Setup public tunnel for access
    use_tunnel = False

    # Always try to setup public tunnel for access (except when host is localhost)
    if cmd_args.host not in ["127.0.0.1", "localhost"]:
        print("\n🌐 Setting up public URL access...")
        print("🎯 Using ngrok (primary) + Cloudflare (fallback) for reliable access")
        use_tunnel = setup_public_tunnel(cmd_args.port)

    # Configure launch parameters based on environment
    if IN_COLAB:
        # Colab configuration - use built-in sharing + tunnels as backup
        print("\n🚀 Launching on Google Colab...")
        print("🔗 Colab will provide a gradio.live URL")
        if use_tunnel:
            print("🌐 Additional tunnel URLs available (see above)")

        demo.queue(20)
        demo.launch(
            server_name="0.0.0.0",
            server_port=cmd_args.port,
            share=True,  # Create public URL for Colab
            debug=False,
            quiet=False
        )
    elif IN_KAGGLE:
        # Kaggle configuration with tunnel access
        print("\n🚀 Launching on Kaggle...")
        if use_tunnel:
            print("🌐 Public access via tunnel URLs (see above)")
        else:
            print("🔗 Interface will be available in Kaggle's output panel")
            print("⚠️  For public access, try running with --host 0.0.0.0")

        demo.queue(20)
        demo.launch(
            server_name="0.0.0.0",
            server_port=cmd_args.port,
            share=False,  # Use tunnels instead
            debug=False,
            quiet=False
        )
    else:
        # Local development configuration
        print(f"\n🚀 Launching locally...")
        if use_tunnel:
            print("🌐 Public access via tunnel URLs (see above)")
        print(f"🏠 Local access: http://{cmd_args.host}:{cmd_args.port}")

        demo.queue(20)
        demo.launch(
            server_name=cmd_args.host,
            server_port=cmd_args.port,
            share=False,  # Use tunnels for public access if enabled
            debug=False,
            quiet=False
        )
