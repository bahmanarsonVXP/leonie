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
            # Utilise la clé Service Role si disponible (pour les opérations backend/admin)
            # Sinon, utilise la clé standard (qui doit alors être une clé service ou avoir les droits suffisants)
            key_to_use = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
            
            # Log (masqué) pour debug
            if settings.SUPABASE_SERVICE_ROLE_KEY:
                # On ne logge pas via logger ici pour éviter imports circulaires si logger dépend de config/db
                pass
            
            cls._instance = create_client(
                settings.SUPABASE_URL,
                key_to_use
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


def get_all_courtiers() -> List[Dict[str, Any]]:
    """
    Récupère tous les courtiers (admin).

    Returns:
        Liste de tous les courtiers
    """
    db = get_db()
    response = db.table("courtiers").select("*").order("created_at", desc=True).execute()
    return response.data


def get_all_courtiers_actifs() -> List[Dict[str, Any]]:
    """
    Récupère tous les courtiers actifs.

    Utilisé pour rapport quotidien.

    Returns:
        Liste des courtiers actifs
    """
    db = get_db()
    response = db.table("courtiers").select("*").eq("actif", True).execute()
    return response.data


def update_courtier(courtier_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Met à jour un courtier existant.

    Args:
        courtier_id: ID du courtier à mettre à jour.
        data: Données à mettre à jour.

    Returns:
        Dict contenant les données du courtier mis à jour.

    Raises:
        Exception: Si la mise à jour échoue.
    """
    db = get_db()
    response = db.table("courtiers").update(data).eq("id", str(courtier_id)).execute()
    return response.data[0] if response.data else None


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


def find_client_by_name(
    courtier_id: UUID,
    nom: str,
    prenom: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Cherche client par nom (fuzzy match ILIKE).

    Utilise ILIKE pour match insensible à la casse.

    Args:
        courtier_id: ID du courtier (isolation)
        nom: Nom du client à chercher
        prenom: Prénom du client (optionnel)

    Returns:
        Client si trouvé, None sinon
    """
    db = get_db()
    query = db.table("clients").select("*").eq("courtier_id", str(courtier_id)).ilike("nom", f"%{nom}%")

    if prenom:
        query = query.ilike("prenom", f"%{prenom}%")

    response = query.limit(1).execute()

    return response.data[0] if response.data else None


def add_secondary_email(client_id: UUID, email: str) -> None:
    """
    Ajoute un email secondaire à un client.

    Permet de gérer les clients qui envoient depuis plusieurs adresses.

    Args:
        client_id: ID du client
        email: Email à ajouter aux emails secondaires
    """
    import structlog
    logger = structlog.get_logger()

    client = get_client_by_id(client_id)

    if not client:
        return

    emails_secondaires = client.get("emails_secondaires", []) or []

    if email not in emails_secondaires:
        emails_secondaires.append(email)
        update_client(client_id, {"emails_secondaires": emails_secondaires})

        logger.info(
            "Email secondaire ajouté",
            client_id=str(client_id),
            email=email
        )


def get_clients_modified_since(
    courtier_id: UUID,
    since_datetime
) -> List[Dict[str, Any]]:
    """
    Récupère les clients modifiés depuis une date.

    Utilisé pour rapport quotidien.

    Args:
        courtier_id: ID du courtier
        since_datetime: Date limite (clients modifiés après cette date)

    Returns:
        Liste des clients modifiés
    """
    db = get_db()
    response = (
        db.table("clients")
        .select("*")
        .eq("courtier_id", str(courtier_id))
        .gte("updated_at", since_datetime.isoformat())
        .order("updated_at", desc=True)
        .execute()
    )
    return response.data


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


def get_pieces_dossier(client_id: UUID) -> List[Dict[str, Any]]:
    """
    Alias de get_pieces_by_client pour compatibilité.

    Args:
        client_id: ID du client.

    Returns:
        Liste des pièces du client.
    """
    return get_pieces_by_client(client_id)


def get_type_piece(type_piece_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Récupère un type de pièce par son ID.

    Args:
        type_piece_id: ID du type de pièce

    Returns:
        Dict contenant les données du type de pièce, ou None si non trouvé
    """
    db = get_db()
    response = db.table("types_pieces").select("*").eq("id", str(type_piece_id)).execute()

    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


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


def create_log(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crée un log d'activité (alias de log_activity).

    Args:
        data: Données du log contenant action, details, client_id, courtier_id

    Returns:
        Dict contenant les données du log créé
    """
    return log_activity(
        action=data.get("action"),
        details=data.get("details"),
        client_id=UUID(data["client_id"]) if data.get("client_id") else None,
        courtier_id=UUID(data["courtier_id"]) if data.get("courtier_id") else None
    )


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
