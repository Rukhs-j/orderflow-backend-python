from typing import Literal
from pydantic import Field
from core import Database, InputModel, Problem, User, new_id, now, text

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
 ID INTEGER PRIMARY KEY, NAME TEXT NOT NULL, PRICE_PAISE INTEGER NOT NULL,
 STOCK INTEGER NOT NULL CHECK(STOCK>=0)
);
CREATE TABLE IF NOT EXISTS orders (
 ID TEXT PRIMARY KEY, OWNER TEXT NOT NULL, PRODUCT_ID INTEGER REFERENCES products(ID),
 QUANTITY INTEGER CHECK(QUANTITY>0), TOTAL_PAISE INTEGER NOT NULL,
 STATUS TEXT NOT NULL, REQUEST_KEY TEXT NOT NULL, FINGERPRINT TEXT NOT NULL,
 CREATED_AT TEXT NOT NULL, UNIQUE(OWNER,REQUEST_KEY)
);
"""


class OrderInput(InputModel):
    productId: int = Field(ge=1, strict=True)
    quantity: int = Field(ge=1, le=1000, strict=True)
    requestKey: str = Field(min_length=1, max_length=100)
    payment: Literal["success", "failure", "timeout"]


def seed(db, kb):
    with db.transaction() as connection:
        if connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            connection.executemany("INSERT INTO products VALUES(?,?,?,?)", [
                (1, "Mechanical Keyboard", 450000, 5),
                (2, "USB-C Hub", 180000, 10),
                (3, "Last-item Monitor", 1200000, 1),
            ])


class Service:
    def __init__(self, db: Database):
        self.db = db

    def create(self, owner: str, request: OrderInput):
        key = text(request.requestKey, 100, "requestKey")
        fingerprint = f"{request.productId}:{request.quantity}:{request.payment}"
        with self.db.transaction() as connection:
            previous = connection.execute("SELECT * FROM orders WHERE OWNER=? AND REQUEST_KEY=?", (owner, key)).fetchone()
            if previous:
                if previous["FINGERPRINT"] != fingerprint:
                    raise Problem(409, "Idempotency key used with different inputs")
                return dict(previous)
            product = connection.execute("SELECT * FROM products WHERE ID=?", (request.productId,)).fetchone()
            if not product:
                raise Problem(404, "Product not found")
            changed = connection.execute(
                "UPDATE products SET STOCK=STOCK-? WHERE ID=? AND STOCK>=?",
                (request.quantity, request.productId, request.quantity)).rowcount
            if changed != 1:
                raise Problem(409, "Insufficient stock")
            if request.payment != "success":
                raise Problem(422, f"Simulated payment {request.payment}; stock reservation rolled back")
            order_id = new_id()
            connection.execute("INSERT INTO orders VALUES(?,?,?,?,?,?,?,?,?)", (
                order_id, owner, request.productId, request.quantity,
                product["PRICE_PAISE"]*request.quantity, "PAID", key, fingerprint, now()))
            return dict(connection.execute("SELECT * FROM orders WHERE ID=?", (order_id,)).fetchone())

    def cancel(self, user: User, order_id: str):
        with self.db.transaction() as connection:
            order = connection.execute("SELECT * FROM orders WHERE ID=?", (order_id,)).fetchone()
            if not order:
                raise Problem(404, "Order not found")
            user.require_owner(order["OWNER"])
            changed = connection.execute("UPDATE orders SET STATUS='CANCELLED' WHERE ID=? AND STATUS='PAID'", (order_id,)).rowcount
            if changed:
                connection.execute("UPDATE products SET STOCK=STOCK+? WHERE ID=?", (order["QUANTITY"], order["PRODUCT_ID"]))
            return dict(connection.execute("SELECT * FROM orders WHERE ID=?", (order_id,)).fetchone())
