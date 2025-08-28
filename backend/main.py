import json
from typing import Annotated, Optional
from datetime import date
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from app import models, schemas, crud, security
from app.database import SessionLocal, engine
from app.ocr_utils import extract_text_from_image
from app.llm_utils import parse_receipt_with_gemini

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

def get_current_admin_user(current_user: Annotated[models.User, Depends(get_current_user)]):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

@app.post("/token", tags=["Authentication"])
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = security.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "is_admin": user.is_admin, "user_email": user.email}

@app.post("/users/", response_model=schemas.User, tags=["Authentication"])
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Personal Finance Assistant API"}

@app.get("/api/receipts/", response_model=list[schemas.Receipt], tags=["Receipts"])
def read_user_receipts(current_user: Annotated[models.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    return crud.get_receipts_by_user(db=db, user_id=current_user.id, limit=20)

@app.get("/api/receipts/all", response_model=list[schemas.Receipt], tags=["Receipts"])
def read_all_user_receipts(current_user: Annotated[models.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    return crud.get_all_receipts_by_user(db=db, user_id=current_user.id)

@app.post("/api/receipts/", response_model=schemas.Receipt, tags=["Receipts"])
async def upload_and_process_receipt(current_user: Annotated[models.User, Depends(get_current_user)], db: Session = Depends(get_db), file: UploadFile = File(...)):
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())
    ocr_text = extract_text_from_image(temp_file_path)
    if not ocr_text.strip():
        raise HTTPException(status_code=400, detail="OCR failed to extract any text from the image.")
    parsed_data = parse_receipt_with_gemini(ocr_text)
    if not parsed_data:
        raise HTTPException(status_code=500, detail="Gemini failed to parse the receipt text.")
    try:
        receipt_to_create = schemas.ReceiptCreate(**parsed_data)
        return crud.create_receipt(db=db, receipt=receipt_to_create, user_id=current_user.id, user_email=current_user.email)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error for Gemini's output: {e}")

@app.delete("/api/receipts/{receipt_id}", tags=["Receipts"])
def delete_user_receipt(receipt_id: int, current_user: Annotated[models.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    db_receipt = crud.get_receipt_by_id(db, receipt_id=receipt_id)
    if not db_receipt or db_receipt.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Receipt not found")
    crud.delete_receipt(db=db, receipt_id=receipt_id)
    return {"detail": "Receipt deleted successfully"}

@app.get("/api/dashboard/kpis", response_model=schemas.KPIData, tags=["Dashboard"])
def get_kpi_data_for_user(current_user: Annotated[models.User, Depends(get_current_user)], db: Session = Depends(get_db), start_date: Optional[date] = None, end_date: Optional[date] = None):
    return crud.get_kpi_data(db=db, user_id=current_user.id, start_date=start_date, end_date=end_date)

@app.get("/api/dashboard/time-series", response_model=list[schemas.TimeSeriesData], tags=["Dashboard"])
def get_time_series_data_for_user(current_user: Annotated[models.User, Depends(get_current_user)], db: Session = Depends(get_db), start_date: Optional[date] = None, end_date: Optional[date] = None):
    return crud.get_spending_over_time(db=db, user_id=current_user.id, start_date=start_date, end_date=end_date)

@app.get("/api/dashboard/chart-data", response_model=list[schemas.ChartData], tags=["Dashboard"])
def get_chart_data(current_user: Annotated[models.User, Depends(get_current_user)], db: Session = Depends(get_db), start_date: Optional[date] = None, end_date: Optional[date] = None):
    return crud.get_spending_by_category(db=db, user_id=current_user.id, start_date=start_date, end_date=end_date)

@app.get("/api/dashboard/top-items", response_model=list[schemas.ChartData], tags=["Dashboard"])
def get_top_items_data(current_user: Annotated[models.User, Depends(get_current_user)], db: Session = Depends(get_db), start_date: Optional[date] = None, end_date: Optional[date] = None):
    return crud.get_top_items(db=db, user_id=current_user.id, start_date=start_date, end_date=end_date)

@app.get("/api/dashboard/top-items", response_model=list[schemas.ChartData], tags=["Dashboard"])
def get_top_items_data(
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    return crud.get_top_items(db=db, user_id=current_user.id, start_date=start_date, end_date=end_date)

@app.get("/api/admin/users", response_model=list[schemas.User], tags=["Admin"])
def get_all_users_as_admin(admin_user: Annotated[models.User, Depends(get_current_admin_user)], db: Session = Depends(get_db)):
    return crud.get_all_users(db=db)

@app.get("/api/admin/receipts", response_model=list[schemas.Receipt], tags=["Admin"])
def get_all_receipts_as_admin(admin_user: Annotated[models.User, Depends(get_current_admin_user)], db: Session = Depends(get_db)):
    return crud.get_all_receipts(db=db)

@app.delete("/api/admin/users/{user_id}", tags=["Admin"])
def delete_user_as_admin(user_id: int, admin_user: Annotated[models.User, Depends(get_current_admin_user)], db: Session = Depends(get_db)):
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Admin cannot delete their own account.")
    if not crud.delete_user(db=db, user_id=user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User and all their data deleted successfully"}