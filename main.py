from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
import models, database, shutil, os

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./uploads"
if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- Schemas ---
class RegisterRequest(BaseModel):
    login_id: str; password: str; name: str; university: str; major: str; age: int; height: int

class LoginRequest(BaseModel):
    login_id: str; password: str

class ProfileUpdate(BaseModel):
    user_id: int; nickname: str; university: str; major: str; age: int; height: int
    mbti: str; ideal_type: str; pref_mbti: str; pref_age: str; must_have: str; description: str; meeting_type: str

# --- APIs ---
@app.post("/users/register")
def register(request: RegisterRequest, db: Session = Depends(database.get_db)):
    if db.query(models.User).filter(models.User.login_id == request.login_id).first():
        raise HTTPException(400, "아이디 중복")
    new_user = models.User(login_id=request.login_id, password=request.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.add(models.Profile(
        user_id=new_user.id, nickname=request.name, university=request.university, 
        major=request.major, age=request.age, height=request.height
    ))
    db.commit()
    return {"user_id": new_user.id}

@app.post("/users/login")
def login(request: LoginRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.login_id == request.login_id, models.User.password == request.password).first()
    if not user: raise HTTPException(401, "로그인 실패")
    return {"user_id": user.id, "is_verified": user.is_verified, "nickname": user.profile.nickname, "univ": user.profile.university, "major": user.profile.major, "age": user.profile.age}

@app.put("/profiles/")
def update_profile(request: ProfileUpdate, db: Session = Depends(database.get_db)):
    p = db.query(models.Profile).filter(models.Profile.user_id == request.user_id).first()
    for key, value in request.dict().items():
        setattr(p, key, value)
    db.commit()
    return {"message": "저장 완료"}

@app.post("/upload/student-card/{user_id}")
async def upload_card(user_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    path = f"{UPLOAD_DIR}/{user_id}_{file.filename}"
    with open(path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.student_card_url = f"http://127.0.0.1:8000/uploads/{user_id}_{file.filename}"
    db.commit()
    return {"url": user.student_card_url}

@app.get("/admin/users/")
def admin_list(db: Session = Depends(database.get_db)):
    return [{"id": u.id, "nickname": u.profile.nickname, "university": u.profile.university, "is_verified": u.is_verified, "student_card_url": u.student_card_url} for u in db.query(models.User).all()]

@app.patch("/admin/verify/{user_id}")
def verify_user(user_id: int, status: str, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.is_verified = status
    db.commit()
    return {"message": "OK"}