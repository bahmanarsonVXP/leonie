"""
Tests unitaires pour les background jobs RQ.

Ces tests vérifient le bon fonctionnement des jobs de traitement
asynchrone des emails (NOUVEAU_DOSSIER, ENVOI_DOCUMENTS, MODIFIER_LISTE).
"""

from unittest.mock import Mock, patch, MagicMock
import pytest

from app.workers.jobs import (
    process_nouveau_dossier,
    process_envoi_documents,
    process_modifier_liste,
    calculate_file_hash
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def courtier_id():
    """ID de courtier pour les tests."""
    return "courtier_123"


@pytest.fixture
def email_data():
    """Email de test."""
    return {
        "message_id": "test@example.com",
        "from_email": "courtier@test.com",
        "from_address": "Courtier Test <courtier@test.com>",
        "subject": "Nouveau dossier Martin",
        "body_text": "Créer un dossier pour Jean Martin",
        "body_html": "<p>Créer un dossier pour Jean Martin</p>",
        "attachments": [],
        "date": "2025-01-01T10:00:00Z"
    }


@pytest.fixture
def classification_nouveau_dossier():
    """Classification pour nouveau dossier."""
    return {
        "action": "NOUVEAU_DOSSIER",
        "resume": "Création dossier Jean Martin",
        "confiance": 0.95,
        "details": {
            "client_nom": "Martin",
            "client_prenom": "Jean",
            "client_email": "jean.martin@test.com",
            "type_pret": "immobilier",
            "pieces_mentionnees": ["Carte d'identité", "Bulletin de salaire"]
        }
    }


@pytest.fixture
def classification_envoi_documents():
    """Classification pour envoi documents."""
    return {
        "action": "ENVOI_DOCUMENTS",
        "resume": "Envoi de 2 documents",
        "confiance": 0.92,
        "details": {
            "client_nom": "Martin",
            "types_detectes": ["bulletin_salaire", "carte_identite"]
        }
    }


@pytest.fixture
def classification_modifier_liste():
    """Classification pour modification liste."""
    return {
        "action": "MODIFIER_LISTE",
        "resume": "Ajout de pièces",
        "confiance": 0.88,
        "details": {
            "client_nom": "Martin",
            "pieces_a_ajouter": ["Attestation employeur", "RIB"],
            "pieces_a_retirer": []
        }
    }


# =============================================================================
# TESTS - NOUVEAU DOSSIER
# =============================================================================

@patch('app.workers.jobs.DriveManager')
@patch('app.workers.jobs.MistralService')
def test_process_nouveau_dossier_success(
    mock_mistral,
    mock_drive,
    courtier_id,
    email_data,
    classification_nouveau_dossier
):
    """Test création nouveau dossier - succès."""
    
    # Mock DriveManager
    mock_drive_instance = Mock()
    mock_drive_instance.master_folder_id = "master_folder_123"
    mock_drive_instance.get_or_create_folder.side_effect = [
        "courtier_folder_123",  # Dossier courtier
        "client_folder_456"     # Dossier client
    ]
    mock_drive.return_value = mock_drive_instance
    
    # Mock MistralService
    mock_mistral_instance = Mock()
    mock_mistral_instance.extract_pieces_from_text_sync.return_value = [
        {"nom_piece": "Carte d'identité", "categorie": "identite"},
        {"nom_piece": "Bulletin de salaire", "categorie": "revenus"}
    ]
    mock_mistral.return_value = mock_mistral_instance
    
    # Appel du job
    result = process_nouveau_dossier(
        courtier_id=courtier_id,
        email_data=email_data,
        classification=classification_nouveau_dossier
    )
    
    # Vérifications
    assert result["status"] == "success"
    assert "client_nom" in result
    assert result["client_nom"] == "Jean Martin"
    assert "client_folder_id" in result
    assert result["client_folder_id"] == "client_folder_456"
    
    # Vérifier que les méthodes ont été appelées
    assert mock_drive_instance.get_or_create_folder.call_count == 2
    mock_mistral_instance.extract_pieces_from_text_sync.assert_called_once()


@patch('app.workers.jobs.DriveManager')
@patch('app.workers.jobs.MistralService')
def test_process_nouveau_dossier_missing_client_info(
    mock_mistral,
    mock_drive,
    courtier_id,
    email_data
):
    """Test création nouveau dossier - infos client manquantes."""
    
    classification_incomplete = {
        "action": "NOUVEAU_DOSSIER",
        "resume": "Test",
        "confiance": 0.8,
        "details": {
            "client_nom": "Martin",
            # Manque client_prenom
            "type_pret": "immobilier"
        }
    }
    
    # Doit lever ValueError
    with pytest.raises(ValueError, match="Nom ou prénom client manquant"):
        process_nouveau_dossier(
            courtier_id=courtier_id,
            email_data=email_data,
            classification=classification_incomplete
        )


# =============================================================================
# TESTS - ENVOI DOCUMENTS
# =============================================================================

@patch('app.workers.jobs.DriveManager')
@patch('app.workers.jobs.MistralService')
def test_process_envoi_documents_success(
    mock_mistral,
    mock_drive,
    courtier_id,
    classification_envoi_documents
):
    """Test traitement documents - succès."""
    
    email_with_attachments = {
        "message_id": "test@example.com",
        "from_email": "client@test.com",
        "subject": "Documents",
        "body_text": "Voici mes documents",
        "attachments": [
            {
                "filename": "bulletin.pdf",
                "content_base64": "cGRmIGNvbnRlbnQ=",  # "pdf content" en base64
                "content_type": "application/pdf",
                "size_bytes": 1024
            },
            {
                "filename": "carte.jpg",
                "content_base64": "anBnIGNvbnRlbnQ=",  # "jpg content" en base64
                "content_type": "image/jpeg",
                "size_bytes": 2048
            }
        ]
    }
    
    # Mock DriveManager
    mock_drive_instance = Mock()
    mock_drive_instance.master_folder_id = "client_folder_789"
    mock_drive_instance.upload_file.side_effect = ["file_id_1", "file_id_2"]
    mock_drive.return_value = mock_drive_instance
    
    # Appel du job
    result = process_envoi_documents(
        courtier_id=courtier_id,
        email_data=email_with_attachments,
        classification=classification_envoi_documents
    )
    
    # Vérifications
    assert result["status"] == "success"
    assert result["pieces_traitees"] == 2
    assert result["pieces_non_reconnues"] == 0
    assert len(result["pieces"]) == 2
    
    # Vérifier que upload a été appelé 2 fois
    assert mock_drive_instance.upload_file.call_count == 2


@patch('app.workers.jobs.DriveManager')
@patch('app.workers.jobs.MistralService')
def test_process_envoi_documents_no_attachments(
    mock_mistral,
    mock_drive,
    courtier_id,
    email_data,
    classification_envoi_documents
):
    """Test traitement documents - pas de pièces jointes."""
    
    # Appel du job (email_data n'a pas d'attachments)
    result = process_envoi_documents(
        courtier_id=courtier_id,
        email_data=email_data,
        classification=classification_envoi_documents
    )
    
    # Vérifications
    assert result["status"] == "success"
    assert result["pieces_traitees"] == 0
    assert result["pieces_non_reconnues"] == 0


# =============================================================================
# TESTS - MODIFIER LISTE
# =============================================================================

@patch('app.workers.jobs.MistralService')
def test_process_modifier_liste_success(
    mock_mistral,
    courtier_id,
    email_data,
    classification_modifier_liste
):
    """Test modification liste - succès."""
    
    # Mock MistralService
    mock_mistral_instance = Mock()
    mock_mistral_instance.extract_pieces_from_text_sync.return_value = [
        {"nom_piece": "Attestation employeur", "categorie": "revenus"},
        {"nom_piece": "RIB", "categorie": "bancaire"}
    ]
    mock_mistral.return_value = mock_mistral_instance
    
    # Appel du job
    result = process_modifier_liste(
        courtier_id=courtier_id,
        email_data=email_data,
        classification=classification_modifier_liste
    )
    
    # Vérifications
    assert result["status"] == "success"
    assert result["pieces_ajoutees"] == 2
    assert result["pieces_retirees"] == 0
    assert len(result["ajoutees"]) == 2
    assert "Attestation employeur" in result["ajoutees"]
    
    # Vérifier que extract_pieces_from_text_sync a été appelé
    mock_mistral_instance.extract_pieces_from_text_sync.assert_called_once()


@patch('app.workers.jobs.MistralService')
def test_process_modifier_liste_retirer_pieces(
    mock_mistral,
    courtier_id,
    email_data
):
    """Test modification liste - retirer des pièces."""
    
    classification_retrait = {
        "action": "MODIFIER_LISTE",
        "resume": "Retrait de pièces",
        "confiance": 0.9,
        "details": {
            "client_nom": "Martin",
            "pieces_a_ajouter": [],
            "pieces_a_retirer": ["Ancien document", "Pièce obsolète"]
        }
    }
    
    # Appel du job
    result = process_modifier_liste(
        courtier_id=courtier_id,
        email_data=email_data,
        classification=classification_retrait
    )
    
    # Vérifications
    assert result["status"] == "success"
    assert result["pieces_ajoutees"] == 0
    assert result["pieces_retirees"] == 2
    assert len(result["retirees"]) == 2


# =============================================================================
# TESTS - HELPERS
# =============================================================================

def test_calculate_file_hash(tmp_path):
    """Test calcul hash fichier."""
    
    # Créer un fichier de test
    test_file = tmp_path / "test.txt"
    test_content = b"Hello World Test"
    test_file.write_bytes(test_content)
    
    # Calculer hash
    file_hash = calculate_file_hash(test_file)
    
    # Vérifications
    assert isinstance(file_hash, str)
    assert len(file_hash) == 64  # SHA256 = 64 caractères hex
    
    # Vérifier que le même contenu donne le même hash
    test_file2 = tmp_path / "test2.txt"
    test_file2.write_bytes(test_content)
    file_hash2 = calculate_file_hash(test_file2)
    
    assert file_hash == file_hash2


def test_calculate_file_hash_different_content(tmp_path):
    """Test que des contenus différents donnent des hash différents."""
    
    test_file1 = tmp_path / "file1.txt"
    test_file1.write_bytes(b"Content 1")
    
    test_file2 = tmp_path / "file2.txt"
    test_file2.write_bytes(b"Content 2")
    
    hash1 = calculate_file_hash(test_file1)
    hash2 = calculate_file_hash(test_file2)
    
    assert hash1 != hash2
