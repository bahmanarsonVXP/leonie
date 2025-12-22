"""
Tests unitaires pour le service email_fetcher.

Ces tests utilisent des mocks pour éviter les vraies connexions IMAP.
"""

import email
from datetime import datetime
from email.message import Message
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.models.email import EmailAttachment, EmailData
from app.services.email_fetcher import EmailFetcher


@pytest.fixture
def mock_settings():
    """Fixture des settings mockés."""
    settings = Mock()
    settings.IMAP_HOST = "imap.gmail.com"
    settings.IMAP_PORT = 993
    settings.IMAP_EMAIL = "test@example.com"
    settings.IMAP_PASSWORD = "password"
    settings.IMAP_FOLDER = "INBOX"
    return settings


@pytest.fixture
def sample_raw_email():
    """Fixture d'un email brut simple."""
    msg = Message()
    msg["From"] = "Sophie Martin <sophie.martin@email.com>"
    msg["To"] = "leonie@voxperience.com"
    msg["Cc"] = "courtier@exemple.fr"
    msg["Subject"] = "Documents prêt immobilier"
    msg["Date"] = "Mon, 15 Jan 2024 10:30:00 +0100"
    msg["Message-ID"] = "<abc123@gmail.com>"
    msg.set_payload("Bonjour, voici mes documents pour le dossier de prêt.")
    return msg


@pytest.fixture
def sample_multipart_email():
    """Fixture d'un email multipart avec pièce jointe."""
    msg = Message()
    msg["From"] = "Jean Dupont <jean.dupont@email.com>"
    msg["To"] = "leonie@voxperience.com"
    msg["Subject"] = "Nouveau dossier client"
    msg["Date"] = "Tue, 16 Jan 2024 14:00:00 +0100"
    msg["Message-ID"] = "<def456@gmail.com>"

    # Corps de l'email (multipart)
    msg.set_type("multipart/mixed")

    # Partie texte
    text_part = Message()
    text_part.set_type("text/plain")
    text_part.set_payload("Voici les documents demandés.")
    msg.attach(text_part)

    # Partie HTML
    html_part = Message()
    html_part.set_type("text/html")
    html_part.set_payload("<p>Voici les documents demandés.</p>")
    msg.attach(html_part)

    # Pièce jointe
    attachment = Message()
    attachment.set_type("application/pdf")
    attachment.add_header("Content-Disposition", "attachment", filename="document.pdf")
    attachment.set_payload(b"fake pdf content")
    msg.attach(attachment)

    return msg


class TestEmailFetcher:
    """Tests pour la classe EmailFetcher."""

    @patch("app.services.email_fetcher.imaplib.IMAP4_SSL")
    @patch("app.services.email_fetcher.get_settings")
    def test_connect_success(self, mock_get_settings, mock_imap_class, mock_settings):
        """Test de connexion IMAP réussie."""
        # Setup
        mock_get_settings.return_value = mock_settings
        mock_imap = MagicMock()
        mock_imap_class.return_value = mock_imap

        # Exécution
        fetcher = EmailFetcher()
        result = fetcher.connect()

        # Vérifications
        assert result is True
        assert fetcher.connected is True
        mock_imap.login.assert_called_once_with(
            mock_settings.IMAP_EMAIL,
            mock_settings.IMAP_PASSWORD
        )

    @patch("app.services.email_fetcher.imaplib.IMAP4_SSL")
    @patch("app.services.email_fetcher.get_settings")
    def test_connect_failure(self, mock_get_settings, mock_imap_class, mock_settings):
        """Test d'échec de connexion IMAP après 3 tentatives."""
        # Setup
        mock_get_settings.return_value = mock_settings
        mock_imap_class.side_effect = Exception("Connection failed")

        # Exécution et vérification
        fetcher = EmailFetcher()
        with pytest.raises(Exception, match="Échec de connexion IMAP"):
            fetcher.connect()

    @patch("app.services.email_fetcher.get_settings")
    def test_parse_email_address(self, mock_get_settings, mock_settings):
        """Test du parsing d'adresse email."""
        mock_get_settings.return_value = mock_settings
        fetcher = EmailFetcher()

        # Test avec nom et email
        addr, name = fetcher._parse_email_address("John Doe <john@example.com>")
        assert addr == "john@example.com"
        assert name == "John Doe"

        # Test avec email seul
        addr, name = fetcher._parse_email_address("jane@example.com")
        assert addr == "jane@example.com"
        assert name is None

        # Test avec header vide
        addr, name = fetcher._parse_email_address("")
        assert addr == "unknown@unknown.com"
        assert name is None

    @patch("app.services.email_fetcher.get_settings")
    def test_parse_email_list(self, mock_get_settings, mock_settings):
        """Test du parsing de liste d'emails."""
        mock_get_settings.return_value = mock_settings
        fetcher = EmailFetcher()

        # Test avec plusieurs adresses
        header = "john@example.com, Jane Doe <jane@example.com>"
        emails = fetcher._parse_email_list(header)
        assert len(emails) == 2
        assert "john@example.com" in emails
        assert "jane@example.com" in emails

        # Test avec header vide
        emails = fetcher._parse_email_list("")
        assert emails == []

    @patch("app.services.email_fetcher.get_settings")
    def test_decode_header(self, mock_get_settings, mock_settings):
        """Test du décodage de header."""
        mock_get_settings.return_value = mock_settings
        fetcher = EmailFetcher()

        # Test avec texte simple
        decoded = fetcher._decode_header("Simple text")
        assert decoded == "Simple text"

        # Test avec header vide
        decoded = fetcher._decode_header("")
        assert decoded == ""

    @patch("app.services.email_fetcher.get_settings")
    def test_parse_simple_email(self, mock_get_settings, mock_settings, sample_raw_email):
        """Test du parsing d'un email simple."""
        mock_get_settings.return_value = mock_settings
        fetcher = EmailFetcher()

        # Parsing
        email_data = fetcher._parse_email(sample_raw_email)

        # Vérifications
        assert isinstance(email_data, EmailData)
        assert email_data.from_address == "sophie.martin@email.com"
        assert email_data.from_name == "Sophie Martin"
        assert "leonie@voxperience.com" in email_data.to_addresses
        assert "courtier@exemple.fr" in email_data.cc_addresses
        assert email_data.subject == "Documents prêt immobilier"
        assert email_data.message_id == "<abc123@gmail.com>"
        assert "Bonjour" in (email_data.body_text or "")
        assert len(email_data.attachments) == 0

    @patch("app.services.email_fetcher.get_settings")
    def test_extract_body_simple(self, mock_get_settings, mock_settings, sample_raw_email):
        """Test de l'extraction du corps d'un email simple."""
        mock_get_settings.return_value = mock_settings
        fetcher = EmailFetcher()

        body_text, body_html = fetcher._extract_body(sample_raw_email)

        assert body_text is not None
        assert "Bonjour" in body_text
        assert body_html is None

    @patch("app.services.email_fetcher.get_settings")
    def test_extract_attachments(self, mock_get_settings, mock_settings, sample_multipart_email):
        """Test de l'extraction des pièces jointes."""
        mock_get_settings.return_value = mock_settings
        fetcher = EmailFetcher()

        attachments = fetcher._extract_attachments(sample_multipart_email)

        assert len(attachments) == 1
        assert isinstance(attachments[0], EmailAttachment)
        assert attachments[0].filename == "document.pdf"
        assert attachments[0].content_type == "application/pdf"
        assert attachments[0].size_bytes > 0

    @patch("app.services.email_fetcher.imaplib.IMAP4_SSL")
    @patch("app.services.email_fetcher.get_settings")
    def test_fetch_new_emails_success(
        self, mock_get_settings, mock_imap_class, mock_settings, sample_raw_email
    ):
        """Test de récupération des nouveaux emails."""
        # Setup
        mock_get_settings.return_value = mock_settings
        mock_imap = MagicMock()
        mock_imap_class.return_value = mock_imap

        # Configuration du mock IMAP
        mock_imap.select.return_value = ("OK", [b"1"])
        mock_imap.search.return_value = ("OK", [b"1 2"])

        # Mock de fetch avec email brut
        raw_email_bytes = sample_raw_email.as_bytes()
        mock_imap.fetch.return_value = ("OK", [(b"1", raw_email_bytes)])

        # Exécution
        fetcher = EmailFetcher()
        fetcher.connected = True
        fetcher.imap = mock_imap

        emails = fetcher.fetch_new_emails()

        # Vérifications
        assert len(emails) == 2
        assert all(isinstance(e, EmailData) for e in emails)

    @patch("app.services.email_fetcher.imaplib.IMAP4_SSL")
    @patch("app.services.email_fetcher.get_settings")
    def test_mark_as_read(self, mock_get_settings, mock_imap_class, mock_settings):
        """Test du marquage d'un email comme lu."""
        # Setup
        mock_get_settings.return_value = mock_settings
        mock_imap = MagicMock()
        mock_imap_class.return_value = mock_imap

        # Configuration du mock
        mock_imap.search.return_value = ("OK", [b"1"])
        mock_imap.store.return_value = ("OK", None)

        # Exécution
        fetcher = EmailFetcher()
        fetcher.connected = True
        fetcher.imap = mock_imap

        result = fetcher.mark_as_read("<test@example.com>")

        # Vérifications
        assert result is True
        mock_imap.store.assert_called_once()

    @patch("app.services.email_fetcher.imaplib.IMAP4_SSL")
    @patch("app.services.email_fetcher.get_settings")
    def test_disconnect(self, mock_get_settings, mock_imap_class, mock_settings):
        """Test de la déconnexion IMAP."""
        # Setup
        mock_get_settings.return_value = mock_settings
        mock_imap = MagicMock()
        mock_imap_class.return_value = mock_imap

        # Exécution
        fetcher = EmailFetcher()
        fetcher.connected = True
        fetcher.imap = mock_imap
        fetcher.disconnect()

        # Vérifications
        assert fetcher.connected is False
        mock_imap.close.assert_called_once()
        mock_imap.logout.assert_called_once()

    @patch("app.services.email_fetcher.imaplib.IMAP4_SSL")
    @patch("app.services.email_fetcher.get_settings")
    def test_context_manager(self, mock_get_settings, mock_imap_class, mock_settings):
        """Test du context manager."""
        # Setup
        mock_get_settings.return_value = mock_settings
        mock_imap = MagicMock()
        mock_imap_class.return_value = mock_imap

        # Exécution
        with EmailFetcher() as fetcher:
            assert fetcher.connected is True

        # Vérifications - déconnexion automatique
        mock_imap.close.assert_called_once()
        mock_imap.logout.assert_called_once()
