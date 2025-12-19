"""
Service de génération de rapports Word.

Ce module génère des rapports quotidiens au format Word
pour les courtiers.

TODO (Session 5): Implémenter la génération de rapports
"""

from uuid import UUID


class ReportService:
    """Service de génération de rapports Word."""

    def generate_daily_report(self, courtier_id: UUID) -> str:
        """
        Génère le rapport quotidien pour un courtier.

        Args:
            courtier_id: ID du courtier.

        Returns:
            Chemin du fichier Word généré.

        TODO: Implémenter la génération de rapport quotidien
        """
        pass

    def generate_client_report(self, client_id: UUID) -> str:
        """
        Génère un rapport détaillé pour un client.

        Args:
            client_id: ID du client.

        Returns:
            Chemin du fichier Word généré.

        TODO: Implémenter la génération de rapport client
        """
        pass
