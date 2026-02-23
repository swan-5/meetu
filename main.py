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
    login_id: str; password: str; name: str; university: str; major: str; age: int; height: int; gender: str

class LoginRequest(BaseModel):
    login_id: str; password: str

class ProfileUpdate(BaseModel):
    user_id: int; nickname: str; university: str; major: str; age: int; height: int; gender: str
    mbti: str; ideal_type: str; pref_mbti: str; pref_age: str; must_have: str; description: str; meeting_type: str

class RoomCreate(BaseModel):
    title: str; capacity: int; creator_id: int

# --- APIs ---
@app.post("/users/register")
def register(request: RegisterRequest, db: Session = Depends(database.get_db)):
    if db.query(models.User).filter(models.User.login_id == request.login_id).first():
        raise HTTPException(400, "아이디 중복")
    new_user = models.User(login_id=request.login_id, password=request.password)
    db.add(new_user); db.commit(); db.refresh(new_user)
    db.add(models.Profile(
        user_id=new_user.id, nickname=request.name, university=request.university, 
        major=request.major, age=request.age, height=request.height, gender=request.gender
    ))
    db.commit()
    return {"user_id": new_user.id}
# main.py 에 추가
# main.py (관리자 관련 API 부분)
@app.get("/admin/users/")
def admin_list(db: Session = Depends(database.get_db)):
    users = db.query(models.User).all()
    return [{
        "id": u.id,
        "nickname": u.profile.nickname,
        "university": u.profile.university,
        "gender": u.profile.gender,
        "is_verified": u.is_verified, # 'pending', 'verified', 'rejected'
        "student_card_url": u.student_card_url
    } for u in users]

@app.patch("/admin/verify/{user_id}")
def verify_user(user_id: int, status: str, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(404, "유저 없음")
    user.is_verified = status # 여기서 'verified'로 바꿔줌
    db.commit()
    return {"message": f"상태가 {status}로 변경되었습니다."}
@app.post("/users/login")
def login(request: LoginRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.login_id == request.login_id, models.User.password == request.password).first()
    if not user: raise HTTPException(401, "로그인 실패")
    p = user.profile
    return {"user_id": user.id, "is_verified": user.is_verified, "nickname": p.nickname, "univ": p.university, "major": p.major, "age": p.age, "gender": p.gender, "height": p.height}

@app.get("/rooms/")
def get_rooms(db: Session = Depends(database.get_db)):
    rooms = db.query(models.Room).all()
    output = []
    for r in rooms:
        m_data = []
        for m in r.members:
            m_data.append({
                "nickname": m.profile.nickname,
                "univ": m.profile.university,
                "major": m.profile.major,
                "gender": m.profile.gender
            })
        output.append({"id": r.id, "title": r.title, "capacity": r.capacity, "members": m_data})
    return output

@app.post("/rooms/")
def create_room(req: RoomCreate, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == req.creator_id).first()
    new_room = models.Room(title=req.title, capacity=req.capacity, creator_id=req.creator_id)
    new_room.members.append(user)
    db.add(new_room); db.commit()
    return {"id": new_room.id}

@app.post("/rooms/{room_id}/join")
def join_room(room_id: int, user_id: int, db: Session = Depends(database.get_db)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if any(m.id == user_id for m in room.members): return {"message": "이미 참여 중"}
    if len(room.members) >= room.capacity: raise HTTPException(400, "정원 초과")
    room.members.append(user); db.commit()
    return {"status": "success"}

@app.put("/profiles/")
def update_profile(request: ProfileUpdate, db: Session = Depends(database.get_db)):
    p = db.query(models.Profile).filter(models.Profile.user_id == request.user_id).first()
    for key, value in request.dict().items(): setattr(p, key, value)
    db.commit()
    return {"message": "저장완료"}

@app.post("/upload/student-card/{user_id}")
async def upload_card(user_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    path = f"{UPLOAD_DIR}/{user_id}_{file.filename}"
    with open(path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.student_card_url = f"/uploads/{user_id}_{file.filename}"
    db.commit()
    return {"url": user.student_card_url}


# main.py 하단에 추가
@app.get("/users/{user_id}/rooms")
def get_user_rooms(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(404, "유저 없음")
    
    # 유저가 참여 중인 모든 방 목록 추출
    rooms_data = []
    for r in user.rooms:
        rooms_data.append({
            "id": r.id,
            "title": r.title,
            "capacity": r.capacity,
            "current_count": len(r.members),
            "is_creator": r.creator_id == user_id, # 내가 만든 방인지 여부
            "members": [{
                "nickname": m.profile.nickname,
                "univ": m.profile.university,
                "gender": m.profile.gender
            } for m in r.members]
        })
    return rooms_data

# main.py 추가 및 수정 API

# 1. 방 나가기 (2회 제한 로직 포함)
@app.post("/rooms/{room_id}/exit")
def exit_room(room_id: int, user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    
    if user.profile.exit_count >= 2:
        raise HTTPException(400, "방 나가기 제한 횟수(2회)를 초과하여 나갈 수 없습니다.")
    
    if room.creator_id == user_id:
        raise HTTPException(400, "방장은 방을 나가기 전 방장을 위임하거나 방을 폐쇄해야 합니다.")

    if user in room.members:
        room.members.remove(user)
        user.profile.exit_count += 1 # 탈퇴 횟수 증가
        db.commit()
        return {"message": "탈퇴 완료", "remaining": 2 - user.profile.exit_count}
    raise HTTPException(404, "참여 중인 방이 아닙니다.")

# 2. 방 폐쇄 (방장 전용)
@app.delete("/rooms/{room_id}")
def delete_room(room_id: int, user_id: int, db: Session = Depends(database.get_db)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if room.creator_id != user_id:
        raise HTTPException(403, "방장만 방을 폐쇄할 수 있습니다.")
    db.delete(room)
    db.commit()
    return {"message": "방이 폐쇄되었습니다."}

# 3. 방장 위임 (토스)
@app.patch("/rooms/{room_id}/handover")
def handover_room(room_id: int, creator_id: int, new_creator_id: int, db: Session = Depends(database.get_db)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if room.creator_id != creator_id:
        raise HTTPException(403, "권한이 없습니다.")
    room.creator_id = new_creator_id
    db.commit()
    return {"message": "방장이 변경되었습니다."}

@app.get("/")
async def read_index():
    # 현재 실행 파일 위치에서 index.html을 찾아 보냅니다.
    return FileResponse('index.html')