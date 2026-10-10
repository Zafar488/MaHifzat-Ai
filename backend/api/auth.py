"""Persistent identities, role checks and token invalidation."""
from datetime import datetime, timedelta
import hashlib
import uuid
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from backend.config import settings
from backend.api.deps import get_db
from backend.db.models import User, LoginThrottle, AuditLog
from backend.schemas.auth import TokenPayload, TokenResponse, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
auth_router = APIRouter(prefix="/auth", tags=["auth"])


def _hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain, hashed):
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False


def create_access_token(data, expires_delta=None):
    payload = {**data, "exp": datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)), "iss": "maahifazat", "aud": "maahifazat-api"}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM], issuer="maahifazat", audience="maahifazat-api")
        return TokenPayload(sub=payload["sub"], role=UserRole(payload["role"]), exp=payload["exp"], token_version=payload["token_version"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(401, "Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    payload = verify_token(token)
    user = await db.get(User, payload.sub)
    if user is None or not user.is_active or user.token_version != payload.token_version or user.role != payload.role.value:
        raise HTTPException(401, "Session no longer valid")
    return payload


def require_role(*roles):
    async def check(user: TokenPayload = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(403, "Role not authorized")
        return user
    return check


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=12, max_length=72)
    full_name: str = Field(min_length=1, max_length=100)
    role: UserRole = UserRole.PATIENT

    @field_validator("password")
    @classmethod
    def password_bytes(cls, value):
        if len(value.encode()) > 72:
            raise ValueError("Password exceeds bcrypt byte limit")
        return value


async def create_user(db, request):
    if await db.scalar(select(User.id).where(User.username == request.username.lower())):
        raise HTTPException(409, "Username already registered")
    user = User(id=str(uuid.uuid4()), username=request.username.lower(), hashed_password=_hash_password(request.password), role=request.role.value, full_name=request.full_name)
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Username already registered")
    return user


@auth_router.post("/signup", status_code=201)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    if request.role != UserRole.PATIENT:
        raise HTTPException(422, "Self-registration permits only the patient role")
    user = await create_user(db, request)
    db.add(AuditLog(agent_name="identity", action="self_registered", output_summary={"user_id": user.id}))
    return {"message": "User registered", "user_id": user.id}


@auth_router.post("/users", status_code=201)
async def provision(request: SignupRequest, db: AsyncSession = Depends(get_db), user=Depends(require_role(UserRole.ADMIN))):
    created = await create_user(db, request)
    db.add(AuditLog(agent_name="identity", action="user_provisioned", input_summary={"actor_id": user.sub}, output_summary={"user_id": created.id, "role": created.role}))
    return {"user_id": created.id, "role": created.role}


class UserStatusUpdate(BaseModel):
    role: UserRole
    is_active: bool


@auth_router.put("/users/{user_id}")
async def update_user(user_id: str, payload: UserStatusUpdate, db: AsyncSession = Depends(get_db), actor=Depends(require_role(UserRole.ADMIN))):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    if actor.sub == user_id and (not payload.is_active or payload.role != UserRole.ADMIN):
        raise HTTPException(409, "Cannot remove your own administrative access")
    user.role, user.is_active = payload.role.value, payload.is_active
    user.token_version += 1
    db.add(AuditLog(agent_name="identity", action="user_access_changed", input_summary={"actor_id": actor.sub}, output_summary={"user_id": user_id, "role": user.role, "active": user.is_active}))
    return {"user_id": user_id, "role": user.role, "is_active": user.is_active}


@auth_router.post("/login", response_model=TokenResponse)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Persistent per-identity+IP rate limiting shared across workers.
    key = hashlib.sha256((form_data.username.lower() + "|" + (request.client.host if request.client else "")).encode()).hexdigest()
    throttle = await db.get(LoginThrottle, key)
    now = datetime.utcnow()
    if throttle and now - throttle.window_start > timedelta(minutes=15):
        throttle.failures, throttle.window_start = 0, now
    if throttle and throttle.failures >= 10:
        raise HTTPException(429, "Too many attempts; retry after 15 minutes")
    user = await db.scalar(select(User).where(User.username == form_data.username.lower()))
    if user is None or not user.is_active or not _verify_password(form_data.password, user.hashed_password):
        if throttle is None:
            throttle = LoginThrottle(key=key, failures=0, window_start=now)
            db.add(throttle)
        throttle.failures += 1
        await db.commit()  # failed attempt must survive HTTPException rollback
        raise HTTPException(401, "Incorrect username or password")
    if throttle:
        throttle.failures = 0
    token = create_access_token({"sub": user.id, "role": user.role, "token_version": user.token_version})
    return TokenResponse(access_token=token, expires_in=settings.JWT_EXPIRE_MINUTES * 60)


@auth_router.post("/logout")
async def logout(payload=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await db.get(User, payload.sub)
    user.token_version += 1
    return {"message": "All sessions invalidated"}


@auth_router.get("/me")
async def me(payload=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await db.get(User, payload.sub)
    return {"user_id": user.id, "role": user.role, "username": user.username, "full_name": user.full_name}


class Preferences(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: str = Field("en", pattern="^(en|ur|ps|sk)$")
    email_notifications: bool = False
    sms_notifications: bool = False


@auth_router.get("/preferences")
async def preferences(payload=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await db.get(User, payload.sub)
    return Preferences.model_validate(user.preferences or {})


@auth_router.put("/preferences")
async def save_preferences(preferences: Preferences, payload=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await db.get(User, payload.sub)
    user.preferences = preferences.model_dump()
    return preferences
