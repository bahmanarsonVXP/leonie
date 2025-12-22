"""
Tests unitaires pour le service Google Drive.

Ce module teste les fonctionnalités du DriveManager:
- Création de dossiers (courtiers, clients)
- Upload de fichiers
- Téléchargement de fichiers
- Génération de liens partageables
- Recherche de fichiers/dossiers
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.services.drive import DriveManager


@pytest.fixture
def mock_credentials():
    """Mock des credentials Google."""
    return {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test"
    }


@pytest.fixture
def mock_settings(mock_credentials):
    """Mock des settings."""
    with patch('app.services.drive.get_settings') as mock_get_settings:
        mock_settings_obj = Mock()
        mock_settings_obj.GOOGLE_CREDENTIALS_JSON = json.dumps(mock_credentials)
        mock_settings_obj.GOOGLE_DRIVE_MASTER_FOLDER_ID = "test-master-folder-id"
        mock_get_settings.return_value = mock_settings_obj
        yield mock_settings_obj


@pytest.fixture
def mock_drive_service():
    """Mock du service Google Drive."""
    with patch('app.services.drive.build') as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        yield mock_service


@pytest.fixture
def drive_manager(mock_settings, mock_drive_service):
    """Instance de DriveManager avec mocks."""
    with patch('app.services.drive.service_account'):
        manager = DriveManager()
        manager.service = mock_drive_service
        return manager


class TestDriveManager:
    """Tests pour la classe DriveManager."""

    def test_initialization(self, mock_settings, mock_drive_service):
        """Test l'initialisation du DriveManager."""
        with patch('app.services.drive.service_account'):
            manager = DriveManager()

            assert manager.master_folder_id == "test-master-folder-id"
            assert manager.service is not None

    def test_create_folder(self, drive_manager, mock_drive_service):
        """Test la création d'un dossier."""
        # Mock de la réponse de l'API
        mock_drive_service.files().create().execute.return_value = {
            'id': 'test-folder-id',
            'name': 'Test Folder',
            'webViewLink': 'https://drive.google.com/test'
        }

        folder_id = drive_manager.create_folder("Test Folder", "parent-folder-id")

        assert folder_id == "test-folder-id"

        # Vérifier que l'API a été appelée correctement
        mock_drive_service.files().create.assert_called_once()
        call_args = mock_drive_service.files().create.call_args
        assert call_args[1]['body']['name'] == "Test Folder"
        assert call_args[1]['body']['parents'] == ["parent-folder-id"]
        assert call_args[1]['body']['mimeType'] == 'application/vnd.google-apps.folder'

    def test_create_courtier_folder(self, drive_manager, mock_drive_service):
        """Test la création d'un dossier courtier."""
        mock_drive_service.files().create().execute.return_value = {
            'id': 'courtier-folder-id',
            'name': 'Courtier_Jean_Dupont',
            'webViewLink': 'https://drive.google.com/test'
        }

        folder_id = drive_manager.create_courtier_folder("Dupont", "Jean")

        assert folder_id == "courtier-folder-id"

        # Vérifier le nom du dossier
        call_args = mock_drive_service.files().create.call_args
        assert call_args[1]['body']['name'] == "Courtier_Jean_Dupont"
        assert call_args[1]['body']['parents'] == ["test-master-folder-id"]

    def test_create_client_folder(self, drive_manager, mock_drive_service):
        """Test la création d'un dossier client."""
        mock_drive_service.files().create().execute.return_value = {
            'id': 'client-folder-id',
            'name': 'CLIENT_Marie_Martin',
            'webViewLink': 'https://drive.google.com/test'
        }

        folder_id = drive_manager.create_client_folder(
            "Martin",
            "Marie",
            "courtier-folder-id"
        )

        assert folder_id == "client-folder-id"

        # Vérifier le nom et le parent
        call_args = mock_drive_service.files().create.call_args
        assert call_args[1]['body']['name'] == "CLIENT_Marie_Martin"
        assert call_args[1]['body']['parents'] == ["courtier-folder-id"]

    def test_upload_file(self, drive_manager, mock_drive_service, tmp_path):
        """Test l'upload d'un fichier."""
        # Créer un fichier de test
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"Test PDF content")

        # Mock de la réponse
        mock_drive_service.files().create().execute.return_value = {
            'id': 'uploaded-file-id',
            'name': 'test.pdf',
            'webViewLink': 'https://drive.google.com/file/d/uploaded-file-id/view',
            'size': '16'
        }

        file_id = drive_manager.upload_file(
            test_file,
            "folder-id",
            filename="test.pdf"
        )

        assert file_id == "uploaded-file-id"

        # Vérifier l'appel
        mock_drive_service.files().create.assert_called_once()
        call_args = mock_drive_service.files().create.call_args
        assert call_args[1]['body']['name'] == "test.pdf"
        assert call_args[1]['body']['parents'] == ["folder-id"]

    def test_upload_file_default_filename(self, drive_manager, mock_drive_service, tmp_path):
        """Test l'upload avec nom de fichier par défaut."""
        test_file = tmp_path / "original_name.pdf"
        test_file.write_bytes(b"Test")

        mock_drive_service.files().create().execute.return_value = {
            'id': 'file-id',
            'name': 'original_name.pdf',
            'webViewLink': 'https://drive.google.com/file/d/file-id/view',
            'size': '4'
        }

        file_id = drive_manager.upload_file(test_file, "folder-id")

        assert file_id == "file-id"

        # Le nom devrait être celui du fichier
        call_args = mock_drive_service.files().create.call_args
        assert call_args[1]['body']['name'] == "original_name.pdf"

    def test_download_file(self, drive_manager, mock_drive_service, tmp_path):
        """Test le téléchargement d'un fichier."""
        output_path = tmp_path / "downloaded.pdf"

        # Mock du média
        mock_request = MagicMock()
        mock_drive_service.files().get_media.return_value = mock_request

        # Mock du downloader
        with patch('app.services.drive.MediaIoBaseDownload') as mock_downloader_class:
            mock_downloader = MagicMock()
            mock_downloader.next_chunk.side_effect = [
                (MagicMock(progress=lambda: 0.5), False),
                (MagicMock(progress=lambda: 1.0), True)
            ]
            mock_downloader_class.return_value = mock_downloader

            # Créer le fichier simulé
            output_path.write_bytes(b"Downloaded content")

            result = drive_manager.download_file("file-id", output_path)

            assert result == output_path
            assert output_path.exists()
            mock_drive_service.files().get_media.assert_called_once_with(fileId="file-id")

    def test_delete_file(self, drive_manager, mock_drive_service):
        """Test la suppression d'un fichier."""
        mock_drive_service.files().delete().execute.return_value = None

        result = drive_manager.delete_file("file-id-to-delete")

        assert result is True
        mock_drive_service.files().delete.assert_called_once_with(fileId="file-id-to-delete")

    def test_delete_file_error(self, drive_manager, mock_drive_service):
        """Test la suppression avec erreur."""
        mock_drive_service.files().delete().execute.side_effect = Exception("API Error")

        result = drive_manager.delete_file("file-id")

        assert result is False

    def test_get_shareable_link(self, drive_manager, mock_drive_service):
        """Test la génération d'un lien partageable."""
        # Mock création permission
        mock_drive_service.permissions().create().execute.return_value = None

        # Mock récupération du lien
        mock_drive_service.files().get().execute.return_value = {
            'webViewLink': 'https://drive.google.com/file/d/test-file-id/view'
        }

        link = drive_manager.get_shareable_link("test-file-id")

        assert link == 'https://drive.google.com/file/d/test-file-id/view'

        # Vérifier création de la permission
        mock_drive_service.permissions().create.assert_called_once()
        perm_call = mock_drive_service.permissions().create.call_args
        assert perm_call[1]['fileId'] == "test-file-id"
        assert perm_call[1]['body']['type'] == 'anyone'
        assert perm_call[1]['body']['role'] == 'reader'

    def test_get_shareable_link_error(self, drive_manager, mock_drive_service):
        """Test génération lien avec erreur."""
        mock_drive_service.permissions().create().execute.side_effect = Exception("Error")

        link = drive_manager.get_shareable_link("test-file-id")

        # Devrait retourner un lien de fallback
        assert link == "https://drive.google.com/file/d/test-file-id/view"

    def test_list_files_in_folder(self, drive_manager, mock_drive_service):
        """Test le listing de fichiers dans un dossier."""
        mock_drive_service.files().list().execute.return_value = {
            'files': [
                {
                    'id': 'file1',
                    'name': 'document1.pdf',
                    'mimeType': 'application/pdf',
                    'size': '1024',
                    'createdTime': '2025-01-01T00:00:00Z'
                },
                {
                    'id': 'file2',
                    'name': 'document2.pdf',
                    'mimeType': 'application/pdf',
                    'size': '2048',
                    'createdTime': '2025-01-02T00:00:00Z'
                }
            ]
        }

        files = drive_manager.list_files_in_folder("folder-id")

        assert len(files) == 2
        assert files[0]['id'] == 'file1'
        assert files[1]['name'] == 'document2.pdf'

        # Vérifier la requête
        call_args = mock_drive_service.files().list.call_args
        assert "'folder-id' in parents and trashed=false" in call_args[1]['q']

    def test_list_files_with_mime_filter(self, drive_manager, mock_drive_service):
        """Test le listing avec filtre MIME."""
        mock_drive_service.files().list().execute.return_value = {'files': []}

        drive_manager.list_files_in_folder("folder-id", mime_type="application/pdf")

        # Vérifier le filtre MIME dans la query
        call_args = mock_drive_service.files().list.call_args
        assert "mimeType='application/pdf'" in call_args[1]['q']

    def test_find_file_by_name(self, drive_manager, mock_drive_service):
        """Test la recherche de fichier par nom."""
        mock_drive_service.files().list().execute.return_value = {
            'files': [
                {
                    'id': 'found-file-id',
                    'name': 'searched_file.pdf'
                }
            ]
        }

        file_id = drive_manager.find_file_by_name("searched_file.pdf", "folder-id")

        assert file_id == "found-file-id"

        # Vérifier la query
        call_args = mock_drive_service.files().list.call_args
        assert "name='searched_file.pdf'" in call_args[1]['q']

    def test_find_file_by_name_not_found(self, drive_manager, mock_drive_service):
        """Test recherche fichier non trouvé."""
        mock_drive_service.files().list().execute.return_value = {'files': []}

        file_id = drive_manager.find_file_by_name("nonexistent.pdf", "folder-id")

        assert file_id is None

    def test_folder_exists(self, drive_manager, mock_drive_service):
        """Test vérification existence dossier."""
        mock_drive_service.files().list().execute.return_value = {
            'files': [
                {
                    'id': 'existing-folder-id',
                    'name': 'Existing Folder'
                }
            ]
        }

        folder_id = drive_manager.folder_exists("Existing Folder", "parent-id")

        assert folder_id == "existing-folder-id"

        # Vérifier que c'est bien un dossier
        call_args = mock_drive_service.files().list.call_args
        assert "mimeType='application/vnd.google-apps.folder'" in call_args[1]['q']

    def test_folder_exists_not_found(self, drive_manager, mock_drive_service):
        """Test dossier n'existe pas."""
        mock_drive_service.files().list().execute.return_value = {'files': []}

        folder_id = drive_manager.folder_exists("Nonexistent", "parent-id")

        assert folder_id is None

    def test_get_or_create_folder_existing(self, drive_manager, mock_drive_service):
        """Test get_or_create avec dossier existant."""
        # Mock: dossier existe déjà
        mock_drive_service.files().list().execute.return_value = {
            'files': [{'id': 'existing-id', 'name': 'Test'}]
        }

        folder_id = drive_manager.get_or_create_folder("Test", "parent-id")

        assert folder_id == "existing-id"

        # Ne devrait pas appeler create()
        mock_drive_service.files().create.assert_not_called()

    def test_get_or_create_folder_create_new(self, drive_manager, mock_drive_service):
        """Test get_or_create avec création."""
        # Mock: dossier n'existe pas
        mock_drive_service.files().list().execute.return_value = {'files': []}

        # Mock: création
        mock_drive_service.files().create().execute.return_value = {
            'id': 'new-folder-id',
            'name': 'New Folder',
            'webViewLink': 'https://drive.google.com/test'
        }

        folder_id = drive_manager.get_or_create_folder("New Folder", "parent-id")

        assert folder_id == "new-folder-id"

        # Devrait avoir appelé create()
        mock_drive_service.files().create.assert_called_once()


class TestDriveManagerErrors:
    """Tests des gestions d'erreurs."""

    def test_create_folder_error(self, drive_manager, mock_drive_service):
        """Test erreur lors création dossier."""
        mock_drive_service.files().create().execute.side_effect = Exception("API Error")

        with pytest.raises(RuntimeError, match="Échec création dossier"):
            drive_manager.create_folder("Test", "parent-id")

    def test_upload_file_error(self, drive_manager, mock_drive_service, tmp_path):
        """Test erreur lors upload."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"Test")

        mock_drive_service.files().create().execute.side_effect = Exception("Upload failed")

        with pytest.raises(RuntimeError, match="Échec upload"):
            drive_manager.upload_file(test_file, "folder-id")

    def test_download_file_error(self, drive_manager, mock_drive_service, tmp_path):
        """Test erreur lors téléchargement."""
        output_path = tmp_path / "output.pdf"

        mock_drive_service.files().get_media.side_effect = Exception("Download error")

        with pytest.raises(RuntimeError, match="Échec téléchargement"):
            drive_manager.download_file("file-id", output_path)

    def test_list_files_error(self, drive_manager, mock_drive_service):
        """Test erreur lors listing."""
        mock_drive_service.files().list().execute.side_effect = Exception("List error")

        # Ne devrait pas lever d'exception, mais retourner liste vide
        files = drive_manager.list_files_in_folder("folder-id")

        assert files == []


# ==============================================================================
# Tests d'intégration (nécessitent credentials réels, à lancer manuellement)
# ==============================================================================

@pytest.mark.integration
@pytest.mark.skip(reason="Nécessite credentials Google réels")
def test_real_drive_integration():
    """
    Test d'intégration avec Google Drive réel.

    Pour exécuter ce test:
    1. Configurer GOOGLE_CREDENTIALS_JSON et GOOGLE_DRIVE_MASTER_FOLDER_ID
    2. pytest tests/test_drive.py -m integration -v
    """
    # Ce test nécessite de vraies credentials
    drive_manager = DriveManager()

    # Test création dossier
    folder_id = drive_manager.create_folder(
        "TEST_Integration_Leonie",
        drive_manager.master_folder_id
    )
    assert folder_id is not None

    # Test upload fichier
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b"Test PDF content")
        test_file_path = Path(f.name)

    file_id = drive_manager.upload_file(
        test_file_path,
        folder_id,
        filename="test_integration.pdf"
    )
    assert file_id is not None

    # Test lien partageable
    link = drive_manager.get_shareable_link(file_id)
    assert "drive.google.com" in link

    # Nettoyage
    drive_manager.delete_file(file_id)
    test_file_path.unlink()

    print(f"✅ Test d'intégration réussi! Dossier: {folder_id}")
