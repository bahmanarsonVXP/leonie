-- ============================================================================
-- LÉONIE - Schéma de base de données Supabase
-- ============================================================================
-- Ce fichier doit être exécuté manuellement dans l'éditeur SQL de Supabase
-- Ordre d'exécution : créer les tables, puis les indexes, puis les policies RLS
-- ============================================================================

-- Activer les extensions nécessaires
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- TABLE: courtiers
-- ============================================================================
-- Stocke les informations des courtiers en prêts immobiliers/professionnels
-- ============================================================================

CREATE TABLE IF NOT EXISTS courtiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    dossier_drive_id TEXT NOT NULL,
    actif BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE courtiers IS 'Courtiers en prêts immobiliers et professionnels';
COMMENT ON COLUMN courtiers.dossier_drive_id IS 'ID du dossier racine Google Drive du courtier. DOIT être valide : ce dossier est créé automatiquement lors de la création du courtier et ne doit jamais être invalide';
COMMENT ON COLUMN courtiers.actif IS 'Indique si le courtier peut encore utiliser le système';

-- ============================================================================
-- TABLE: clients
-- ============================================================================
-- Stocke les dossiers clients des courtiers
-- ============================================================================

CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    courtier_id UUID NOT NULL REFERENCES courtiers(id) ON DELETE CASCADE,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    email_principal TEXT NOT NULL,
    emails_secondaires TEXT[] DEFAULT '{}',
    type_pret TEXT NOT NULL CHECK (type_pret IN ('immobilier', 'professionnel')),
    statut TEXT DEFAULT 'en_cours' CHECK (statut IN ('en_cours', 'complet', 'archive')),
    dossier_drive_id TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE clients IS 'Dossiers clients gérés par les courtiers';
COMMENT ON COLUMN clients.emails_secondaires IS 'Emails secondaires du client (conjoint, co-emprunteur, etc.)';
COMMENT ON COLUMN clients.type_pret IS 'Type de prêt: immobilier ou professionnel';
COMMENT ON COLUMN clients.statut IS 'Statut du dossier: en_cours, complet, archive';
COMMENT ON COLUMN clients.dossier_drive_id IS 'ID du dossier Google Drive du client';

-- ============================================================================
-- TABLE: types_pieces
-- ============================================================================
-- Définit les types de pièces justificatives par type de prêt
-- ============================================================================

CREATE TABLE IF NOT EXISTS types_pieces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type_pret TEXT NOT NULL CHECK (type_pret IN ('immobilier', 'professionnel', 'commun')),
    categorie TEXT NOT NULL,
    nom_piece TEXT NOT NULL,
    description TEXT,
    obligatoire BOOLEAN DEFAULT true,
    ordre INTEGER,
    regles_validation JSONB,
    UNIQUE(type_pret, categorie, nom_piece)
);

COMMENT ON TABLE types_pieces IS 'Catalogue des types de pièces justificatives';
COMMENT ON COLUMN types_pieces.type_pret IS 'Type de prêt concerné (immobilier, professionnel, ou commun aux deux)';
COMMENT ON COLUMN types_pieces.categorie IS 'Catégorie: identite, domicile, revenus, patrimoine, projet, etc.';
COMMENT ON COLUMN types_pieces.nom_piece IS 'Nom du type de pièce: CNI, Passeport, Justificatif de domicile, etc.';
COMMENT ON COLUMN types_pieces.ordre IS 'Ordre d''affichage dans la liste';
COMMENT ON COLUMN types_pieces.regles_validation IS 'Règles de validation JSON: durée validité, pages requises, etc.';

-- ============================================================================
-- TABLE: pieces_dossier
-- ============================================================================
-- Stocke les pièces justificatives reçues pour chaque client
-- ============================================================================

CREATE TABLE IF NOT EXISTS pieces_dossier (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    type_piece_id UUID REFERENCES types_pieces(id) ON DELETE SET NULL,
    statut TEXT DEFAULT 'manquante' CHECK (statut IN ('manquante', 'recue', 'non_conforme', 'non_reconnu')),
    fichier_drive_id TEXT,
    fichier_hash TEXT,
    date_reception TIMESTAMPTZ,
    commentaire_conformite TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE pieces_dossier IS 'Pièces justificatives des dossiers clients';
COMMENT ON COLUMN pieces_dossier.statut IS 'manquante: attendue, recue: OK, non_conforme: reçue mais non conforme, non_reconnu: type non identifié';
COMMENT ON COLUMN pieces_dossier.fichier_hash IS 'Hash SHA256 du fichier pour détecter les doublons';
COMMENT ON COLUMN pieces_dossier.metadata IS 'Métadonnées extraites: dates, montants, noms, etc.';

-- ============================================================================
-- TABLE: config
-- ============================================================================
-- Stocke la configuration globale du système
-- ============================================================================

CREATE TABLE IF NOT EXISTS config (
    cle TEXT PRIMARY KEY,
    valeur JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE config IS 'Configuration globale du système';
COMMENT ON COLUMN config.cle IS 'Clé unique de configuration: mistral_prompt_template, gdrive_folder_structure, etc.';
COMMENT ON COLUMN config.valeur IS 'Valeur JSON de la configuration';

-- ============================================================================
-- TABLE: logs_activite
-- ============================================================================
-- Journal d'activité pour audit et debug
-- ============================================================================

CREATE TABLE IF NOT EXISTS logs_activite (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    courtier_id UUID REFERENCES courtiers(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE logs_activite IS 'Journal d''activité du système';
COMMENT ON COLUMN logs_activite.action IS 'Type d''action: email_recu, piece_classee, dossier_cree, rapport_envoye, etc.';
COMMENT ON COLUMN logs_activite.details IS 'Détails JSON de l''action';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index pour les clients
CREATE INDEX IF NOT EXISTS idx_clients_courtier ON clients(courtier_id);
CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email_principal);
CREATE INDEX IF NOT EXISTS idx_clients_emails_sec ON clients USING gin(emails_secondaires);
CREATE INDEX IF NOT EXISTS idx_clients_statut ON clients(statut);
CREATE INDEX IF NOT EXISTS idx_clients_type_pret ON clients(type_pret);

-- Index pour les pièces
CREATE INDEX IF NOT EXISTS idx_pieces_client ON pieces_dossier(client_id);
CREATE INDEX IF NOT EXISTS idx_pieces_type ON pieces_dossier(type_piece_id);
CREATE INDEX IF NOT EXISTS idx_pieces_statut ON pieces_dossier(statut);
CREATE INDEX IF NOT EXISTS idx_pieces_hash ON pieces_dossier(fichier_hash);

-- Index pour les types de pièces
CREATE INDEX IF NOT EXISTS idx_types_pieces_type_pret ON types_pieces(type_pret);
CREATE INDEX IF NOT EXISTS idx_types_pieces_categorie ON types_pieces(categorie);

-- Index pour les logs
CREATE INDEX IF NOT EXISTS idx_logs_client ON logs_activite(client_id);
CREATE INDEX IF NOT EXISTS idx_logs_courtier ON logs_activite(courtier_id);
CREATE INDEX IF NOT EXISTS idx_logs_created ON logs_activite(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_action ON logs_activite(action);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pieces_updated_at BEFORE UPDATE ON pieces_dossier
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_config_updated_at BEFORE UPDATE ON config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================
-- Permet d'isoler les données de chaque courtier
-- Note: Nécessite de définir app.current_courtier_id dans la session
-- ============================================================================

-- Activer RLS sur les tables sensibles
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE pieces_dossier ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs_activite ENABLE ROW LEVEL SECURITY;

-- Policy pour les clients : un courtier ne voit que ses clients
CREATE POLICY courtier_clients_policy ON clients
    FOR ALL
    USING (
        courtier_id = (current_setting('app.current_courtier_id', true)::uuid)
        OR current_setting('app.is_admin', true)::boolean = true
    );

-- Policy pour les pièces : accès via les clients du courtier
CREATE POLICY courtier_pieces_policy ON pieces_dossier
    FOR ALL
    USING (
        client_id IN (
            SELECT id FROM clients
            WHERE courtier_id = current_setting('app.current_courtier_id', true)::uuid
        )
        OR current_setting('app.is_admin', true)::boolean = true
    );

-- Policy pour les logs : accès via courtier_id
CREATE POLICY courtier_logs_policy ON logs_activite
    FOR ALL
    USING (
        courtier_id = current_setting('app.current_courtier_id', true)::uuid
        OR current_setting('app.is_admin', true)::boolean = true
    );

-- ============================================================================
-- DONNÉES INITIALES
-- ============================================================================

-- Insérer quelques types de pièces par défaut (exemples)
INSERT INTO types_pieces (type_pret, categorie, nom_piece, description, obligatoire, ordre) VALUES
    -- Pièces communes
    ('commun', 'identite', 'Pièce d''identité', 'CNI recto-verso ou Passeport', true, 1),
    ('commun', 'domicile', 'Justificatif de domicile', 'Moins de 3 mois', true, 2),
    ('commun', 'revenus', 'Avis d''imposition', 'Dernière année', true, 3),
    ('commun', 'revenus', 'Bulletins de salaire', '3 derniers mois', true, 4),

    -- Prêt immobilier
    ('immobilier', 'revenus', 'Dernier relevé de compte', 'Compte principal', true, 5),
    ('immobilier', 'projet', 'Compromis de vente', 'Signé', true, 6),
    ('immobilier', 'projet', 'Offre de prêt', 'Si refinancement', false, 7),

    -- Prêt professionnel
    ('professionnel', 'entreprise', 'Kbis', 'Moins de 3 mois', true, 8),
    ('professionnel', 'entreprise', 'Statuts de la société', 'À jour', true, 9),
    ('professionnel', 'entreprise', 'Bilans', '3 derniers exercices', true, 10),
    ('professionnel', 'entreprise', 'Liasse fiscale', 'Dernière année', true, 11)
ON CONFLICT (type_pret, categorie, nom_piece) DO NOTHING;

-- Configuration initiale
INSERT INTO config (cle, valeur, description) VALUES
    ('mistral_model', '"mistral-large-latest"', 'Modèle Mistral AI utilisé pour la classification'),
    ('email_polling_interval', '300', 'Intervalle de polling IMAP en secondes'),
    ('max_attachment_size_mb', '25', 'Taille max des pièces jointes en MB'),
    ('rapport_quotidien_heure', '"08:00"', 'Heure d''envoi du rapport quotidien')
ON CONFLICT (cle) DO NOTHING;

-- ============================================================================
-- FIN DU SCHÉMA
-- ============================================================================
