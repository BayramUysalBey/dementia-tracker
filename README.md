# Dementia Tracker (v1)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📌 Project Overview

**Dementia Tracker** is a dedicated web application designed to help caregivers monitor, log, and share the symptoms and progress of loved ones living with dementia. 

**Live Demo**: [https://dementia-tracker.onrender.com](https://dementia-tracker.onrender.com)

This project was developed over 5 months (May 2023 - February 2026) as a personal journey to master backend development through real-world application, heavily inspired by Miguel Grinberg's "Flask Mega-Tutorial" and fueled by my personal experience as a caregiver.

### 🌟 Inspiration
In May 2023, my mother was diagnosed with dementia. Since August 2024, I have been her primary caregiver while transitioning my career into backend development. This project represents both my technical growth and my commitment to improving life for fellow caregivers.

---

## 🚀 Key Features

- **Symptom Logging**: Record diagnoses and observations with 4 levels of severity (Mild, Moderate, Severe, Critical).
- **Caregiver Network**: Follow other caregivers to stay updated on their updates and shared experiences.
- **Real-time Notifications**: Instant feedback on messages and background task progress.
- **Private Messaging**: Secure communication channel for caregivers to coordinate and support each other.
- **Advanced Search**: Full-text search for symptom logs powered by Elasticsearch.
- **Data Export**: Background tasks to export symptom history as JSON, delivered directly via email.
- **Global & User Feeds**: "Explore" public logs or stay focused on those you follow.
- **Responsive Profiles**: Customizable profiles with Gravatar integration and specialized admin badges.
- **Multi-language Support**: Fully localized infrastructure using Flask-Babel.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.9+, Flask (Web Framework)
- **Database**: PostgreSQL (Production) / SQLAlchemy (ORM)
- **Migrations**: Flask-Migrate (Alembic)
- **Authentication**: Flask-Login, JWT (Password Resets)
- **Search Engine**: Elasticsearch
- **Task Queue**: RQ (Redis Queue)
- **Frontend**: Jinja2 Templates, Vanilla CSS, Moment.js (Time formatting)
- **Deployment**: Docker, Docker Compose, Gunicorn
- **Styling**: Bootstrap (via tutorial patterns) & Custom CSS

---

## ⚙️ Setup & Installation

### Option 1: Using Docker (Recommended)
1.  Clone the repository.
2.  Create a `.env` file based on `.env.example`.
3.  Run the containers:
    ```bash
    docker-compose up --build
    ```
4.  Access the app at `http://localhost:5000`.

### Option 2: Local Development
1.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set environment variables in `.env`.
4.  Initialize the database:
    ```bash
    flask db upgrade
    ```
5.  Run the application:
    ```bash
    flask run
    ```

---

## 📂 Project Structure

```text
├── app/                  # Application logic, routes, and models
│   ├── auth/             # Authentication blueprint
│   ├── errors/           # Error handling blueprint
│   ├── main/             # Main application logic and routes
│   ├── templates/        # Jinja2 templates
│   ├── static/           # CSS, JS, and Images
│   ├── models.py         # Database models (Caregiver, SymptomLog, etc.)
│   └── tasks.py          # Background tasks (RQ)
├── migrations/           # Database migration scripts
├── tests.py              # Unit tests
├── config.py             # Configuration settings
├── docker-compose.yml    # Docker services configuration
└── requirements.txt      # Python dependencies
```

---

## 🏁 Closure: Version 1

This project has been a monumental learning experience. It taught me the complexities of database design, the nuance of background processing, and the importance of user-centric features. 

As I "finish" this project in my mind, the code here serves as a foundation for **Dementia Tracker v2**, where I plan to transition to **FastAPI**, implement a more structured data model (aggression levels, sleep patterns), and focus on professional PDF reporting for medical visits.

**Onward to v2.** 🚀

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
