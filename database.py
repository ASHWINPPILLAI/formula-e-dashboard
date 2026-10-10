import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
# For production, this would be read from os.environ.get("DATABASE_URL")
# e.g., postgresql://user:pass@localhost/dbname
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(_THIS_DIR, 'telemetry_v2.db')}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class TelemetryRecord(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(String, index=True, nullable=False)
    lap_number = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    turn_3_regen = Column(Float, nullable=False)
    turn_13_regen = Column(Float, nullable=False)
    lift_coast = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
