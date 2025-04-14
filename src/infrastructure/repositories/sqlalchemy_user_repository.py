import json
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from src.domain.entities.user import ProficiencyLevel, User, UserProgress
from src.domain.interfaces.user_repository import UserRepository

Base = declarative_base()


class UserModel(Base):
    """Modelo SQLAlchemy para a tabela de usuários"""

    __tablename__ = "users"

    id = Column(String, primary_key=True)
    discord_id = Column(String, unique=True, index=True)
    username = Column(String)
    proficiency_level = Column(String)
    vocabulary_mastered = Column(Integer, default=0)
    lessons_completed = Column(Integer, default=0)
    practice_sessions = Column(Integer, default=0)
    pronunciation_score = Column(Float, default=0.0)
    grammar_accuracy = Column(Float, default=0.0)
    last_active = Column(DateTime, default=datetime.now)
    completed_topics = Column(JSON, default=lambda: json.dumps([]))
    conversation_history = Column(JSON, default=lambda: json.dumps([]))
    created_at = Column(DateTime, default=datetime.now)
    last_interaction = Column(DateTime, nullable=True)


class SQLAlchemyUserRepository(UserRepository):
    """Implementação do repositório de usuários usando SQLAlchemy"""

    def __init__(self, database_url: str):
        """Inicializa o repositório com a URL do banco de dados"""
        self.database_url = database_url

        if database_url.startswith("sqlite"):
            # Para SQLite, usamos um engine síncrono com emulação assíncrona
            # já que SQLite não suporta operações assíncronas nativas
            self.engine = create_engine(database_url)
            self.async_session = None
            self.Session = sessionmaker(bind=self.engine)

            # Cria as tabelas se não existirem
            Base.metadata.create_all(self.engine)
        else:
            # Garantir que estamos usando o driver asyncpg
            db_url = database_url
            if db_url.startswith("postgresql:") and "+asyncpg" not in db_url:
                db_url = db_url.replace("postgresql:", "postgresql+asyncpg:")
            elif db_url.startswith("postgres:") and "+asyncpg" not in db_url:
                db_url = db_url.replace("postgres:", "postgresql+asyncpg:")

            # Para PostgreSQL com SSL, verificamos o certificado
            connect_args = {}
            # Para PostgreSQL, usamos engine assíncrono
            self.engine = create_async_engine(
                db_url, echo=False, future=True, connect_args=connect_args
            )
            self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)
            self.Session = None

            # Criar tabelas assincronamente se possível
            try:

                async def create_tables():
                    async with self.engine.begin() as conn:
                        await conn.run_sync(Base.metadata.create_all)

                try:
                    # Tentar executar no loop atual se existir
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        print(
                            "Loop em execução, as tabelas serão criadas posteriormente"
                        )
                    else:
                        loop.run_until_complete(create_tables())
                except RuntimeError:
                    # Criar um novo loop se necessário
                    asyncio.run(create_tables())
            except Exception as e:
                print(f"Aviso ao criar tabelas: {e}")
                print("Você pode precisar criar as tabelas manualmente.")

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Recupera um usuário pelo ID"""
        if self.async_session:
            async with self.async_session() as session:
                async with session.begin():
                    result = await session.execute(
                        select(UserModel).where(UserModel.id == user_id)
                    )
                    user_model = result.scalars().first()
                    return self._map_to_entity(user_model) if user_model else None
        else:
            with self.Session() as session:
                user_model = (
                    session.query(UserModel).filter(UserModel.id == user_id).first()
                )
                return self._map_to_entity(user_model) if user_model else None

    async def get_by_discord_id(self, discord_id: str) -> Optional[User]:
        """Recupera um usuário pelo ID do Discord"""
        if self.async_session:
            async with self.async_session() as session:
                async with session.begin():
                    result = await session.execute(
                        select(UserModel).where(UserModel.discord_id == discord_id)
                    )
                    user_model = result.scalars().first()
                    return self._map_to_entity(user_model) if user_model else None
        else:
            with self.Session() as session:
                user_model = (
                    session.query(UserModel)
                    .filter(UserModel.discord_id == discord_id)
                    .first()
                )
                return self._map_to_entity(user_model) if user_model else None

    async def save(self, user: User) -> User:
        """Salva ou atualiza um usuário no repositório"""
        # Mapeia a entidade de domínio para o modelo do SQLAlchemy
        user_dict = {
            "id": user.id,
            "discord_id": user.discord_id,
            "username": user.username,
            "proficiency_level": user.proficiency_level.value,
            "vocabulary_mastered": user.progress.vocabulary_mastered,
            "lessons_completed": user.progress.lessons_completed,
            "practice_sessions": user.progress.practice_sessions,
            "pronunciation_score": user.progress.pronunciation_score,
            "grammar_accuracy": user.progress.grammar_accuracy,
            "last_active": user.progress.last_active,
            "completed_topics": json.dumps(user.progress.completed_topics),
            "conversation_history": json.dumps(user.conversation_history),
            "created_at": user.created_at,
            "last_interaction": user.last_interaction,
        }

        if self.async_session:
            async with self.async_session() as session:
                # Verifica se o usuário já existe
                result = await session.execute(
                    select(UserModel).where(UserModel.id == user.id)
                )
                existing_user = result.scalars().first()

                if existing_user:
                    # Atualiza os campos do usuário existente
                    for key, value in user_dict.items():
                        setattr(existing_user, key, value)
                else:
                    # Cria um novo usuário
                    session.add(UserModel(**user_dict))

                await session.commit()
        else:
            with self.Session() as session:
                # Verifica se o usuário já existe
                existing_user = (
                    session.query(UserModel).filter(UserModel.id == user.id).first()
                )

                if existing_user:
                    # Atualiza os campos do usuário existente
                    for key, value in user_dict.items():
                        setattr(existing_user, key, value)
                else:
                    # Cria um novo usuário
                    session.add(UserModel(**user_dict))

                session.commit()

        return user

    async def delete(self, user_id: str) -> bool:
        """Remove um usuário do repositório"""
        try:
            if self.async_session:
                async with self.async_session() as session:
                    result = await session.execute(
                        select(UserModel).where(UserModel.id == user_id)
                    )
                    user = result.scalars().first()

                    if user:
                        await session.delete(user)
                        await session.commit()
                        return True
                    return False
            else:
                with self.Session() as session:
                    user = (
                        session.query(UserModel).filter(UserModel.id == user_id).first()
                    )

                    if user:
                        session.delete(user)
                        session.commit()
                        return True
                    return False
        except Exception as e:
            print(f"Erro ao excluir usuário: {e}")
            return False

    async def list_all(self) -> List[User]:
        """Lista todos os usuários"""
        if self.async_session:
            async with self.async_session() as session:
                result = await session.execute(select(UserModel))
                return [self._map_to_entity(user) for user in result.scalars().all()]
        else:
            with self.Session() as session:
                return [
                    self._map_to_entity(user) for user in session.query(UserModel).all()
                ]

    async def list_by_proficiency(self, proficiency_level: str) -> List[User]:
        """Lista usuários por nível de proficiência"""
        if self.async_session:
            async with self.async_session() as session:
                result = await session.execute(
                    select(UserModel).where(
                        UserModel.proficiency_level == proficiency_level
                    )
                )
                return [self._map_to_entity(user) for user in result.scalars().all()]
        else:
            with self.Session() as session:
                return [
                    self._map_to_entity(user)
                    for user in session.query(UserModel)
                    .filter(UserModel.proficiency_level == proficiency_level)
                    .all()
                ]

    async def get_user_statistics(self) -> Dict:
        """Retorna estatísticas agregadas sobre os usuários"""
        stats = {
            "total_users": 0,
            "active_users_last_week": 0,
            "proficiency_distribution": {
                "beginner": 0,
                "intermediate": 0,
                "advanced": 0,
            },
            "average_lessons_completed": 0,
            "average_practice_sessions": 0,
            "average_pronunciation_score": 0,
            "average_grammar_accuracy": 0,
        }

        # Define uma semana atrás para usuários ativos
        one_week_ago = datetime.now().timestamp() - (7 * 24 * 60 * 60)

        users = await self.list_all()

        if not users:
            return stats

        stats["total_users"] = len(users)

        # Contadores para médias
        total_lessons = 0
        total_practice = 0
        total_pronunciation = 0
        total_grammar = 0

        for user in users:
            # Contagem por nível de proficiência
            level = user.proficiency_level.value
            if level in stats["proficiency_distribution"]:
                stats["proficiency_distribution"][level] += 1

            # Usuários ativos na última semana
            if (
                user.last_interaction
                and user.last_interaction.timestamp() > one_week_ago
            ):
                stats["active_users_last_week"] += 1

            # Acumuladores para médias
            total_lessons += user.progress.lessons_completed
            total_practice += user.progress.practice_sessions
            total_pronunciation += user.progress.pronunciation_score
            total_grammar += user.progress.grammar_accuracy

        # Calcula médias
        stats["average_lessons_completed"] = total_lessons / len(users)
        stats["average_practice_sessions"] = total_practice / len(users)
        stats["average_pronunciation_score"] = total_pronunciation / len(users)
        stats["average_grammar_accuracy"] = total_grammar / len(users)

        return stats

    def _map_to_entity(self, model: UserModel) -> User:
        """Converte um modelo SQLAlchemy para uma entidade de domínio"""
        if not model:
            return None

        # Cria o objeto de progresso
        progress = UserProgress(
            vocabulary_mastered=model.vocabulary_mastered,
            lessons_completed=model.lessons_completed,
            practice_sessions=model.practice_sessions,
            pronunciation_score=model.pronunciation_score,
            grammar_accuracy=model.grammar_accuracy,
            last_active=model.last_active,
            completed_topics=(
                json.loads(model.completed_topics)
                if isinstance(model.completed_topics, str)
                else []
            ),
        )

        # Cria o objeto de usuário
        return User(
            id=model.id,
            discord_id=model.discord_id,
            username=model.username,
            proficiency_level=ProficiencyLevel(model.proficiency_level),
            progress=progress,
            conversation_history=(
                json.loads(model.conversation_history)
                if isinstance(model.conversation_history, str)
                else []
            ),
            created_at=model.created_at,
            last_interaction=model.last_interaction,
        )
