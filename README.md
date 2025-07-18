# 🏦 JD Fintech Platform

A comprehensive open banking and financial data aggregation platform leveraging JoPACC’s Jordan Open Finance APIs.

---

## 🚀 Features

- **Account Aggregation**: View and manage accounts across banks.
- **Wallet Integration**: Fund and manage JD Dinar digital wallets.
- **Transaction Insights**: Get categorized spending, analytics & fraud detection.
- **Profile Sync**: Onboard users with unified KYC + account data.
- **Credit Scoring**: Generate credit scores from AIS/PIS data.
- **AML & Fraud Detection**: Monitor suspicious activity using ML.
- **Gallery Dashboard**: Real-time visualization of financial events.

---

## ⚙️ Setup Guide

Follow the instructions below to run the project locally:

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/jd-fintech-platform.git
cd jd-fintech-platform
```

### 2. Environment Configuration

Create a `.env` file in both the backend and frontend directories.

#### `backend/.env`

```env
JOPACC_CLIENT_ID=your_client_id
JOPACC_CLIENT_SECRET=your_client_secret
JOPACC_BASE_URL=https://api.jopacc.jo/openbanking
JOPACC_TOKEN=your_direct_auth_token
MONGO_URI=mongodb://localhost:27017
DB_NAME=jd_stablecoin
AML_MODEL_PATH=models/aml_model.pkl
RISK_MODEL_PATH=models/risk_model.pkl
SECRET_KEY=supersecretkey
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### `frontend/.env`

```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### 3. Start MongoDB

**Option A: Local MongoDB**

```bash
mongod
```

**Option B: MongoDB via Docker**

```bash
docker run -d -p 27017:27017 --name mongo-db mongo
```

### 4. Run the Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 5. Run the Frontend

```bash
cd frontend
npm install
npm start
```

> The app will run at: [http://localhost:3000](http://localhost:3000)

### 6. Run with Docker Compose (Optional)

```bash
docker-compose up --build
```

### 7. Access the App

- Frontend: [http://localhost:3000](http://localhost:3000)
- API Docs: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## 📁 Project Structure

```
jd-fintech-platform/
├── backend/
│   ├── main.py
│   ├── models/
│   ├── services/
│   ├── routers/
│   ├── utils/
│   └── .env
├── frontend/
│   ├── public/
│   ├── src/
│   └── .env
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

## 🧠 Tech Stack

- **Frontend**: React, Axios, Tailwind CSS
- **Backend**: FastAPI, Python, MongoDB, Pydantic
- **AI/ML**: Sklearn, Custom AML & Risk Scoring Models
- **Open Banking API**: JoPACC (Jordan)
- **DevOps**: Docker, Uvicorn, dotenv

---

## 🧪 Test Users

| Bank         | User     | Password |
|--------------|----------|----------|
| Capital Bank | demo1    | 123456   |
| Cairo Amman  | demo2    | 123456   |
| Housing Bank | demo3    | 123456   |
| Jordan Kuwait| demo4    | 123456   |

---

## 👥 Authors

- **Oduai Abrb**
- **Omar Sawalmeh**
- Code & coins Team @ ASU

---

## 📜 License

MIT License