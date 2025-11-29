from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Float
from datetime import datetime
from database import Base

class AcceptedPlan(Base):
    __tablename__ = 'accepted_plans'
    
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    plan_data = Column(JSON, nullable=False)
    user_id = Column(Integer, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'severity': self.severity,
            'timestamp': self.timestamp,
            'plan_data': self.plan_data,
            'user_id': self.user_id
        }

class RejectedPlan(Base):
    __tablename__ = 'rejected_plans'
    
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    reason = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'severity': self.severity,
            'timestamp': self.timestamp,
            'reason': self.reason,
            'user_id': self.user_id
        }

class AlertSent(Base):
    __tablename__ = 'alerts_sent'
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    message = Column(Text, nullable=False)
    recipients_count = Column(Integer, default=0)
    delivery_status = Column(String(50), default='simulated')
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.alert_type,
            'city': self.city,
            'severity': self.severity,
            'timestamp': self.timestamp,
            'message': self.message,
            'recipients_count': self.recipients_count,
            'delivery_status': self.delivery_status
        }

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200))
    hospital_name = Column(String(200))
    city = Column(String(100))
    role = Column(String(50), default='hospital_admin')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'hospital_name': self.hospital_name,
            'city': self.city,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'last_login': self.last_login
        }

class DataSnapshot(Base):
    __tablename__ = 'data_snapshots'
    
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    aqi = Column(Float)
    pm25 = Column(Float)
    pm10 = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    total_cases = Column(Integer)
    respiratory_cases = Column(Integer)
    hospitalizations = Column(Integer)
    weather_condition = Column(String(100))
    data_source = Column(String(50), default='csv')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'date': self.date,
            'aqi': self.aqi,
            'pm25': self.pm25,
            'pm10': self.pm10,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'wind_speed': self.wind_speed,
            'total_cases': self.total_cases,
            'respiratory_cases': self.respiratory_cases,
            'hospitalizations': self.hospitalizations,
            'weather_condition': self.weather_condition,
            'data_source': self.data_source,
            'created_at': self.created_at
        }
