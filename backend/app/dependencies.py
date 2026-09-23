from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.study_models import User
from app.services.security import decode_access_token

bearer_scheme = HTTPBearer()


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        user_id = decode_access_token(creds.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail="Unauthorized User")

    user = db.get(User, UUID(user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized User")

    return user
