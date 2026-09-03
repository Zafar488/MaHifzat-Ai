"""JWT authentication and role-based authorization."""
import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import bcrypt

from backend.config import settings
from backend.schemas.auth import TokenPayload, TokenResponse, UserRole, UserInDB

# ---------------------------------------------------------------------------
# Crypto & OAuth
# ---------------------------------------------------------------------------


def _hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ---------------------------------------------------------------------------
# Hardcoded MVP users (replace with DB-backed store in production)
# ---------------------------------------------------------------------------

_MVP_USERS = {
    "admin": UserInDB(
        user_id="u-admin-001",
        username="admin",
        hashed_password=_hash_password("admin"),
        role=UserRole.ADMIN,
        full_name="System Administrator",
        created_at=datetime.utcnow(),
    ),
    "clinician": UserInDB(
        user_id="u-clinician-001",
        username="clinician",
        hashed_password=_hash_password("clinician"),
        role=UserRole.CLINICIAN,
        full_name="Dr. Ayesha Khan",
        created_at=datetime.utcnow(),
    ),
    "lhw": UserInDB(
        user_id="u-lhw-001",
        username="lhw",
        hashed_password=_hash_password("lhw"),
        role=UserRole.LHW,
        full_name="Fatima Bibi (LHW)",
        created_at=datetime.utcnow(),
    ),
    "patient": UserInDB(
        user_id="u-patient-001",
        username="patient",
        hashed_password=_hash_password("patient"),
        role=UserRole.PATIENT,
        full_name="Sample Patient",
        created_at=datetime.utcnow(),
    ),
}

# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token, returning TokenPayload."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        sub: str = payload.get("sub")
        role: str = payload.get("role")
        if sub is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenPayload(sub=sub, role=UserRole(role), exp=payload.get("exp"))
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """Dependency: extract and verify JWT from Authorization header."""
    return verify_token(token)


def require_role(*roles: UserRole):
    """Dependency factory: ensure the current user has one of the given roles."""

    def _check(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' is not authorized. Required: {[r.value for r in roles]}",
            )
        return current_user

    return _check


# ---------------------------------------------------------------------------
# Auth router  (mounted at /api/auth)
# ---------------------------------------------------------------------------

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    MVP login — accepts username/password form data and returns a JWT.

    Hardcoded test accounts:
        admin / admin, clinician / clinician, lhw / lhw, patient / patient
    """
    user = _MVP_USERS.get(form_data.username)
    if user is None or not _verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": user.user_id, "role": user.role.value})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


from pydantic import BaseModel

class SignupRequest(BaseModel):
    username: str
    password: str
    full_name: str
    role: UserRole = UserRole.CLINICIAN

@auth_router.post("/signup", response_model=dict)
async def signup(request: SignupRequest):
    """Register a new user in the in-memory MVP store."""
    if request.username in _MVP_USERS:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = UserInDB(
        user_id=f"u-{uuid.uuid4().hex[:8]}",
        username=request.username,
        hashed_password=_hash_password(request.password),
        role=request.role,
        full_name=request.full_name,
        created_at=datetime.utcnow(),
    )
    _MVP_USERS[request.username] = new_user
    return {"message": "User registered successfully", "user_id": new_user.user_id}



@auth_router.get("/me", response_model=dict)
async def me(current_user: TokenPayload = Depends(get_current_user)):
    """Return the current authenticated user's token payload."""
    return {
        "user_id": current_user.sub,
        "role": current_user.role.value,
    }
