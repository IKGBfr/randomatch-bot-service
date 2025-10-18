-- ============================================================
-- NETTOYAGE ANCIEN SYSTÈME BOT (Edge Functions)
-- ============================================================
-- Désactive/supprime UNIQUEMENT les triggers et fonctions de 
-- l'ancien système de réponse automatique (Edge Functions)
-- GARDE les triggers utiles (stats, presence, etc.)
-- ============================================================

-- ============================================================
-- ÉTAPE 1 : DÉSACTIVER LE TRIGGER PRINCIPAL (CRITIQUE)
-- ============================================================
-- Ce trigger appelait l'Edge Function pour chaque nouveau message
-- IL DOIT être désactivé pour éviter les doublons avec Railway

DROP TRIGGER IF EXISTS on_message_insert_smart_wait ON messages;

RAISE NOTICE '✅ Trigger principal désactivé : on_message_insert_smart_wait';

-- ============================================================
-- ÉTAPE 2 : DÉSACTIVER LES TRIGGERS DE QUEUE (EDGE FUNCTIONS)
-- ============================================================
-- Ces triggers géraient la queue avec Edge Functions
-- Maintenant géré par Railway + Redis

DROP TRIGGER IF EXISTS trigger_mark_grouped_jobs ON bot_message_queue;
DROP TRIGGER IF EXISTS on_typing_stop_process_pending ON typing_events;

RAISE NOTICE '✅ Triggers de queue désactivés';

-- ============================================================
-- ÉTAPE 3 : SUPPRIMER LES FONCTIONS D''ORCHESTRATION (Edge Functions)
-- ============================================================
-- Ces fonctions appelaient les Edge Functions
-- Plus nécessaires avec Railway

DROP FUNCTION IF EXISTS enqueue_bot_with_smart_wait() CASCADE;
DROP FUNCTION IF EXISTS enqueue_bot_and_trigger_orchestrator() CASCADE;
DROP FUNCTION IF EXISTS enqueue_bot_message_on_insert() CASCADE;
DROP FUNCTION IF EXISTS enqueue_bot_simple_on_insert() CASCADE;
DROP FUNCTION IF EXISTS trigger_bot_reply_on_message() CASCADE;
DROP FUNCTION IF EXISTS trigger_bot_reply_instant() CASCADE;
DROP FUNCTION IF EXISTS trigger_bot_instant_reply_with_typing() CASCADE;
DROP FUNCTION IF EXISTS trigger_bot_reply_with_indicators() CASCADE;
DROP FUNCTION IF EXISTS trigger_bot_reply_with_presence() CASCADE;

RAISE NOTICE '✅ Fonctions d''orchestration supprimées';

-- ============================================================
-- ÉTAPE 4 : SUPPRIMER LES FONCTIONS DE QUEUE (Edge Functions)
-- ============================================================

DROP FUNCTION IF EXISTS process_bot_queue() CASCADE;
DROP FUNCTION IF EXISTS process_pending_bot_jobs() CASCADE;
DROP FUNCTION IF EXISTS claim_bot_queue_job() CASCADE;
DROP FUNCTION IF EXISTS complete_bot_queue_job() CASCADE;
DROP FUNCTION IF EXISTS on_bot_job_completed() CASCADE;
DROP FUNCTION IF EXISTS cleanup_stuck_bot_jobs() CASCADE;
DROP FUNCTION IF EXISTS cleanup_old_bot_queue_jobs() CASCADE;
DROP FUNCTION IF EXISTS cleanup_stuck_queue_jobs() CASCADE;

RAISE NOTICE '✅ Fonctions de queue supprimées';

-- ============================================================
-- ÉTAPE 5 : GARDER LES FONCTIONS UTILES
-- ============================================================
-- Ces fonctions/triggers sont toujours utiles et sont GARDÉS :
--
-- ✅ GARDE : increment_bot_messages_count() - Stats importantes
-- ✅ GARDE : update_bot_last_seen_on_message() - Presence
-- ✅ GARDE : mark_bot_conversation_delivered() - Status messages
-- ✅ GARDE : mark_previous_on_bot_reply() - Status messages
-- ✅ GARDE : stop_bot_typing_after_message() - Typing indicator
-- ✅ GARDE : update_bot_presence_after_message() - Presence
-- ✅ GARDE : update_bot_memory_updated_at() - Mémoire bot
-- ✅ GARDE : handle_bot_auto_like() - Matching
-- ✅ GARDE : on_swipe_auto_match_bot() - Matching
-- ✅ GARDE : check_bot_message_limit() - Limites
-- ✅ GARDE : is_user_a_bot() - Helper
-- ✅ GARDE : get_bot_profile() - Helper
-- ✅ GARDE : get_user_profile_for_bot() - Helper

RAISE NOTICE '✅ Fonctions utiles gardées (stats, presence, helpers)';

-- ============================================================
-- ÉTAPE 6 : CRÉER LE NOUVEAU TRIGGER RAILWAY
-- ============================================================
-- Crée la fonction qui envoie les notifications PostgreSQL NOTIFY

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

RAISE NOTICE '✅ Fonction notify_bot_message() créée';

-- Créer le trigger qui appelle cette fonction
CREATE TRIGGER on_message_notify_bot
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION notify_bot_message();

RAISE NOTICE '✅ Trigger on_message_notify_bot créé';

-- ============================================================
-- VÉRIFICATION FINALE
-- ============================================================

-- Lister les triggers restants sur la table messages
DO $$
DECLARE
    trigger_rec RECORD;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '📋 TRIGGERS RESTANTS SUR TABLE MESSAGES:';
    FOR trigger_rec IN 
        SELECT trigger_name 
        FROM information_schema.triggers 
        WHERE event_object_table = 'messages' 
        AND trigger_schema = 'public'
        ORDER BY trigger_name
    LOOP
        RAISE NOTICE '   - %', trigger_rec.trigger_name;
    END LOOP;
END $$;

-- ============================================================
-- RÉSUMÉ
-- ============================================================
/*
✅ DÉSACTIVÉ : 
   - on_message_insert_smart_wait (Edge Function orchestrator)
   - Fonctions de queue Edge Functions
   
✅ CRÉÉ :
   - notify_bot_message() (PostgreSQL NOTIFY)
   - on_message_notify_bot (trigger nouveau système)
   
✅ GARDÉ :
   - Tous les triggers de stats, presence, typing
   - Fonctions helpers utiles
*/

RAISE NOTICE '';
RAISE NOTICE '🎉 NETTOYAGE TERMINÉ !';
RAISE NOTICE '✅ Ancien système désactivé';
RAISE NOTICE '✅ Nouveau système Railway activé';
RAISE NOTICE '';
