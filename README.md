# ARND & Co Chatbot - Render.com Deployment

## 🚀 FREE Python Flask API with Firestore

### Features:
- ✅ 4 Virtual Agents (Priya, Ananya, Arjun, Rahul)
- ✅ Multi-language Support (Bengali, Hindi, English)
- ✅ Product Search & Recommendations
- ✅ User Authentication (Signup/Login)
- ✅ Chat History Storage in Firestore
- ✅ Real-time Brand & Product Data

### API Endpoints:
- `GET /` - API info
- `GET /health` - Health check
- `POST /signup` - User registration
- `POST /login` - User authentication
- `GET /brands` - Get all brands
- `POST /chat_init` - Initialize chat session
- `POST /chat` - Send chat message

### Deployment Steps:

1. **Create Render.com Account** (FREE - no card needed)
   - Go to: https://render.com/
   - Sign up with GitHub (recommended) or Email

2. **Connect GitHub Repository**
   - Push this folder to a GitHub repo
   - Or use Render's manual deploy

3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your repository
   - Select branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Plan: **Free**

4. **Add Environment Variable**
   - Go to "Environment" tab
   - Add: `PYTHON_VERSION` = `3.11.0`

5. **Deploy!**
   - Click "Create Web Service"
   - Wait 5-10 minutes for first deploy
   - You'll get a URL like: `https://arndco-chatbot.onrender.com`

### Update Frontend:

Edit `arndco.in/application/views/footertrynew.php`:

```javascript
var API = 'https://YOUR-APP-NAME.onrender.com';
```

Replace `YOUR-APP-NAME` with your actual Render app name.

### Testing:

```bash
# Health check
curl https://YOUR-APP-NAME.onrender.com/health

# Signup
curl -X POST https://YOUR-APP-NAME.onrender.com/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","password":"test123"}'

# Login
curl -X POST https://YOUR-APP-NAME.onrender.com/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### Free Tier Limits:
- ✅ 750 hours/month (always on)
- ✅ Automatic SSL
- ✅ No credit card required
- ✅ Cold starts after 15 mins of inactivity (first request takes 30-60 seconds)

### Production Notes:
- Free tier apps spin down after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds to wake up
- For always-on service, upgrade to paid plan ($7/month)

### Support:
For issues, check Render logs in dashboard or contact support.
