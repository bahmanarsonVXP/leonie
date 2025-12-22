"""
Service de traitement des documents.

Ce module gère la conversion, compression, fusion et manipulation
des fichiers PDF et images pour le projet Léonie.
"""

import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image
from pypdf import PdfReader, PdfWriter

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Service de traitement des documents.

    Fournit des méthodes pour convertir, compresser, fusionner et analyser
    des documents PDF et images.
    """

    def __init__(self, temp_dir: Optional[str] = None, max_file_size_mb: int = 10, target_pdf_size_mb: float = 1.8):
        """
        Initialise le service de traitement de documents.

        Args:
            temp_dir: Répertoire temporaire pour les conversions. Si None, utilise tempfile.
            max_file_size_mb: Taille maximale d'un fichier en entrée (MB).
            target_pdf_size_mb: Taille cible pour la compression PDF (MB).
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.max_file_size_mb = max_file_size_mb
        self.target_pdf_size_mb = target_pdf_size_mb

        # Créer le répertoire temporaire si nécessaire
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)

        logger.info(
            f"DocumentProcessor initialisé",
            extra={
                "temp_dir": self.temp_dir,
                "max_file_size_mb": max_file_size_mb,
                "target_pdf_size_mb": target_pdf_size_mb
            }
        )

    def convert_to_pdf(self, file_path: str) -> Optional[str]:
        """
        Convertit un fichier en PDF.

        Supporte:
        - Images: JPG, PNG, GIF, BMP, TIFF, WEBP, HEIC (si pillow-heif installé)
        - Documents Office: DOCX, XLSX, PPTX, DOC, XLS, PPT (via LibreOffice)
        - PDF: Retourne le chemin sans conversion

        Args:
            file_path: Chemin du fichier à convertir.

        Returns:
            Chemin du PDF généré, ou None en cas d'erreur.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
            ValueError: Si le format n'est pas supporté ou fichier trop gros.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {file_path}")

        # Vérification taille
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise ValueError(
                f"Fichier trop gros: {file_size_mb:.2f} MB "
                f"(limite: {self.max_file_size_mb} MB)"
            )

        extension = file_path.suffix.lower()

        logger.info(
            f"Conversion en PDF demandée",
            extra={
                "file": file_path.name,
                "extension": extension,
                "size_mb": f"{file_size_mb:.2f}"
            }
        )

        # Si déjà PDF, retourner le chemin
        if extension == ".pdf":
            logger.info("Fichier déjà au format PDF")
            return str(file_path)

        # Images
        if extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".heic"]:
            if extension == ".heic" and not HEIF_SUPPORT:
                raise ValueError(
                    "Format HEIC non supporté. Installer pillow-heif: pip install pillow-heif"
                )
            return self._convert_image_to_pdf(file_path)

        # Documents Office
        if extension in [".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".odt", ".ods", ".odp"]:
            return self._convert_office_to_pdf(file_path)

        raise ValueError(f"Format de fichier non supporté: {extension}")

    def _convert_image_to_pdf(self, image_path: Path) -> str:
        """
        Convertit une image en PDF.

        Args:
            image_path: Chemin de l'image.

        Returns:
            Chemin du PDF généré.
        """
        try:
            # Ouvrir l'image avec Pillow
            img = Image.open(image_path)

            # Convertir en RGB si nécessaire (pour PNG avec transparence, etc.)
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Générer le nom du fichier PDF
            pdf_path = Path(self.temp_dir) / f"{image_path.stem}_converted.pdf"

            # Sauvegarder en PDF
            img.save(pdf_path, "PDF", resolution=100.0)

            logger.info(
                f"Image convertie en PDF",
                extra={
                    "input": image_path.name,
                    "output": pdf_path.name,
                    "size_kb": f"{pdf_path.stat().st_size / 1024:.2f}"
                }
            )

            return str(pdf_path)

        except Exception as e:
            logger.error(
                f"Erreur lors de la conversion d'image en PDF: {e}",
                exc_info=True
            )
            return None

    def _convert_office_to_pdf(self, office_path: Path) -> str:
        """
        Convertit un document Office en PDF via LibreOffice.

        Args:
            office_path: Chemin du document Office.

        Returns:
            Chemin du PDF généré.

        Raises:
            RuntimeError: Si LibreOffice n'est pas installé ou la conversion échoue.
        """
        try:
            # Vérifier que LibreOffice est installé
            libreoffice_cmd = self._get_libreoffice_command()
            if not libreoffice_cmd:
                raise RuntimeError(
                    "LibreOffice n'est pas installé. "
                    "Installer avec: sudo apt-get install libreoffice (Linux) "
                    "ou brew install --cask libreoffice (macOS)"
                )

            # Créer un répertoire temporaire pour la sortie
            output_dir = Path(self.temp_dir)

            # Commande LibreOffice pour conversion
            cmd = [
                libreoffice_cmd,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(output_dir),
                str(office_path)
            ]

            logger.info(f"Conversion Office en PDF: {' '.join(cmd)}")

            # Exécuter la conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # Timeout de 60 secondes
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Erreur LibreOffice: {result.stderr}"
                )

            # Le PDF généré a le même nom que le fichier d'entrée
            pdf_path = output_dir / f"{office_path.stem}.pdf"

            if not pdf_path.exists():
                raise RuntimeError(
                    f"PDF non généré par LibreOffice: {pdf_path}"
                )

            logger.info(
                f"Document Office converti en PDF",
                extra={
                    "input": office_path.name,
                    "output": pdf_path.name,
                    "size_kb": f"{pdf_path.stat().st_size / 1024:.2f}"
                }
            )

            return str(pdf_path)

        except subprocess.TimeoutExpired:
            logger.error("Timeout lors de la conversion LibreOffice")
            raise RuntimeError("Conversion LibreOffice timeout (>60s)")
        except Exception as e:
            logger.error(
                f"Erreur lors de la conversion Office en PDF: {e}",
                exc_info=True
            )
            raise

    def _get_libreoffice_command(self) -> Optional[str]:
        """
        Détecte la commande LibreOffice disponible sur le système.

        Returns:
            Commande LibreOffice, ou None si non trouvé.
        """
        # Chemins possibles pour LibreOffice
        possible_commands = [
            "libreoffice",
            "/usr/bin/libreoffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "soffice"
        ]

        for cmd in possible_commands:
            if shutil.which(cmd) or Path(cmd).exists():
                return cmd

        return None

    def compress_pdf(self, pdf_path: str, target_size_mb: Optional[float] = None) -> str:
        """
        Compresse un fichier PDF pour réduire sa taille.

        Utilise Ghostscript avec deux niveaux de compression:
        1. /ebook (qualité moyenne, ~150 DPI)
        2. /screen (basse qualité, ~72 DPI) si /ebook dépasse encore la cible

        Args:
            pdf_path: Chemin du PDF à compresser.
            target_size_mb: Taille cible en MB. Si None, utilise self.target_pdf_size_mb.

        Returns:
            Chemin du PDF compressé.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
            RuntimeError: Si Ghostscript n'est pas installé.
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"Fichier PDF non trouvé: {pdf_path}")

        target_size_mb = target_size_mb or self.target_pdf_size_mb

        # Taille actuelle
        current_size_mb = pdf_path.stat().st_size / (1024 * 1024)

        logger.info(
            f"Compression PDF demandée",
            extra={
                "file": pdf_path.name,
                "current_size_mb": f"{current_size_mb:.2f}",
                "target_size_mb": f"{target_size_mb:.2f}"
            }
        )

        # Si déjà sous la taille cible, retourner le fichier original
        if current_size_mb <= target_size_mb:
            logger.info(f"PDF déjà sous la taille cible ({current_size_mb:.2f} MB)")
            return str(pdf_path)

        # Vérifier que Ghostscript est installé
        gs_cmd = self._get_ghostscript_command()
        if not gs_cmd:
            raise RuntimeError(
                "Ghostscript n'est pas installé. "
                "Installer avec: sudo apt-get install ghostscript (Linux) "
                "ou brew install ghostscript (macOS)"
            )

        # Essayer compression /ebook d'abord
        compressed_path = self._compress_with_ghostscript(
            pdf_path, gs_cmd, quality="ebook"
        )

        compressed_size_mb = Path(compressed_path).stat().st_size / (1024 * 1024)

        # Si encore trop gros, essayer /screen
        if compressed_size_mb > target_size_mb:
            logger.warning(
                f"Compression /ebook insuffisante ({compressed_size_mb:.2f} MB), "
                f"tentative avec /screen"
            )
            compressed_path = self._compress_with_ghostscript(
                pdf_path, gs_cmd, quality="screen"
            )
            compressed_size_mb = Path(compressed_path).stat().st_size / (1024 * 1024)

        logger.info(
            f"PDF compressé",
            extra={
                "original_size_mb": f"{current_size_mb:.2f}",
                "compressed_size_mb": f"{compressed_size_mb:.2f}",
                "reduction_pct": f"{(1 - compressed_size_mb / current_size_mb) * 100:.1f}"
            }
        )

        return compressed_path

    def _get_ghostscript_command(self) -> Optional[str]:
        """
        Détecte la commande Ghostscript disponible sur le système.

        Returns:
            Commande Ghostscript, ou None si non trouvé.
        """
        possible_commands = ["gs", "ghostscript"]

        for cmd in possible_commands:
            if shutil.which(cmd):
                return cmd

        return None

    def _compress_with_ghostscript(
        self, pdf_path: Path, gs_cmd: str, quality: str = "ebook"
    ) -> str:
        """
        Compresse un PDF avec Ghostscript.

        Args:
            pdf_path: Chemin du PDF.
            gs_cmd: Commande Ghostscript.
            quality: Niveau de qualité ("ebook" ou "screen").

        Returns:
            Chemin du PDF compressé.
        """
        output_path = Path(self.temp_dir) / f"{pdf_path.stem}_compressed_{quality}.pdf"

        cmd = [
            gs_cmd,
            "-sDEVICE=pdfwrite",
            f"-dPDFSETTINGS=/{quality}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            "-dCompatibilityLevel=1.4",
            f"-sOutputFile={output_path}",
            str(pdf_path)
        ]

        logger.debug(f"Compression Ghostscript /{quality}: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Erreur Ghostscript: {result.stderr}"
                )

            if not output_path.exists():
                raise RuntimeError(
                    f"PDF compressé non généré: {output_path}"
                )

            return str(output_path)

        except subprocess.TimeoutExpired:
            logger.error("Timeout lors de la compression Ghostscript")
            raise RuntimeError("Compression Ghostscript timeout (>120s)")
        except Exception as e:
            logger.error(
                f"Erreur lors de la compression Ghostscript: {e}",
                exc_info=True
            )
            raise

    def merge_pdfs(
        self,
        pdf_paths: List[str],
        output_path: str,
        recto_verso: bool = False,
        sort_chronological: bool = False
    ) -> str:
        """
        Fusionne plusieurs PDFs en un seul.

        Args:
            pdf_paths: Liste des chemins des PDFs à fusionner.
            output_path: Chemin du PDF de sortie.
            recto_verso: Si True, fusionne les PDFs en alternant recto/verso
                        (utile pour bulletins de salaire scannés recto puis verso).
            sort_chronological: Si True, trie les PDFs par date de modification.

        Returns:
            Chemin du PDF fusionné.

        Raises:
            ValueError: Si la liste de PDFs est vide.
            FileNotFoundError: Si un PDF n'existe pas.
        """
        if not pdf_paths:
            raise ValueError("Liste de PDFs vide")

        # Vérifier que tous les fichiers existent
        for pdf_path in pdf_paths:
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF non trouvé: {pdf_path}")

        logger.info(
            f"Fusion de {len(pdf_paths)} PDFs",
            extra={
                "recto_verso": recto_verso,
                "sort_chronological": sort_chronological
            }
        )

        # Tri chronologique si demandé
        if sort_chronological:
            pdf_paths = sorted(
                pdf_paths,
                key=lambda p: Path(p).stat().st_mtime
            )
            logger.debug(
                f"PDFs triés par date: {[Path(p).name for p in pdf_paths]}"
            )

        # Créer le writer
        writer = PdfWriter()

        if recto_verso:
            # Mode recto/verso: fusionner page par page en alternance
            # Exemple: [doc1_p1, doc2_p1, doc1_p2, doc2_p2, ...]
            readers = [PdfReader(pdf_path) for pdf_path in pdf_paths]
            max_pages = max(len(reader.pages) for reader in readers)

            for page_idx in range(max_pages):
                for reader in readers:
                    if page_idx < len(reader.pages):
                        writer.add_page(reader.pages[page_idx])
        else:
            # Mode normal: fusionner PDF par PDF
            for pdf_path in pdf_paths:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    writer.add_page(page)

        # Écrire le PDF fusionné
        output_path = Path(output_path)
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        logger.info(
            f"PDFs fusionnés",
            extra={
                "output": output_path.name,
                "total_pages": len(writer.pages),
                "size_kb": f"{output_path.stat().st_size / 1024:.2f}"
            }
        )

        return str(output_path)

    def calculate_file_hash(self, file_path: str) -> str:
        """
        Calcule le hash SHA256 d'un fichier.

        Utile pour détecter les doublons de fichiers.

        Args:
            file_path: Chemin du fichier.

        Returns:
            Hash SHA256 du fichier (hexadécimal).

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {file_path}")

        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Lire par blocs de 64 KB
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)

        hash_hex = sha256_hash.hexdigest()

        logger.debug(
            f"Hash calculé pour {file_path.name}: {hash_hex[:16]}..."
        )

        return hash_hex

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extrait le texte d'un PDF.

        Args:
            pdf_path: Chemin du PDF.

        Returns:
            Texte extrait du PDF.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF non trouvé: {pdf_path}")

        try:
            reader = PdfReader(pdf_path)

            text_parts = []
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            full_text = "\n\n".join(text_parts)

            logger.info(
                f"Texte extrait du PDF",
                extra={
                    "file": pdf_path.name,
                    "pages": len(reader.pages),
                    "chars": len(full_text)
                }
            )

            return full_text

        except Exception as e:
            logger.error(
                f"Erreur lors de l'extraction de texte: {e}",
                exc_info=True
            )
            return ""

    def get_pdf_page_count(self, pdf_path: str) -> int:
        """
        Compte le nombre de pages d'un PDF.

        Args:
            pdf_path: Chemin du PDF.

        Returns:
            Nombre de pages.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF non trouvé: {pdf_path}")

        try:
            reader = PdfReader(pdf_path)
            page_count = len(reader.pages)

            logger.debug(
                f"PDF {pdf_path.name}: {page_count} page(s)"
            )

            return page_count

        except Exception as e:
            logger.error(
                f"Erreur lors du comptage de pages: {e}",
                exc_info=True
            )
            return 0
