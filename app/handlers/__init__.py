from .admin import get_router as get_admin_router
from .user import get_router as get_user_router
from aiogram import Router


def get_router() -> Router:
    """
    Creates and configures a new Router instance by including
    admin and user routers.

    Returns:
        Router: A configured Router instance with admin and user routers included.
    """
    router = Router()
    router.include_router(get_admin_router())
    router.include_router(get_user_router())
    return router
