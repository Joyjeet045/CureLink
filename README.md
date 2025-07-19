# 🩺 CureLink

**CureLink** is a Django-powered healthcare **superapp** that seamlessly connects patients, doctors, hospitals, and pharmacies on a unified platform.

![Healthcare Platform](https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?w=800&h=400&fit=crop)
![Medical Technology](https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=800&h=400&fit=crop)

---

## 🌟 Key Features

### 👥 Patient Portal
- **Appointment Booking** with route navigation to hospitals
- **e-Prescriptions** with medicine ordering and cart functionality
- **Diagnostic Tests** booking within 50km radius with conflict detection
- **Video Consultations** via WebRTC with AI-powered doctor matching
- **Email reminders** 5 hours before appointments
- **Reviews & Ratings** for healthcare providers

### 💊 Pharmacy & Medicine Ordering
- **Prescription validation** for restricted drugs
- **Inventory management** for multiple sellers
- **Seamless search and checkout** experience

### 🏥 Hospital & Clinic Admin Portal
- **Facility registration** and doctor management
- **Inventory control** for pharmacies and test centers
- **Doctor verification** system

### 🩺 Doctor Portal
- **Self-registration** with location linking
- **Appointment management** and patient history access
- **e-Prescription issuance** and video consultations

---

## 🛠️ Technology Stack

- **Backend**: Django
- **Database**: PostgreSQL
- **Frontend**: Django Templates + Bootstrap
- **Scheduler**: Celery + Redis
- **Maps**: React Leaflet API
- **Video Calls**: WebRTC + Django Channels
- **AI Matching**: SentenceTransformers + FAISS + Groq
- **Containerization**: Docker & Docker Compose

---

## ▶️ Quick Start

### Manual Setup
```bash
daphne doctors_app.asgi:application
redis-server
celery -A doctors_app beat --loglevel=info
celery -A doctors_app worker --pool=eventlet -l info
```

### Docker Setup
```bash
docker compose up --build
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- Create an issue on GitHub
- Check the test files for usage examples
- Review the architecture documentation

Happy Trading! 🚀📈


