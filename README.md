# Inventory & Billing Management System

A starter MVP using FastAPI, React (Vite), Electron and Supabase PostgreSQL.

## Roles
- `superadmin`: create users, manage products/stock, view all orders.
- `inventory_manager`: manage products and stock, view all orders.
- `sales_person`: view products, create orders, view own orders.

## Architecture
Electron hosts the React UI. React calls FastAPI. FastAPI owns business rules and connects to Supabase PostgreSQL using SQLAlchemy. Supabase Storage is optional and can be added for product images/invoice PDFs.

## 1. Create GitHub repository
Create an empty repository named `inventory-billing-management-system`.
Do not initialize it with a README if you plan to push this folder as-is.

## 2. Configure Supabase
1. Create a project at https://supabase.com/dashboard.
2. Open **Connect** and copy the PostgreSQL connection string.
3. Prefer the Session Pooler connection if your deployment host requires IPv4 compatibility.
4. Convert the URL to SQLAlchemy format:
   - `postgresql://...` -> `postgresql+psycopg://...`
5. Copy `backend/.env.example` to `backend/.env` and set `DATABASE_URL`, `SECRET_KEY`, and `CORS_ORIGINS`.

The application creates its tables at startup for this starter project. For production, use Alembic migrations instead of `create_all`.

## 3. Run backend locally
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows CMD; on PowerShell use Copy-Item
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

On first run, a default superadmin is created:
- Username: `admin`
- Password: `ChangeMe123!`

Change this immediately using environment variables before deployment:
`BOOTSTRAP_ADMIN_USERNAME` and `BOOTSTRAP_ADMIN_PASSWORD`.

## 4. Run React web UI
In a second terminal:
```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```
Open http://localhost:5173.

Set `VITE_API_URL=http://127.0.0.1:8000` in `frontend/.env`.

## 5. Run Electron desktop app
The Electron app loads the Vite dev server during development:
```bash
cd frontend
npm install
npm run electron:dev
```
Build a desktop installer:
```bash
npm run electron:build
```
The packaged app loads the deployed frontend URL configured in `electron/main.cjs` (`APP_URL`). Update it before building for production.

## 6. Deploy
### Supabase
- Supabase hosts PostgreSQL and optionally Storage; it does not host this FastAPI server or Electron desktop app.
- Configure the backend `DATABASE_URL` with your Supabase connection string.
- Never put database passwords, JWT secrets, or Supabase service-role keys in frontend environment variables.

### FastAPI (Render example)
1. Push this repository to GitHub.
2. In Render, create a **Web Service** from the repository.
3. Set Root Directory to `backend`.
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables:
   - `DATABASE_URL`
   - `SECRET_KEY` (long random secret)
   - `CORS_ORIGINS` (your deployed frontend origin, comma-separated)
   - `BOOTSTRAP_ADMIN_USERNAME`
   - `BOOTSTRAP_ADMIN_PASSWORD`
7. Deploy and test `/health` and `/docs`.

For production deployments, run Alembic migrations as a release/pre-deploy command and disable automatic bootstrap admin creation after the initial account has been created.

### React (Vercel example)
1. Import the GitHub repository into Vercel.
2. Set Root Directory to `frontend`.
3. Build command: `npm run build`.
4. Output directory: `dist`.
5. Add `VITE_API_URL=https://YOUR-API-HOST`.
6. Deploy.

### Electron
Electron is packaged separately for each target operating system. Set `APP_URL` in `electron/main.cjs` to your deployed frontend URL, then run `npm run electron:build` from `frontend`. Distribute the generated installer from `frontend/release`.

## 7. Push to GitHub
From the project root:
```bash
git init
git add .
git commit -m "Initial inventory and billing application"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/inventory-billing-management-system.git
git push -u origin main
```

## Important production notes
- This is an MVP starter, not a fully audited production POS.
- Change the bootstrap credentials and JWT secret.
- Use HTTPS for deployed API/frontend.
- Configure Supabase backups and monitor usage.
- Add Alembic migrations, automated tests, audit logging, invoice numbering policy, tax rules and payment reconciliation before real commercial use.
- Stock deduction uses a database transaction and `SELECT FOR UPDATE` on PostgreSQL to reduce overselling. SQLite is supported for local smoke testing but does not provide the same row-locking behavior.
- Product deletion is soft deletion (`is_active=false`) so historical order lines remain valid.
