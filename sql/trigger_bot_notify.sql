-- ============================================================
-- TRIGGER POSTGRESQL NOTIFY POUR BOT SERVICE
-- ============================================================
-- Ce trigger détecte les nouveaux messages destinés aux bots
-- et envoie une notification PostgreSQL au bridge Python
-- ============================================================

-- Fonction qui envoie la notification
CREATE OR REPLACE FUNCTION notify_bot_message()
RETURNS TRIGGER AS $$
DECLARE
    bot_profile_id UUID;
    notification_payload JSON;
BEGIN
    -- Récupérer l'ID du bot dans le match
    -- Si le sender est user1, alors le bot est user2 et vice-versa
    SELECT 
        CASE 
            WHEN NEW.sender_id = m.user1_id THEN m.user2_id
            ELSE m.user1_id
        END INTO bot_profile_id
    FROM matches m
    WHERE m.id = NEW.match_id;
    
    -- Vérifier que le destinataire est bien un bot
    IF EXISTS (
        SELECT 1 FROM profiles p 
        WHERE p.id = bot_profile_id 
        AND p.is_bot = true
    ) THEN
        -- Construire le payload JSON avec toutes les infos nécessaires
        notification_payload := json_build_object(
            'match_id', NEW.match_id,
            'bot_id', bot_profile_id,
            'user_id', NEW.sender_id,
            'message_id', NEW.id,
            'message_content', NEW.content,
            'sender_id', NEW.sender_id,
            'created_at', NEW.created_at
        );
        
        -- Envoyer la notification sur le canal 'bot_events'
        PERFORM pg_notify('bot_events', notification_payload::text);
        
        -- Log pour debugging (visible dans Supabase logs)
        RAISE LOG 'Bot notification sent for match % to bot %', NEW.match_id, bot_profile_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Supprimer l'ancien trigger s'il existe
DROP TRIGGER IF EXISTS on_message_notify_bot ON messages;

-- Créer le trigger sur INSERT de messages
CREATE TRIGGER on_message_notify_bot
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION notify_bot_message();

-- ============================================================
-- COMMENT TESTER:
-- ============================================================
-- 1. Exécute ce SQL dans Supabase SQL Editor
-- 2. Lance le bridge: python -m app.test_bridge
-- 3. Envoie un message dans Flutter à un bot
-- 4. Le bridge devrait recevoir la notification instantanément !
-- ============================================================
