from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Classe base para os modelos do SQLAlchemy. Todos os modelos devem herdar desta classe para garantir a consistência e a integração com o ORM.
    """
