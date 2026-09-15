# 🏙️ AI CivicFix

### Turn Citizen Complaints Into Actionable Municipal Work

AI CivicFix is an AI-powered civic complaint management prototype designed to transform citizen complaints into **structured, prioritized, and actionable municipal work**.

Traditional complaint systems mainly collect reports. AI CivicFix goes further by helping identify the issue, estimate severity, detect duplicate reports, assign the responsible department, prioritize the complaint, track SLA timelines, and verify resolution.

---

## 🚀 The Problem

Citizens report problems such as:

* 🕳️ Potholes
* 🗑️ Garbage
* 💡 Broken streetlights
* 🌊 Overflowing drains
* 🛣️ Road damage
* 🏙️ Other civic issues

But after submitting a complaint, several problems can occur:

❌ Duplicate complaints
❌ Incorrect classification
❌ Poor prioritization
❌ Wrong department assignment
❌ No visibility into progress
❌ Delayed resolution
❌ Lack of verification

**The real challenge isn't collecting complaints — it's turning them into actionable municipal work.**

---

## 💡 Our Solution

AI CivicFix creates an end-to-end workflow:

**📸 Photo → 📍 Location → 🤖 AI Classification → ⚠️ Severity → 🔍 Duplicate Detection → 🏢 Department Assignment → 🚨 Priority → ⏱️ SLA → 📊 Tracking → 📸 Verification → ✅ Resolution**

The goal is to **close the loop between citizens and municipal authorities.**

---

## 🧠 Example AI Analysis

A citizen reports:

> "There is a very large pothole on the main road near the college. Many vehicles are struggling to pass and an accident may happen."

CivicFix can generate an analysis such as:

| Attribute                  | Result                 |
| -------------------------- | ---------------------- |
| 🕳️ Detected Issue         | Pothole                |
| 🤖 Confidence              | High                   |
| ⚠️ Severity                | High                   |
| 📐 Estimated Affected Area | 12 m²                  |
| 🔍 Duplicate Reports       | 7                      |
| 🚨 Priority                | P1                     |
| 🏢 Department              | Roads & Infrastructure |

This allows municipal teams to focus on **what needs attention first**.

---

# 🔧 Key Features

## 👤 Citizen Portal

Citizens can:

* Submit civic complaints
* Upload a photo as evidence
* Enter complaint location
* Capture GPS coordinates
* Select an issue type
* Add a detailed description
* Receive a unique tracking ID
* Track complaint status
* View AI analysis
* View resolution/verification information

---

## 🤖 AI Civic Analysis

After submission, CivicFix analyzes the complaint and generates:

* AI-detected issue category
* AI confidence score
* Severity score
* Priority level
* Estimated affected area
* Responsible department
* SLA duration
* Duplicate detection
* Related complaint cluster

Supported categories include:

* 🕳️ Pothole
* 🗑️ Garbage
* 💡 Streetlight
* 🌊 Drain
* 🔧 Other

---

## 🚨 Priority System

Complaints are organized into four priority levels:

| Priority | Meaning  |
| -------- | -------- |
| 🔴 P1    | Critical |
| 🟠 P2    | High     |
| 🟡 P3    | Medium   |
| 🟢 P4    | Low      |

Priority can consider factors such as:

* Severity
* Issue type
* Duplicate reports
* Risk-related keywords
* Estimated affected area

---

## 🔍 Duplicate Detection

Multiple citizens may report the same civic problem.

CivicFix attempts to identify related complaints using:

* Description similarity
* Geographic distance
* Existing complaint information

Example:

```text
Citizen A → Large pothole near college gate
Citizen B → Huge pothole near college entrance
Citizen C → Road damaged with pothole at college gate
```

These reports can be grouped into a related complaint cluster:

```text
Pothole Cluster
│
├── Complaint A
├── Complaint B
└── Complaint C
```

This can help reduce duplicate municipal work and reveal areas with repeated problems.

---

# 🏢 Department Assignment

CivicFix can automatically map issues to the appropriate municipal department.

| Issue          | Department             |
| -------------- | ---------------------- |
| 🕳️ Pothole    | Roads & Infrastructure |
| 🗑️ Garbage    | Sanitation             |
| 💡 Streetlight | Electrical Department  |
| 🌊 Drain       | Drainage Department    |
| 🔧 Other       | General Civic Services |

---

# ⏱️ SLA Tracking

Each complaint can receive an estimated Service Level Agreement (SLA).

The system tracks:

* SLA duration
* Due date/time
* Overdue status

This helps administrators identify complaints that require attention before they become delayed.

---

# 📊 Municipal Dashboard

The admin dashboard focuses on **actionable municipal information**, not just complaint storage.

### Dashboard capabilities:

* 🗺️ Complaint/problem map
* 🚨 Priority queue
* 🔗 Duplicate complaint clustering
* 🏢 Department assignment
* ⏱️ SLA tracking
* 📸 Before/after verification
* 📈 Complaint analytics
* 📊 Status analytics
* 📋 Complaint management
* 🤖 AI-assisted workload insights

---

# 🗺️ Civic Issue Map

Complaints with GPS coordinates can be displayed on an interactive map.

The map can help identify:

* Complaint locations
* Civic issue hotspots
* Areas with repeated complaints
* Geographic distribution of problems

The prototype uses **Leaflet.js** for map visualization.

---

# 📸 Before & After Verification

CivicFix supports resolution verification through before/after evidence.

Municipal teams can upload an after-resolution image and add verification information.

The system can store:

* Before image
* After image
* Verification status
* Verification notes
* Verification timestamp

This provides visual evidence of the resolution process.

---

# 📱 Complaint Tracking

Every complaint receives a unique tracking ID.

Citizens can use this ID to check the current status.

### Status Flow

```text
Submitted
    ↓
In Progress
    ↓
Resolved
```

The tracking interface can automatically refresh complaint information.

API endpoint:

```text
/api/track/<tracking_id>
```

---

# 🧠 AI Architecture

The current prototype uses a lightweight local **AI-style analysis engine**.

```text
Citizen Complaint
       │
       ▼
Photo + Description + GPS
       │
       ▼
Issue Classification
       │
       ▼
Confidence Score
       │
       ▼
Severity Analysis
       │
       ▼
Duplicate Detection
       │
       ▼
Priority Calculation
       │
       ▼
Department Assignment
       │
       ▼
SLA Calculation
       │
       ▼
Municipal Priority Queue
       │
       ▼
Resolution & Verification
```

### ⚠️ Current AI Implementation

The current version is a **deterministic AI-style prototype** based on text/keyword scoring, similarity analysis, and geographic distance calculations.

It does **not** currently use a trained computer-vision model.

This approach keeps the prototype lightweight and runnable without external AI APIs.

---

# 🛠️ Technology Stack

### Backend

* Python
* Flask
* SQLite

### AI / Data Processing

* Python text analysis
* Keyword scoring
* Sequence similarity
* Geographic distance calculations

### Frontend

* HTML5
* CSS3
* JavaScript
* Bootstrap
* Chart.js
* Leaflet.js

### Storage

* SQLite
* Local image uploads

### Notifications

* Gmail SMTP integration

---

# 📁 Project Structure

```text
AI-CivicFix/
│
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── uploads/
│   └── .gitkeep
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── success.html
│   ├── track.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   └── complaint_detail.html
│
└── static/
    ├── css/
    │   └── style.css
    │
    └── js/
        └── app.js
```

---

# 💻 Installation

## 1. Clone the Repository

```bash
git clone https://github.com/MohammedDesai/City_Complaints.git
```

Enter the project directory:

```bash
cd City_Complaints
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate:

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
```

Activate:

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ⚙️ Environment Configuration

Copy `.env.example` to `.env`.

### Windows

```bash
copy .env.example .env
```

Example:

```env
SECRET_KEY=change-this-secret-key

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
MAIL_FROM=
```

> ⚠️ Never commit your real `.env` file, passwords, API keys, or other secrets to GitHub.

---

# ▶️ Run the Application

Start Flask:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

---

# 🔐 Admin Dashboard

Admin login:

```text
http://127.0.0.1:5000/admin/login
```

Default demo credentials:

```text
Username: admin
Password: admin123
```

**Change these credentials before production deployment.**

---

# 📧 Email Notifications

Email notifications are optional.

Configure Gmail SMTP in `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
MAIL_FROM=your-email@gmail.com
```

If SMTP is not configured, the main application can still run without email notifications.

---

# 🗃️ Database

CivicFix uses SQLite for the prototype.

The database is initialized automatically when the application starts.

Complaint information can include:

* Tracking ID
* Citizen information
* Issue type
* Description
* Location
* Latitude
* Longitude
* Photo
* AI classification
* AI confidence
* Severity
* Priority
* Department
* SLA
* Duplicate cluster
* Status
* Resolution information
* Verification information
* Timestamps

---

# 🔄 Complete Complaint Lifecycle

```text
Citizen
   │
   ▼
Submit Complaint
   │
   ▼
Generate Tracking ID
   │
   ▼
AI Analysis
   │
   ├── Classification
   ├── Severity
   ├── Duplicate Detection
   ├── Priority
   ├── Department
   └── SLA
   │
   ▼
Municipal Priority Queue
   │
   ▼
Admin Review
   │
   ▼
In Progress
   │
   ▼
Municipal Action
   │
   ▼
After Photo
   │
   ▼
Verification
   │
   ▼
Resolved
```

---

# 📈 Future Improvements

The current prototype can be upgraded with more advanced AI capabilities.

## 1️⃣ Computer Vision

Integrate models such as:

* YOLO
* CNN
* Vision Transformers

Potential detection:

* Potholes
* Garbage
* Road damage
* Broken streetlights
* Drain overflow

---

## 2️⃣ Advanced NLP

Use NLP/LLMs for:

* Complaint understanding
* Classification
* Severity prediction
* Department assignment
* Complaint summarization

---

## 3️⃣ Embedding-Based Duplicate Detection

Use embeddings with technologies such as:

* Sentence Transformers
* BGE
* OpenAI embeddings

Potential vector databases:

* FAISS
* ChromaDB
* Qdrant
* Pinecone

This could provide more accurate semantic duplicate detection.

---

## 4️⃣ Geospatial Intelligence

Use:

* Haversine distance
* DBSCAN
* GeoPandas
* PostGIS

to identify civic issue hotspots.

Example:

```text
100 Complaints
      ↓
GPS Clustering
      ↓
Problem Hotspot
      ↓
Municipal Action
```

---

# 🤖 Future AI Agent

The long-term vision is to evolve CivicFix into an AI-assisted municipal operations agent.

```text
Citizen Complaint
       ↓
AI Agent
       ↓
Understand Issue
       ↓
Check Duplicate Reports
       ↓
Analyze Location
       ↓
Determine Severity
       ↓
Assign Department
       ↓
Create Work Order
       ↓
Notify Officer
       ↓
Monitor SLA
       ↓
Send Reminder
       ↓
Verify Resolution
       ↓
Close Complaint
```

The goal is to move from a simple complaint management system toward an **AI-powered municipal operations platform**.

---

# 🔒 Security Considerations

Before production deployment, additional security measures should be implemented:

* Strong authentication
* Password hashing
* Role-based access control
* Secure file validation
* File type restrictions
* Upload size limits
* CSRF protection
* Rate limiting
* Secure sessions
* HTTPS
* Database backups
* Audit logs
* Input validation
* Production secret management

---

# ⚠️ Prototype Disclaimer

AI CivicFix is currently a **student/MVP prototype**.

The current AI analysis is intended for demonstration and workflow automation. It should not be treated as a production-grade computer-vision or machine-learning system.

A production implementation would require:

* Real AI/ML models
* Model evaluation
* Better semantic duplicate detection
* Secure authentication
* Scalable infrastructure
* Cloud storage
* Municipal system integration
* Privacy controls
* Monitoring
* Security testing
* Human review

---

# 🎯 Project Objective

The core idea behind AI CivicFix is simple:

> **Submitting a complaint is easy. Turning that complaint into actionable municipal work is the real challenge.**

CivicFix attempts to close this gap:

```text
Citizen Complaint
       ↓
AI Analysis
       ↓
Priority
       ↓
Department
       ↓
SLA
       ↓
Municipal Action
       ↓
Verification
       ↓
Resolution
```

---

# 🌟 Why AI CivicFix?

### Traditional Complaint System

```text
Complaint
    ↓
Database
    ↓
Wait
```

### AI CivicFix

```text
Complaint
    ↓
AI Classification
    ↓
Severity
    ↓
Duplicate Detection
    ↓
Priority
    ↓
Department
    ↓
SLA
    ↓
Municipal Action
    ↓
Verification
    ↓
Resolution
```

---

# 🚀 Vision

AI CivicFix aims to create a transparent feedback loop between:

```text
Citizens
    ↕
AI CivicFix
    ↕
Municipal Departments
```

Moving from:

**Complaint Collection → Complaint Resolution**

and eventually toward:

**Reactive Governance → AI-Assisted Proactive Governance**

---

# 👨‍💻 Project

**AI CivicFix — Turn Citizen Complaints Into Actionable Municipal Work**

Built with:

**Python • Flask • SQLite • JavaScript • Bootstrap • Leaflet • Chart.js**

Developed as a practical civic-tech prototype using **vibe coding** to rapidly turn a real-world problem into a working product.

---

## 🔗 Repository

**GitHub:**
https://github.com/MohammedDesai/City_Complaints

---

## 📌 Keywords

`AI` `Artificial Intelligence` `CivicTech` `Smart City` `Municipal Technology` `Python` `Flask` `SQLite` `Machine Learning` `Automation` `Geospatial` `Complaint Management` `Vibe Coding` `Student Project`
