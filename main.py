from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import models
from database import engine, get_db
import shutil # 파일 복사용
import os    # 폴더 생성용
from fastapi import File, UploadFile # 파일 수신용

# 서버 실행 시 DB 테이블 자동 생성/업데이트
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MeetU API Server")

# 브라우저 접근 허용 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 데이터 수신 규격 (Schema) ---

class KakaoLoginRequest(BaseModel):
    email: str
    nickname: str
    kakao_id: str

class ProfileUpdate(BaseModel):
    user_id: int
    nickname: str
    university: str
    major: str
    age: int
    mbti: str
    hobbies: str
    charms: str
    pref_age: str
    pref_univ_group: str

# --- API 엔드포인트 ---

@app.get("/")
def read_root():
    return {"message": "MeetU API 서버가 정상적으로 실행 중입니다! 🚀"}

# 1. 회원가입 (카카오 로그인 시 호출)
@app.post("/users/")
def create_user(request: KakaoLoginRequest, db: Session = Depends(get_db)):
    # 이미 존재하는 유저인지 확인 (kakao_id 기준)
    existing_user = db.query(models.User).filter(models.User.oauth_id == request.kakao_id).first()
    if existing_user:
        return {"message": "기존 유저 로그인", "user_id": existing_user.id}

    # 새 유저 생성
    new_user = models.User(
        oauth_provider="kakao", 
        oauth_id=request.kakao_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 프로필 공간도 함께 생성
    new_profile = models.Profile(
        user_id=new_user.id,
        nickname=request.nickname
    )
    db.add(new_profile)
    db.commit()

    return {
        "message": "유저 생성 완료 💗",
        "user_id": new_user.id,
        "nickname": request.nickname
    }

# 2. 프로필 상세 정보 저장
@app.put("/profiles/")
def update_profile(request: ProfileUpdate, db: Session = Depends(get_db)):
    # 프로필 찾기
    db_profile = db.query(models.Profile).filter(models.Profile.user_id == request.user_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")

    # 정보 업데이트
    db_profile.nickname = request.nickname
    db_profile.university = request.university
    db_profile.major = request.major
    db_profile.age = request.age
    db_profile.mbti = request.mbti
    db_profile.hobbies = request.hobbies
    db_profile.charms = request.charms

    # 선호도(이상형) 정보 업데이트 또는 생성
    db_pref = db.query(models.Preference).filter(models.Preference.user_id == request.user_id).first()
    if not db_pref:
        db_pref = models.Preference(user_id=request.user_id)
        db.add(db_pref)
    
    db_pref.pref_univ_group = request.pref_univ_group
    # pref_age 등 추가 필드 저장 가능

    db.commit()
    return {"message": "프로필 저장 완료! 💾"}

# 3. [관리자] 전체 유저 목록 조회
@app.get("/admin/users/")
def get_admin_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    result = []
    for user in users:
        # 프로필이 없을 경우를 대비해 안전하게 처리
        p = user.profile
        result.append({
            "id": user.id,
            "nickname": p.nickname if p else "N/A",
            "university": p.university if p else "미설정",
            "is_verified": user.is_verified,
            "student_card_url": user.student_card_url,
            "created_at": user.created_at
        })
    return result

# 4. [관리자] 유저 인증 승인/반려
@app.patch("/admin/verify/{user_id}")
def verify_user(user_id: int, status: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저 없음")
    
    user.is_verified = status
    db.commit()
    return {"message": f"{user_id}번 유저가 {status} 되었습니다."}

# 5. 유저 데이터 확인용 (브라우저에서 접속용)
@app.get("/users/")
def get_all_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

UPLOAD_DIR = "./uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# 관리자 페이지에서 사진 파일을 볼 수 있도록 경로 노출 설정 (중요!)
from fastapi.staticfiles import StaticFiles
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 학생증 사진 업로드 API
@app.post("/upload/student-card/{user_id}")
async def upload_student_card(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 파일명 결정 (예: 1_student_card.jpg)
    file_path = f"{UPLOAD_DIR}/{user_id}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # DB에 사진 주소 저장
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.student_card_url = f"http://127.0.0.1:8000/uploads/{user_id}_{file.filename}"
    db.commit()
    
    return {"message": "사진 업로드 완료!", "url": user.student_card_url}