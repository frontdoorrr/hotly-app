"""Import all models for Alembic autogeneration."""

# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa

# Import your models here as they are created
from app.models.place import Place  # noqa
