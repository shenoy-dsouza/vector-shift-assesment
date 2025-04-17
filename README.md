# 🧠 VectorShift Integrations Technical Assessment

Thank you for taking the time to review this project! This assessment consists of both backend and frontend components and demonstrates a working integration with HubSpot OAuth and item loading. This project follows the patterns used for Notion and Airtable integrations.

For detailed project requirements provided by the interviewer, refer to the document below:  
📝 **Interview Document**: [Google Doc](https://drive.google.com/file/d/1rlHedvalR0021mlB9wSY9ddbTmH16Xxp/view?usp=drive_link)

---

## 🚀 Tech Stack

- **Frontend**: React (JavaScript)
- **Backend**: FastAPI (Python)
- **Database/Cache**: Redis

---

## 📁 Project Structure

```
├── frontend
│   └── src
│       └── integrations
│           ├── airtable.js
│           ├── notion.js
│           └── hubspot.js  ← You complete this
├── backend
│   ├── main.py              ← FastAPI entry point
│   └── integrations
│       ├── airtable.py      ← Provided
│       ├── notion.py        ← Provided
│       └── hubspot.py       ← You complete this
```

---

## 🛠️ Setup Instructions


### 🔁 Clone the Repository

```bash
git clone https://github.com/shenoy-dsouza/vector-shift-assesment.git
cd vector-shift-assesment
```

### 📦 Backend (FastAPI)

1. Navigate to the backend folder:

```bash
cd backend
```

2. Create a virtual environment and activate it:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run Redis server (in a new terminal window):

```bash
redis-server
```

5. Start the FastAPI server:

```bash
uvicorn main:app --reload
```

### 🌐 Frontend (React)

1. Navigate to the frontend folder:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run start
```

---


### Video

[![Watch the demo](https://img.youtube.com/vi/716n4p0epFo/hqdefault.jpg)](https://youtu.be/716n4p0epFo)
