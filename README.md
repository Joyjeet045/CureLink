# 🩺 CureLink

**CureLink** is a Django-powered healthcare **superapp** designed to seamlessly connect patients, doctors, hospitals, and pharmacies on a unified platform.

---

## 🌟 Features

### 👥 Patient Portal

- **Register & Manage Profile**
- **Book Appointments**
  - Choose from multiple hospitals and clinics
  - Select preferred slots (subject to availability)
- **Navigation**
  - Get the **shortest route to the hospital** via integrated maps after booking
- **e-Prescriptions**
  - View prescriptions issued by your doctor
  - Includes recommended medicines
- **Medicines**
  - Order medicines from the in-app pharmacy
  - **Cart functionality** for selecting multiple medicines
  - Prescription validation required for **restricted drugs**
- **Tests & Diagnostics**
  - Book diagnostic tests at nearby hospitals/clinics within **50 km radius**
  - **Conflict detection** between tests to avoid overlaps or contradictions
  - **Cart system** for bundling tests
- **Video Consultations**
  - **Real-time consultations** via **WebRTC** powered by Django Channels
  - **LLM + Semantic Similarity** based **doctor matching** based on symptoms provided by the patient
- **Notifications**
  - Receive **appointment reminders 5 hours in advance via email**
- **Reviews & Ratings**
  - Submit in-app **reviews and ratings for doctors and hospitals**

---

### 💊 Pharmacy & Medicine Ordering

- **Browse and order prescribed medicines** through the in-app **pharmacy service**
- Medicines with restrictions (e.g., requiring a prescription) are **validated before delivery**
- Sellers from different companies can **update inventory**
- **Search, add to cart, and checkout seamlessly**

---

### 🏥 Hospital & Clinic Admin Portal

- **Register Clinics or Hospitals**
- **Manage Doctors**
  - Add doctors already practicing at your facility
  - Verify doctor self-registrations linking to your clinic
- **Inventory Management** for associated pharmacies and test centers

---

### 🩺 Doctor Portal

- **Self-Registration**
  - Doctors can register themselves
  - Link existing practicing locations (pending admin verification)
- **Manage Appointments**
  - View upcoming appointments and patient details
- **Issue e-Prescriptions**
  - Prescribe medicines directly to patients
- **View Patient History**
  - Access prior appointments, prescriptions, and diagnostic results
- **Conduct Video Consultations** in-app

---

## 🛠️ Technology Stack

- **Backend**: Django
- **Database**: PostgreSQL
- **Frontend**: Django Templates + Bootstrap
- **Scheduler**: Celery + Redis (for cron reminders)
- **Maps Integration**: React Leaflet API
- **Video Calls**: WebRTC + Django Channels
- **Doctor Matching**: LLM + Semantic Similarity on patient symptoms
- **Email Notifications**: Django Email Backend
- **Containerization**: Docker & Docker Compose

---

## ▶️ Running the Application

To start the backend server, Redis, Celery beat, and Celery worker manually:

```bash
daphne doctors_app.asgi:application
redis-server
celery -A doctors_app beat --loglevel=info
celery -A doctors_app worker --pool=eventlet -l info
```
To run the full stack using Docker Compose:

```bash
docker compose up --build

