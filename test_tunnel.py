#!/usr/bin/env python3
"""
Test script to verify Cloudflare tunnel setup
"""

import subprocess
import time
import threading
import sys

def test_cloudflared_installation():
    """Test if cloudflared can be installed and run"""
    print("🧪 Testing cloudflared installation...")
    
    try:
        # Try to run cloudflared
        result = subprocess.run(['cloudflared', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ cloudflared is already installed")
            print(f"Version: {result.stdout.strip()}")
            return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Try to install cloudflared
    try:
        print("📦 Installing cloudflared...")
        subprocess.run([
            'wget', '-q', 
            'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb'
        ], check=True, timeout=30)
        
        subprocess.run(['dpkg', '-i', 'cloudflared-linux-amd64.deb'], check=True, timeout=30)
        
        # Verify installation
        result = subprocess.run(['cloudflared', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ cloudflared installed successfully")
            print(f"Version: {result.stdout.strip()}")
            return True
        else:
            print("❌ cloudflared installation verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Failed to install cloudflared: {e}")
        return False

def test_tunnel_creation():
    """Test creating a tunnel to a dummy HTTP server"""
    print("\n🧪 Testing tunnel creation...")
    
    # Start a simple HTTP server
    import http.server
    import socketserver
    import threading
    
    PORT = 8888
    
    class TestHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>IndexTTS Test Server</h1><p>Tunnel is working!</p>')
    
    # Start test server
    try:
        httpd = socketserver.TCPServer(("", PORT), TestHandler)
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        print(f"✅ Test HTTP server started on port {PORT}")
    except Exception as e:
        print(f"❌ Failed to start test server: {e}")
        return False
    
    # Start tunnel
    tunnel_url = None
    try:
        print("🌐 Starting Cloudflare tunnel...")
        process = subprocess.Popen([
            'cloudflared', 'tunnel', '--url', f'http://localhost:{PORT}'
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        # Monitor for tunnel URL
        start_time = time.time()
        timeout = 45  # 45 seconds timeout
        
        for line in iter(process.stdout.readline, ''):
            if time.time() - start_time > timeout:
                print("⏰ Timeout waiting for tunnel URL")
                break
                
            line = line.strip()
            if line:
                print(f"[Cloudflare] {line}")
                
                # Look for tunnel URL
                if any(domain in line for domain in ['trycloudflare.com', '.cloudflare.com', 'cfargotunnel.com']):
                    words = line.split()
                    for word in words:
                        if word.startswith('http') and any(domain in word for domain in ['trycloudflare.com', '.cloudflare.com']):
                            tunnel_url = word
                            print(f"\n🎉 SUCCESS! Tunnel URL found: {tunnel_url}")
                            break
                    
                    if tunnel_url:
                        break
        
        # Clean up
        process.terminate()
        httpd.shutdown()
        
        if tunnel_url:
            print(f"✅ Tunnel test successful!")
            print(f"🔗 Generated URL: {tunnel_url}")
            return True
        else:
            print("❌ No tunnel URL was generated")
            return False
            
    except Exception as e:
        print(f"❌ Tunnel test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 IndexTTS Cloudflare Tunnel Test")
    print("=" * 40)
    
    # Test 1: Installation
    if not test_cloudflared_installation():
        print("\n❌ Installation test failed!")
        sys.exit(1)
    
    # Test 2: Tunnel creation
    if not test_tunnel_creation():
        print("\n❌ Tunnel creation test failed!")
        sys.exit(1)
    
    print("\n🎉 All tests passed!")
    print("✅ Cloudflare tunnel setup is working correctly")
    print("💡 You can now use IndexTTS with public URL access")

if __name__ == "__main__":
    main()
