# 🏋️ Elite Performance – Fitness Web App

![Elite Performance](https://img.shields.io/badge/Status-Live-brightgreen?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.3.3-black?style=flat-square&logo=flask)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green?style=flat-square&logo=mongodb)
![Vercel](https://img.shields.io/badge/Deployed-Vercel-black?style=flat-square&logo=vercel)

> A feature-rich, AI-powered fitness web application with personalized training plans, real-time coaching, workout tracking, leaderboards, and more.

🔗 **Live Demo:** [elite-fitness-main.vercel.app](https://elite-fitness-main.vercel.app)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Secure Auth** | Email/password login with Gmail OTP verification |
| 🤖 **AI Coach** | Gemini-powered personalized fitness coaching |
| 📋 **Workout Plans** | Auto-generated plans based on goals & body stats |
| 📊 **Progress Tracking** | Workout logs, sleep tracking, and statistics |
| 🏆 **Leaderboard** | Global ranking and community challenges |
| 🎮 **Fitness Game** | Gamified workout experience with aura system |
| 🎯 **Goal Setting** | Set and track personalized fitness goals |
| 🏅 **Sports Mode** | Sport-specific training programs |
| 🔑 **Forgot Password** | OTP-based secure password reset via Gmail |

---

## 🛠️ Tech Stack

- **Backend:** Python 3.12, Flask 2.3.3
- **Database:** MongoDB Atlas (PyMongo)
- **Email (OTP):** Flask-Mail with Gmail SMTP
- **AI:** Google Gemini API (`google-generativeai`)
- **Auth:** Session-based + Gmail OTP (stored in MongoDB)
- **Deployment:** Vercel (serverless)
- **Frontend:** Vanilla HTML, CSS, JavaScript

---

## 📁 Project Structure

```
elite-fitness-main/
├── app.py                  # Main Flask application & all API routes
├── auth.py                 # OAuth helper functions
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel deployment config
├── Procfile                # Gunicorn process config
├── runtime.txt             # Python version spec
├── .env                    # Local environment variables (NOT committed)
├── .gitignore
├── templates/
│   ├── index.html          # Landing page
│   ├── login.html          # Login & Register page
│   ├── forgot_password.html
│   ├── plan.html           # Workout plan dashboard
│   ├── ai.html             # AI coaching interface
│   ├── game.html           # Fitness game
│   ├── goal.html           # Goal tracking
│   ├── leader.html         # Leaderboard
│   ├── stat.html           # Statistics & progress
│   ├── aura.html           # Aura / gamification
│   ├── sports.html         # Sports training
│   └── workout.html        # Workout logging
└── static/                 # CSS, JS, images
```

---

## ⚙️ Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/ShanmukhaPabolu/elite-fitness.git
cd elite-fitness
```

### 2. Create a virtual environment & install dependencies

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### 3. Create a `.env` file

Create a file named `.env` in the project root with the following content:

```dotenv
# Flask
FLASK_SECRET_KEY=your_random_secret_key_here

# MongoDB Atlas
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?appName=Cluster0

# Gmail SMTP (for OTP emails)
MAIL_USERNAME=your_gmail@gmail.com
MAIL_PASSWORD=your_16_char_app_password

# Google Gemini AI
GOOGLE_API_KEY=your_gemini_api_key
```

> **Note:** For `MAIL_PASSWORD`, use a **Gmail App Password** (not your regular Gmail password).
> Go to Google Account → Security → 2-Step Verification → App Passwords → Create one for "Fitness App".

### 4. Run the app

```bash
python app.py
```

The app will open automatically at **http://localhost:5000**

---

## 🌐 Deployment (Vercel)

This project is deployed on **Vercel**. To deploy your own copy:

### Prerequisites
- Install Vercel CLI: `npm install -g vercel`
- Login: `vercel login`

### Deploy

```bash
vercel --prod --yes
```

### Required Environment Variables on Vercel

Set these in **Vercel Dashboard → Settings → Environment Variables**:

| Variable | Value |
|---|---|
| `FLASK_SECRET_KEY` | A long random string |
| `MONGODB_URI` | Your MongoDB Atlas connection string |
| `MAIL_USERNAME` | Your Gmail address |
| `MAIL_PASSWORD` | Your Gmail App Password |
| `GOOGLE_API_KEY` | Your Gemini API key |

---

## 🔐 Authentication Flow

```
User logs in with email & password
        ↓
Credentials verified against MongoDB
        ↓
OTP generated & emailed via Gmail SMTP
        ↓
OTP stored in MongoDB (otp_store collection)
        ↓
User enters OTP → verified against MongoDB
        ↓
Session created → User logged in
```

> OTPs are stored in **MongoDB** (not Flask sessions) to ensure compatibility with Vercel's serverless architecture where sessions don't persist between requests.

---

## 📧 Gmail OTP Setup

1. Go to your [Google Account](https://myaccount.google.com)
2. Navigate to **Security → 2-Step Verification** (must be enabled)
3. Go to **App Passwords**
4. Create a new App Password (name it "Fitness App")
5. Copy the 16-character password into `MAIL_PASSWORD` in your `.env` file

---

## 🤖 AI Coach Setup

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Generate a free Gemini API key
3. Add it to your `.env` as `GOOGLE_API_KEY`

---

## 📦 Key Dependencies

```
Flask==2.3.3
Flask-Mail==0.10.0
pymongo==4.6.1
google-generativeai==0.7.2
python-dotenv==1.0.1
gunicorn==21.2.0
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 👤 Author

**Shanmukha Pabolu**
- GitHub: [@ShanmukhaPabolu](https://github.com/ShanmukhaPabolu)
- Live App: [elite-fitness-main.vercel.app](https://elite-fitness-main.vercel.app)
