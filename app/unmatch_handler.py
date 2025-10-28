"""
Unmatch Handler - Intercepte le marqueur [UNMATCH] et déclenche unmatch backend

Utilisé pour que le bot puisse décider d'unmatcher sans que l'utilisateur
voie le marqueur [UNMATCH] dans la conversation.
"""

import re
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class UnmatchHandler:
    """Gère l'interception [UNMATCH] et le déclenchement unmatch"""
    
    # Patterns pour détecter [UNMATCH]
    UNMATCH_PATTERNS = [
        r'\[UNMATCH\]',    # Basique
        r'\[unmatch\]',    # Lowercase
        r'\[ UNMATCH \]',  # Avec espaces
        r'\[UN-MATCH\]',   # Variante
    ]
    
    async def process_message_with_unmatch(
        self,
        content: str,
        match_id: str,
        bot_id: str
    ) -> tuple[str, bool]:
        """
        Traite un message et gère l'unmatch si nécessaire
        
        Args:
            content: Contenu du message (potentiellement avec [UNMATCH])
            match_id: ID du match
            bot_id: ID du bot
            
        Returns:
            tuple: (clean_content, unmatch_triggered)
            - clean_content: Message sans le marqueur
            - unmatch_triggered: True si unmatch déclenché
        """
        # Détecter si [UNMATCH] présent
        has_unmatch = self._detect_unmatch_marker(content)
        
        if not has_unmatch:
            # Pas de marqueur → message normal
            return content, False
        
        logger.info(f"🚨 Marqueur [UNMATCH] détecté dans message du bot")
        logger.info(f"   Match: {match_id[:8]}...")
        logger.info(f"   Message brut: {content[:100]}...")
        
        # Retirer le marqueur du texte
        clean_content = self._remove_unmatch_marker(content)
        
        logger.info(f"   Message propre: {clean_content[:100]}...")
        
        # Déclencher unmatch backend
        unmatch_success = await self._trigger_unmatch(match_id, bot_id)
        
        if unmatch_success:
            logger.info(f"✅ Unmatch déclenché avec succès pour match {match_id[:8]}")
        else:
            logger.error(f"❌ Échec déclenchement unmatch pour match {match_id[:8]}")
        
        return clean_content, unmatch_success
    
    def _detect_unmatch_marker(self, content: str) -> bool:
        """Détecte si le marqueur [UNMATCH] est présent"""
        for pattern in self.UNMATCH_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _remove_unmatch_marker(self, content: str) -> str:
        """Retire tous les marqueurs [UNMATCH] du texte"""
        clean = content
        
        for pattern in self.UNMATCH_PATTERNS:
            clean = re.sub(pattern, '', clean, flags=re.IGNORECASE)
        
        # Nettoyer espaces multiples
        clean = re.sub(r'\s+', ' ', clean)
        clean = clean.strip()
        
        return clean
    
    async def _trigger_unmatch(self, match_id: str, bot_id: str) -> bool:
        """
        Déclenche l'unmatch côté backend via API Supabase
        
        Effectue:
        1. INSERT dans unmatched_pairs
        2. DELETE du match
        3. DELETE des messages
        4. UPDATE profile counts
        """
        try:
            logger.info(f"🔧 Déclenchement unmatch backend...")
            
            # Récupérer les IDs des deux users
            async with httpx.AsyncClient(timeout=30) as client:
                # Fetch match pour avoir user1_id et user2_id
                match_resp = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/matches",
                    params={"id": f"eq.{match_id}", "select": "user1_id,user2_id"},
                    headers={
                        "apikey": settings.SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"
                    }
                )
                
                if match_resp.status_code != 200:
                    logger.error(f"❌ Erreur fetch match: {match_resp.status_code}")
                    return False
                
                match_data = match_resp.json()
                
                if not match_data:
                    logger.error(f"❌ Match {match_id} non trouvé")
                    return False
                
                user1_id = match_data[0]['user1_id']
                user2_id = match_data[0]['user2_id']
                
                logger.info(f"   User1: {user1_id[:8]}, User2: {user2_id[:8]}")
                
                # 1. INSERT dans unmatched_pairs
                logger.info("   📝 INSERT unmatched_pairs...")
                
                unmatch_resp = await client.post(
                    f"{settings.SUPABASE_URL}/rest/v1/unmatched_pairs",
                    json={
                        "user1_id": user1_id,
                        "user2_id": user2_id,
                        "unmatched_by": bot_id
                    },
                    headers={
                        "apikey": settings.SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                        "Content-Type": "application/json",
                        "Prefer": "resolution=merge-duplicates"
                    }
                )
                
                if unmatch_resp.status_code not in [200, 201, 204]:
                    logger.warning(f"⚠️ Erreur insert unmatched_pairs: {unmatch_resp.status_code}")
                    logger.warning(f"   Response: {unmatch_resp.text}")
                else:
                    logger.info("   ✅ unmatched_pairs OK")
                
                # 2. DELETE messages
                logger.info("   🗑️ DELETE messages...")
                
                messages_resp = await client.delete(
                    f"{settings.SUPABASE_URL}/rest/v1/messages",
                    params={"match_id": f"eq.{match_id}"},
                    headers={
                        "apikey": settings.SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"
                    }
                )
                
                if messages_resp.status_code not in [200, 204]:
                    logger.warning(f"⚠️ Erreur delete messages: {messages_resp.status_code}")
                else:
                    logger.info("   ✅ Messages deleted")
                
                # 3. DELETE match
                logger.info("   🗑️ DELETE match...")
                
                match_delete_resp = await client.delete(
                    f"{settings.SUPABASE_URL}/rest/v1/matches",
                    params={"id": f"eq.{match_id}"},
                    headers={
                        "apikey": settings.SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"
                    }
                )
                
                if match_delete_resp.status_code not in [200, 204]:
                    logger.error(f"❌ Erreur delete match: {match_delete_resp.status_code}")
                    return False
                
                logger.info("   ✅ Match deleted")
                
                # 4. Décrémenter matches_count pour les deux users
                logger.info("   📉 UPDATE profiles matches_count...")
                
                for user_id in [user1_id, user2_id]:
                    # Fetch current count
                    profile_resp = await client.get(
                        f"{settings.SUPABASE_URL}/rest/v1/profiles",
                        params={"id": f"eq.{user_id}", "select": "matches_count"},
                        headers={
                            "apikey": settings.SUPABASE_SERVICE_KEY,
                            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"
                        }
                    )
                    
                    if profile_resp.status_code == 200:
                        profile_data = profile_resp.json()
                        if profile_data:
                            current_count = profile_data[0].get('matches_count', 0)
                            new_count = max(0, current_count - 1)
                            
                            # Update
                            update_resp = await client.patch(
                                f"{settings.SUPABASE_URL}/rest/v1/profiles",
                                params={"id": f"eq.{user_id}"},
                                json={"matches_count": new_count},
                                headers={
                                    "apikey": settings.SUPABASE_SERVICE_KEY,
                                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                                    "Content-Type": "application/json"
                                }
                            )
                            
                            if update_resp.status_code not in [200, 204]:
                                logger.warning(f"⚠️ Erreur update profile {user_id[:8]}")
                
                logger.info("   ✅ Profiles updated")
                
                logger.info("✅ Unmatch backend terminé avec succès")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur trigger unmatch: {e}", exc_info=True)
            return False


# Instance globale
unmatch_handler = UnmatchHandler()
