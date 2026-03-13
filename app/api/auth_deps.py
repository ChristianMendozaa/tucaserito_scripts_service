import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pydantic import ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Valida el token JWT y retorna el UUID (sub) del usuario que hace la petición."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            issuer="tucaserito-auth-service",
            audience="tucaserito-microservices"
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token no contiene user ID (sub)")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El token ha expirado. Por favor, vuelva a iniciar sesión.")
    except (jwt.InvalidTokenError, ValidationError) as e:
        logger.warning(f"Invalid JWT Token: {e}")
        raise HTTPException(status_code=401, detail="Credenciales de autenticación no válidas")
