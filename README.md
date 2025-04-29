**Health Monitoring Dashboard**

A comprehensive health monitoring system with real-time data visualization capabilities.

**Overview**

This project combines a Django backend with a Streamlit frontend to create a powerful health monitoring dashboard. The system processes health metrics (heart rate, blood pressure, SpO2, etc.), and presents the data in an intuitive interface.
Show Image
Features

**User Authentication:** Secure JWT-based authentication system

**Real-time Monitoring:** Live updates of health metrics

**Interactive Visualizations:** Customizable charts and graphs

**Data Simulation:** Realistic health data generation for testing

**Architecture**

The system follows a client-server architecture:

**Backend:** Django REST API for data storage and processing

**Frontend:** Streamlit app for visualization and user interaction

**Data Processing:** Various anomaly detection algorithms (statistical, ML, time series)

**Simulation:** Configurable data generators for testing

**Project Structure**

health_monitoring_system/

├── backend/                       # Django Project Root

│   ├── core/                      # Django project settings

│   ├── users/                     # User authentication app

│   ├── health_metrics/            # Health data app

├── frontend/                      # Streamlit App Root

│   ├── app.py                     # Main Streamlit app

│   ├── pages/                     # Streamlit pages

│   └── utils/                     # Frontend utilities

├── data_simulation/               # Data simulation module

│   ├── simulator.py               # Main simulation orchestrator

│   ├── generators/                # Data generators

│   └── models/                    # Statistical models

└── deployment/                    # Deployment configurations

**Getting Started**

**Prerequisites**

Python 3.8+
pip
virtualenv (recommended)
PostgreSQL (recommended for production)

**Installation**

**Clone the repository:**

git clone https://github.com/yourusername/health-monitoring-dashboard.git

cd health-monitoring-dashboard

**Set up the backend:**

cd backend

python -m venv venv

source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate

python manage.py createsuperuser

python manage.py runserver

**Set up the frontend:**

cd ../frontend

python -m venv venv

source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt

streamlit run app.py

