from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from Backend.config import settings
# DATABASE_URL="postgresql+asyncpg://postgres:Ads2023!@localhost/puda_database"
# DATABASE_URL="postgresql+asyncpg://postgres:Ads2023!@localhost:5432/PUDA_DATABASE"

engine=create_async_engine(settings.DATABASE_URL,echo=True)

SessionLocal= sessionmaker(bind=engine,
                           class_=AsyncSession,
                           expire_on_commit=False)

Base=declarative_base()

async def get_db():

    db=SessionLocal()
    try:
        yield db
    finally:
        await db.close()