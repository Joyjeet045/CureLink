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
- **Notifications**
  - Receive **appointment reminders 5 hours in advance via email**
- **Reviews & Ratings**
  - Submit in-app **reviews and ratings for doctors and hospitals**

---

### 💊 Pharmacy & Medicine Ordering

- **Browse and order prescribed medicines** through the in-app **pharmacy service**
- Medicines with restrictions (e.g., requiring a prescription) are **validated before delivery**
- Sellers of various companies can update this **inventory**

---

### 🏥 Hospital & Clinic Admin Portal

- **Register Clinics or Hospitals**
- **Manage Doctors**
  - Add doctors already practicing at your facility
  - Verify doctor self-registrations linking to your clinic

---

### 🩺 Doctor Portal

- **Self-Registration**
  - Doctors can register themselves
  - Link existing practicing locations (pending admin verification)
- **Manage Appointments**
- **Issue e-Prescriptions**
  - Prescribe medicines directly to patients
- **View Patient History**

---

## 🛠️ Technology Stack

- **Backend**: Django
- **Database**: PostgreSQL
- **Frontend**: Django Templates + Bootstrap
- **Scheduler**: Celery + Redis (for cron reminders)
- **Maps Integration**: React Leaflet API
- **Email Notifications**: Django Email Backend

---

## ▶️ Running Celery

To start Celery for scheduled tasks and background processing:

```bash
.\redis-server.exe
celery -A doctors_app beat --loglevel=info
celery -A doctors_app worker --pool=eventlet -l info
