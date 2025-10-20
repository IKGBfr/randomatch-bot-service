"""
Response Cache - Évite génération de réponses identiques/similaires

Utilise Redis pour stocker:
1. Intent de réponse (flag "generating")
2. Réponses récentes (pour deduplication)
3. TTL 60s (expire automatiquement)
"""

import json
import hashlib
import re
from datetime import datetime
from typing import Optional, List, Dict, Set
import redis.asyncio as redis
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class ResponseCache:
    """Cache Redis pour éviter doublons de réponses"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.CACHE_TTL = 60  # Secondes - expire auto
        
        # Seuils de détection (multi-niveaux)
        self.TEXT_SIMILARITY_THRESHOLD = 0.75  # 75% similarité textuelle
        self.KEYWORD_OVERLAP_THRESHOLD = 0.70  # 70% mots-clés communs
        self.START_SIMILARITY_THRESHOLD = 0.85 # 85% début identique
    
    def _make_key(self, match_id: str, key_type: str) -> str:
        """Génère clé Redis"""
        return f"response:{key_type}:{match_id}"
    
    def _normalize_text(self, text: str) -> str:
        """Normalise un texte pour comparaison"""
        # Lowercase
        text = text.lower()
        
        # Enlever ponctuation (garder lettres, chiffres, espaces)
        text = re.sub(r'[^a-z0-9àâäéèêëïîôùûüÿœæç\s]', '', text)
        
        # Normaliser espaces
        text = ' '.join(text.split())
        
        return text
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extrait mots-clés importants (>3 caractères, pas stop words)"""
        # Stop words français communs
        stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du',
            'et', 'ou', 'mais', 'donc', 'car', 'ni',
            'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
            'mon', 'ton', 'son', 'ma', 'ta', 'sa', 'mes', 'tes', 'ses',
            'ce', 'cette', 'ces', 'cet',
            'qui', 'que', 'quoi', 'dont', 'où',
            'sur', 'sous', 'dans', 'avec', 'sans', 'pour', 'par',
            'au', 'aux', 'à', 'en',
            'est', 'sont', 'était', 'été', 'être', 'avoir', 'avait', 'eu',
            'fait', 'faire', 'fais', 'faisait',
            'pas', 'plus', 'très', 'bien', 'tout', 'tous', 'toute',
            'comme', 'comment', 'quand', 'pourquoi',
            'toi', 'moi', 'lui',
            'oui', 'non', 'peut', 'peu', 'beaucoup',
            'ça', 'cela', 'ça va', 'va', 'vais', 'vas',
        }
        
        normalized = self._normalize_text(text)
        words = normalized.split()
        
        # Garder mots >3 chars, pas stop words
        keywords = {
            word for word in words 
            if len(word) > 3 and word not in stop_words
        }
        
        return keywords
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calcule similarité textuelle pure (SequenceMatcher)"""
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _calculate_keyword_overlap(self, text1: str, text2: str) -> float:
        """Calcule overlap des mots-clés (Jaccard similarity)"""
        keywords1 = self._extract_keywords(text1)
        keywords2 = self._extract_keywords(text2)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Jaccard similarity: intersection / union
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_start_similarity(self, text1: str, text2: str) -> float:
        """Calcule similarité des débuts de phrases"""
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        
        # Prendre les 50 premiers caractères ou moins
        length = min(50, len(norm1), len(norm2))
        if length < 10:  # Trop court pour comparer
            return 0.0
        
        start1 = norm1[:length]
        start2 = norm2[:length]
        
        return SequenceMatcher(None, start1, start2).ratio()
    
    def _are_responses_similar(self, response1: str, response2: str) -> tuple[bool, str]:
        """
        Détection multi-niveaux de similarité
        
        Returns:
            (is_similar, reason)
        """
        # Niveau 1 : Similarité textuelle pure
        text_sim = self._calculate_text_similarity(response1, response2)
        if text_sim >= self.TEXT_SIMILARITY_THRESHOLD:
            return True, f"Similarité textuelle: {text_sim:.2%}"
        
        # Niveau 2 : Overlap des mots-clés
        keyword_overlap = self._calculate_keyword_overlap(response1, response2)
        if keyword_overlap >= self.KEYWORD_OVERLAP_THRESHOLD:
            keywords1 = self._extract_keywords(response1)
            keywords2 = self._extract_keywords(response2)
            common = keywords1 & keywords2
            return True, f"Mots-clés communs ({keyword_overlap:.2%}): {common}"
        
        # Niveau 3 : Début identique + longueur similaire
        start_sim = self._calculate_start_similarity(response1, response2)
        length_ratio = min(len(response1), len(response2)) / max(len(response1), len(response2))
        
        if start_sim >= self.START_SIMILARITY_THRESHOLD and length_ratio >= 0.7:
            return True, f"Début identique ({start_sim:.2%}) + longueur similaire ({length_ratio:.2%})"
        
        return False, "Réponses suffisamment différentes"
    
    async def is_generating(self, match_id: str) -> bool:
        """Check si une génération est déjà en cours"""
        key = self._make_key(match_id, "generating")
        exists = await self.redis.exists(key)
        
        if exists:
            data = await self.redis.get(key)
            if data:
                generating_data = json.loads(data)
                logger.info(f"⚠️ Génération déjà en cours depuis {generating_data.get('started_at')}")
                return True
        
        return False
    
    async def mark_generating(self, match_id: str, user_message: str):
        """Marque qu'une génération démarre"""
        key = self._make_key(match_id, "generating")
        
        data = {
            'started_at': datetime.now().isoformat(),
            'user_message': user_message,
            'status': 'generating'
        }
        
        await self.redis.setex(
            key,
            self.CACHE_TTL,
            json.dumps(data)
        )
        
        logger.info(f"🔒 Génération marquée en cours (TTL {self.CACHE_TTL}s)")
    
    async def clear_generating(self, match_id: str):
        """Clear le flag de génération"""
        key = self._make_key(match_id, "generating")
        await self.redis.delete(key)
        logger.info("🔓 Flag génération cleared")
    
    async def store_response(self, match_id: str, bot_response: str, user_message: str, sent_successfully: bool = False):
        """Stocke une réponse dans le cache"""
        key = self._make_key(match_id, "recent")
        
        # Récupérer réponses existantes
        existing = await self.redis.get(key)
        
        if existing:
            responses = json.loads(existing)
        else:
            responses = []
        
        # Ajouter nouvelle réponse avec flag sent
        responses.append({
            'response': bot_response,
            'user_message': user_message,
            'timestamp': datetime.now().isoformat(),
            'sent_successfully': sent_successfully  # NOUVEAU FLAG
        })
        
        # Garder seulement les 5 dernières
        responses = responses[-5:]
        
        # Stocker avec TTL
        await self.redis.setex(
            key,
            self.CACHE_TTL,
            json.dumps(responses)
        )
        
        status = "✅ envoyée" if sent_successfully else "⏳ en attente"
        logger.info(f"💾 Réponse stockée en cache ({status}, total: {len(responses)})")
    
    async def mark_as_sent(self, match_id: str, bot_response: str):
        """
        Marque une réponse comme effectivement envoyée
        
        Important : À appeler APRÈS envoi réussi du message
        """
        key = self._make_key(match_id, "recent")
        existing = await self.redis.get(key)
        
        if not existing:
            logger.warning("⚠️ Aucune réponse en cache à marquer comme envoyée")
            return
        
        responses = json.loads(existing)
        
        # Trouver et marquer la réponse correspondante
        for resp_data in responses:
            # Comparer texte de réponse (normaliser pour match flexible)
            if self._normalize_text(resp_data['response']) == self._normalize_text(bot_response):
                resp_data['sent_successfully'] = True
                logger.info(f"✅ Réponse marquée comme envoyée: {bot_response[:50]}")
                break
        
        # Sauvegarder
        await self.redis.setex(
            key,
            self.CACHE_TTL,
            json.dumps(responses)
        )
        
        logger.info("💾 Cache mis à jour avec statut envoi")
    
    async def is_duplicate_response(
        self,
        match_id: str,
        new_response: str,
        force_response: bool = False
    ) -> bool:
        """
        Check si la réponse générée est trop similaire aux récentes
        Utilise détection multi-niveaux
        
        Args:
            match_id: ID du match
            new_response: Réponse à vérifier
            force_response: Si True, ignore cache et retourne toujours False
        
        Returns:
            True si doublon, False sinon
        """
        if force_response:
            logger.info("🚨 Force response activé → Ignore vérification cache")
            return False
        
        key = self._make_key(match_id, "recent")
        existing = await self.redis.get(key)
        
        if not existing:
            return False
        
        responses = json.loads(existing)
        
        # Comparer SEULEMENT avec réponses effectivement envoyées
        for resp_data in responses:
            # NOUVELLE VÉRIFICATION : Skip si pas envoyée
            if not resp_data.get('sent_successfully', False):
                logger.info(f"⏭️  Skip comparaison : réponse non envoyée en cache")
                continue
            
            is_similar, reason = self._are_responses_similar(
                new_response,
                resp_data['response']
            )
            
            if is_similar:
                logger.warning(f"❌ DOUBLON DÉTECTÉ!")
                logger.warning(f"   Nouvelle: {new_response[:60]}")
                logger.warning(f"   Existante: {resp_data['response'][:60]}")
                logger.warning(f"   Raison: {reason}")
                logger.warning(f"   → SKIP cette réponse")
                
                return True
        
        # Toutes les comparaisons ont échoué → Pas de doublon
        logger.info("✅ Réponse suffisamment différente des récentes")
        return False
    
    async def get_recent_responses(self, match_id: str) -> List[Dict]:
        """Récupère toutes les réponses récentes (debug)"""
        key = self._make_key(match_id, "recent")
        existing = await self.redis.get(key)
        
        if existing:
            return json.loads(existing)
        
        return []
