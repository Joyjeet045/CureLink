# 🩺 CureLink

**CureLink** is a Django-powered healthcare **superapp** designed to seamlessly connect patients, doctors, hospitals, pharmacies, and diagnostic labs on a unified platform.

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
  - Includes recommended medicines and lab tests
- **Medicines**
  - Order Medicines from in-app pharmacy
- **Lab Tests**
  - Book diagnostic tests or health packages in **nearby labs (within a 50km radius)**
  - The system uses a combination of **H3 geospatial indexing** and **geodesic distance calculations** to find and sort the **nearest 10 labs then by price filtering**
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
  - Prescribe medicines and recommend tests directly to patients
- **View Patient History**

---

### 🧪 Lab Admin Portal

- **Register Diagnostic Labs**
- **Manage Lab Orders**
  - View and track all incoming test bookings
  - Update test progress across **4 steps**:
    1. Collection of Sample
    2. Tests Conducted
    3. Report Preparation
    4. Report Sent
- **Send Test Reports In-App**

---

## 🛠️ Technology Stack

- **Backend**: Django
- **Database**: PostgreSQL
- **Frontend**: Django Templates + Bootstrap
- **Scheduler**: Celery + Redis (for cron reminders)
- **Maps Integration**: React Leaflet API
- **Email Notifications**: Django Email Backend
- **Geospatial Search**: H3 hexagonal indexing + geodesic distance calculation
