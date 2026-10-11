import datetime

from sqlalchemy import create_engine, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship, sessionmaker, Session
from werkzeug.security import generate_password_hash, check_password_hash

# DB_HOST = os.environ.get('DB_HOST')
# DB_PORT = os.environ.get('DB_PORT')
# DB_NAME = os.environ.get('DB_NAME')
# DB_USER = os.environ.get('DB_USER')
# DB_PASSWORD = os.environ.get('DB_PASSWORD')
#
# engine = create_engine(
#     f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}",
#     echo=True, pool_size=6, max_overflow=10, encoding='utf-8'
# )
#
engine = create_engine(
    "sqlite:///./flask_hw.db?check_same_thread=False",
    echo=True
)
SessionLocal = sessionmaker(bind=engine, class_=Session)

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)

    advertisements: Mapped[list['Advertisement']] = relationship(back_populates='owner')

    def set_password(self, password: str) -> None:
        """Устанавливает хэш пароля (не хранит пароль в открытом виде)."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Проверяет пароль против хэша."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Преобразует пользователя в словарь (без пароля)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
        }


class Advertisement(Base):
    __tablename__ = 'advertisements'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    owner: Mapped['Users'] = relationship(back_populates='advertisements')

    def to_dict(self) -> dict:
        """Преобразует объявление в словарь для JSON."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "owner_id": self.owner_id,
        }

    def __repr__(self) -> str:
        return f"<Advertisement id={self.id} title={self.title!r}>"
