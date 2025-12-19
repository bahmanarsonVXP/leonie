"""
Utilitaires pour la connexion et les opérations Supabase.

Ce module fournit un client Supabase singleton et des méthodes
helper pour les opérations courantes sur la base de données.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client, create_client

from app.config import get_settings


class SupabaseClient:
    """Client Supabase singleton pour l'application."""

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """
        Récupère l'instance unique du client Supabase.

        Returns:
            Client: Instance du client Supabase.

        Raises:
            ValueError: Si les variables d'environnement ne sont pas configurées.
        """
        if cls._instance is None:
            settings = get_settings()
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                raise ValueError(
                    "SUPABASE_URL et SUPABASE_KEY doivent être définis "
                    "dans les variables d'environnement"
                )
            cls._instance = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        return cls._instance


def get_db() -> Client:
    """
    Helper pour récupérer le client Supabase.

    Returns:
        Client: Instance du client Supabase.
    """
    return SupabaseClient.get_client()


# =============================================================================
# HELPERS COURTIERS
# =============================================================================


def get_courtier_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Récupère un courtier par son email.

    Args:
        email: Email du courtier.

    Returns:
        Dict contenant les données du courtier, ou None si non trouvé.
    """
    db = get_db()
    response = db.table("courtiers").select("*").eq("email", email).eq("actif", True).execute()

    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


def get_courtier_by_id(courtier_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Récupère un courtier par son ID.

    Args:
        courtier_id: ID unique du courtier.

    Returns:
        Dict contenant les données du courtier, ou None si non trouvé.
    """
    db = get_db()
    response = db.table("courtiers").select("*").eq("id", str(courtier_id)).execute()

    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


def create_courtier(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crée un nouveau courtier.

    Args:
        data: Données du courtier à créer.

    Returns:
        Dict contenant les données du courtier créé.

    Raises:
        Exception: Si la création échoue.
    """
    db = get_db()
    response = db.table("courtiers").insert(data).execute()
    return response.data[0]


# =============================================================================
# HELPERS CLIENTS
# =============================================================================


def get_client_by_id(client_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Récupère un client par son ID.

    Args:
        client_id: ID unique du client.

    Returns:
        Dict contenant les données du client, ou None si non trouvé.
    """
    db = get_db()
    response = db.table("clients").select("*").eq("id", str(client_id)).execute()

    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


def get_client_by_email(email: str, courtier_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
    """
    Récupère un client par son email principal.

    Args:
        email: Email du client.
        courtier_id: ID du courtier (optionnel, pour filtrer).

    Returns:
        Dict contenant les données du client, ou None si non trouvé.
    """
    db = get_db()
    query = db.table("clients").select("*").eq("email_principal", email)

    if courtier_id:
        query = query.eq("courtier_id", str(courtier_id))

    response = query.execute()

    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


def find_client_by_email_list(emails: List[str], courtier_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Recherche un client par une liste d'emails (principal ou secondaires).

    Args:
        emails: Liste d'emails à rechercher.
        courtier_id: ID du courtier.

    Returns:
        Dict contenant les données du client, ou None si non trouvé.
    """
    db = get_db()

    # Recherche par email principal
    for email in emails:
        client = get_client_by_email(email, courtier_id)
        if client:
            return client

    # Recherche par emails secondaires
    response = db.table("clients").select("*").eq("courtier_id", str(courtier_id)).execute()

    for client in response.data:
        emails_secondaires = client.get("emails_secondaires", [])
        if any(email in emails_secondaires for email in emails):
            return client

    return None


def get_clients_by_courtier(courtier_id: UUID, statut: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Récupère tous les clients d'un courtier.

    Args:
        courtier_id: ID du courtier.
        statut: Filtrer par statut (optionnel).

    Returns:
        Liste des clients du courtier.
    """
    db = get_db()
    query = db.table("clients").select("*").eq("courtier_id", str(courtier_id))

    if statut:
        query = query.eq("statut", statut)

    response = query.order("created_at", desc=True).execute()
    return response.data


def create_client_record(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crée un nouveau client (enregistrement dans la table clients).

    Args:
        data: Données du client à créer.

    Returns:
        Dict contenant les données du client créé.

    Raises:
        Exception: Si la création échoue.
    """
    db = get_db()
    response = db.table("clients").insert(data).execute()
    return response.data[0]


def update_client(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Met à jour un client existant.

    Args:
        client_id: ID du client à mettre à jour.
        data: Données à mettre à jour.

    Returns:
        Dict contenant les données du client mis à jour.

    Raises:
        Exception: Si la mise à jour échoue.
    """
    db = get_db()
    response = db.table("clients").update(data).eq("id", str(client_id)).execute()
    return response.data[0]


# =============================================================================
# HELPERS PIÈCES
# =============================================================================


def get_types_pieces_by_type_pret(type_pret: str) -> List[Dict[str, Any]]:
    """
    Récupère tous les types de pièces pour un type de prêt.

    Args:
        type_pret: Type de prêt (immobilier ou professionnel).

    Returns:
        Liste des types de pièces.
    """
    db = get_db()
    response = (
        db.table("types_pieces")
        .select("*")
        .in_("type_pret", [type_pret, "commun"])
        .order("ordre")
        .execute()
    )
    return response.data


def get_pieces_by_client(client_id: UUID) -> List[Dict[str, Any]]:
    """
    Récupère toutes les pièces d'un client.

    Args:
        client_id: ID du client.

    Returns:
        Liste des pièces du client.
    """
    db = get_db()
    response = (
        db.table("pieces_dossier")
        .select("*, types_pieces(*)")
        .eq("client_id", str(client_id))
        .execute()
    )
    return response.data


def create_piece_dossier(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crée une nouvelle pièce dans un dossier.

    Args:
        data: Données de la pièce à créer.

    Returns:
        Dict contenant les données de la pièce créée.

    Raises:
        Exception: Si la création échoue.
    """
    db = get_db()
    response = db.table("pieces_dossier").insert(data).execute()
    return response.data[0]


def update_piece_dossier(piece_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Met à jour une pièce existante.

    Args:
        piece_id: ID de la pièce à mettre à jour.
        data: Données à mettre à jour.

    Returns:
        Dict contenant les données de la pièce mise à jour.

    Raises:
        Exception: Si la mise à jour échoue.
    """
    db = get_db()
    response = db.table("pieces_dossier").update(data).eq("id", str(piece_id)).execute()
    return response.data[0]


def check_duplicate_piece(fichier_hash: str, client_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Vérifie si une pièce avec le même hash existe déjà pour un client.

    Args:
        fichier_hash: Hash SHA256 du fichier.
        client_id: ID du client.

    Returns:
        Dict contenant les données de la pièce si trouvée, None sinon.
    """
    db = get_db()
    response = (
        db.table("pieces_dossier")
        .select("*")
        .eq("fichier_hash", fichier_hash)
        .eq("client_id", str(client_id))
        .execute()
    )

    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


# =============================================================================
# HELPERS LOGS
# =============================================================================


def log_activity(
    action: str,
    details: Optional[Dict[str, Any]] = None,
    client_id: Optional[UUID] = None,
    courtier_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """
    Enregistre une activité dans les logs.

    Args:
        action: Type d'action effectuée.
        details: Détails JSON de l'action.
        client_id: ID du client concerné (optionnel).
        courtier_id: ID du courtier concerné (optionnel).

    Returns:
        Dict contenant les données du log créé.
    """
    db = get_db()
    log_data = {
        "action": action,
        "details": details or {},
    }

    if client_id:
        log_data["client_id"] = str(client_id)
    if courtier_id:
        log_data["courtier_id"] = str(courtier_id)

    response = db.table("logs_activite").insert(log_data).execute()
    return response.data[0]


# =============================================================================
# HELPERS CONFIG
# =============================================================================


def get_config(cle: str) -> Optional[Any]:
    """
    Récupère une valeur de configuration.

    Args:
        cle: Clé de configuration.

    Returns:
        Valeur JSON de la configuration, ou None si non trouvée.
    """
    db = get_db()
    response = db.table("config").select("valeur").eq("cle", cle).execute()

    if response.data and len(response.data) > 0:
        return response.data[0]["valeur"]
    return None


def set_config(cle: str, valeur: Any, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Définit ou met à jour une valeur de configuration.

    Args:
        cle: Clé de configuration.
        valeur: Valeur JSON à stocker.
        description: Description de la configuration (optionnel).

    Returns:
        Dict contenant les données de configuration.
    """
    db = get_db()
    config_data = {
        "cle": cle,
        "valeur": valeur,
    }

    if description:
        config_data["description"] = description

    response = db.table("config").upsert(config_data).execute()
    return response.data[0]
