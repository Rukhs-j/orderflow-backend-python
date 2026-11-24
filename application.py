from fastapi import Depends
from core import User, current_user
from factory import make_application
from services import SCHEMA, Service, OrderInput, seed


def register(app, db, kb, service):
    @app.get("/api/products")
    def products(user: User = Depends(current_user)):
        return db.rows("SELECT * FROM products ORDER BY ID")

    @app.get("/api/orders")
    def orders(user: User = Depends(current_user)):
        if user.staff:
            return db.rows("SELECT * FROM orders ORDER BY CREATED_AT DESC")
        return db.rows("SELECT * FROM orders WHERE OWNER=? ORDER BY CREATED_AT DESC", (user.username,))

    @app.post("/api/orders")
    def create(body: OrderInput, user: User = Depends(current_user)):
        return service.create(user.username, body)

    @app.post("/api/orders/{order_id}/cancel")
    def cancel(order_id: str, user: User = Depends(current_user)):
        return service.cancel(user, order_id)


def create_app(db_path=None, ai_mode=None, enable_worker=True, ai_client=None):
    return make_application("OrderFlow Python", SCHEMA, register, seed, Service,
                            db_path, ai_mode, enable_worker, ai_client)


app = create_app()
