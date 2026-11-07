from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models import Product, InventoryMovement, User
from app.schemas import StockChange
from app.security import require_roles

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.post("/add-stock")
def add_stock(data: StockChange, db: Session = Depends(get_db),
              user: User = Depends(require_roles("superadmin", "inventory_manager"))):
    product = db.execute(select(Product).where(Product.id == data.product_id).with_for_update()).scalar_one_or_none()
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Active product not found")
    product.stock_quantity += data.quantity
    db.add(InventoryMovement(product_id=product.id, user_id=user.id, movement_type="stock_in",
                             quantity=data.quantity, note=data.note))
    db.commit()
    return {"message": "Stock added", "product_id": product.id, "stock_quantity": product.stock_quantity}

@router.post("/remove-stock")
def remove_stock(data: StockChange, db: Session = Depends(get_db),
                 user: User = Depends(require_roles("superadmin", "inventory_manager"))):
    product = db.execute(select(Product).where(Product.id == data.product_id).with_for_update()).scalar_one_or_none()
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Active product not found")
    if product.stock_quantity < data.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    product.stock_quantity -= data.quantity
    db.add(InventoryMovement(product_id=product.id, user_id=user.id, movement_type="stock_out",
                             quantity=data.quantity, note=data.note))
    db.commit()
    return {"message": "Stock removed", "product_id": product.id, "stock_quantity": product.stock_quantity}

@router.get("/history")
def inventory_history(db: Session = Depends(get_db),
                      user: User = Depends(require_roles("superadmin", "inventory_manager"))):
    rows = db.query(InventoryMovement).order_by(InventoryMovement.id.desc()).limit(200).all()
    return [{"id": r.id, "product_id": r.product_id, "user_id": r.user_id,
             "movement_type": r.movement_type, "quantity": r.quantity,
             "note": r.note, "order_id": r.order_id, "created_at": r.created_at}
            for r in rows]
