#!/usr/bin/env python3
"""
Cloudflare Tunnel Setup Script for IndexTTS
This script sets up a Cloudflare tunnel to provide public URL access
"""

import subprocess
import threading
import time
import os
import sys
import signal

def install_cloudflared():
    """Install cloudflared if not available"""
    try:
        # Check if already installed
        result = subprocess.run(['cloudflared', '--version'], capture_output=True, check=True)
        print("✅ cloudflared is already installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("📦 Installing cloudflared...")
        try:
            # For Ubuntu/Debian systems (Colab/Kaggle)
            if os.path.exists('/usr/bin/apt-get'):
                subprocess.run(['apt-get', 'update'], check=False, capture_output=True)
                subprocess.run([
                    'wget', '-q', 
                    'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb'
                ], check=True)
                subprocess.run(['dpkg', '-i', 'cloudflared-linux-amd64.deb'], check=True)
            else:
                # Alternative installation method
                subprocess.run([
                    'wget', '-O', '/tmp/cloudflared',
                    'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64'
                ], check=True)
                subprocess.run(['chmod', '+x', '/tmp/cloudflared'], check=True)
                subprocess.run(['mv', '/tmp/cloudflared', '/usr/local/bin/cloudflared'], check=True)
            print("✅ cloudflared installed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to install cloudflared: {e}")
            return False

def start_tunnel(port=7860, timeout=30):
    """Start Cloudflare tunnel and return the public URL"""
    print(f"🚀 Starting Cloudflare tunnel for port {port}...")
    
    try:
        # Start the tunnel process
        process = subprocess.Popen([
            'cloudflared', 'tunnel', '--url', f'http://localhost:{port}'
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        # Monitor output for tunnel URL
        start_time = time.time()
        tunnel_url = None
        
        print("⏳ Waiting for tunnel to establish...")
        
        while time.time() - start_time < timeout:
            line = process.stdout.readline()
            if line:
                line = line.strip()
                print(f"[Cloudflare] {line}")
                
                # Look for tunnel URL
                if any(domain in line for domain in ['trycloudflare.com', '.cloudflare.com', 'cfargotunnel.com']):
                    words = line.split()
                    for word in words:
                        if word.startswith('http') and any(domain in word for domain in ['trycloudflare.com', '.cloudflare.com', 'cfargotunnel.com']):
                            tunnel_url = word
                            print(f"\n🎉 SUCCESS! Cloudflare tunnel is ready!")
                            print(f"🔗 Public URL: {tunnel_url}")
                            print(f"🌍 Your IndexTTS interface is accessible at: {tunnel_url}")
                            print(f"📱 Share this URL with anyone!\n")
                            
                            # Keep the process running in background
                            def keep_alive():
                                try:
                                    process.wait()
                                except:
                                    pass
                            
                            thread = threading.Thread(target=keep_alive, daemon=True)
                            thread.start()
                            
                            return tunnel_url
            
            # Check if process is still running
            if process.poll() is not None:
                print("❌ Cloudflare tunnel process ended unexpectedly")
                break
                
            time.sleep(0.5)
        
        print("⏰ Timeout waiting for tunnel URL")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Error starting tunnel: {e}")
        return None

def setup_tunnel_for_gradio(port=7860):
    """Complete setup for Gradio with Cloudflare tunnel"""
    print("🌐 Setting up Cloudflare tunnel for public access...")
    
    # Install cloudflared
    if not install_cloudflared():
        return False
    
    # Start tunnel
    url = start_tunnel(port)
    
    if url:
        print(f"✅ Tunnel setup complete!")
        print(f"🔗 Public URL: {url}")
        return True
    else:
        print("❌ Failed to establish tunnel")
        return False

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Cloudflare tunnel for IndexTTS")
    parser.add_argument("--port", type=int, default=7860, help="Port to tunnel (default: 7860)")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds (default: 30)")
    
    args = parser.parse_args()
    
    print("🌐 IndexTTS Cloudflare Tunnel Setup")
    print("=" * 40)
    
    if setup_tunnel_for_gradio(args.port):
        print("\n✅ Setup complete! The tunnel will remain active.")
        print("💡 Keep this script running to maintain the tunnel.")
        
        # Keep script running
        try:
            while True:
                time.sleep(60)
                print("🔄 Tunnel still active...")
        except KeyboardInterrupt:
            print("\n👋 Tunnel stopped by user")
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
