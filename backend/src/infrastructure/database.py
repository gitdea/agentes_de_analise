
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Carregar o .env diretamente da pasta backend (subindo apenas 2 níveis a partir de infrastructure)
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent  # Ajustado para parar na pasta backend
env_path = project_root / ".env"

load_dotenv(dotenv_path=env_path)

# Obter a DATABASE_URL com um fallback defensivo imediato
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL or DATABASE_URL.strip() == "" or DATABASE_URL == "SUA_DATABASE_URL_DO_NEON_AQUI":
    DATABASE_URL = "sqlite:///:memory:"
    print("⚠️ Aviso: DATABASE_URL não detetada. A usar SQLite em memória para testes.")

# Ajustar prefixo se necessário
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Criar o motor do SQLAlchemy de forma 100% segura
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class AnaliseModel(Base):
    __tablename__ = "historico_analises"

    id = Column(Integer, primary_key=True, index=True)
    data_hora = Column(DateTime, default=datetime.utcnow)
    nome_ficheiro = Column(String(255), nullable=False)
    questao = Column(Text, nullable=False)
    resumo_agente = Column(Text, nullable=False)

def init_db():
    """Cria as tabelas na base de dados se ainda não existirem."""
    Base.metadata.create_all(bind=engine)