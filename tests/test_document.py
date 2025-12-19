"""
Tests unitaires pour le service de traitement de documents.

Ce module teste les fonctionnalités du DocumentProcessor:
- Conversion en PDF (images, documents Office)
- Compression PDF
- Fusion de PDFs
- Extraction de texte
- Calcul de hash
"""

import os
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from app.services.document import DocumentProcessor


@pytest.fixture
def temp_dir():
    """Crée un répertoire temporaire pour les tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def processor(temp_dir):
    """Crée une instance de DocumentProcessor pour les tests."""
    return DocumentProcessor(
        temp_dir=temp_dir,
        max_file_size_mb=10,
        target_pdf_size_mb=1.8
    )


@pytest.fixture
def sample_image(temp_dir):
    """Crée une image de test."""
    img_path = Path(temp_dir) / "test_image.jpg"

    # Créer une image RGB de 800x600
    img = Image.new("RGB", (800, 600), color=(73, 109, 137))
    img.save(img_path, "JPEG")

    return str(img_path)


@pytest.fixture
def sample_png_with_alpha(temp_dir):
    """Crée une image PNG avec transparence pour tester la conversion."""
    img_path = Path(temp_dir) / "test_alpha.png"

    # Créer une image RGBA
    img = Image.new("RGBA", (400, 400), color=(255, 0, 0, 128))
    img.save(img_path, "PNG")

    return str(img_path)


class TestDocumentProcessor:
    """Tests pour la classe DocumentProcessor."""

    def test_initialization(self, temp_dir):
        """Test l'initialisation du DocumentProcessor."""
        processor = DocumentProcessor(
            temp_dir=temp_dir,
            max_file_size_mb=5,
            target_pdf_size_mb=2.0
        )

        assert processor.temp_dir == temp_dir
        assert processor.max_file_size_mb == 5
        assert processor.target_pdf_size_mb == 2.0
        assert Path(temp_dir).exists()

    def test_calculate_file_hash(self, processor, sample_image):
        """Test le calcul du hash SHA256."""
        hash1 = processor.calculate_file_hash(sample_image)
        hash2 = processor.calculate_file_hash(sample_image)

        # Le hash doit être identique pour le même fichier
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 = 64 caractères hexa

    def test_calculate_file_hash_nonexistent(self, processor):
        """Test le calcul de hash sur un fichier inexistant."""
        with pytest.raises(FileNotFoundError):
            processor.calculate_file_hash("/nonexistent/file.pdf")

    def test_convert_image_to_pdf(self, processor, sample_image):
        """Test la conversion d'une image JPG en PDF."""
        pdf_path = processor.convert_to_pdf(sample_image)

        assert pdf_path is not None
        assert Path(pdf_path).exists()
        assert Path(pdf_path).suffix == ".pdf"

        # Vérifier que c'est un PDF valide
        page_count = processor.get_pdf_page_count(pdf_path)
        assert page_count == 1

    def test_convert_png_with_alpha_to_pdf(self, processor, sample_png_with_alpha):
        """Test la conversion d'un PNG avec transparence en PDF."""
        pdf_path = processor.convert_to_pdf(sample_png_with_alpha)

        assert pdf_path is not None
        assert Path(pdf_path).exists()
        assert Path(pdf_path).suffix == ".pdf"

    def test_convert_pdf_returns_same_path(self, processor, temp_dir):
        """Test que la conversion d'un PDF retourne le même chemin."""
        # Créer un PDF factice
        pdf_path = Path(temp_dir) / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")

        result = processor.convert_to_pdf(str(pdf_path))
        assert result == str(pdf_path)

    def test_convert_unsupported_format(self, processor, temp_dir):
        """Test la conversion d'un format non supporté."""
        unsupported_path = Path(temp_dir) / "test.xyz"
        unsupported_path.write_text("test content")

        with pytest.raises(ValueError, match="Format de fichier non supporté"):
            processor.convert_to_pdf(str(unsupported_path))

    def test_convert_nonexistent_file(self, processor):
        """Test la conversion d'un fichier inexistant."""
        with pytest.raises(FileNotFoundError):
            processor.convert_to_pdf("/nonexistent/file.jpg")

    def test_convert_file_too_large(self, processor, temp_dir):
        """Test la conversion d'un fichier trop gros."""
        large_file = Path(temp_dir) / "large.jpg"

        # Créer un fichier de 11 MB (dépasse max_file_size_mb=10)
        large_file.write_bytes(b"0" * (11 * 1024 * 1024))

        with pytest.raises(ValueError, match="Fichier trop gros"):
            processor.convert_to_pdf(str(large_file))

    def test_get_pdf_page_count(self, processor, sample_image):
        """Test le comptage de pages d'un PDF."""
        pdf_path = processor.convert_to_pdf(sample_image)
        page_count = processor.get_pdf_page_count(pdf_path)

        assert page_count == 1

    def test_get_pdf_page_count_nonexistent(self, processor):
        """Test le comptage de pages sur un fichier inexistant."""
        with pytest.raises(FileNotFoundError):
            processor.get_pdf_page_count("/nonexistent/file.pdf")

    def test_extract_text_from_pdf(self, processor, sample_image):
        """Test l'extraction de texte d'un PDF."""
        # Créer un PDF depuis une image (pas de texte attendu)
        pdf_path = processor.convert_to_pdf(sample_image)
        text = processor.extract_text_from_pdf(pdf_path)

        # Une image convertie en PDF n'a généralement pas de texte
        assert isinstance(text, str)

    def test_extract_text_nonexistent(self, processor):
        """Test l'extraction de texte sur un fichier inexistant."""
        with pytest.raises(FileNotFoundError):
            processor.extract_text_from_pdf("/nonexistent/file.pdf")

    def test_compress_pdf_already_small(self, processor, sample_image):
        """Test la compression d'un PDF déjà sous la taille cible."""
        pdf_path = processor.convert_to_pdf(sample_image)

        # Forcer une petite taille cible
        processor.target_pdf_size_mb = 10.0  # 10 MB, bien au-dessus du fichier de test

        compressed_path = processor.compress_pdf(pdf_path)

        # Si déjà petit, devrait retourner le même chemin
        # (ou un chemin compressé si Ghostscript est installé)
        assert compressed_path is not None

    def test_compress_pdf_nonexistent(self, processor):
        """Test la compression d'un fichier inexistant."""
        with pytest.raises(FileNotFoundError):
            processor.compress_pdf("/nonexistent/file.pdf")

    def test_merge_pdfs_simple(self, processor, sample_image, temp_dir):
        """Test la fusion de plusieurs PDFs."""
        # Créer 2 PDFs
        pdf1 = processor.convert_to_pdf(sample_image)

        # Créer une deuxième image
        img2_path = Path(temp_dir) / "test_image2.jpg"
        img2 = Image.new("RGB", (600, 400), color=(200, 100, 50))
        img2.save(img2_path, "JPEG")

        pdf2 = processor.convert_to_pdf(str(img2_path))

        # Fusionner
        output_path = Path(temp_dir) / "merged.pdf"
        merged_path = processor.merge_pdfs(
            [pdf1, pdf2],
            str(output_path),
            recto_verso=False,
            sort_chronological=False
        )

        assert Path(merged_path).exists()

        # Vérifier qu'on a 2 pages
        page_count = processor.get_pdf_page_count(merged_path)
        assert page_count == 2

    def test_merge_pdfs_empty_list(self, processor):
        """Test la fusion avec une liste vide."""
        with pytest.raises(ValueError, match="Liste de PDFs vide"):
            processor.merge_pdfs([], "/tmp/output.pdf")

    def test_merge_pdfs_nonexistent(self, processor):
        """Test la fusion avec un fichier inexistant."""
        with pytest.raises(FileNotFoundError):
            processor.merge_pdfs(
                ["/nonexistent/file1.pdf", "/nonexistent/file2.pdf"],
                "/tmp/output.pdf"
            )

    def test_merge_pdfs_recto_verso(self, processor, sample_image, temp_dir):
        """Test la fusion en mode recto/verso."""
        # Créer 2 PDFs
        pdf1 = processor.convert_to_pdf(sample_image)

        img2_path = Path(temp_dir) / "test_image2.jpg"
        img2 = Image.new("RGB", (600, 400), color=(200, 100, 50))
        img2.save(img2_path, "JPEG")
        pdf2 = processor.convert_to_pdf(str(img2_path))

        # Fusionner en mode recto/verso
        output_path = Path(temp_dir) / "merged_rv.pdf"
        merged_path = processor.merge_pdfs(
            [pdf1, pdf2],
            str(output_path),
            recto_verso=True
        )

        assert Path(merged_path).exists()
        page_count = processor.get_pdf_page_count(merged_path)
        assert page_count == 2

    def test_libreoffice_command_detection(self, processor):
        """Test la détection de LibreOffice."""
        cmd = processor._get_libreoffice_command()

        # Soit LibreOffice est installé, soit None
        if cmd:
            assert isinstance(cmd, str)
        else:
            assert cmd is None

    def test_ghostscript_command_detection(self, processor):
        """Test la détection de Ghostscript."""
        cmd = processor._get_ghostscript_command()

        # Soit Ghostscript est installé, soit None
        if cmd:
            assert isinstance(cmd, str)
        else:
            assert cmd is None


class TestDocumentProcessorIntegration:
    """Tests d'intégration pour le workflow complet."""

    def test_full_workflow_image_to_compressed_pdf(
        self, processor, sample_image, temp_dir
    ):
        """Test le workflow complet: image -> PDF -> compression -> extraction."""
        # 1. Calculer le hash original
        original_hash = processor.calculate_file_hash(sample_image)
        assert len(original_hash) == 64

        # 2. Convertir en PDF
        pdf_path = processor.convert_to_pdf(sample_image)
        assert Path(pdf_path).exists()

        # 3. Compter les pages
        page_count = processor.get_pdf_page_count(pdf_path)
        assert page_count == 1

        # 4. Extraire le texte
        text = processor.extract_text_from_pdf(pdf_path)
        assert isinstance(text, str)

        # 5. Compresser (si Ghostscript installé)
        try:
            compressed_path = processor.compress_pdf(pdf_path)
            assert Path(compressed_path).exists()
        except RuntimeError:
            # Ghostscript pas installé, skip
            pytest.skip("Ghostscript non installé")

    def test_merge_multiple_images(self, processor, temp_dir):
        """Test la fusion de plusieurs images converties en PDF."""
        # Créer 3 images de couleurs différentes
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        pdf_paths = []

        for idx, color in enumerate(colors):
            img_path = Path(temp_dir) / f"image_{idx}.jpg"
            img = Image.new("RGB", (400, 300), color=color)
            img.save(img_path, "JPEG")

            pdf_path = processor.convert_to_pdf(str(img_path))
            pdf_paths.append(pdf_path)

        # Fusionner
        output_path = Path(temp_dir) / "merged_colors.pdf"
        merged_path = processor.merge_pdfs(
            pdf_paths,
            str(output_path),
            sort_chronological=False
        )

        assert Path(merged_path).exists()

        # Vérifier 3 pages
        page_count = processor.get_pdf_page_count(merged_path)
        assert page_count == 3


# ==============================================================================
# Tests de performance (optionnels, à lancer manuellement)
# ==============================================================================

@pytest.mark.slow
def test_performance_large_image(temp_dir):
    """Test la conversion d'une grande image (optionnel)."""
    processor = DocumentProcessor(temp_dir=temp_dir)

    # Créer une grande image (5000x5000)
    large_img_path = Path(temp_dir) / "large_image.jpg"
    img = Image.new("RGB", (5000, 5000), color=(100, 150, 200))
    img.save(large_img_path, "JPEG", quality=95)

    # Convertir et mesurer le temps
    import time
    start = time.time()
    pdf_path = processor.convert_to_pdf(str(large_img_path))
    duration = time.time() - start

    assert Path(pdf_path).exists()
    print(f"Conversion grande image: {duration:.2f}s")


@pytest.mark.slow
def test_performance_compression(temp_dir):
    """Test la compression d'un grand PDF (optionnel)."""
    processor = DocumentProcessor(temp_dir=temp_dir)

    # Créer plusieurs images pour générer un PDF volumineux
    pdf_paths = []
    for i in range(10):
        img_path = Path(temp_dir) / f"perf_{i}.jpg"
        img = Image.new("RGB", (2000, 1500), color=(i*20, i*15, i*10))
        img.save(img_path, "JPEG", quality=95)
        pdf_paths.append(processor.convert_to_pdf(str(img_path)))

    # Fusionner en un gros PDF
    merged_path = Path(temp_dir) / "large.pdf"
    final_pdf = processor.merge_pdfs(pdf_paths, str(merged_path))

    # Tester la compression
    try:
        import time
        start = time.time()
        compressed_path = processor.compress_pdf(final_pdf)
        duration = time.time() - start

        original_size = Path(final_pdf).stat().st_size / (1024 * 1024)
        compressed_size = Path(compressed_path).stat().st_size / (1024 * 1024)

        print(f"Compression: {original_size:.2f} MB -> {compressed_size:.2f} MB en {duration:.2f}s")
        assert compressed_size <= original_size
    except RuntimeError:
        pytest.skip("Ghostscript non installé")
