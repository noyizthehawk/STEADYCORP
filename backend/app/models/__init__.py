"""SQLAlchemy models.

Each model lives in its own module. Uncomment its import below as you write it
so Alembic autogenerate and the test harness register it on ``Base.metadata``.

Order matters only for readability; SQLAlchemy resolves FK relationships by
string name regardless of import order.
"""

from app.models.brick import Brick
from app.models.drop import Drop
from app.models.order import Order
from app.models.quiz import QuizQuestion, QuizSession
from app.models.user import User

__all__ = [
    "User",
    "Drop",
    "Brick",
    "Order",
    "QuizQuestion",
    "QuizSession",
]
