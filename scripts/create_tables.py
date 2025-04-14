"""
Script para criar tabelas no banco de dados PostgreSQL.
Para executar: python -m scripts.create_tables
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from src.infrastructure.repositories.sqlalchemy_user_repository import Base


async def create_database_tables():
    load_dotenv()  # Carregar variáveis de ambiente
    database_url = os.getenv("DATABASE_URL", "")

    if not database_url:
        print("Erro: DATABASE_URL não encontrada no arquivo .env")
        return

    # Garantir uso do driver asyncpg para PostgreSQL
    if database_url.startswith("postgresql:") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql:", "postgresql+asyncpg:")
    elif database_url.startswith("postgres:") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgres:", "postgresql+asyncpg:")

    # Configurar argumentos de conexão para SSL se necessário
    connect_args = {}

    print(f"Conectando ao banco de dados: {database_url}")
    try:
        # Criar engine com timeout maior
        engine = create_async_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,  # Verifica conexão antes de usar
            pool_recycle=3600,  # Recicla conexões após 1 hora
            echo=True,  # Mostra logs SQL para debug
        )

        # Criar tabelas
        async with engine.begin() as conn:
            print("Criando tabelas...")
            await conn.run_sync(Base.metadata.create_all)

        # Fechar engine
        await engine.dispose()
        print("Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(create_database_tables())
    except Exception as e:
        print(f"Falha na execução: {e}")
