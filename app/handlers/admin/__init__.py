from . import change_user_property, edit_merch, edit_quiz, manage_admins, manage_money, merch_add_category, merch_add_item, reward_mailing, scan_qr, see_merch, see_merch_orders, see_transactions, start, write_message
from aiogram import Router


def get_router() -> Router:
    """
    Creates and configures a new Router instance by including various sub-routers.

    This function initializes a Router object from the aiogram library and includes multiple
    sub-routers that handle different parts of the application. Each sub-router is responsible
    for a specific functionality, such as managing users, editing merchandise, handling quizzes,
    and more.

    Returns:
        Router: A configured Router instance with all the included sub-routers.
    """
    router = Router()
    router.include_router(change_user_property.router)
    router.include_router(edit_merch.router)
    router.include_router(edit_quiz.router)
    router.include_router(manage_admins.router)
    router.include_router(manage_money.router)
    router.include_router(merch_add_category.router)
    router.include_router(merch_add_item.router)
    router.include_router(reward_mailing.router)
    router.include_router(see_merch.router)
    router.include_router(see_merch_orders.router)
    router.include_router(see_transactions.router)
    router.include_router(start.router)
    router.include_router(write_message.router)
    router.include_router(scan_qr.router)
    return router
