from fastapi import FastAPI, HTTPException
from schema import UserCreate, UserUpdate
import crud

app = FastAPI()


@app.get("/")
def root():
    return {"status": "FastAPI is running"}


@app.post("/users")
def create(user: UserCreate):
    return crud.create_user(user.model_dump())


@app.get("/users")
def read_all():
    return crud.get_all_users()


@app.get("/users/{user_id}")
def read_one(user_id: str):
    user = crud.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}")
def update(user_id: str, user: UserUpdate):
    updated = crud.update_user(
        user_id,
        {k: v for k, v in user.model_dump().items() if v is not None}
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@app.delete("/users/{user_id}")
def delete(user_id: str):
    success = crud.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}
