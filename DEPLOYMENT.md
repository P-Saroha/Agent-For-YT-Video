# 🚀 Deployment Guide - YouTube AI Assistant

## 🎯 **Quick Deploy Options**

### **Option 1: Vercel (Recommended - Free)**

1. **Fork/Clone** your repository to GitHub
2. **Sign up** at [vercel.com](https://vercel.com)
3. **Connect GitHub** and select your repository
4. **Add Environment Variables**:
   - `GEMINI_API_KEY` = `your_api_key_here`
5. **Deploy** - Vercel will auto-detect and deploy!

**✅ Result**: Your API will be live at `https://your-app.vercel.app`

### **Option 2: Railway (Free Tier)**

1. **Sign up** at [railway.app](https://railway.app)
2. **Connect GitHub** repository
3. **Add Environment Variables**:
   - `GEMINI_API_KEY` = `your_api_key_here`
4. **Deploy** with one click!

**✅ Result**: Your API will be live at `https://your-app.railway.app`

### **Option 3: Heroku (Free with Credit Card)**

1. **Install Heroku CLI**
2. **Login**: `heroku login`
3. **Create app**: `heroku create your-app-name`
4. **Set environment variables**:
   ```bash
   heroku config:set GEMINI_API_KEY=your_api_key_here
   ```
5. **Deploy**:
   ```bash
   git push heroku main
   ```

**✅ Result**: Your API will be live at `https://your-app.herokuapp.com`

---

## 🐳 **Docker Deployment**

### **Local Docker**
```bash
# Build and run
docker-compose up --build

# Or with custom environment
docker build -t youtube-ai .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key youtube-ai
```

### **Deploy to Cloud with Docker**
- **Google Cloud Run**
- **AWS ECS/Fargate**
- **Azure Container Instances**
- **DigitalOcean App Platform**

---

## 🖥️ **VPS/Server Deployment**

### **Ubuntu/Debian Server**
```bash
# Make script executable
chmod +x deploy.sh

# Run deployment script
./deploy.sh
```

### **Manual Steps**:
1. **Clone repository**: `git clone https://github.com/P-Saroha/Agent-For-YT-Video.git`
2. **Setup environment**: `python3 -m venv venv && source venv/bin/activate`
3. **Install dependencies**: `pip install -r server/requirements.txt`
4. **Set environment variables**: `export GEMINI_API_KEY=your_key`
5. **Run server**: `cd server && uvicorn app.main:app --host 0.0.0.0 --port 8000`

---

## 🌐 **Update Extension for Production**

### **Step 1: Update API URL**
In `extension/popup.js`, replace:
```javascript
const API_BASE_URL = 'https://your-deployed-app.vercel.app';
```

### **Step 2: Update Manifest Permissions**
Already configured for multiple domains in `manifest.json`

### **Step 3: Test Extension**
1. **Reload extension** in Chrome
2. **Test with deployed API**
3. **Verify all features work**

---

## 📊 **Environment Variables**

### **Required**:
- `GEMINI_API_KEY` - Your Google Gemini API key

### **Optional**:
- `YOUTUBE_API_KEY` - Enhanced video metadata
- `DEBUG` - Set to `False` for production
- `HOST` - Default: `0.0.0.0`
- `PORT` - Default: `8000`

---

## 🔧 **Production Optimizations**

### **Performance**:
- **Gunicorn** with multiple workers
- **Redis** for caching (future enhancement)
- **PostgreSQL** for persistent storage
- **CDN** for static files

### **Security**:
- **HTTPS** only in production
- **CORS** properly configured
- **Rate limiting**
- **API key rotation**

### **Monitoring**:
- **Health checks** at `/health`
- **Logging** with proper levels
- **Error tracking** (Sentry)
- **Metrics** collection

---

## 🚨 **Troubleshooting**

### **Common Issues**:

1. **CORS Errors**:
   - Update `host_permissions` in manifest.json
   - Check API URL matches deployment

2. **API Key Issues**:
   - Verify environment variables are set
   - Check key permissions in Google Console

3. **Extension Not Loading**:
   - Check Developer Mode is enabled
   - Reload extension after changes
   - Check browser console for errors

### **Debug Steps**:
1. **Check server logs**
2. **Test API endpoints directly**
3. **Verify environment variables**
4. **Check extension permissions**

---

## ✅ **Deployment Checklist**

- [ ] **API deployed** and accessible
- [ ] **Environment variables** configured
- [ ] **Extension updated** with production URL
- [ ] **Extension reloaded** in Chrome
- [ ] **End-to-end testing** completed
- [ ] **Error handling** verified
- [ ] **Performance** acceptable
- [ ] **Security** configurations applied

---

## 🎉 **Go Live!**

Once deployed, your YouTube AI Assistant will be accessible to users worldwide! Share your Chrome extension and let people analyze YouTube videos with AI! 🚀