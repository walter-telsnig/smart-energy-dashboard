from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine

engine = create_engine("postgresql://postgres:ppswy2026@localhost:5432/pv-db", connect_args={"connect_timeout": 5} )
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()