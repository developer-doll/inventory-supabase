import { useEffect, useMemo, useState } from "react";
import { LogOut, Package, Users, ShoppingCart, Boxes, RefreshCw } from "lucide-react";
import api from "./api";

const money = (value) => `₹${Number(value || 0).toFixed(2)}`;

function Login({ onLogin }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("ChangeMe123!");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault(); setError(""); setBusy(true);
    try {
      const { data } = await api.post("/auth/login", { username, password });
      localStorage.setItem("access_token", data.access_token);
      onLogin(data.user);
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    } finally { setBusy(false); }
  }

  return <main className="login-wrap"><form className="login-card" onSubmit={submit}>
    <div className="brand-mark">IB</div>
    <h1>Inventory & Billing</h1><p className="muted">Sign in to your workspace</p>
    <label>Username</label><input value={username} onChange={e => setUsername(e.target.value)} required />
    <label>Password</label><input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
    {error && <p className="error">{error}</p>}
    <button className="primary full" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
    <small className="muted">First login: admin / ChangeMe123! — change before deployment.</small>
  </form></main>;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [tab, setTab] = useState("billing");
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [users, setUsers] = useState([]);
  const [cart, setCart] = useState([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [search, setSearch] = useState("");
  const [tax, setTax] = useState(0);
  const [payment, setPayment] = useState("cash");

  const role = user?.role;
  const canManage = ["superadmin", "inventory_manager"].includes(role);
  const isAdmin = role === "superadmin";
  const subtotal = useMemo(() => cart.reduce((s, item) => s + item.price * item.quantity, 0), [cart]);
  const total = subtotal + subtotal * Number(tax || 0) / 100;

  useEffect(() => {
    if (localStorage.getItem("access_token")) {
      api.get("/auth/me").then(r => setUser(r.data)).catch(() => localStorage.removeItem("access_token"));
    }
  }, []);

  async function refresh() {
    if (!user) return;
    setBusy(true);
    try {
      const [p, o] = await Promise.all([api.get("/products/"), api.get("/orders/")]);
      setProducts(p.data); setOrders(o.data);
      if (isAdmin) { const u = await api.get("/users/"); setUsers(u.data); }
    } catch (e) { setMessage(e.response?.data?.detail || "Could not load data"); }
    finally { setBusy(false); }
  }

  useEffect(() => { refresh(); }, [user]);

  function logout() {
    localStorage.removeItem("access_token"); setUser(null); setProducts([]); setOrders([]); setCart([]);
  }

  function addToCart(product) {
    setCart(old => {
      const found = old.find(x => x.id === product.id);
      if (found) return old.map(x => x.id === product.id ? { ...x, quantity: Math.min(x.quantity + 1, product.stock_quantity) } : x);
      return [...old, { id: product.id, name: product.name, sku: product.sku, price: Number(product.price), stock: product.stock_quantity, quantity: 1 }];
    });
  }

  function changeQty(id, quantity) {
    setCart(old => old.map(x => x.id === id ? { ...x, quantity: Math.max(1, Math.min(Number(quantity) || 1, x.stock)) } : x));
  }

  async function checkout() {
    if (!cart.length) return;
    setMessage("");
    try {
      const { data } = await api.post("/orders/", {
        items: cart.map(x => ({ product_id: x.id, quantity: x.quantity })),
        tax_percent: Number(tax), payment_method: payment
      });
      setMessage(`Order confirmed: ${data.invoice_number} — ${money(data.total_amount)}`);
      setCart([]); await refresh(); setTab("orders");
    } catch (e) { setMessage(e.response?.data?.detail || "Order failed"); await refresh(); }
  }

  if (!user) return <Login onLogin={setUser} />;

  const nav = [
    ...(canManage ? [{ id: "inventory", label: "Inventory", icon: Boxes }] : []),
    ...(isAdmin ? [{ id: "users", label: "Users", icon: Users }] : []),
    ...(role !== "inventory_manager" ? [{ id: "billing", label: "Billing", icon: ShoppingCart }] : []),
    { id: "orders", label: "Orders", icon: Package }
  ];

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="side-brand"><span className="brand-mark small">IB</span><b>Inventory Billing</b></div>
      <div className="profile"><div className="avatar">{user.full_name?.[0]?.toUpperCase()}</div><div><b>{user.full_name}</b><small>{role?.replaceAll("_", " ")}</small></div></div>
      <nav>{nav.map(item => <button key={item.id} className={tab === item.id ? "nav-item active" : "nav-item"} onClick={() => setTab(item.id)}><item.icon size={18}/>{item.label}</button>)}</nav>
      <button className="nav-item logout" onClick={logout}><LogOut size={18}/>Sign out</button>
    </aside>

    <main className="content">
      <header className="topbar"><div><h1>{nav.find(x => x.id === tab)?.label || "Dashboard"}</h1><p className="muted">Manage products, stock and sales</p></div><button className="secondary" onClick={refresh}><RefreshCw size={16}/> Refresh</button></header>
      {message && <div className="notice">{message}<button onClick={() => setMessage("")}>×</button></div>}

      {tab === "billing" && role !== "inventory_manager" && <section className="grid-layout">
        <div className="panel">
          <div className="panel-head"><h2>Products</h2><input className="search" placeholder="Search products..." value={search} onChange={e => setSearch(e.target.value)} /></div>
          <div className="product-grid">{products.filter(p => `${p.name} ${p.sku}`.toLowerCase().includes(search.toLowerCase())).map(p =>
            <button className="product-card" key={p.id} disabled={!p.stock_quantity} onClick={() => addToCart(p)}>
              <span className="product-icon"><Package/></span><b>{p.name}</b><small>{p.sku}</small><strong>{money(p.price)}</strong><small>{p.stock_quantity} in stock</small>
            </button>)}</div>
          {!products.length && <p className="muted empty">No products available. Ask an inventory manager to add products.</p>}
        </div>
        <div className="panel cart-panel">
          <h2>Current bill</h2>
          {cart.map(item => <div className="cart-line" key={item.id}><div><b>{item.name}</b><small>{money(item.price)} each</small></div><input type="number" min="1" max={item.stock} value={item.quantity} onChange={e => changeQty(item.id, e.target.value)}/><b>{money(item.price * item.quantity)}</b><button className="remove" onClick={() => setCart(c => c.filter(x => x.id !== item.id))}>×</button></div>)}
          {!cart.length && <p className="muted empty">Select products to start a bill.</p>}
          <div className="bill-options"><label>Tax (%)</label><input type="number" min="0" max="100" value={tax} onChange={e => setTax(e.target.value)}/><label>Payment method</label><select value={payment} onChange={e => setPayment(e.target.value)}><option value="cash">Cash</option><option value="upi">UPI</option><option value="card">Card</option><option value="credit">Credit</option></select></div>
          <div className="totals"><div><span>Subtotal</span><b>{money(subtotal)}</b></div><div><span>Tax</span><b>{money(total - subtotal)}</b></div><div className="grand"><span>Total</span><b>{money(total)}</b></div></div>
          <button className="primary full" disabled={!cart.length} onClick={checkout}>Confirm order & deduct stock</button>
        </div>
      </section>}

      {tab === "inventory" && canManage && <Inventory products={products} onRefresh={refresh} setMessage={setMessage}/>}
      {tab === "users" && isAdmin && <UsersPage users={users} onRefresh={refresh} setMessage={setMessage}/>}
      {tab === "orders" && <Orders orders={orders}/>}
    </main>
  </div>;
}

function Inventory({ products, onRefresh, setMessage }) {
  const [form, setForm] = useState({ sku: "", name: "", description: "", price: "", opening_stock: 0 });
  const [stock, setStock] = useState({ product_id: "", quantity: 1, note: "" });
  const [mode, setMode] = useState("add");
  async function create(e) {
    e.preventDefault();
    try { await api.post("/products/", { ...form, price: Number(form.price), opening_stock: Number(form.opening_stock) }); setForm({sku:"",name:"",description:"",price:"",opening_stock:0}); setMessage("Product created"); onRefresh(); }
    catch (e) { setMessage(e.response?.data?.detail || "Could not create product"); }
  }
  async function adjust(e) {
    e.preventDefault();
    try { await api.post(`/inventory/${mode === "add" ? "add-stock" : "remove-stock"}`, { ...stock, product_id: Number(stock.product_id), quantity: Number(stock.quantity) }); setMessage("Stock updated"); onRefresh(); }
    catch (e) { setMessage(e.response?.data?.detail || "Stock update failed"); }
  }
  async function deactivate(id) {
    if (!confirm("Deactivate this product? Existing bills will remain unchanged.")) return;
    try { await api.delete(`/products/${id}`); setMessage("Product deactivated"); onRefresh(); }
    catch (e) { setMessage(e.response?.data?.detail || "Could not deactivate product"); }
  }
  return <div className="stack">
    <div className="two-panels">
      <form className="panel form-panel" onSubmit={create}><h2>Add product</h2>
        <label>SKU</label><input required value={form.sku} onChange={e=>setForm({...form,sku:e.target.value})}/>
        <label>Product name</label><input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/>
        <label>Description</label><input value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/>
        <label>Unit price (₹)</label><input required type="number" min="0" step="0.01" value={form.price} onChange={e=>setForm({...form,price:e.target.value})}/>
        <label>Opening stock</label><input type="number" min="0" value={form.opening_stock} onChange={e=>setForm({...form,opening_stock:e.target.value})}/>
        <button className="primary">Save product</button>
      </form>
      <form className="panel form-panel" onSubmit={adjust}><h2>Stock adjustment</h2>
        <label>Product</label><select required value={stock.product_id} onChange={e=>setStock({...stock,product_id:e.target.value})}><option value="">Select product</option>{products.map(p=><option key={p.id} value={p.id}>{p.name} ({p.stock_quantity} available)</option>)}</select>
        <label>Action</label><select value={mode} onChange={e=>setMode(e.target.value)}><option value="add">Add stock</option><option value="remove">Remove stock</option></select>
        <label>Quantity</label><input type="number" min="1" required value={stock.quantity} onChange={e=>setStock({...stock,quantity:e.target.value})}/>
        <label>Reason / note</label><input value={stock.note} onChange={e=>setStock({...stock,note:e.target.value})}/>
        <button className="primary">Update stock</button>
      </form>
    </div>
    <div className="panel"><h2>Product inventory</h2><div className="table-wrap"><table><thead><tr><th>SKU</th><th>Product</th><th>Price</th><th>Stock</th><th>Action</th></tr></thead><tbody>{products.map(p=><tr key={p.id}><td>{p.sku}</td><td>{p.name}</td><td>{money(p.price)}</td><td>{p.stock_quantity}</td><td><button className="danger small-btn" onClick={()=>deactivate(p.id)}>Deactivate</button></td></tr>)}</tbody></table></div></div>
  </div>;
}

function UsersPage({ users, onRefresh, setMessage }) {
  const [form, setForm] = useState({ username: "", full_name: "", password: "", role: "sales_person" });
  async function submit(e) {
    e.preventDefault();
    try { await api.post("/users/", form); setMessage("User created"); setForm({username:"",full_name:"",password:"",role:"sales_person"}); onRefresh(); }
    catch (e) { setMessage(e.response?.data?.detail || "Could not create user"); }
  }
  return <div className="two-panels">
    <form className="panel form-panel" onSubmit={submit}><h2>Create user</h2>
      <label>Username</label><input required minLength="3" value={form.username} onChange={e=>setForm({...form,username:e.target.value})}/>
      <label>Full name</label><input required value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})}/>
      <label>Temporary password</label><input required minLength="8" type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/>
      <label>Role</label><select value={form.role} onChange={e=>setForm({...form,role:e.target.value})}><option value="inventory_manager">Inventory Manager</option><option value="sales_person">Sales Person</option></select>
      <button className="primary">Create account</button>
    </form>
    <div className="panel"><h2>Users</h2><div className="table-wrap"><table><thead><tr><th>Name</th><th>Username</th><th>Role</th></tr></thead><tbody>{users.map(u=><tr key={u.id}><td>{u.full_name}</td><td>{u.username}</td><td>{u.role.replaceAll("_"," ")}</td></tr>)}</tbody></table></div></div>
  </div>;
}

function Orders({ orders }) {
  return <div className="panel"><h2>Order history</h2><div className="table-wrap"><table><thead><tr><th>Invoice</th><th>Date</th><th>Payment</th><th>Items</th><th>Total</th><th>Status</th></tr></thead><tbody>{orders.map(o=><tr key={o.id}><td><b>{o.invoice_number}</b></td><td>{new Date(o.created_at).toLocaleString()}</td><td>{o.payment_method}</td><td>{o.items.reduce((s,i)=>s+i.quantity,0)}</td><td>{money(o.total_amount)}</td><td><span className="status">{o.status}</span></td></tr>)}</tbody></table></div>{!orders.length&&<p className="muted empty">No orders yet.</p>}</div>;
}
