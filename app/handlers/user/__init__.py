from . import exchange, gifts, merch, quiz, start, transfer, transactions, withdraw
from aiogram import Router


def get_router() -> Router:
    """
    Creates and configures a new Router instance by including various sub-routers.

    This function initializes a new Router object and includes multiple sub-routers
    from different modules such as exchange, quiz, start, transfer, transactions,
    withdraw, gifts, and merch. Each sub-router is responsible for handling specific
    routes and functionalities within the application.

    Returns:
        Router: A configured Router instance with all the included sub-routers.
    """
    router = Router()
    router.include_router(exchange.router)
    router.include_router(quiz.router)
    router.include_router(start.router)
    router.include_router(transfer.router)
    router.include_router(transactions.router)
    router.include_router(withdraw.router)
    router.include_router(gifts.router)
    router.include_router(merch.router)
    return router
