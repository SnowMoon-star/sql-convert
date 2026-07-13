DROP TABLE IF EXISTS "orders" CASCADE;
CREATE TABLE "orders" (
  "order_id" INTEGER PRIMARY KEY,
  "price" NUMERIC(10,2)
);
