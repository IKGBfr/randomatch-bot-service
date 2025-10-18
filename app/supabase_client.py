"""Client Supabase pour interactions database."""

from typing import Dict, Optional
from supabase import create_client, Client
from app.config import settings


class SupabaseClient:
    """Client Supabase singleton."""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Retourne instance Supabase client."""
        if cls._instance is None:
            cls._instance = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
        return cls._instance
    
    @classmethod
    def get_bot_profile(cls, bot_id: str) -> Dict:
        """
        Récupère le profil complet d'un bot.
        
        Args:
            bot_id: UUID du bot
            
        Returns:
            Dict avec bot_personality, system_prompt, temperature, etc.
        """
        client = cls.get_client()
        
        # Récupérer bot_profiles + profiles (pour infos de base)
        result = (
            client.table('bot_profiles')
            .select('*, profiles!inner(*)')
            .eq('id', bot_id)
            .single()
            .execute()
        )
        
        if not result.data:
            raise ValueError(f"Bot {bot_id} not found")
        
        return result.data
    
    @classmethod
    def get_all_active_bots(cls) -> list:
        """Récupère tous les bots actifs."""
        client = cls.get_client()
        
        result = (
            client.table('bot_profiles')
            .select('id, profiles!inner(first_name, email)')
            .eq('is_active', True)
            .execute()
        )
        
        return result.data
    
    @classmethod
    def insert_message(cls, match_id: str, sender_id: str, content: str) -> Dict:
        """
        Insère un message dans la table messages.
        
        Args:
            match_id: UUID du match
            sender_id: UUID du bot (sender)
            content: Contenu du message
            
        Returns:
            Message créé
        """
        client = cls.get_client()
        
        result = (
            client.table('messages')
            .insert({
                'match_id': match_id,
                'sender_id': sender_id,
                'content': content,
                'type': 'text',
                'status': 'sent'
            })
            .execute()
        )
        
        return result.data[0] if result.data else None
    
    @classmethod
    def update_typing_status(cls, user_id: str, match_id: str, is_typing: bool):
        """
        Met à jour le statut typing d'un bot.
        
        Args:
            user_id: UUID du bot
            match_id: UUID du match
            is_typing: True si en train de taper
        """
        client = cls.get_client()
        
        client.table('typing_events').upsert({
            'user_id': user_id,
            'match_id': match_id,
            'is_typing': is_typing,
            'started_at': 'now()' if is_typing else None
        }).execute()


# Instance globale
supabase_client = SupabaseClient()


def get_bot_profile(bot_id: str) -> Dict:
    """Helper pour récupérer profil bot."""
    return supabase_client.get_bot_profile(bot_id)


def get_all_active_bots() -> list:
    """Helper pour récupérer tous les bots actifs."""
    return supabase_client.get_all_active_bots()
