import os
from typing import Union
from .storage import InMemoryStorage
from .postgres_storage import PostgreSQLStorage
from .database import get_db_session

class StorageFactory:
    """Фабрика для создания storage в зависимости от конфигурации"""
    
    @staticmethod
    def create_storage() -> Union[InMemoryStorage, PostgreSQLStorage]:
        """Создает storage в зависимости от переменной окружения"""
        storage_type = os.getenv("STORAGE_TYPE", "postgres").lower()
        
        if storage_type == "inmemory":
            return InMemoryStorage()
        elif storage_type == "postgres":
            # Возвращаем None, так как PostgreSQL storage требует сессию
            # которая будет передана при каждом вызове
            return None
        else:
            raise ValueError(f"Неизвестный тип storage: {storage_type}")
    
    @staticmethod
    async def get_postgres_storage():
        """Получает PostgreSQL storage с сессией базы данных"""
        async for session in get_db_session():
            return PostgreSQLStorage(session)
    
    @staticmethod
    def get_storage_type() -> str:
        """Возвращает текущий тип storage"""
        return os.getenv("STORAGE_TYPE", "postgres").lower()
