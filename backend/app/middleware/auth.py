"""
Middleware d'authentification JWT pour l'API Léonie.

Ce module gère l'authentification via tokens JWT Supabase:
- Vérification de la signature JWT
- Extraction des informations utilisateur (courtier)
- Vérification des permissions admin
- Protection des routes API

Architecture:
- Tokens JWT générés par Supabase Auth
- Signature vérifiée avec SUPABASE_JWT_SECRET
- Claims: sub (user_id), email, role
"""

from typing import Optional
from uuid import UUID

import jwt
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings
from app.utils.db import get_courtier_by_email, get_db

logger = structlog.get_logger()
security = HTTPBearer()


class AuthUser:
    """Représente un utilisateur authentifié."""

    def __init__(
        self,
        user_id: str,
        email: str,
        role: Optional[str] = None,
        courtier_data: Optional[dict] = None
    ):
        self.user_id = user_id
        self.email = email
        self.role = role or 'courtier'
        self.courtier_data = courtier_data

    @property
    def is_admin(self) -> bool:
        """Vérifie si l'utilisateur est admin."""
        return self.role == 'admin'

    @property
    def courtier_id(self) -> Optional[UUID]:
        """Retourne l'ID du courtier si disponible."""
        if self.courtier_data:
            return UUID(self.courtier_data.get('id'))
        return None


def decode_jwt_token(token: str) -> dict:
    """
    Décode et vérifie un token JWT Supabase.

    Args:
        token: Token JWT brut

    Returns:
        Payload décodé (claims)

    Raises:
        HTTPException: Si token invalide ou expiré
    """
    settings = get_settings()

    try:
        # Décoder et vérifier signature
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=['HS256'],
            options={
                'verify_signature': True,
                'verify_exp': True,
                'verify_aud': False  # Supabase n'utilise pas toujours aud
            }
        )

        logger.debug(
            "Token JWT décodé",
            sub=payload.get('sub'),
            email=payload.get('email')
        )

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token JWT expiré")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré. Veuillez vous reconnecter.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Token JWT invalide", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide. Authentification requise.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error("Erreur décodage JWT", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur d'authentification"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AuthUser:
    """
    Dependency FastAPI pour récupérer l'utilisateur authentifié.

    Extrait le token JWT du header Authorization et le valide.
    Récupère les données courtier depuis la DB.

    Args:
        credentials: Credentials HTTP Bearer automatiquement extraits

    Returns:
        AuthUser avec données utilisateur

    Raises:
        HTTPException: Si authentification échoue

    Usage:
        @app.get("/dossiers")
        async def list_dossiers(user: AuthUser = Depends(get_current_user)):
            courtier_id = user.courtier_id
            ...
    """
    token = credentials.credentials

    # Décoder token
    payload = decode_jwt_token(token)

    # Extraire infos utilisateur
    user_id = payload.get('sub')
    email = payload.get('email')
    role = payload.get('role')  # Peut être défini dans les metadata Supabase

    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide: informations utilisateur manquantes"
        )

    # Récupérer données courtier depuis DB
    courtier_data = None
    settings = get_settings()

    try:
        # Vérifier si l'utilisateur est admin
        # Les admins peuvent ne pas être dans la table courtiers
        is_admin = (
            email == settings.ADMIN_EMAIL or
            role == 'admin' or
            payload.get('user_metadata', {}).get('role') == 'admin'
        )

        courtier_data = get_courtier_by_email(email)

        if not courtier_data:
            # Si admin, autoriser même sans courtier_data
            if is_admin:
                logger.info(
                    "Admin authentifié (sans courtier_data)",
                    email=email,
                    user_id=user_id
                )
                return AuthUser(
                    user_id=user_id,
                    email=email,
                    role='admin',
                    courtier_data=None
                )

            # Sinon, refuser l'accès
            logger.warning(
                "Utilisateur authentifié mais courtier non trouvé en DB",
                email=email,
                user_id=user_id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte courtier non trouvé. Contactez l'administrateur."
            )

        if not courtier_data.get('actif', True):
            logger.warning(
                "Tentative d'accès par courtier inactif",
                email=email,
                courtier_id=courtier_data.get('id')
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte courtier désactivé. Contactez l'administrateur."
            )

        logger.info(
            "Utilisateur authentifié",
            email=email,
            courtier_id=courtier_data.get('id'),
            courtier_nom=f"{courtier_data.get('prenom')} {courtier_data.get('nom')}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Erreur récupération courtier",
            email=email,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des données utilisateur"
        )

    return AuthUser(
        user_id=user_id,
        email=email,
        role=role,
        courtier_data=courtier_data
    )


async def require_admin(
    user: AuthUser = Depends(get_current_user)
) -> AuthUser:
    """
    Dependency FastAPI pour routes admin uniquement.

    Vérifie que l'utilisateur authentifié a le rôle admin.

    Args:
        user: Utilisateur authentifié

    Returns:
        AuthUser si admin

    Raises:
        HTTPException: Si utilisateur n'est pas admin

    Usage:
        @app.post("/admin/courtiers")
        async def create_courtier(
            data: CourtierCreate,
            admin: AuthUser = Depends(require_admin)
        ):
            ...
    """
    settings = get_settings()

    # Vérifier si admin via role
    if user.is_admin:
        logger.info("Accès admin autorisé (role)", email=user.email)
        return user

    # Vérifier si admin via email whitelist
    if user.email == settings.ADMIN_EMAIL:
        logger.info("Accès admin autorisé (email)", email=user.email)
        return user

    # Accès refusé
    logger.warning(
        "Tentative d'accès admin refusée",
        email=user.email,
        role=user.role
    )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Accès réservé aux administrateurs"
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthUser]:
    """
    Dependency FastAPI pour authentification optionnelle.

    Retourne l'utilisateur si authentifié, None sinon.
    Utile pour routes publiques avec comportement différencié.

    Args:
        credentials: Credentials HTTP Bearer (optionnel)

    Returns:
        AuthUser si authentifié, None sinon

    Usage:
        @app.get("/public/stats")
        async def get_stats(user: Optional[AuthUser] = Depends(get_optional_user)):
            if user:
                # Stats personnalisées
                ...
            else:
                # Stats globales
                ...
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
