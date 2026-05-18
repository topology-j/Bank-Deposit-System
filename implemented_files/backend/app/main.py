from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.registry import TABLES
from app import services
from app.utils import clean_payload, model_to_dict


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "tables": len(TABLES)}


@app.get("/api/meta/tables")
def table_meta() -> dict:
    return {"tables": list(TABLES.keys())}


@app.get("/api/{table_name}")
def list_rows(table_name: str, limit: int = 100, offset: int = 0, db: Session = Depends(get_db)) -> list[dict]:
    model, pk = get_table(table_name)
    rows = db.scalars(select(model).order_by(getattr(model, pk)).limit(limit).offset(offset)).all()
    return [model_to_dict(row) for row in rows]


@app.post("/api/{table_name}", status_code=201)
def create_row(table_name: str, payload: dict, db: Session = Depends(get_db)) -> dict:
    model, _pk = get_table(table_name)
    row = model(**clean_payload(model, payload))
    db.add(row)
    db.commit()
    db.refresh(row)
    return model_to_dict(row)


@app.get("/api/{table_name}/{row_id}")
def get_row(table_name: str, row_id: int, db: Session = Depends(get_db)) -> dict:
    model, _pk = get_table(table_name)
    row = db.get(model, row_id)
    if not row:
        raise HTTPException(status_code=404, detail="row not found")
    return model_to_dict(row)


@app.patch("/api/{table_name}/{row_id}")
def update_row(table_name: str, row_id: int, payload: dict, db: Session = Depends(get_db)) -> dict:
    model, _pk = get_table(table_name)
    row = db.get(model, row_id)
    if not row:
        raise HTTPException(status_code=404, detail="row not found")
    for key, value in clean_payload(model, payload, partial=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return model_to_dict(row)


@app.delete("/api/{table_name}/{row_id}", status_code=204)
def delete_row(table_name: str, row_id: int, db: Session = Depends(get_db)) -> None:
    model, _pk = get_table(table_name)
    row = db.get(model, row_id)
    if not row:
        raise HTTPException(status_code=404, detail="row not found")
    db.delete(row)
    db.commit()


@app.post("/contracts", status_code=201)
def create_contract(payload: dict, db: Session = Depends(get_db)) -> dict:
    return model_to_dict(services.create_contract_with_account(db, payload))


@app.post("/transactions/deposit", status_code=201)
def deposit(payload: dict, db: Session = Depends(get_db)) -> dict:
    return model_to_dict(services.deposit(db, payload))


@app.post("/transactions/withdraw", status_code=201)
def withdraw(payload: dict, db: Session = Depends(get_db)) -> dict:
    return model_to_dict(services.withdraw(db, payload))


@app.post("/transactions/transfer", status_code=201)
def transfer(payload: dict, db: Session = Depends(get_db)) -> dict:
    return model_to_dict(services.transfer(db, payload))


@app.post("/transactions/payment", status_code=201)
def payment(payload: dict, db: Session = Depends(get_db)) -> dict:
    return model_to_dict(services.payment(db, payload))


@app.post("/transactions/savings-payment", status_code=201)
def savings_payment(payload: dict, db: Session = Depends(get_db)) -> dict:
    return model_to_dict(services.savings_payment(db, payload))


@app.post("/transactions/{transaction_id}/reversal", status_code=201)
def reversal(transaction_id: int, payload: dict, db: Session = Depends(get_db)) -> dict:
    return model_to_dict(services.reverse_transaction(db, transaction_id, payload))


@app.post("/interests/pay", status_code=201)
def pay_interest(payload: dict, db: Session = Depends(get_db)) -> dict:
    return model_to_dict(services.pay_interest(db, payload))


@app.patch("/products/{product_id}/status")
def change_product_status(product_id: int, payload: dict, db: Session = Depends(get_db)) -> dict:
    from app.models import Product

    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="product not found")
    product.product_status = payload["product_status"]
    db.commit()
    db.refresh(product)
    return model_to_dict(product)


def get_table(table_name: str):
    if table_name not in TABLES:
        raise HTTPException(status_code=404, detail=f"unknown table: {table_name}")
    return TABLES[table_name]
