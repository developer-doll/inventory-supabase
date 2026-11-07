from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product, InventoryMovement, User
from app.schemas import ProductCreate, ProductUpdate
from app.security import get_current_user, require_roles

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/")
def list_products(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.name).all()

@router.post("/")
def create_product(data: ProductCreate, db: Session = Depends(get_db),
                   user: User = Depends(require_roles("superadmin", "inventory_manager"))):
    if db.query(Product).filter(Product.sku == data.sku).first():
        raise HTTPException(status_code=409, detail="SKU already exists")
    product = Product(sku=data.sku, name=data.name, description=data.description,
                      price=data.price, stock_quantity=data.opening_stock)
    db.add(product)
    db.flush()
    if data.opening_stock:
        db.add(InventoryMovement(product_id=product.id, user_id=user.id,
                                 movement_type="stock_in", quantity=data.opening_stock,
                                 note="Opening stock"))
    db.commit()
    db.refresh(product)
    return product

@router.patch("/{product_id}")
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db),
                   user: User = Depends(require_roles("superadmin", "inventory_manager"))):
    product = db.get(Product, product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}")
def deactivate_product(product_id: int, db: Session = Depends(get_db),
                       user: User = Depends(require_roles("superadmin", "inventory_manager"))):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    db.commit()
    return {"message": "Product deactivated"}
