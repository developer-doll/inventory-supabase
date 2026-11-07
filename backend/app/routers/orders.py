from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from app.database import get_db
from app.models import Product, Order, OrderItem, InventoryMovement, User
from app.schemas import OrderCreate
from app.security import get_current_user, require_roles

router = APIRouter(prefix="/orders", tags=["Billing"])

@router.post("/")
def create_order(data: OrderCreate, db: Session = Depends(get_db),
                 user: User = Depends(require_roles("superadmin", "sales_person"))):
    try:
        # Combine duplicate product lines so stock is checked and deducted once per product.
        quantities = {}
        for line in data.items:
            quantities[line.product_id] = quantities.get(line.product_id, 0) + line.quantity

        products = {}
        subtotal = Decimal("0.00")
        for product_id in sorted(quantities):
            product = db.execute(
                select(Product).where(Product.id == product_id).with_for_update()
            ).scalar_one_or_none()
            if not product or not product.is_active:
                raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
            qty = quantities[product_id]
            if product.stock_quantity < qty:
                raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")
            products[product_id] = product
            subtotal += Decimal(str(product.price)) * qty

        tax = (subtotal * Decimal(str(data.tax_percent)) / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total = subtotal + tax
        invoice = "INV-" + uuid4().hex[:10].upper()
        order = Order(invoice_number=invoice, created_by=user.id, status="confirmed",
                      subtotal=subtotal, tax_amount=tax, total_amount=total,
                      payment_method=data.payment_method)
        db.add(order)
        db.flush()

        for product_id, qty in quantities.items():
            product = products[product_id]
            unit_price = Decimal(str(product.price))
            line_total = unit_price * qty
            product.stock_quantity -= qty
            db.add(OrderItem(order_id=order.id, product_id=product.id,
                             product_name=product.name, sku=product.sku,
                             quantity=qty, unit_price=unit_price, line_total=line_total))
            db.add(InventoryMovement(product_id=product.id, user_id=user.id,
                                     movement_type="sale", quantity=qty,
                                     note=f"Sale {invoice}", order_id=order.id))
        db.commit()
        db.refresh(order)
        return {"id": order.id, "invoice_number": order.invoice_number,
                "created_by": order.created_by, "status": order.status,
                "subtotal": float(order.subtotal), "tax_amount": float(order.tax_amount),
                "total_amount": float(order.total_amount), "payment_method": order.payment_method,
                "created_at": order.created_at.isoformat(),
                "items": [{"product_id": item.product_id, "product_name": item.product_name,
                           "sku": item.sku, "quantity": item.quantity,
                           "unit_price": float(item.unit_price), "line_total": float(item.line_total)}
                          for item in order.items]}
    except Exception:
        db.rollback()
        raise

@router.get("/")
def list_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Order).options(joinedload(Order.items)).order_by(Order.id.desc())
    if user.role.name == "sales_person":
        query = query.filter(Order.created_by == user.id)
    orders = query.limit(200).all()
    return [{"id": o.id, "invoice_number": o.invoice_number, "created_by": o.created_by,
             "status": o.status, "subtotal": float(o.subtotal), "tax_amount": float(o.tax_amount),
             "total_amount": float(o.total_amount), "payment_method": o.payment_method,
             "created_at": o.created_at.isoformat(),
             "items": [{"product_id": i.product_id, "product_name": i.product_name,
                        "sku": i.sku, "quantity": i.quantity, "unit_price": float(i.unit_price),
                        "line_total": float(i.line_total)} for i in o.items]} for o in orders]

@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    order = db.query(Order).options(joinedload(Order.items)).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if user.role.name == "sales_person" and order.created_by != user.id:
        raise HTTPException(status_code=403, detail="You can only view your own orders")
    return {"id": order.id, "invoice_number": order.invoice_number,
            "created_by": order.created_by, "status": order.status,
            "subtotal": float(order.subtotal), "tax_amount": float(order.tax_amount),
            "total_amount": float(order.total_amount), "payment_method": order.payment_method,
            "created_at": order.created_at.isoformat(),
            "items": [{"product_id": i.product_id, "product_name": i.product_name,
                       "sku": i.sku, "quantity": i.quantity, "unit_price": float(i.unit_price),
                       "line_total": float(i.line_total)} for i in order.items]}
