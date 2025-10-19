-- Table pour gérer les initiations de conversation par les bots
-- Phase 3 : Initiation Post-Match

CREATE TABLE IF NOT EXISTS bot_initiations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Relations
  match_id uuid NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  bot_id uuid NOT NULL REFERENCES profiles(id),
  user_id uuid NOT NULL REFERENCES profiles(id),
  
  -- Timing
  scheduled_for timestamp with time zone NOT NULL,
  sent_at timestamp with time zone,
  
  -- Contenu
  first_message text NOT NULL,
  
  -- Status
  status text NOT NULL DEFAULT 'pending' 
    CHECK (status IN ('pending', 'sent', 'cancelled')),
  
  -- Metadata
  cancellation_reason text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_bot_initiations_status_scheduled 
  ON bot_initiations(status, scheduled_for) 
  WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_bot_initiations_match 
  ON bot_initiations(match_id);

-- Commentaires
COMMENT ON TABLE bot_initiations IS 'Gère les premiers messages envoyés par les bots après un match';
COMMENT ON COLUMN bot_initiations.scheduled_for IS 'Quand envoyer le message (15min-6h après match)';
COMMENT ON COLUMN bot_initiations.first_message IS 'Message pré-généré par Grok basé sur profil user';
