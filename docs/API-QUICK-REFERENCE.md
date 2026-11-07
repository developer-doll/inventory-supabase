# API quick reference

All routes except `/health` and `/auth/login` require:
`Authorization: Bearer <access_token>`

- `POST /auth/login` — login
- `GET /auth/me` — current user
- `POST /users/` — superadmin creates a user
- `GET /users/` — superadmin lists users
- `GET /products/` — all authenticated roles
- `POST /products/` — superadmin/inventory manager
- `PATCH /products/{id}` — superadmin/inventory manager
- `DELETE /products/{id}` — soft-deactivate product
- `POST /inventory/add-stock` — superadmin/inventory manager
- `POST /inventory/remove-stock` — superadmin/inventory manager
- `GET /inventory/history` — superadmin/inventory manager
- `POST /orders/` — superadmin/sales person; deducts stock transactionally
- `GET /orders/` — sales people see only their own orders; managers/admin see all
- `GET /orders/{id}` — sales people can view only their own order
