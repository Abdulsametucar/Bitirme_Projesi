from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Worker(Base):
    __tablename__ = 'workers'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    towel_processes = relationship('TowelProcess', back_populates='worker')

class TowelProcess(Base):
    __tablename__ = 'towel_processes'
    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, ForeignKey('workers.id'))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    total_steps = Column(Integer, nullable=False)
    correct_fold = Column(Boolean, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    steps = relationship('Step', back_populates='process', cascade='all, delete-orphan')
    worker = relationship('Worker', back_populates='towel_processes')

class Step(Base):
    __tablename__ = 'steps'
    id = Column(Integer, primary_key=True)
    process_id = Column(Integer, ForeignKey('towel_processes.id'), nullable=False)
    name = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    process = relationship('TowelProcess', back_populates='steps')
