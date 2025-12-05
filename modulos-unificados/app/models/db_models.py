# app/models/db_models.py
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from app.database import Base

class Patient(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    age = Column(Integer)
    diabetes_type = Column(String)
    diagnosis_date = Column(DateTime)
    created_at = Column(DateTime)
    current_cluster = Column(Integer, nullable=True)
    last_analysis_date = Column(DateTime, nullable=True)

class GlucoseReading(Base):
    __tablename__ = "glucose_readings"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    value = Column(Float)
    created_at = Column(DateTime)

class DailyMetrics(Base):
    __tablename__ = "daily_metrics"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    date = Column(DateTime, index=True)
    mean_glucose = Column(Float)
    std_glucose = Column(Float)
    cv = Column(Float)
    tir = Column(Float)
    tbr = Column(Float)
    tbr_severe = Column(Float)
    tar = Column(Float)
    tar_severe = Column(Float)
    gmi = Column(Float)
    glucose_range = Column(Float)
    n_readings = Column(Integer)
    created_at = Column(DateTime)

class ClusterAssignment(Base):
    __tablename__ = "cluster_assignments"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    cluster_id = Column(Integer)
    cluster_name = Column(String)
    confidence_score = Column(Float)
    assigned_at = Column(DateTime)
    avg_tir = Column(Float)
    avg_cv = Column(Float)
    avg_gmi = Column(Float)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    formulario_inicio = Column(Boolean, default=False)
    created_at = Column(DateTime)
