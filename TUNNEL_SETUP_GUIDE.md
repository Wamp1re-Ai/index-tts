# 🌐 Cloudflare Tunnel Setup Guide for IndexTTS

This guide explains how to get public URL access for IndexTTS using Cloudflare tunnels.

## 🚀 Quick Start

### For Cloud Platforms (Recommended)

#### Google Colab
1. Open the Colab notebook: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Wamp1re-Ai/index-tts/blob/feat/english-colab-notebook/IndexTTS_Colab_EN.ipynb)
2. Run all cells in order
3. Wait for both URLs:
   - **Gradio.live URL** (Colab's built-in sharing)
   - **Cloudflare URL** (trycloudflare.com domain)

#### Kaggle
1. Open the Kaggle notebook: [![Open In Kaggle](https://kaggle.com/static/images/open-in-kaggle.svg)](https://kaggle.com/kernels/welcome?src=https://github.com/Wamp1re-Ai/index-tts/blob/feat/english-colab-notebook/IndexTTS_Kaggle_EN.ipynb)
2. Enable Internet access in notebook settings
3. Run all cells in order
4. Wait for the **Cloudflare URL** (trycloudflare.com domain)

### For Local Development

#### Option 1: Automatic Setup (Recommended)
```bash
# Clone the repository
git clone https://github.com/Wamp1re-Ai/index-tts.git
cd index-tts
git checkout feat/english-colab-notebook

# Install dependencies
pip install -r requirements.txt

# Run with public URL access
python webui.py --host 0.0.0.0 --port 7860
```

#### Option 2: Manual Tunnel Setup
```bash
# Test tunnel setup first
python test_tunnel.py

# If test passes, run the main application
python webui.py --host 0.0.0.0 --port 7860
```

#### Option 3: Standalone Tunnel
```bash
# Run tunnel setup separately
python setup_tunnel.py --port 7860

# In another terminal, run IndexTTS
python webui.py --host 127.0.0.1 --port 7860
```

## 🔧 Troubleshooting

### No Public URL Generated

**Symptoms:**
- No `trycloudflare.com` URL appears
- Only local access available
- Tunnel setup fails

**Solutions:**

1. **Check Internet Connection**
   ```bash
   # Test connectivity
   ping cloudflare.com
   wget -q --spider https://github.com
   ```

2. **Verify Cloudflared Installation**
   ```bash
   # Test installation
   python test_tunnel.py
   ```

3. **Manual Installation**
   ```bash
   # Download and install cloudflared manually
   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared-linux-amd64.deb
   
   # Test installation
   cloudflared --version
   ```

4. **Check Firewall/Network**
   - Ensure outbound connections are allowed
   - Check if corporate firewall blocks tunnel services
   - Try different network if possible

5. **Use Explicit Arguments**
   ```bash
   # Ensure proper host binding
   python webui.py --host 0.0.0.0 --port 7860 --language en_US
   ```

### Tunnel URL Not Accessible

**Symptoms:**
- URL is generated but not accessible
- Connection timeouts or errors

**Solutions:**

1. **Wait for Full Startup**
   - Tunnel URL appears before Gradio is ready
   - Wait 30-60 seconds after URL appears
   - Look for "Running on local URL" message

2. **Check URL Format**
   - Should end with `.trycloudflare.com`
   - Should start with `https://`
   - Example: `https://abc123.trycloudflare.com`

3. **Verify Service Status**
   ```bash
   # Check if Gradio is running
   curl http://localhost:7860
   
   # Check tunnel status
   ps aux | grep cloudflared
   ```

### Performance Issues

**Symptoms:**
- Slow loading
- Timeouts during audio generation

**Solutions:**

1. **Use Local Access for Development**
   ```bash
   # For development, use local access
   python webui.py --host 127.0.0.1 --port 7860
   ```

2. **Optimize for Cloud Platforms**
   - Use the provided notebooks for best performance
   - Cloud platforms have optimized network routing

## 📱 Usage Tips

### Sharing Your Interface

1. **Get the Public URL**
   - Look for messages starting with "🔗 Public URL:"
   - Copy the complete URL including `https://`

2. **Share Safely**
   - URLs are temporary (expire when session ends)
   - No personal data is exposed
   - Safe to share for demonstrations

3. **Multiple Users**
   - Multiple people can access the same URL
   - Each user gets their own session
   - Audio generation is queued automatically

### Best Practices

1. **For Demonstrations**
   - Use cloud platforms (Colab/Kaggle) for reliability
   - Share the Cloudflare URL (more stable than gradio.live)

2. **For Development**
   - Use local access for faster iteration
   - Enable public access only when needed

3. **For Production**
   - Consider proper hosting solutions
   - Cloudflare tunnels are for temporary/demo use

## 🧪 Testing

### Quick Test
```bash
# Run the test script
python test_tunnel.py
```

### Manual Test
```bash
# Start tunnel manually
cloudflared tunnel --url http://localhost:7860

# In another terminal, start a test server
python -m http.server 7860

# Look for the tunnel URL in the first terminal
```

## 🆘 Getting Help

If you're still having issues:

1. **Check the logs** - Look for error messages in the console output
2. **Try the test script** - Run `python test_tunnel.py` to diagnose issues
3. **Use cloud platforms** - Colab and Kaggle have more reliable networking
4. **Check network restrictions** - Corporate/school networks may block tunnels

## 🔗 URLs and Links

- **Colab Notebook**: [IndexTTS_Colab_EN.ipynb](https://colab.research.google.com/github/Wamp1re-Ai/index-tts/blob/feat/english-colab-notebook/IndexTTS_Colab_EN.ipynb)
- **Kaggle Notebook**: [IndexTTS_Kaggle_EN.ipynb](https://kaggle.com/kernels/welcome?src=https://github.com/Wamp1re-Ai/index-tts/blob/feat/english-colab-notebook/IndexTTS_Kaggle_EN.ipynb)
- **Repository**: [Wamp1re-Ai/index-tts](https://github.com/Wamp1re-Ai/index-tts)
- **Cloudflare Tunnel Docs**: [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
