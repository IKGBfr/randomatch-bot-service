# 🗺️ Plan d'Action - Bot Intelligence Avancée

> **Date :** 19 octobre 2025  
> **Status :** Phase 3+ à implémenter  
> **Objectif :** Bot conversationnel véritablement intelligent et indétectable

---

## 🎯 État Actuel vs Vision

### ✅ Implémenté (Phases 1-2)

**Architecture de base :**
- ✅ Bridge Intelligence avec PostgreSQL NOTIFY
- ✅ Worker Intelligence avec analyse contextuelle
- ✅ Timing adaptatif basique (4-15s réflexion, 3-40s frappe)
- ✅ Multi-messages avec `[MSG_BREAK]`
- ✅ Typing indicator
- ✅ Chargement historique (50 messages) + bot_memory

**Comportements existants :**
- ✅ Délais variables selon urgency/complexity
- ✅ Réponses adaptées au contexte immédiat
- ✅ Détection émotions basique

### ❌ Manquant (Vision Architecture Intelligente)

**Initiation & Proactivité :**
- ❌ Système d'initiation post-match (premier message)
- ❌ Relances contextuelles basées sur mémoire
- ❌ Messages spontanés après silence

**Disponibilité Réaliste :**
- ❌ Délais variables 2min → 3h+ selon heure/jour
- ❌ Horaires d'activité réalistes (indispo 9-17h, actif 20-23h)
- ❌ Absences spontanées (2-6h)
- ❌ Peut "oublier" de répondre

**Intelligence Conversationnelle :**
- ❌ Engagement proportionnel au user
- ❌ Ne pas avoir le dernier mot (40-50% du temps)
- ❌ Abandonner conversations mortes (20-30%)
- ❌ Détection questions redondantes
- ❌ Évolution vocabulaire selon relation
- ❌ Gestion conversations qui s'éteignent

---

## 📐 Architecture Cible Complète

### Nouveaux Composants à Créer

```
1. Match Monitor (Railway)
   ↓
2. Initiation Scheduler (Redis)
   ↓
3. Availability Manager (contrôle délais)
   ↓
4. Engagement Analyzer (décide si répondre)
   ↓
5. Conversation Manager (track état relation)
   ↓
6. Memory Analyzer (évite redondances)
   ↓
7. Response Scheduler (peut attendre 3h+)
```

---

## 🚀 Plan d'Implémentation par Phase

### Phase 3 : Système d'Initiation Post-Match (4-5h)

**Objectif :** Le bot peut envoyer le premier message après un nouveau match

#### 3.1 - Match Monitor (2h)

**Nouveau service** : `app/match_monitor.py`

```python
"""
Surveille les nouveaux matchs et décide si initier
"""
class MatchMonitor:
    async def monitor_new_matches(self):
        """Poll matches table pour nouveaux matchs"""
        
    def should_initiate(self, bot_profile, user_profile) -> tuple[bool, delay]:
        """
        Décide si initier et quand
        Returns: (should_init, delay_seconds)
        """
        # 40-60% chance selon personnalité bot
        # Délai : 15min à 6h
        
    def build_first_message(self, user_profile) -> str:
        """
        Construit premier message personnalisé
        Utilise bio, intérêts, photos, level rando
        """
```

**Fichiers à modifier :**
- Nouveau : `app/match_monitor.py`
- Nouveau : `app/initiation_builder.py`
- Update : `Procfile` (ajouter process monitor)

**Tests :**
```bash
# Créer nouveau match dans Supabase
# Vérifier que bot initie dans 15min-6h
# Vérifier message personnalisé
```

#### 3.2 - Initiation Scheduler (1h)

**Table Supabase** : `bot_initiations`

```sql
CREATE TABLE bot_initiations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id uuid REFERENCES matches(id),
  bot_id uuid REFERENCES profiles(id),
  user_id uuid REFERENCES profiles(id),
  scheduled_for timestamp NOT NULL,
  status text DEFAULT 'pending',  -- pending/sent/cancelled
  first_message text,
  created_at timestamp DEFAULT now()
);
```

**Logic :**
- Match détecté → should_initiate() → Schedule dans Redis
- Worker check scheduled initiations
- Si user envoie message avant → Cancel initiation

#### 3.3 - Tests & Validation (1h)

**Scénarios à tester :**
1. ✅ Nouveau match → Bot initie dans délai
2. ✅ Message personnalisé utilisé
3. ✅ Si user envoie avant → Bot répond normalement
4. ✅ 40-60% des matchs seulement

---

### Phase 4 : Disponibilité Variable Réaliste (6-8h)

**Objectif :** Délais variables de 2min à 3h+ selon contexte

#### 4.1 - Availability Manager (3h)

**Nouveau composant** : `app/availability_manager.py`

```python
class AvailabilityManager:
    def calculate_response_delay(
        self,
        current_time: datetime,
        day_of_week: str,
        last_user_message_time: datetime,
        conversation_quality: float,
        bot_profile: dict
    ) -> int:
        """
        Retourne délai en secondes (120 → 10800+)
        
        Facteurs :
        - Heure : 20-23h = rapide, 9-17h = lent/pas dispo
        - Jour : weekend = plus flexible
        - Qualité convo : bonne = rapide, mauvaise = lent
        - Humeur bot : random variance
        """
```

**Horaires d'activité par défaut :**
```python
ACTIVITY_SCHEDULE = {
    'weekday': {
        '7-9h': 'low',      # Réveil, prépa → délais 30min-2h
        '9-12h': 'offline',  # Travail → peut ne pas répondre
        '12-14h': 'medium',  # Pause déj → 10-30min
        '14-18h': 'offline', # Travail → peut ne pas répondre
        '18-20h': 'medium',  # Retour → 5-20min
        '20-23h': 'high',    # ⭐ Peak → 2-10min
        '23-7h': 'offline'   # Dodo → ne répond pas
    },
    'weekend': {
        '8-12h': 'medium',   # Matinée → 10-30min
        '12-20h': 'variable', # Activités → 30min-3h
        '20-23h': 'high',    # Soirée → 2-10min
        '23-8h': 'offline'   # Dodo
    }
}
```

**Absences spontanées :**
```python
def trigger_spontaneous_absence(self) -> tuple[bool, duration]:
    """
    Probabilité 10-15% de s'absenter spontanément
    Durée : 2-6h
    Raisons : rando, sport, soirée, travail intense
    """
```

#### 4.2 - Response Scheduler (2h)

**Table Supabase** : `scheduled_responses`

```sql
CREATE TABLE scheduled_responses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id uuid REFERENCES matches(id),
  bot_id uuid REFERENCES profiles(id),
  user_message_id uuid REFERENCES messages(id),
  scheduled_for timestamp NOT NULL,
  status text DEFAULT 'pending',
  context_snapshot jsonb,
  created_at timestamp DEFAULT now()
);
```

**Logic :**
- Message reçu → Calculate delay (peut être 3h)
- Schedule response dans table
- Worker check scheduled_responses
- Si user envoie nouveau message avant → Re-évaluer

#### 4.3 - Tests & Validation (1h)

**Scénarios :**
1. ✅ Message 20h → Réponse 2-10min
2. ✅ Message 10h (travail) → Réponse 1-3h ou pas du tout
3. ✅ Message 3h nuit → Réponse matin 8-9h
4. ✅ Absence spontanée déclenchée → 2-6h
5. ✅ Conversation bonne → Délais courts
6. ✅ Conversation mauvaise → Délais longs

---

### Phase 5 : Engagement Variable & Non-Relance (4-5h)

**Objectif :** Ne pas relancer systématiquement, adapter engagement au user

#### 5.1 - Engagement Analyzer (2h)

**Nouveau composant** : `app/engagement_analyzer.py`

```python
class EngagementAnalyzer:
    def analyze_user_engagement(self, history: list) -> dict:
        """
        Retourne score engagement user 0-100
        
        Indicateurs engagement élevé :
        - Messages longs (>50 chars)
        - Questions personnelles
        - Partage anecdotes
        - Émojis
        - Répond rapidement
        
        Indicateurs engagement faible :
        - Monosyllabique ("ok", "ouais", "cool")
        - Jamais de questions
        - Délais très longs
        - Messages courts (<15 chars)
        """
    
    def should_respond(
        self,
        user_engagement: int,
        conversation_age_days: int,
        last_messages: list
    ) -> tuple[bool, reason]:
        """
        Décide si répondre ou abandonner
        
        Ne répond PAS si :
        - User monosyllabique 3+ fois
        - User ne relance plus depuis 2+ messages
        - Conversation tourne en rond
        - User engagement < 30
        
        Returns: (should_respond, reason)
        """
    
    def should_have_last_word(self) -> bool:
        """
        40-50% du temps, bot N'A PAS le dernier mot
        """
        return random.random() < 0.55  # 55% chance d'avoir dernier mot
```

#### 5.2 - Conversation Manager (2h)

**Nouveau composant** : `app/conversation_manager.py`

```python
class ConversationManager:
    def get_conversation_phase(self, messages_count: int) -> str:
        """
        Returns: 'observation', 'interest', 'connection', 'complicity'
        
        observation: 1-5 messages
        interest: 6-15 messages
        connection: 16-30 messages
        complicity: 30+ messages
        """
    
    def is_conversation_dying(self, last_messages: list) -> bool:
        """
        Détecte si conversation meurt
        
        Signes :
        - 3 échanges courts successifs
        - User ne relance plus
        - Messages espacés de plus en plus
        - Topics répétitifs
        """
    
    def should_abandon_conversation(
        self,
        engagement_score: int,
        days_since_start: int,
        is_dying: bool
    ) -> bool:
        """
        20-30% des conversations abandonnées
        """
```

#### 5.3 - Update Worker (1h)

**Modifier** : `app/worker_intelligence.py`

```python
async def process_message(self, event_data: dict):
    # ... existing code ...
    
    # NOUVEAU : Check engagement avant de répondre
    user_engagement = engagement_analyzer.analyze_user_engagement(
        context['history']
    )
    
    should_respond, reason = engagement_analyzer.should_respond(
        user_engagement,
        conversation_age_days,
        context['history'][-5:]
    )
    
    if not should_respond:
        logger.info(f"🚫 Ne répond pas : {reason}")
        return  # Abandonne la conversation
    
    # NOUVEAU : Décider si avoir dernier mot
    if not engagement_analyzer.should_have_last_word():
        logger.info("🤐 Pas le dernier mot cette fois")
        return  # Ne répond pas pour laisser respirer
    
    # ... continuer le traitement normal ...
```

---

### Phase 6 : Intelligence Conversationnelle (5-6h)

**Objectif :** Évolution vocabulaire, détection redondances, mémoire avancée

#### 6.1 - Memory Analyzer (2h)

**Nouveau composant** : `app/memory_analyzer.py`

```python
class MemoryAnalyzer:
    def extract_facts(self, history: list) -> dict:
        """
        Extrait facts mentionnés par user
        
        Returns: {
            'user_name': 'Anthony',
            'user_location': 'Lyon',
            'user_job': 'Développeur',
            'user_hobbies': ['trail', 'escalade'],
            'mentioned_events': [
                {'what': 'rando GR20', 'when': 'le mois prochain'}
            ]
        }
        """
    
    def has_asked_before(self, question: str, history: list) -> bool:
        """
        Détecte si question similaire déjà posée
        
        Utilise similarité sémantique
        """
    
    def find_relance_opportunities(
        self,
        history: list,
        days_since_last: int
    ) -> list:
        """
        Trouve occasions de relancer basé sur mémoire
        
        Exemples :
        - User a dit "je pars en rando ce weekend"
        - Maintenant lundi → "Alors, ta rando ?"
        """
```

#### 6.2 - Vocabulary Adapter (2h)

**Nouveau composant** : `app/vocabulary_adapter.py`

```python
class VocabularyAdapter:
    def get_tone_for_phase(self, phase: str) -> dict:
        """
        Adapte ton selon phase relation
        
        observation (1-5 msgs):
        - Conditionnel, poli
        - "Tu aurais des recommandations ?"
        
        interest (6-15 msgs):
        - Plus direct
        - "Tu recommandes quoi ?"
        
        connection (16-30 msgs):
        - Décontracté
        - "carrément", "grave"
        
        complicity (30+ msgs):
        - Très naturel
        - Prénom fréquent
        - Inside jokes
        """
    
    def adapt_response_vocabulary(
        self,
        response: str,
        phase: str,
        trust_score: int
    ) -> str:
        """
        Modifie vocabulaire selon contexte
        """
```

#### 6.3 - Integration dans Prompt (1h)

**Modifier** : `app/worker_intelligence.py`

```python
def build_prompt(self, ...):
    # ... existing code ...
    
    # NOUVEAU : Instructions vocabulaire adaptées
    phase = conversation_manager.get_conversation_phase(
        len(context['history'])
    )
    
    tone_instructions = vocabulary_adapter.get_tone_for_phase(phase)
    
    # NOUVEAU : Check questions déjà posées
    if memory_analyzer.has_asked_similar_before(history):
        instructions += "\n- NE REPOSE PAS de question similaire déjà posée"
    
    # NOUVEAU : Opportunités de relance
    relance_opps = memory_analyzer.find_relance_opportunities(
        history,
        days_since_last
    )
    
    if relance_opps:
        instructions += f"\n- Tu peux rebondir sur : {relance_opps[0]}"
```

---

## 🗓️ Timeline Estimée

| Phase | Fonctionnalité | Temps Estimé | Priorité |
|-------|---------------|--------------|----------|
| **Phase 3** | Initiation Post-Match | 4-5h | ⭐⭐⭐ Haute |
| **Phase 4** | Disponibilité Variable | 6-8h | ⭐⭐⭐ Haute |
| **Phase 5** | Engagement Variable | 4-5h | ⭐⭐ Moyenne |
| **Phase 6** | Intelligence Avancée | 5-6h | ⭐ Basse |
| **Total** | | **20-24h** | |

**Rythme recommandé :** 1 phase par semaine = 1 mois pour tout implémenter

---

## 📊 Critères de Succès

### Phase 3 : Initiation
- [ ] 40-60% des matchs initiés par bot
- [ ] Délai 15min-6h respecté
- [ ] Message personnalisé unique
- [ ] Pas de conflit si user initie avant

### Phase 4 : Disponibilité
- [ ] Délais variables 2min → 3h+ observés
- [ ] Horaires d'activité respectés
- [ ] Absences spontanées déclenchées
- [ ] Bot peut "oublier" de répondre

### Phase 5 : Engagement
- [ ] 40-50% conversations sans dernier mot bot
- [ ] 20-30% conversations abandonnées
- [ ] Engagement proportionnel au user
- [ ] Conversations mortes détectées

### Phase 6 : Intelligence
- [ ] Vocabulaire évolue avec relation
- [ ] Zéro question redondante
- [ ] Relances contextuelles réussies
- [ ] Facts extraits de l'historique

---

## 🧪 Plan de Tests Global

### Tests Unitaires
```bash
pytest app/tests/test_availability_manager.py
pytest app/tests/test_engagement_analyzer.py
pytest app/tests/test_memory_analyzer.py
```

### Tests d'Intégration

**Scénario 1 : Nouveau Match**
1. Créer match dans Supabase
2. Vérifier initiation schedulée
3. Attendre délai
4. Vérifier message personnalisé envoyé

**Scénario 2 : Conversation Normale**
1. User envoie message à 21h
2. Bot répond 3-8min après
3. User répond
4. Bot peut ne pas avoir dernier mot

**Scénario 3 : Conversation Morte**
1. User envoie 3 "ok" successifs
2. Bot détecte engagement faible
3. Bot abandonne conversation

**Scénario 4 : Horaires**
1. User envoie message 10h (travail)
2. Bot ne répond pas ou répond 2-3h après
3. User envoie message 21h
4. Bot répond rapidement

**Scénario 5 : Évolution Relation**
1. Messages 1-5 : Ton poli
2. Messages 10-20 : Ton direct
3. Messages 30+ : Ton complice, inside jokes

---

## 🚀 Quick Start - Commencer Phase 3

```bash
cd /Users/anthony/Projects/randomatch-bot-service

# Créer branch
git checkout -b feat/phase3-initiation

# Créer fichiers
touch app/match_monitor.py
touch app/initiation_builder.py
touch app/tests/test_match_monitor.py

# SQL
touch sql/bot_initiations_table.sql

# Doc
touch docs/Phase3-Initiation.md
```

---

## 💡 Notes Importantes

### Principe Clé : Simplicité d'Abord

Chaque phase doit :
1. ✅ Fonctionner en isolation
2. ✅ Être testable indépendamment
3. ✅ Ne pas casser les phases précédentes
4. ✅ Avoir des toggles on/off

### Configuration par Bot Profile

Ajouter colonnes à `bot_profiles` :

```sql
ALTER TABLE bot_profiles ADD COLUMN initiation_probability float DEFAULT 0.5;
ALTER TABLE bot_profiles ADD COLUMN activity_schedule jsonb;
ALTER TABLE bot_profiles ADD COLUMN engagement_threshold int DEFAULT 30;
```

### Monitoring Essentiel

Créer dashboard avec :
- Taux d'initiation par bot
- Distribution délais de réponse
- Taux d'abandon conversations
- Score engagement moyen users
- Questions redondantes détectées

---

## 🔄 Rollback Plan

Si Phase X pose problème :

```bash
# Désactiver feature
UPDATE bot_profiles SET feature_enabled = false WHERE feature = 'phase_X';

# Rollback code
git revert HEAD

# Redeploy
git push origin main
```

---

**Prêt à commencer Phase 3 ? Besoin de plus de détails sur une phase ?** 🚀
