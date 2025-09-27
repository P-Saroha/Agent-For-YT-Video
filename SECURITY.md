# 🔐 Security & Privacy Notice

## ⚠️ **Important: API Key Security**

Your API keys and sensitive information are protected by our comprehensive `.gitignore` file. However, please ensure you follow these security best practices:

### 🛡️ **Protected Files**
The following sensitive files are automatically excluded from Git:
- `server/.env` - Contains your actual API keys
- `server/store/` - Vector store data and caches
- `myenv/` & `venv/` - Virtual environment files
- `__pycache__/` - Python cache files
- `*.log` - Log files that might contain sensitive data

### 🔑 **API Key Setup**
1. Copy `server/.env.example` to `server/.env`
2. Add your actual API keys to `server/.env`
3. Never commit the `.env` file to Git

### 📋 **Required API Keys**
- **GEMINI_API_KEY** (Required) - Get from Google AI Studio
- **YOUTUBE_API_KEY** (Optional) - For enhanced video metadata

### 🚨 **If You Accidentally Expose API Keys**
1. **Immediately revoke** the exposed API key from the provider
2. **Generate new API keys** 
3. **Update your `.env` file** with new keys
4. **Force push** to remove from Git history if needed

### 💡 **Best Practices**
- ✅ Always use `.env.example` as template
- ✅ Keep actual `.env` file local only
- ✅ Regular security audits of committed files
- ✅ Use different API keys for development/production
- ❌ Never hardcode API keys in source code
- ❌ Never share screenshots with API keys visible

## 🔍 **Verify Security**
Check that sensitive files are ignored:
```bash
git status --ignored
```

## 🆘 **Need Help?**
If you suspect any security issues, please:
1. Check your Git history for accidentally committed keys
2. Revoke any exposed API keys immediately
3. Update your keys and test the application

---
**Remember**: Security is everyone's responsibility! 🔐