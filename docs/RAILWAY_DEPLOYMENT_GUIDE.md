# 🚀 Railway Deployment Guide - HomeView AI

Complete guide to deploy HomeView AI to Railway.app with PostgreSQL database.

---

## 📋 Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository
2. **Railway Account** - Sign up at https://railway.app (free $5 credit/month)
3. **API Keys** - Get these before deployment:
   - **Gemini API Key**: https://aistudio.google.com/app/apikey
   - **DeepSeek API Key**: https://platform.deepseek.com/api_keys
   - **YouTube API Key**: https://console.cloud.google.com/apis/credentials

---

## 🎯 Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Railway Project                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Backend    │  │  Frontend    │  │  PostgreSQL  │ │
│  │   (FastAPI)  │◄─┤  (Next.js)   │  │   Database   │ │
│  │              │  │              │  │              │ │
│  │ Port: $PORT  │  │ Port: 3000   │  │ Port: 5432   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         ▲                  │                  ▲         │
│         │                  │                  │         │
│         └──────────────────┴──────────────────┘         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Step-by-Step Deployment

### **Step 1: Push Code to GitHub**

```bash
# Make sure all changes are committed
git add .
git commit -m "feat: Railway deployment configuration"
git push origin main
```

### **Step 2: Create Railway Project**

1. Go to https://railway.app
2. Click **"Start a New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select repository: `ram660/augment`

### **Step 3: Add PostgreSQL Database**

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will automatically:
   - Create a PostgreSQL instance
   - Generate `DATABASE_URL` environment variable
   - Connect it to your services

### **Step 4: Deploy Backend Service**

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repository
3. Railway will auto-detect Python
4. Click on the service to configure

**Configure Backend Environment Variables:**

Click **"Variables"** tab and add:

```env
# Database (auto-provided by Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# API Keys (required)
GEMINI_API_KEY=your_gemini_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO

# CORS (update after frontend deployment)
CORS_ORIGINS=https://your-frontend.railway.app

# Optional: File uploads
UPLOAD_DIR=/app/uploads
```

**Configure Backend Settings:**

1. Go to **"Settings"** tab
2. **Root Directory**: Leave empty (uses root)
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. **Deploy**!

### **Step 5: Deploy Frontend Service**

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repository again
3. Railway will auto-detect Node.js
4. Click on the service to configure

**Configure Frontend Environment Variables:**

Click **"Variables"** tab and add:

```env
# Backend API URL (update with your backend URL)
NEXT_PUBLIC_API_URL=https://your-backend-name.railway.app
```

**Configure Frontend Settings:**

1. Go to **"Settings"** tab
2. **Root Directory**: `homeview-frontend`
3. **Build Command**: `npm install && npm run build`
4. **Start Command**: `npm start`
5. **Deploy**!

### **Step 6: Get Your URLs**

After deployment completes:

1. **Backend URL**: Click backend service → **"Settings"** → **"Generate Domain"**
   - Example: `https://homeview-backend-production.railway.app`

2. **Frontend URL**: Click frontend service → **"Settings"** → **"Generate Domain"**
   - Example: `https://homeview-frontend-production.railway.app`

### **Step 7: Update Environment Variables**

**Update Backend CORS:**
```env
CORS_ORIGINS=https://homeview-frontend-production.railway.app
```

**Update Frontend API URL:**
```env
NEXT_PUBLIC_API_URL=https://homeview-backend-production.railway.app
```

**Redeploy both services** after updating variables.

---

## ✅ Verify Deployment

### **1. Check Backend Health**

Visit: `https://your-backend.railway.app/api/v1/monitoring/health`

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T10:00:00Z",
  "database": "connected"
}
```

### **2. Check API Documentation**

Visit: `https://your-backend.railway.app/docs`

You should see the Swagger UI with all API endpoints.

### **3. Check Frontend**

Visit: `https://your-frontend.railway.app`

You should see the HomeView AI dashboard.

### **4. Test Chat Functionality**

1. Go to Chat tab
2. Send a message: "Show me modern kitchen designs"
3. Verify you get a response

---

## 🔧 Troubleshooting

### **Issue: Backend won't start**

**Check logs:**
1. Click backend service
2. Go to **"Deployments"** tab
3. Click latest deployment
4. View logs

**Common fixes:**
- Verify `DATABASE_URL` is set
- Check all required API keys are present
- Ensure `PORT` variable exists (Railway provides this)

### **Issue: Frontend can't connect to backend**

**Check:**
1. `NEXT_PUBLIC_API_URL` is set correctly
2. Backend CORS includes frontend URL
3. Backend is running (check health endpoint)

**Fix:**
```env
# Backend
CORS_ORIGINS=https://your-frontend.railway.app

# Frontend
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### **Issue: Database connection failed**

**Check:**
1. PostgreSQL service is running
2. `DATABASE_URL` variable is linked: `${{Postgres.DATABASE_URL}}`
3. Backend logs for connection errors

**Fix:**
- Restart PostgreSQL service
- Verify DATABASE_URL format: `postgresql://user:pass@host:port/db`

### **Issue: 422 Unprocessable Entity**

**This means:**
- Request validation failed
- Check request format matches API expectations

**Fix:**
- Check browser console for request details
- Verify API documentation at `/docs`
- Ensure form data is sent correctly

---

## 💰 Cost Estimation

### **Free Tier ($5 credit/month)**

Covers approximately:
- **500 execution hours/month**
- **100-500 users/month**
- **1GB database storage**

### **After Free Tier**

Estimated monthly costs:
- **Backend**: ~$5/month (512MB RAM)
- **Frontend**: ~$5/month (512MB RAM)
- **Database**: ~$5/month (1GB storage)
- **Total**: ~$15/month

### **Scaling**

As usage grows:
- **Medium traffic**: $20-30/month
- **High traffic**: $50-100/month

---

## 🎨 Custom Domain (Optional)

### **Add Custom Domain**

1. Click service → **"Settings"** → **"Domains"**
2. Click **"Custom Domain"**
3. Enter your domain: `app.yourdomain.com`
4. Add DNS records (Railway provides instructions)

**DNS Configuration:**
```
Type: CNAME
Name: app
Value: your-service.railway.app
```

---

## 🔐 Security Best Practices

### **1. Environment Variables**

✅ **DO:**
- Store all secrets in Railway environment variables
- Use different API keys for production
- Rotate keys regularly

❌ **DON'T:**
- Commit `.env` files to git
- Share API keys publicly
- Use development keys in production

### **2. CORS Configuration**

```env
# Specific origins only
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# NOT this in production:
CORS_ORIGINS=*
```

### **3. Database Backups**

Railway provides automatic backups, but consider:
- Regular manual backups
- Export important data periodically
- Test restore procedures

---

## 📊 Monitoring

### **Railway Dashboard**

Monitor:
- **CPU usage**
- **Memory usage**
- **Request count**
- **Error rates**

### **Application Logs**

View logs in real-time:
1. Click service
2. Go to **"Deployments"**
3. Click **"View Logs"**

### **Health Checks**

Set up monitoring:
- Use `/api/v1/monitoring/health` endpoint
- Set up external monitoring (UptimeRobot, Pingdom)
- Configure alerts for downtime

---

## 🚀 Next Steps

After successful deployment:

1. ✅ **Test all features** thoroughly
2. ✅ **Set up custom domain** (optional)
3. ✅ **Configure monitoring** and alerts
4. ✅ **Share with users** and gather feedback
5. ✅ **Monitor costs** and optimize as needed

---

## 📞 Support

**Railway Support:**
- Documentation: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

**HomeView AI:**
- GitHub: https://github.com/ram660/augment
- Issues: https://github.com/ram660/augment/issues

---

## ✨ Success!

Your HomeView AI application is now live on Railway! 🎉

**Share your deployment:**
- Frontend: `https://your-frontend.railway.app`
- API Docs: `https://your-backend.railway.app/docs`

Happy deploying! 🚀

