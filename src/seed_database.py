import os
import random
from datetime import timedelta
from faker import Faker
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()
fake = Faker()

DB_NAME = os.getenv("DB_NAME", "appdb")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "apppassword")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)
cur = conn.cursor()

NUM_USERS = int(os.getenv("SEED_USERS", "100"))
NUM_CUSTOMERS = int(os.getenv("SEED_CUSTOMERS", "500"))
NUM_PRODUCTS = int(os.getenv("SEED_PRODUCTS", "200"))
NUM_LOCATIONS = int(os.getenv("SEED_LOCATIONS", "5"))
NUM_ORDERS = int(os.getenv("SEED_ORDERS", "1000"))

roles = [("admin",), ("sales",), ("warehouse",), ("finance",)]
execute_values(cur, "INSERT INTO app.roles (name) VALUES %s ON CONFLICT DO NOTHING", roles)

users = [(fake.unique.email(), fake.name()) for _ in range(NUM_USERS)]
execute_values(cur, "INSERT INTO app.users (email, full_name) VALUES %s", users)

cur.execute("SELECT user_id FROM app.users")
user_ids = [row[0] for row in cur.fetchall()]
cur.execute("SELECT role_id FROM app.roles")
role_ids = [row[0] for row in cur.fetchall()]
assignments = [(random.choice(user_ids), random.choice(role_ids)) for _ in range(NUM_USERS * 2)]
execute_values(cur, "INSERT INTO app.user_roles (user_id, role_id) VALUES %s ON CONFLICT DO NOTHING", assignments)

customers = [(fake.company(), fake.unique.company_email(), fake.phone_number()) for _ in range(NUM_CUSTOMERS)]
execute_values(cur, "INSERT INTO app.customers (name, email, phone) VALUES %s", customers)

locations = [(f"LOC-{i+1}", fake.city()) for i in range(NUM_LOCATIONS)]
execute_values(cur, "INSERT INTO app.inventory_locations (code, name) VALUES %s", locations)

products = [(f"SKU-{i+1000}", fake.word().capitalize(), round(random.uniform(5, 500), 2)) for i in range(NUM_PRODUCTS)]
execute_values(cur, "INSERT INTO app.products (sku, name, price) VALUES %s", products)

cur.execute("SELECT product_id FROM app.products")
product_ids = [r[0] for r in cur.fetchall()]
cur.execute("SELECT location_id FROM app.inventory_locations")
location_ids = [r[0] for r in cur.fetchall()]
inventory = [(p, random.choice(location_ids), random.randint(10, 500)) for p in product_ids]
execute_values(cur, "INSERT INTO app.inventory (product_id, location_id, quantity) VALUES %s ON CONFLICT DO NOTHING", inventory)

cur.execute("SELECT customer_id FROM app.customers")
customer_ids = [r[0] for r in cur.fetchall()]
orders = []
now = fake.date_time_this_year()
statuses = ['draft','confirmed','shipped','delivered','cancelled','refunded']
for _ in range(NUM_ORDERS):
    ts = fake.date_time_between(start_date="-9M", end_date="now")
    orders.append((random.choice(customer_ids), random.choice(statuses), ts))
execute_values(cur, "INSERT INTO app.orders (customer_id, status, ordered_at) VALUES %s", orders)

cur.execute("SELECT order_id, ordered_at FROM app.orders")
orders_time = cur.fetchall()
order_items = []
for order_id, ordered_at in orders_time:
    for line_no in range(1, random.randint(2, 6)):
        prod = random.choice(product_ids)
        qty = random.randint(1, 10)
        price = round(random.uniform(5, 500), 2)
        order_items.append((order_id, line_no, prod, qty, price))
execute_values(cur, "INSERT INTO app.order_items (order_id, line_no, product_id, quantity, unit_price) VALUES %s", order_items)

cur.execute("SELECT order_id, ordered_at, status FROM app.orders WHERE status IN ('confirmed','shipped','delivered','refunded')")
pay_orders = cur.fetchall()
payments = []
for order_id, ordered_at, status in pay_orders:
    n = random.randint(1, 2)
    for _ in range(n):
        paid_at = ordered_at + timedelta(days=random.randint(0, 20))
        payments.append((order_id, random.choice(['card','transfer','cash','paypal']), round(random.uniform(20, 800), 2), paid_at))
execute_values(cur, "INSERT INTO app.payments (order_id, method, amount, paid_at) VALUES %s", payments)

conn.commit()
cur.close()
conn.close()
print("Seed completado")

