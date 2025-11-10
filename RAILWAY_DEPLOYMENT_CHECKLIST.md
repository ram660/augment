# ✅ Railway Deployment Checklist

Quick checklist for deploying HomeView AI to Railway.

---

## 📋 Pre-Deployment

- [ ] Code is committed and pushed to GitHub
- [ ] All tests pass locally
- [ ] API keys ready:
  - [ ] Gemini API Key
  - [ ] DeepSeek API Key
  - [ ] YouTube API Key
- [ ] Railway account created (https://railway.app)

---

## 🚀 Deployment Steps

### **1. Create Railway Project**
- [ ] Sign in to Railway
- [ ] Create new project from GitHub repo
- [ ] Repository connected: `ram660/augment`

### **2. Add PostgreSQL Database**
- [ ] Click "+ New" → "Database" → "PostgreSQL"
- [ ] Database created successfully
- [ ] `DATABASE_URL` variable auto-generated

### **3. Deploy Backend**
- [ ] Create service from GitHub repo
- [ ] Root directory: (empty - uses root)
- [ ] Environment variables added:
  - [ ] `DATABASE_URL=${{Postgres.DATABASE_URL}}`
  - [ ] `GEMINI_API_KEY=your_key`
  - [ ] `DEEPSEEK_API_KEY=your_key`
  - [ ] `YOUTUBE_API_KEY=your_key`
  - [ ] `ENVIRONMENT=production`
  - [ ] `LOG_LEVEL=INFO`
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- [ ] Backend deployed successfully
- [ ] Generate domain for backend
- [ ] Backend URL: `https://_____.railway.app`

### **4. Deploy Frontend**
- [ ] Create service from GitHub repo
- [ ] Root directory: `homeview-frontend`
- [ ] Environment variables added:
  - [ ] `NEXT_PUBLIC_API_URL=https://your-backend.railway.app`
- [ ] Build command: `npm install && npm run build`
- [ ] Start command: `npm start`
- [ ] Frontend deployed successfully
- [ ] Generate domain for frontend
- [ ] Frontend URL: `https://_____.railway.app`

### **5. Update CORS**
- [ ] Update backend `CORS_ORIGINS` with frontend URL
- [ ] Redeploy backend

---

## ✅ Verification

### **Backend Health Check**
- [ ] Visit: `https://your-backend.railway.app/api/v1/monitoring/health`
- [ ] Response: `{"status": "healthy"}`

### **API Documentation**
- [ ] Visit: `https://your-backend.railway.app/docs`
- [ ] Swagger UI loads correctly

### **Frontend**
- [ ] Visit: `https://your-frontend.railway.app`
- [ ] Dashboard loads correctly
- [ ] No console errors

### **Chat Functionality**
- [ ] Go to Chat tab
- [ ] Send test message
- [ ] Receive AI response
- [ ] No 422 errors

---

## 📝 Post-Deployment

- [ ] Save URLs:
  - Backend: `_____________________`
  - Frontend: `_____________________`
  - Database: `_____________________`
- [ ] Test all major features
- [ ] Set up monitoring (optional)
- [ ] Configure custom domain (optional)
- [ ] Share with team/users

---

## 🎉 Deployment Complete!

**Your HomeView AI is now live!**

- 🌐 Frontend: https://your-frontend.railway.app
- 📚 API Docs: https://your-backend.railway.app/docs
- 💾 Database: PostgreSQL on Railway

---

## 📞 Need Help?

- **Full Guide**: See `docs/RAILWAY_DEPLOYMENT_GUIDE.md`
- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway

