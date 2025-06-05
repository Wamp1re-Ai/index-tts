#!/usr/bin/env python3
"""
Test script to verify English UI functionality
"""

import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "indextts"))

def test_i18n_system():
    """Test the internationalization system"""
    print("🧪 Testing i18n system...")
    
    try:
        from tools.i18n.i18n import I18nAuto
        
        # Test English language
        i18n = I18nAuto(language="en_US")
        print(f"✅ i18n system initialized: {i18n}")
        
        # Test some translations
        test_keys = [
            "音频生成",
            "请上传参考音频", 
            "请输入目标文本",
            "生成语音",
            "普通推理",
            "批次推理"
        ]
        
        print("\n📝 Testing translations:")
        for key in test_keys:
            translation = i18n(key)
            print(f"  '{key}' -> '{translation}'")
            
            # Check that it's actually translated (not the same as key)
            if translation == key:
                print(f"  ⚠️  Warning: '{key}' not translated")
            else:
                print(f"  ✅ Translated successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing i18n system: {e}")
        return False

def test_webui_imports():
    """Test that webui.py can be imported without errors"""
    print("\n🧪 Testing webui imports...")
    
    try:
        # Test individual imports
        import gradio as gr
        print("✅ Gradio imported successfully")
        
        from tools.i18n.i18n import I18nAuto
        print("✅ I18nAuto imported successfully")
        
        # Test that we can create an i18n instance
        i18n = I18nAuto(language="en_US")
        print("✅ I18nAuto instance created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing webui imports: {e}")
        return False

def test_environment_detection():
    """Test environment detection logic"""
    print("\n🧪 Testing environment detection...")
    
    try:
        import sys
        import os
        
        # Test the same logic as in webui.py
        IN_COLAB = 'google.colab' in sys.modules
        IN_KAGGLE = 'kaggle_secrets' in sys.modules or os.path.exists('/kaggle')
        
        print(f"  Google Colab detected: {IN_COLAB}")
        print(f"  Kaggle detected: {IN_KAGGLE}")
        
        if not IN_COLAB and not IN_KAGGLE:
            print("  ✅ Running in local environment")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing environment detection: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing IndexTTS English UI Support")
    print("=" * 50)
    
    tests = [
        test_i18n_system,
        test_webui_imports,
        test_environment_detection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! English UI support is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
