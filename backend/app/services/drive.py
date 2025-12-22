"""
Service d'interaction avec Google Drive.

Ce module gère l'organisation hiérarchique sur Google Drive:
- Créer dossiers courtiers et clients
- Uploader fichiers (PDFs traités)
- Télécharger fichiers (pour fusion)
- Générer liens partageables
- Structure: DOSSIERS_PRETS/Courtier_Nom/CLIENT_Nom_Prenom/fichiers
"""

import io
import json
import logging
from pathlib import Path
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from app.config import get_settings

logger = logging.getLogger(__name__)


class DriveManager:
    """
    Gère les opérations Google Drive.

    Utilise un Service Account pour authentification
    (pas besoin OAuth utilisateur).
    """

    def __init__(self):
        """
        Initialise connexion Google Drive avec Service Account.

        Le JSON credentials est stocké dans env var GOOGLE_CREDENTIALS_JSON
        """
        settings = get_settings()

        try:
            # Charger credentials depuis env var
            creds_dict = json.loads(settings.GOOGLE_CREDENTIALS_JSON)

            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )

            self.service = build('drive', 'v3', credentials=credentials)

            # ID du dossier maître (depuis config)
            self.master_folder_id = settings.GOOGLE_DRIVE_MASTER_FOLDER_ID

            logger.info(
                "DriveManager initialisé",
                extra={
                    "master_folder": self.master_folder_id
                }
            )

        except json.JSONDecodeError as e:
            logger.error(
                f"Erreur parsing GOOGLE_CREDENTIALS_JSON: {e}",
                exc_info=True
            )
            raise ValueError(
                "GOOGLE_CREDENTIALS_JSON doit être un JSON valide"
            )
        except Exception as e:
            logger.error(
                f"Erreur initialisation DriveManager: {e}",
                exc_info=True
            )
            raise

    def create_folder(
        self,
        folder_name: str,
        parent_folder_id: str
    ) -> str:
        """
        Crée un dossier dans Google Drive.

        Args:
            folder_name: Nom du dossier à créer
            parent_folder_id: ID du dossier parent

        Returns:
            ID du dossier créé

        Raises:
            RuntimeError: Si création échoue
        """
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }

            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink',
                supportsAllDrives=True
            ).execute()

            folder_id = folder.get('id')

            logger.info(
                "Dossier créé sur Drive",
                extra={
                    "folder_name": folder_name,
                    "folder_id": folder_id,
                    "parent_id": parent_folder_id
                }
            )

            return folder_id

        except Exception as e:
            logger.error(
                f"Erreur création dossier Drive: {e}",
                extra={
                    "folder_name": folder_name
                },
                exc_info=True
            )
            raise RuntimeError(f"Échec création dossier: {e}")

    def create_courtier_folder(
        self,
        courtier_nom: str,
        courtier_prenom: str
    ) -> str:
        """
        Crée le dossier d'un courtier sous le dossier maître.

        Structure: DOSSIERS_PRETS/Courtier_Nom_Prenom/

        Args:
            courtier_nom: Nom du courtier
            courtier_prenom: Prénom du courtier

        Returns:
            ID du dossier courtier créé
        """
        folder_name = f"Courtier_{courtier_prenom}_{courtier_nom}"
        return self.create_folder(folder_name, self.master_folder_id)

    def create_client_folder(
        self,
        client_nom: str,
        client_prenom: str,
        courtier_folder_id: str
    ) -> str:
        """
        Crée le dossier d'un client sous le dossier du courtier.

        Structure: .../Courtier_X/CLIENT_Nom_Prenom/

        Args:
            client_nom: Nom du client
            client_prenom: Prénom du client
            courtier_folder_id: ID dossier du courtier

        Returns:
            ID du dossier client créé
        """
        folder_name = f"CLIENT_{client_prenom}_{client_nom}"
        return self.create_folder(folder_name, courtier_folder_id)

    def upload_file(
        self,
        file_path: Path,
        folder_id: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Upload un fichier dans un dossier Drive.

        Args:
            file_path: Chemin local du fichier
            folder_id: ID du dossier destination
            filename: Nom du fichier sur Drive (si différent)

        Returns:
            ID du fichier uploadé

        Raises:
            RuntimeError: Si upload échoue
        """
        if filename is None:
            filename = file_path.name

        try:
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }

            media = MediaFileUpload(
                str(file_path),
                mimetype='application/pdf',
                resumable=True
            )

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, size',
                supportsAllDrives=True
            ).execute()

            file_id = file.get('id')
            file_size = file.get('size')

            logger.info(
                "Fichier uploadé sur Drive",
                extra={
                    "file_name": filename,
                    "file_id": file_id,
                    "size_bytes": file_size,
                    "folder_id": folder_id
                }
            )

            return file_id

        except Exception as e:
            logger.error(
                f"Erreur upload fichier Drive: {e}",
                extra={
                    "file_name": filename
                },
                exc_info=True
            )
            raise RuntimeError(f"Échec upload: {e}")

    def download_file(
        self,
        file_id: str,
        output_path: Path
    ) -> Path:
        """
        Télécharge un fichier depuis Drive.

        Utile pour récupérer un fichier existant (ex: recto carte ID)
        avant de le fusionner avec un nouveau (verso).

        Args:
            file_id: ID du fichier sur Drive
            output_path: Chemin local destination

        Returns:
            Path du fichier téléchargé

        Raises:
            RuntimeError: Si téléchargement échoue
        """
        try:
            request = self.service.files().get_media(
                fileId=file_id,
                supportsAllDrives=True
            )

            with io.FileIO(str(output_path), 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False

                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.debug(
                            f"Download progress: {int(status.progress() * 100)}%"
                        )

            logger.info(
                "Fichier téléchargé depuis Drive",
                extra={
                    "file_id": file_id,
                    "output_path": str(output_path)
                }
            )

            return output_path

        except Exception as e:
            logger.error(
                f"Erreur téléchargement Drive: {e}",
                extra={
                    "file_id": file_id
                },
                exc_info=True
            )
            raise RuntimeError(f"Échec téléchargement: {e}")

    def delete_file(self, file_id: str) -> bool:
        """
        Supprime un fichier de Drive.

        Utilisé lors de fusion (supprimer recto seul après fusion recto/verso).

        Args:
            file_id: ID du fichier à supprimer

        Returns:
            True si succès
        """
        try:
            self.service.files().delete(
                fileId=file_id,
                supportsAllDrives=True
            ).execute()

            logger.info(
                "Fichier supprimé de Drive",
                extra={"file_id": file_id}
            )
            return True

        except Exception as e:
            logger.error(
                f"Erreur suppression fichier Drive: {e}",
                extra={"file_id": file_id},
                exc_info=True
            )
            return False

    def get_shareable_link(self, file_id: str) -> str:
        """
        Génère un lien de partage pour un fichier.

        Permissions: Lecture pour toute personne ayant le lien.

        Args:
            file_id: ID du fichier

        Returns:
            URL de partage
        """
        try:
            # Créer permission "anyone with link can view"
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }

            self.service.permissions().create(
                fileId=file_id,
                body=permission,
                supportsAllDrives=True
            ).execute()

            # Récupérer le lien
            file = self.service.files().get(
                fileId=file_id,
                fields='webViewLink',
                supportsAllDrives=True
            ).execute()

            link = file.get('webViewLink')

            logger.info(
                "Lien partageable généré",
                extra={
                    "file_id": file_id,
                    "link": link
                }
            )

            return link

        except Exception as e:
            logger.error(
                f"Erreur génération lien: {e}",
                extra={"file_id": file_id},
                exc_info=True
            )
            return f"https://drive.google.com/file/d/{file_id}/view"

    def list_files_in_folder(
        self,
        folder_id: str,
        mime_type: Optional[str] = None
    ) -> list[dict]:
        """
        Liste les fichiers dans un dossier.

        Args:
            folder_id: ID du dossier
            mime_type: Filtrer par type MIME (optionnel)

        Returns:
            Liste de dicts avec id, name, mimeType
        """
        try:
            query = f"'{folder_id}' in parents and trashed=false"

            if mime_type:
                query += f" and mimeType='{mime_type}'"

            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, size, createdTime)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            files = results.get('files', [])

            logger.info(
                "Fichiers listés",
                extra={
                    "folder_id": folder_id,
                    "count": len(files)
                }
            )

            return files

        except Exception as e:
            logger.error(
                f"Erreur listing fichiers: {e}",
                extra={"folder_id": folder_id},
                exc_info=True
            )
            return []

    def find_file_by_name(
        self,
        filename: str,
        folder_id: str
    ) -> Optional[str]:
        """
        Cherche un fichier par nom dans un dossier.

        Utile pour détecter si un fichier existe déjà
        (ex: "Dupont_Jean_Carte_Identite_Recto.pdf").

        Args:
            filename: Nom exact du fichier
            folder_id: ID du dossier où chercher

        Returns:
            ID du fichier si trouvé, None sinon
        """
        try:
            query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"

            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            files = results.get('files', [])

            if files:
                file_id = files[0]['id']
                logger.info(
                    "Fichier trouvé",
                    extra={
                        "file_name": filename,
                        "file_id": file_id
                    }
                )
                return file_id

            return None

        except Exception as e:
            logger.error(
                f"Erreur recherche fichier: {e}",
                extra={"file_name": filename},
                exc_info=True
            )
            return None

    def folder_exists(
        self,
        folder_name: str,
        parent_folder_id: str
    ) -> Optional[str]:
        """
        Vérifie si un dossier existe déjà.

        Args:
            folder_name: Nom du dossier
            parent_folder_id: ID du dossier parent

        Returns:
            ID du dossier si trouvé, None sinon
        """
        try:
            query = (
                f"name='{folder_name}' and "
                f"'{parent_folder_id}' in parents and "
                f"mimeType='application/vnd.google-apps.folder' and "
                f"trashed=false"
            )

            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            files = results.get('files', [])

            if files:
                folder_id = files[0]['id']
                logger.info(
                    "Dossier déjà existant",
                    extra={
                        "folder_name": folder_name,
                        "folder_id": folder_id
                    }
                )
                return folder_id

            return None

        except Exception as e:
            logger.error(
                f"Erreur vérification dossier: {e}",
                extra={"folder_name": folder_name},
                exc_info=True
            )
            return None

    def get_or_create_folder(
        self,
        folder_name: str,
        parent_folder_id: str
    ) -> str:
        """
        Récupère l'ID d'un dossier existant ou le crée.

        Args:
            folder_name: Nom du dossier
            parent_folder_id: ID du dossier parent

        Returns:
            ID du dossier (existant ou créé)
        """
        # Vérifier si existe
        existing_id = self.folder_exists(folder_name, parent_folder_id)

        if existing_id:
            return existing_id

        # Créer si n'existe pas
        return self.create_folder(folder_name, parent_folder_id)

    def update_file(
        self,
        file_id: str,
        new_file_path: Path
    ) -> str:
        """
        Met à jour le contenu d'un fichier existant sur Google Drive.

        Remplace le contenu du fichier tout en conservant le même file_id.
        Utile pour mettre à jour les rapports sans créer de duplicatas.

        Args:
            file_id: ID du fichier à mettre à jour
            new_file_path: Chemin vers le nouveau fichier local

        Returns:
            ID du fichier mis à jour (même que file_id)

        Raises:
            RuntimeError: Si mise à jour échoue
        """
        try:
            # Créer media upload
            media = MediaFileUpload(
                str(new_file_path),
                resumable=True
            )

            # Mettre à jour le fichier
            updated_file = self.service.files().update(
                fileId=file_id,
                media_body=media,
                supportsAllDrives=True
            ).execute()

            logger.info(
                "Fichier mis à jour sur Drive",
                extra={
                    "file_id": file_id,
                    "file_name": updated_file.get('name'),
                    "size": new_file_path.stat().st_size
                }
            )

            return file_id

        except Exception as e:
            logger.error(
                f"Erreur mise à jour fichier: {e}",
                extra={
                    "file_id": file_id,
                    "local_path": str(new_file_path)
                },
                exc_info=True
            )
            raise RuntimeError(f"Échec mise à jour fichier Drive: {e}")
