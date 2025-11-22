import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order


app = FastAPI(title="Vistro API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ObjectIdStr(str):
    pass


def serialize_doc(doc: dict):
    if not doc:
        return doc
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    # Convert any nested ObjectId
    for k, v in d.items():
        if isinstance(v, ObjectId):
            d[k] = str(v)
    return d


@app.get("/")
def read_root():
    return {"brand": "Vistro", "message": "Vistro backend is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the Vistro backend API!"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# ---------------------- Products ----------------------
@app.get("/api/products")
def list_products(category: Optional[str] = None, featured: Optional[bool] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    query = {}
    if category:
        query["category"] = category
    if featured is not None:
        query["featured"] = featured
    products = get_documents("product", query)
    return [serialize_doc(p) for p in products]


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        doc = db["product"].find_one({"_id": ObjectId(product_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product id")
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_doc(doc)


@app.post("/api/products", status_code=201)
def create_product(product: Product):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    new_id = create_document("product", product)
    doc = db["product"].find_one({"_id": ObjectId(new_id)})
    return serialize_doc(doc)


# ---------------------- Orders ----------------------
@app.post("/api/orders", status_code=201)
def create_order(order: Order):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # naive stock check: ensure each product exists
    for item in order.items:
        try:
            pid = ObjectId(item.product_id)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid product id: {item.product_id}")
        prod = db["product"].find_one({"_id": pid})
        if not prod:
            raise HTTPException(status_code=400, detail=f"Product not found: {item.product_id}")
    order_id = create_document("order", order)
    doc = db["order"].find_one({"_id": ObjectId(order_id)})
    return serialize_doc(doc)


# ---------------------- Seed sample data ----------------------
SAMPLE_PRODUCTS: List[Product] = [
    Product(
        title="Vistro Classic Tee",
        description="Soft cotton tee with minimalist Vistro logo.",
        price=28.0,
        category="T-Shirts",
        images=["https://images.unsplash.com/photo-1520975916090-3105956dac38?q=80&w=1200"],
        tags=["tee", "classic", "logo"],
        variants=[{"size": s, "color": "Black", "sku": f"VT-TEE-BLK-{s}", "stock": 50} for s in ["S", "M", "L", "XL"]],
        featured=True,
    ),
    Product(
        title="Vistro Cozy Hoodie",
        description="Premium fleece hoodie built for comfort.",
        price=64.0,
        category="Hoodies",
        images=["https://images.unsplash.com/photo-1516826957135-700dedea698c?q=80&w=1200"],
        tags=["hoodie", "fleece", "cozy"],
        variants=[{"size": s, "color": "Heather Gray", "sku": f"VT-HDY-GRY-{s}", "stock": 30} for s in ["S", "M", "L", "XL"]],
        featured=True,
    ),
    Product(
        title="Vistro Performance Joggers",
        description="Stretch joggers for all-day movement.",
        price=54.0,
        category="Bottoms",
        images=["https://images.unsplash.com/photo-1519741497674-611481863552?q=80&w=1200"],
        tags=["joggers", "athleisure"],
        variants=[{"size": s, "color": "Charcoal", "sku": f"VT-JGR-CHR-{s}", "stock": 40} for s in ["S", "M", "L", "XL"]],
        featured=False,
    ),
]


@app.post("/api/seed")
def seed_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    count = db["product"].count_documents({})
    if count > 0:
        return {"message": "Products already seeded", "count": count}
    inserted = []
    for p in SAMPLE_PRODUCTS:
        new_id = create_document("product", p)
        inserted.append(new_id)
    return {"message": "Seeded sample products", "inserted": inserted}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
