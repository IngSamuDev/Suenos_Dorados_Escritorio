from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from api.serialization import model_to_dict
from database import get_db


def register_crud_routes(router: APIRouter, path: str, model, primary_key: str):
    @router.get(path)
    def list_items(db: Session = Depends(get_db)):
        return [model_to_dict(item) for item in db.query(model).all()]

    @router.get(f"{path}/{{item_id}}")
    def get_item(item_id, db: Session = Depends(get_db)):
        return model_to_dict(db.get(model, item_id))

    @router.post(path)
    async def create_item(request: Request, db: Session = Depends(get_db)):
        data = await request.json()
        item = model(**data)
        db.add(item)
        db.commit()
        db.refresh(item)
        return model_to_dict(item)

    @router.put(f"{path}/{{item_id}}")
    async def replace_item(item_id, request: Request, db: Session = Depends(get_db)):
        data = await request.json()
        item = db.get(model, item_id)
        for field, value in data.items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return model_to_dict(item)

    @router.patch(f"{path}/{{item_id}}")
    async def update_item(item_id, request: Request, db: Session = Depends(get_db)):
        data = await request.json()
        item = db.get(model, item_id)
        for field, value in data.items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return model_to_dict(item)

    @router.delete(f"{path}/{{item_id}}")
    def delete_item(item_id, db: Session = Depends(get_db)):
        item = db.get(model, item_id)
        db.delete(item)
        db.commit()
        return model_to_dict(item)


