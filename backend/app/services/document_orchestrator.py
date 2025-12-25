
"""
Service d'Orchestration Documentaire.

Gère le cycle de vie avancé des documents :
- Réception et analyse
- Fusion intelligente (Smart Merging)
- Renommage standardisé
- Stockage structuré
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


from app.services.document import DocumentProcessor
from app.services.drive import DriveManager
from app.models.email import EmailAttachment
from app.utils.db import (
    get_dossier_context, update_dossier_context, get_config,
    get_db, create_piece_dossier, update_piece_dossier, get_pieces_by_client
)

logger = logging.getLogger(__name__)


class DocumentOrchestrator:
    """
    Orchestre le traitement, la fusion et le rangement des documents.
    Effectue le lien entre le fichier brut et le besoin métier.
    """

    def __init__(self):
        self.doc_processor = DocumentProcessor()
        self.drive_manager = DriveManager()
        
    def process_attachments(
        self, 
        attachments: List[EmailAttachment], 
        client: Dict,
        courtier_id: str
    ) -> List[Dict]:
        """
        Traite et consolide les pièces jointes par type.
        Stratégie "Smart Merging Global":
        1. Groupe les fichiers par type (ex: 3 relevés).
        2. Fusionne localement.
        3. Vérifie sur Drive si un fichier Maître existe (Append).
        4. Upload ou Update.
        5. Enregistrement en base de données.
        """
        processed_docs = []
        client_id = client.get('id')
        folder_id = client.get('dossier_drive_id')
        
        if not folder_id:
            logger.error(f"Pas de dossier Drive pour client {client_id}, impossible de traiter les documents.")
            return []

        # 1. Regroupement par Type Maître
        grouped = {}
        
        for att in attachments:
            # Sauvegarde temporaire
            temp_path = Path(self.doc_processor.temp_dir) / att.filename
            with open(temp_path, "wb") as f:
                if att.content: f.write(att.content)
            
            # Analyse type
            raw_type = self._simulate_vision_analysis(att.filename)
            master_type = self._get_master_type(raw_type)
            
            if master_type not in grouped:
                grouped[master_type] = []
            grouped[master_type].append(temp_path)

        # 2. Traitement par Groupe
        for master_type, paths in grouped.items():
            try:
                # A. Consolidation Locale (ex: 3 relevés -> 1 PDF)
                local_pdf = self._consolidate_local_files(paths, master_type, client_id)
                if not local_pdf: continue

                # B. Nommage Standard Maître (Sans date, unique par type)
                final_name = self._generate_master_name(master_type, client)
                
                # C. Vérification Drive (Append Logic)
                existing_file_id = self.drive_manager.find_file_by_name(final_name, folder_id)
                final_file_id = None
                
                if existing_file_id:
                    logger.info(f"Fichier Maître existant trouvé sur Drive ({final_name}). Mode: APPEND.")
                    
                    # 1. Télécharger l'existant
                    download_path = Path(self.doc_processor.temp_dir) / f"drive_master_{client_id}_{master_type}.pdf"
                    self.drive_manager.download_file(existing_file_id, download_path)
                    
                    # 2. Fusionner (Existant + Nouveau)
                    merged_output = Path(self.doc_processor.temp_dir) / f"updated_master_{client_id}_{master_type}.pdf"
                    self.doc_processor.merge_pdfs([download_path, local_pdf], str(merged_output))
                    
                    # 3. Update sur Drive
                    self.drive_manager.update_file(existing_file_id, merged_output)
                    final_file_id = existing_file_id
                    
                else:
                    logger.info(f"Création nouveau Fichier Maître sur Drive ({final_name}).")
                    final_file_id = self.drive_manager.upload_file(local_pdf, folder_id, final_name)

                # D. Enregistrement en base de données
                db_record = self._register_in_database(
                    client_id=client_id,
                    master_type=master_type,
                    final_name=final_name,
                    file_id=final_file_id
                )

                processed_docs.append({
                    "original_name": f"{len(paths)} fichiers fusionnés",
                    "final_name": final_name,
                    "type": master_type,
                    "file_id": final_file_id,
                    "status": "processed",
                    "db_id": db_record.get('id') if db_record else None
                })

            except Exception as e:
                logger.error(f"Erreur traitement groupe {master_type}: {e}", exc_info=True)

        return processed_docs

    def _register_in_database(self, client_id: str, master_type: str, final_name: str, file_id: str) -> Optional[Dict]:
        """Enregistre ou met à jour la pièce dans la table pieces_dossier."""
        try:
            db = get_db()
            
            # 1. Trouver le type_piece_id correspondant
            type_id = self._resolve_type_id_from_master(master_type)
            
            # 2. Vérifier si une pièce de ce type ou avec ce nom existe déjà pour ce client
            existing_pieces = get_pieces_by_client(client_id)
            target_piece = None
            
            for p in existing_pieces:
                # On match soit par le type de pièce (si défini), soit par le nom du fichier id Drive
                if p.get('fichier_drive_id') == file_id:
                    target_piece = p
                    break
                # Si pas de drive ID (ancien), on regarde le type
                if type_id and p.get('type_piece_id') == type_id:
                    target_piece = p
                    break

            data = {
                "client_id": str(client_id),
                "statut": "recue",
                "fichier_drive_id": file_id,
                "date_reception": datetime.now().isoformat()
            }
            # Note: schema 'nom_fichier' n'existe pas dans pieces_dossier, c'est 'metadata' ou implicite. 
            # Le schema a 'fichier_drive_id', 'fichier_hash'. 
            # On va mettre le nom dans metadata
            data["metadata"] = {"nom_fichier": final_name, "source": "email_agent"}

            if type_id:
                data["type_piece_id"] = type_id

            if target_piece:
                logger.info(f"Mise à jour pièce DB {target_piece['id']} ({master_type})")
                return update_piece_dossier(target_piece['id'], data)
            else:
                logger.info(f"Création nouvelle pièce DB ({master_type})")
                return create_piece_dossier(data)

        except Exception as e:
            logger.error(f"Erreur enregistrement DB pour {final_name}: {e}")
            return None

    def _resolve_type_id_from_master(self, master_type: str) -> Optional[str]:
        """Tente de trouver l'UUID du type de pièce à partir du master_type."""
        # Map master_type -> nom_piece dans la DB
        # Voir schema.sql pour les valeurs exactes
        mapping = {
            "CNI": "Pièce d'identité",
            "BULLETIN_SALAIRE": "Bulletins de salaire",
            "AVIS_IMPOT": "Avis d'imposition",
            "RELEVE_BANCAIRE": "Dernier relevé de compte",
            "KBIS": "Kbis",
            "LIVRET_FAMILLE": "Livret de famille" # Pas dans les inserts par défaut mais possible
        }
        
        target_name = mapping.get(master_type)
        if not target_name:
            return None
            
        try:
            db = get_db()
            # On cherche un type qui a ce nom (peu importe la categorie/pret pour l'instant, on prend le premier)
            # Idéalement faudrait filtrer par type_pret du client, mais ici on simplifie
            resp = db.table("types_pieces").select("id").eq("nom_piece", target_name).limit(1).execute()
            if resp.data:
                return resp.data[0]['id']
        except Exception:
            pass
        return None

    def _simulate_vision_analysis(self, filename: str) -> str:
        """Simulateur basique d'analyse vision."""
        lower = filename.lower()
        if "cni" in lower or "identite" in lower or "identité" in lower:
            if "recto" in lower: return "CNI_RECTO"
            if "verso" in lower: return "CNI_VERSO"
            return "CNI_COMPLETE"
        if "salaire" in lower or "paie" in lower: return "BULLETIN_SALAIRE"
        if "impot" in lower or "avis" in lower or "fiscal" in lower: return "AVIS_IMPOT"
        if "kbis" in lower: return "KBIS"
        if "releve" in lower or "rlv" in lower or "bancaire" in lower or "banque" in lower: return "RELEVE_BANCAIRE"
        if "livret" in lower: return "LIVRET_FAMILLE"
        return "AUTRE_DOCUMENT"

    def _get_master_type(self, raw_type: str) -> str:
        """Mappe les sous-types vers des types maîtres pour consolidation."""
        if raw_type in ["CNI_RECTO", "CNI_VERSO", "CNI_COMPLETE"]:
            return "CNI"
        return raw_type

    def _consolidate_local_files(self, paths: List[Path], master_type: str, client_id: str) -> Optional[Path]:
        """Fusionne une liste de fichiers locaux en un seul PDF."""
        if not paths: return None
        
        # Conversion tous en PDF d'abord
        pdf_paths = []
        for p in paths:
            pdf = self.doc_processor.convert_to_pdf(p)
            if pdf: pdf_paths.append(pdf)
            
        if not pdf_paths: return None
        
        # Si un seul fichier, pas besoin de fusion (sauf si conversion faite)
        if len(pdf_paths) == 1:
            return pdf_paths[0]
            
        # Fusion multiple
        output = Path(self.doc_processor.temp_dir) / f"consolidation_{master_type}_{client_id}.pdf"
        try:
            # Tri simple (pour CNI Recto/Verso ou Relevés chronologiques si nommés ainsi)
            pdf_paths.sort() 
            self.doc_processor.merge_pdfs(pdf_paths, str(output))
            return output
        except Exception as e:
            logger.error(f"Erreur content consolidation locale: {e}")
            return pdf_paths[0] # Fallback sur le premier

    def _generate_master_name(self, master_type: str, client: Dict) -> str:
        """Génère le nom Maître (Sans date, unique par type)."""
        prenom = client.get('prenom', 'Inconnu')
        nom = client.get('nom', 'Client')
        client_str = f"{nom}_{prenom}".upper().replace(" ", "_")
        
        type_map = {
            "CNI": "CNI",
            "BULLETIN_SALAIRE": "Bulletin_Salaire",
            "AVIS_IMPOT": "Avis_Impot",
            "RELEVE_BANCAIRE": "Releves_Bancaires",
            "KBIS": "KBIS",
            "LIVRET_FAMILLE": "Livret_Famille",
            "AUTRE_DOCUMENT": "Documents_Divers"
        }
        
        nice_type = type_map.get(master_type, master_type)
        return f"{nice_type}_{client_str}.pdf"
