# 🗺️ Plan d'Action - Bot Intelligence RandoMatch

> **Date :** 19 octobre 2025  
> **Version :** 3.0  
> **Objectif :** Implémenter un bot indistinguable d'un humain

---

## 📊 Audit de l'État Actuel

### ✅ Ce Qui Est Fait (Phases 1-2)

**Architecture de Base**
- ✅ Bridge Intelligence avec grouping (3s)
- ✅ Worker avec analyse contextuelle
- ✅ Timing Engine (thinking + typing)
- ✅ Pre-Processor (typing check, history, memory)
- ✅ Message Analyzer (urgency, complexity, tone)
- ✅ Intégration Grok 4 Fast

**Comportements Implémentés**
- ✅ Grouping messages rapides
- ✅ Délais adaptatifs (2-15s)
- ✅ Typing indicator
- ✅ Multi-messages naturels
- ✅ Chargement historique conversationnel
- ✅ Chargement bot_memory

**Status :** 🟡 Code complet, **PAS TESTÉ**, pas déployé

---

### ❌ Ce Qui Manque (Architecture Intelligente)

Basé sur le document **"Architecture d'un Bot Conversationnel Véritablement Intelligent"** :

#### 1. Mémoire Conversationnelle Évolutive ❌
**Actuellement :** Le worker charge la mémoire, mais ne la met jamais à jour  
**Manque :**
- Update automatique du trust_score après chaque échange
- Détection et sauvegarde des topics discutés
- Évolution du relationship_level (stranger → friend → complicity)
- Extraction des facts importants
- Détection sujets à éviter

#### 2. Capacité d'Initiation Post-Match ❌
**Actuellement :** Le bot attend TOUJOURS que l'user parle en premier  
**Manque :**
- Logique pour décider quand initier (40-60% des matchs)
- Timing d'initiation réaliste (15min-6h après match)
- Premier message personnalisé basé sur profil
- Utilisation des photos/bio/intérêts pour accroche

#### 3. Disponibilité Variable et Imprédictible ❌
**Actuellement :** Le bot répond toujours avec délais courts (2-15s)  
**Manque :**
- Horaires d'activité réalistes (actif 20h-23h, dormant la nuit)
- Délais variables selon heure du jour (10-45min en journée)
- Simulation d'activités (rando weekend → indisponible 2-6h)
- Absences spontanées non annoncées
- Retours après absence ("J'étais en rando")

#### 4. Engagement Proportionnel ❌
**Actuellement :** Engagement constant, répond toujours  
**Manque :**
- Détection engagement de l'user (monosyllabique = faible)
- Adaptation engagement du bot selon l'user
- Capacité de ne PAS relancer (40-50% des messages)
- Possibilité d'abandonner conversation (20-30%)
- Phases d'engagement (observation → intérêt → connexion)

#### 5. L'Art de Ne Pas Avoir le Dernier Mot ❌
**Actuellement :** Le bot répond systématiquement  
**Manque :**
- Logique pour accepter fin de conversation
- Pas de double relance si user ne répond pas
- Silence assumé après échange naturel
- Éviter sur-relance (max 1 relance par conversation)

#### 6. Relances Contextuelles Intelligentes ❌
**Actuellement :** Aucune relance proactive  
**Manque :**
- Relance après 3-7 jours de silence
- Basée sur mémoire ("Tu as fait ta rando finalement ?")
- Timing naturel (lundi soir si événement weekend)
- Personnalisée selon historique

#### 7. Adaptation Vocabulaire/Ton Selon Relation ❌
**Actuellement :** Ton constant  
**Manque :**
- Évolution du ton (formel → familier → complice)
- Utilisation progressive du prénom
- Inside jokes si relation établie
- Références à éléments partagés

#### 8. Détection et Adaptation Profil User ❌
**Actuellement :** Charge le profil mais utilisation limitée  
**Manque :**
- Références contextuelles à bio/intérêts
- Suggestions basées sur niveau rando
- Mentions spots locaux (département)
- Rebonds sur photos
- Adaptation vocabulaire selon âge

---

## 🎯 Plan d'Action en 7 Phases

### Phase 0️⃣ : Validation Base Existante ⭐ PRIORITÉ

**Objectif :** S'assurer que Phase 1-2 fonctionnent correctement  
**Durée :** 1-2 heures  
**Criticité :** 🔴 HAUTE

#### Actions Techniques

```bash
# 1. Activer l'environnement
cd /Users/anthony/Projects/randomatch-bot-service
source venv/bin/activate

# 2. Vérifier configuration
python -m app.test_config

# 3. Tester connexions
python -m app.test_all_connections

# 4. Test Bridge (Terminal 1)
python -m app.bridge_intelligence

# 5. Test Worker (Terminal 2)
python -m app.worker_intelligence

# 6. Test Grouping (Terminal 3)
python -m app.test_grouping
```

#### Checklist Validation

- [ ] Bridge se connecte à PostgreSQL
- [ ] Bridge se connecte à Redis
- [ ] Bridge écoute NOTIFY sans erreur
- [ ] Worker se connecte à tout (Supabase, Redis, OpenRouter)
- [ ] Worker attend messages dans queue
- [ ] Test grouping envoie messages
- [ ] Bridge détecte et groupe messages rapides
- [ ] Worker traite et répond avec délais naturels
- [ ] Typing indicator fonctionne
- [ ] Messages envoyés apparaissent dans Supabase

#### Résultats Attendus

✅ **Succès :** Logs propres, pas d'erreur, comportement naturel  
❌ **Échec :** Debug nécessaire avant de continuer

**Décision :**
- Si succès → Passer Phase 1
- Si échec → Fixer bugs, puis Phase 1

---

### Phase 1️⃣ : Memory Manager - Mémoire Évolutive

**Objectif :** Le bot se souvient et évolue naturellement  
**Durée :** 2-3 heures  
**Criticité :** 🔴 HAUTE

#### Fichiers à Créer

```
app/
├── memory_manager.py          # Gestionnaire mémoire bot
└── detectors/
    ├── __init__.py
    ├── topic_detector.py      # Détecte topics conversation
    ├── fact_extractor.py      # Extrait facts importants
    └── relationship_scorer.py # Calcule trust + relationship
```

#### Fonctionnalités Clés

**1. Update Automatique Trust Score**

```python
def update_trust_score(
    current_score: int,
    interaction_quality: str,  # positive/neutral/negative
    message_length: int,
    engagement_level: int
) -> int:
    """
    Ajuste trust_score après chaque interaction
    
    Facteurs :
    - Interaction positive : +2 à +5 points
    - Longueur message user : +1 si >100 chars
    - Engagement élevé : +2 points
    - Interaction négative : -3 points
    
    Max : 100, Min : 0
    """
```

**2. Détection Topics**

```python
def detect_topics(message: str, history: list) -> list:
    """
    Détecte topics mentionnés dans conversation
    
    Topics courants :
    - Rando (spots, niveaux, matériel)
    - Sport (trail, vélo, escalade)
    - Voyage (pays, villes)
    - Boulot (métier, projets)
    - Passions (photo, musique, lecture)
    
    Retourne : ['rando', 'photo', 'voyage']
    """
```

**3. Évolution Relationship Level**

```python
def calculate_relationship_level(
    trust_score: int,
    total_messages: int,
    positive_interactions: int
) -> str:
    """
    Détermine niveau de relation
    
    Levels :
    - stranger (0-20 trust, <5 messages)
    - acquaintance (20-40 trust, 5-15 messages)
    - friend (40-70 trust, 15-30 messages)
    - close_friend (70-90 trust, 30+ messages)
    - complicity (90-100 trust, 50+ messages)
    """
```

**4. Extraction Facts Importants**

```python
def extract_important_facts(
    message: str,
    context: dict
) -> list:
    """
    Extrait informations importantes à mémoriser
    
    Facts types :
    - Nom animal : "Mon chien s'appelle Rex"
    - Événements futurs : "Je pars en Corse la semaine prochaine"
    - Préférences fortes : "Je déteste le froid"
    - Anecdotes marquantes : "Je me suis perdu 6h en montagne"
    
    Retourne : [
        {"type": "event", "content": "Corse semaine prochaine", "date": "..."},
        {"type": "preference", "content": "Déteste le froid"}
    ]
    """
```

#### Intégration dans Worker

```python
# Dans worker_intelligence.py après envoi messages

# Update memory
await memory_manager.update_after_interaction(
    bot_id=bot_id,
    user_id=user_id,
    user_message=user_message,
    bot_response=response,
    analysis=analysis
)
```

#### Tests

```bash
# Test memory manager
python -m app.test_memory_manager

# Test avec vraie conversation
# Observer bot_memory table après échanges
```

#### Critères de Succès

- [ ] Trust score augmente après interaction positive
- [ ] Topics détectés et sauvegardés
- [ ] Relationship level évolue naturellement
- [ ] Facts importants extraits et mémorisés
- [ ] Pas d'erreur lors update mémoire

---

### Phase 2️⃣ : Initiation Intelligence - Premier Message

**Objectif :** Le bot peut initier la conversation après un match  
**Durée :** 2-3 heures  
**Criticité :** 🟡 MOYENNE-HAUTE

#### Fichiers à Créer

```
app/
├── initiation_manager.py      # Gestion initiation conversations
└── templates/
    ├── __init__.py
    └── first_messages.py      # Templates premiers messages
```

#### Logique Décision Initiation

**1. Quand Initier (40-60% des nouveaux matchs)**

```python
def should_initiate(bot_personality: dict, time_of_day: str) -> bool:
    """
    Décide si bot initie conversation
    
    Facteurs :
    - Personnalité bot (extraverti → 60%, introverti → 40%)
    - Random (pas systématique)
    - Heure du jour (éviter tard nuit)
    
    Retourne : True/False
    """
```

**2. Timing Initiation (15min - 6h après match)**

```python
def calculate_initiation_delay(
    match_time: datetime,
    bot_personality: dict,
    time_of_day: str
) -> int:
    """
    Calcule délai avant premier message
    
    Facteurs :
    - Base : 15min - 2h (pas instantané)
    - Si match en journée : attendre soirée (18h-22h)
    - Si match tard soir : attendre lendemain matin
    - Random variance : ±30min
    
    Retourne : délai en secondes
    """
```

**3. Construction Premier Message Personnalisé**

```python
def build_first_message(user_profile: dict, bot_profile: dict) -> str:
    """
    Crée premier message basé sur profil
    
    Stratégies :
    1. Référence photo spécifique
       "Salut ! Les gorges du Verdon sur ta photo ? J'adore cet endroit !"
    
    2. Intérêt commun
       "Hey ! J'ai vu qu'on aimait tous les deux le trail 😊"
    
    3. Bio mention
       "Hello ! Passionné de photographie aussi ?"
    
    4. Niveau rando
       "Salut [prénom] ! Expert en rando je vois 👀"
    
    5. Approche simple (fallback)
       "Salut [prénom] ! Comment ça va ?"
    
    Jamais générique. Toujours montrer qu'on a lu le profil.
    """
```

#### Système d'Événements

**Nouveau type d'événement : `new_match`**

```sql
-- Trigger sur table matches
CREATE OR REPLACE FUNCTION notify_new_match()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.user1_id IN (SELECT id FROM bot_profiles WHERE is_active = true)
       OR NEW.user2_id IN (SELECT id FROM bot_profiles WHERE is_active = true) THEN
        
        PERFORM pg_notify('bot_events', json_build_object(
            'type', 'new_match',
            'match_id', NEW.id,
            'bot_id', CASE 
                WHEN NEW.user1_id IN (SELECT id FROM bot_profiles) 
                THEN NEW.user1_id 
                ELSE NEW.user2_id 
            END,
            'user_id', CASE 
                WHEN NEW.user1_id IN (SELECT id FROM bot_profiles) 
                THEN NEW.user2_id 
                ELSE NEW.user1_id 
            END,
            'created_at', NEW.created_at
        )::text);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_new_match_notify
    AFTER INSERT ON matches
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_match();
```

#### Intégration Bridge

```python
# Dans bridge_intelligence.py

async def handle_notification(payload):
    event = json.loads(payload)
    
    if event['type'] == 'new_match':
        # Décider si initier
        if should_initiate():
            # Calculer délai
            delay = calculate_initiation_delay(...)
            
            # Scheduler initiation (Redis avec delay)
            await schedule_initiation(event, delay)
    
    elif event['type'] == 'message':
        # Flow normal
        ...
```

#### Tests

```bash
# Test initiation
python -m app.test_initiation

# Test réel : Créer nouveau match dans Supabase
# Observer si bot initie et comment
```

#### Critères de Succès

- [ ] Bot initie ~50% des nouveaux matchs
- [ ] Timing réaliste (pas instantané)
- [ ] Premier message personnalisé (jamais générique)
- [ ] Référence profil user (photo/bio/intérêts)
- [ ] Moment opportun (pas 3h du matin)

---

### Phase 3️⃣ : Availability Manager - Disponibilité Variable

**Objectif :** Le bot n'est pas toujours disponible instantanément  
**Durée :** 3-4 heures  
**Criticité :** 🟡 MOYENNE

#### Fichiers à Créer

```
app/
├── availability_manager.py    # Gestion disponibilité bot
├── activity_simulator.py      # Simule activités (rando, sport)
└── schedule/
    ├── __init__.py
    ├── time_zones.py          # Horaires activité
    └── events.py              # Événements vie (rando, boulot)
```

#### Horaires d'Activité Réalistes

```python
class AvailabilitySchedule:
    """
    Définit quand le bot est actif/inactif
    
    Plages horaires :
    - 7h-9h : Peu actif (réveil, préparation)
    - 9h-12h : Indisponible (travail)
    - 12h-14h : Moyennement actif (pause)
    - 14h-18h : Indisponible (travail)
    - 18h-20h : Moyennement actif (transition)
    - 20h-23h : TRÈS actif (prime time)
    - 23h-7h : Inactif (sommeil)
    
    Weekend : Plus flexible, mais périodes rando/sport
    """
    
    def get_response_delay_range(
        self,
        hour: int,
        day_of_week: int,
        analysis: dict
    ) -> tuple[int, int]:
        """
        Retourne (min_delay, max_delay) en secondes
        
        Exemples :
        - 21h (prime time) + urgent : (2, 8)
        - 14h (travail) + normal : (30*60, 2*3600) = 30min-2h
        - 3h (nuit) : Ne répond pas
        """
```

#### Simulation d'Activités

```python
class ActivitySimulator:
    """
    Simule activités qui rendent bot indisponible
    """
    
    def get_current_activity(self, bot_id: str) -> dict:
        """
        Vérifie si bot a une activité en cours
        
        Types activités :
        - rando_weekend : Indispo samedi 9h - dimanche 18h
        - sport : Indispo 1-2h
        - soirée : Indispo vendredi/samedi 20h-2h
        - travail_intense : Réponses très espacées plusieurs jours
        
        Retourne :
        {
            'active': True/False,
            'type': 'rando_weekend',
            'end_time': datetime,
            'excuse': "J'étais en rando, pas de réseau 😅"
        }
        """
    
    def schedule_random_activities(self, bot_id: str):
        """
        Programme activités aléatoires pour bot
        
        Fréquence :
        - Rando weekend : 1-2 fois par mois
        - Sport : 2-3 fois par semaine
        - Soirée : 1 fois par semaine
        """
```

#### Absences et Retours

```python
class ReturnManager:
    """
    Gère retours après absence
    """
    
    def should_explain_absence(
        self,
        absence_duration: int,  # minutes
        relationship_level: str
    ) -> bool:
        """
        Décide si expliquer l'absence
        
        Règles :
        - <30min : Jamais
        - 30min-2h : Rarement (20%)
        - 2h-6h : Parfois (50%)
        - >6h : Souvent (80%)
        - >24h : Toujours (100%)
        
        Plus la relation est forte, plus on explique
        """
    
    def generate_return_message(
        self,
        absence_reason: str,
        user_message: str
    ) -> str:
        """
        Génère message de retour
        
        Options :
        - Excuse simple : "Désolé j'étais occupé"
        - Activité spécifique : "J'étais en rando, pas de réseau"
        - Pas d'excuse : Reprend conversation directement
        """
```

#### Intégration Worker

```python
# Dans worker_intelligence.py

async def process_message(self, event_data: dict):
    ...
    
    # Avant traitement
    availability = await availability_manager.check_availability(
        bot_id, 
        current_time
    )
    
    if not availability['available']:
        # Bot indisponible
        delay = availability['available_at'] - current_time
        
        logger.info(f"🚫 Bot indisponible ({availability['reason']})")
        logger.info(f"⏳ Disponible dans {delay}s")
        
        # Reprogrammer message
        await schedule_delayed_response(event_data, delay)
        return
    
    # Si disponible, calculer délai adapté à l'heure
    base_delay = availability_manager.get_response_delay(
        current_hour,
        analysis
    )
    
    ...
```

#### Tests

```bash
# Test horaires
python -m app.test_availability

# Test activités
python -m app.test_activity_simulator

# Envoyer message à 15h (journée travail) → Délai long
# Envoyer message à 21h (prime time) → Délai court
```

#### Critères de Succès

- [ ] Réponses rapides 20h-23h
- [ ] Réponses lentes/absentes 9h-18h
- [ ] Indisponible la nuit (23h-7h)
- [ ] Absences simulées (rando weekend)
- [ ] Retours avec/sans excuse selon durée
- [ ] Variance naturelle des délais

---

### Phase 4️⃣ : Engagement Analyzer - Engagement Proportionnel

**Objectif :** Le bot adapte son engagement selon celui de l'user  
**Durée :** 2-3 heures  
**Criticité :** 🟢 MOYENNE

#### Fichiers à Créer

```
app/
├── engagement_analyzer.py     # Analyse engagement user
└── conversation_controller.py # Contrôle engagement bot
```

#### Détection Engagement User

```python
class EngagementAnalyzer:
    """
    Analyse niveau d'engagement de l'utilisateur
    """
    
    def analyze_user_engagement(
        self,
        recent_messages: list,  # 5-10 derniers
        user_id: str
    ) -> dict:
        """
        Détecte engagement user
        
        Indicateurs faible engagement :
        - Messages monosyllabiques ("ok", "cool", "ouais")
        - Pas de questions
        - Réponses courtes (<20 chars)
        - Délais longs entre messages
        - Pas de partage personnel
        
        Indicateurs fort engagement :
        - Messages longs (>100 chars)
        - Questions personnelles
        - Réponses rapides
        - Partage d'anecdotes
        - Emojis, humour
        
        Retourne :
        {
            'level': 'high' | 'medium' | 'low' | 'very_low',
            'score': 0-100,
            'indicators': {...}
        }
        """
```

#### Adaptation Engagement Bot

```python
class ConversationController:
    """
    Contrôle engagement bot selon user
    """
    
    def should_bot_respond(
        self,
        user_engagement: dict,
        conversation_history: list,
        bot_memory: dict
    ) -> dict:
        """
        Décide si bot doit répondre et comment
        
        Règles :
        - User engagement très faible (3+ msgs courts)
          → 50% chance abandon conversation
        
        - User ne pose jamais questions
          → Bot ne relance pas après 2-3 échanges
        
        - Conversation tourne en rond
          → Bot accepte silence
        
        - User met 2-3h à répondre
          → Bot peut mettre 1-2h aussi
        
        Retourne :
        {
            'should_respond': True/False,
            'engagement_level': 'high' | 'medium' | 'low',
            'should_ask_question': True/False,
            'should_use_multi_messages': True/False
        }
        """
    
    def detect_conversation_death(
        self,
        messages: list
    ) -> bool:
        """
        Détecte si conversation est morte
        
        Signes :
        - 3 échanges consécutifs très courts
        - User ne relance plus depuis 2-3 msgs
        - Même sujet répété sans profondeur
        - Délais croissants entre messages
        
        Si True → Bot arrête de répondre
        """
```

#### Logique "Ne Pas Avoir Dernier Mot"

```python
def should_have_last_word(context: dict) -> bool:
    """
    Décide si bot doit avoir le dernier mot
    
    Cas où bot NE répond PAS :
    - User dit "ok", "cool", "d'accord" (fin naturelle)
    - Bot vient d'envoyer 3-4 messages d'affilée
    - Bot a posé une question → Attend réponse
    - Conversation arrive à pause logique
    - Random 30% du temps (variabilité)
    
    Retourne : False dans 40-50% des cas
    """
```

#### Intégration Worker

```python
# Dans worker_intelligence.py

async def process_message(self, event_data: dict):
    ...
    
    # Analyser engagement user
    user_engagement = engagement_analyzer.analyze(
        context['history'],
        user_id
    )
    
    # Décider si répondre
    decision = conversation_controller.should_bot_respond(
        user_engagement,
        context['history'],
        context['memory']
    )
    
    if not decision['should_respond']:
        logger.info("🚫 Bot choisit de ne pas répondre (faible engagement)")
        return
    
    # Adapter prompt selon engagement
    prompt = self.build_prompt(
        ...,
        engagement_level=user_engagement['level']
    )
    
    ...
```

#### Tests

```bash
# Test engagement analyzer
python -m app.test_engagement

# Test conversation morte
# Envoyer 3-4 msgs monosyllabiques → Bot arrête
```

#### Critères de Succès

- [ ] Bot détecte faible engagement user
- [ ] Bot adapte son engagement proportionnellement
- [ ] Bot abandonne conversation si user désengagé
- [ ] Bot ne relance pas systématiquement
- [ ] Bot accepte silences naturels
- [ ] 40-50% du temps bot n'a pas dernier mot

---

### Phase 5️⃣ : Relance Manager - Relances Contextuelles

**Objectif :** Le bot peut relancer après plusieurs jours de silence  
**Durée :** 2-3 heures  
**Criticité :** 🟢 BASSE-MOYENNE

#### Fichiers à Créer

```
app/
├── relance_manager.py         # Gestion relances intelligentes
└── scheduler/
    ├── __init__.py
    └── delayed_messages.py    # Messages programmés
```

#### Logique Relance

```python
class RelanceManager:
    """
    Gère relances après silence prolongé
    """
    
    def should_relance(
        self,
        last_message_date: datetime,
        conversation_history: list,
        bot_memory: dict,
        relationship_level: str
    ) -> bool:
        """
        Décide si relancer conversation
        
        Conditions :
        - Silence > 3 jours
        - Dernière conversation était positive
        - Relationship level >= acquaintance
        - Pas plus d'une relance déjà tentée
        - Bot n'était pas le dernier à parler
        - Random (pas systématique)
        
        Fréquence :
        - 20-30% des conversations dormantes
        """
    
    def find_relance_hook(
        self,
        conversation_history: list,
        bot_memory: dict
    ) -> dict:
        """
        Trouve élément pour relancer naturellement
        
        Hooks possibles :
        1. Événement mentionné
           Mem: "Corse semaine prochaine"
           Hook: "Alors, c'était comment la Corse ?"
        
        2. Projet discuté
           Hist: "J'aimerais faire le GR20"
           Hook: "Tu as avancé sur ton projet GR20 ?"
        
        3. Passion partagée
           Mem: preferred_topics = ['photographie']
           Hook: "Au fait, tu as fait des photos récemment ?"
        
        4. Simple check-in (fallback)
           Hook: "Ça fait un moment ! Comment ça va ?"
        
        Retourne :
        {
            'type': 'event' | 'project' | 'passion' | 'checkup',
            'message': "...",
            'confidence': 0-100
        }
        """
```

#### Timing Relance

```python
def calculate_relance_timing(
    last_message_date: datetime,
    relationship_level: str
) -> datetime:
    """
    Détermine quand envoyer relance
    
    Règles :
    - Minimum 3 jours après dernier message
    - Maximum 7 jours (après c'est trop tard)
    - Moment opportun : lundi/mardi soir (21h)
    - Éviter weekend (paraît désespéré)
    - Pas la nuit
    
    Retourne : datetime de relance programmée
    """
```

#### Scheduler Redis

```python
class DelayedMessageScheduler:
    """
    Programme messages dans le futur
    """
    
    async def schedule_relance(
        self,
        match_id: str,
        bot_id: str,
        message: str,
        send_at: datetime
    ):
        """
        Programme une relance
        
        Stockage Redis :
        - Key: "scheduled_messages:{timestamp}"
        - Value: {match_id, bot_id, message}
        - TTL: Jusqu'à send_at
        
        Worker dédié vérifie scheduled messages
        """
    
    async def check_scheduled_messages(self):
        """
        Worker qui vérifie messages programmés
        
        Toutes les 5 minutes :
        - Scan "scheduled_messages:*"
        - Si timestamp passé → Envoie message
        - Supprime de Redis après envoi
        """
```

#### Intégration

**Nouveau worker : relance_worker.py**

```python
# app/relance_worker.py

async def scan_dormant_conversations():
    """
    Scan conversations dormantes (silence >3 jours)
    """
    
    # Query Supabase
    dormant = await supabase.query("""
        SELECT DISTINCT m.match_id, m.user1_id, m.user2_id
        FROM matches m
        WHERE m.last_message_at < NOW() - INTERVAL '3 days'
        AND EXISTS (
            SELECT 1 FROM messages msg 
            WHERE msg.match_id = m.id
        )
    """)
    
    for match in dormant:
        # Déterminer bot_id et user_id
        bot_id = get_bot_id(match)
        user_id = get_user_id(match)
        
        # Charger contexte
        history = await load_history(match['match_id'])
        memory = await load_memory(bot_id, user_id)
        
        # Décider si relancer
        if relance_manager.should_relance(history, memory):
            # Trouver hook
            hook = relance_manager.find_relance_hook(history, memory)
            
            # Calculer timing
            send_at = relance_manager.calculate_relance_timing(
                match['last_message_at'],
                memory['relationship_level']
            )
            
            # Scheduler
            await scheduler.schedule_relance(
                match['match_id'],
                bot_id,
                hook['message'],
                send_at
            )

# Lancer 1 fois par jour
```

**Update Procfile**

```
bridge: python -m app.bridge_intelligence
worker: python -m app.worker_intelligence
relance: python -m app.relance_worker
```

#### Tests

```bash
# Test relance manager
python -m app.test_relance

# Test réel :
# 1. Conversation dormante (>3 jours)
# 2. Observer si relance programmée
# 3. Vérifier message envoyé au bon moment
```

#### Critères de Succès

- [ ] Détecte conversations dormantes (>3j)
- [ ] Décide intelligemment si relancer
- [ ] Trouve hook contextuel (événement/passion)
- [ ] Timing naturel (lundi/mardi soir)
- [ ] Message personnalisé (jamais générique)
- [ ] Max 1 relance par conversation

---

### Phase 6️⃣ : Profile Adapter - Utilisation Profil User

**Objectif :** Le bot utilise contextuellement les données profil  
**Durée :** 1-2 heures  
**Criticité :** 🟢 BASSE

#### Fichiers à Créer

```
app/
└── profile_adapter.py         # Utilisation intelligente profil
```

#### Références Contextuelles

```python
class ProfileAdapter:
    """
    Injecte références profil naturellement
    """
    
    def suggest_local_spots(
        self,
        user_location: dict,
        hiking_level: str
    ) -> list:
        """
        Suggère spots locaux adaptés
        
        Exemples :
        - User dept 34 + beginner 
          → "Le Pic Saint-Loup est top pour débuter"
        
        - User dept 74 + expert
          → "Tu as fait le Mont Blanc ?"
        """
    
    def reference_bio_contextually(
        self,
        bio: str,
        conversation_context: str
    ) -> str:
        """
        Fait référence à bio naturellement
        
        User bio: "Passionné de photographie"
        Context: Discussion voyage
        
        Bot: "Tu as dû faire de super photos lors de ton voyage !"
        
        Jamais forcé. Seulement si pertinent.
        """
    
    def adapt_vocabulary_to_age(
        self,
        user_age: int
    ) -> dict:
        """
        Adapte vocabulaire selon âge
        
        18-25 ans :
        - Plus décontracté
        - Emojis fréquents
        - Refs culture récente
        
        40-55 ans :
        - Plus standard
        - Moins d'emojis
        - Vocabulaire classique
        """
```

#### Intégration Prompt

```python
# Dans build_prompt()

# Ajouter section profil user enrichie
user_context = f"""
PROFIL UTILISATEUR:
- Prénom: {user_profile['first_name']}
- Âge: {calculate_age(user_profile['birth_date'])}
- Localisation: {user_profile['city']}, {user_profile['department']}
- Niveau rando: {user_profile['hiking_level']}
- Bio: {user_profile['bio']}
- Intérêts: {', '.join(user_profile['interests'])}

CONTEXTE GÉOGRAPHIQUE:
{profile_adapter.get_local_context(user_profile['department'])}

SUGGESTIONS CONTEXTUELLES:
{profile_adapter.suggest_conversation_hooks(user_profile)}
"""
```

#### Tests

```bash
# Test profile adapter
python -m app.test_profile_adapter

# Test réel :
# Observer si bot mentionne spots locaux
# Vérifie adaptation vocabulaire selon âge
```

#### Critères de Succès

- [ ] Références spots locaux cohérents
- [ ] Mentions bio/intérêts contextuelles
- [ ] Adaptation vocabulaire selon âge
- [ ] Jamais générique ("T'aimes quoi ?")
- [ ] Toujours personnalisé

---

### Phase 7️⃣ : Tone Evolution - Évolution Ton/Relation

**Objectif :** Le ton évolue naturellement avec la relation  
**Durée :** 1-2 heures  
**Criticité :** 🟢 BASSE

#### Fichiers à Créer

```
app/
└── tone_manager.py            # Gestion évolution ton
```

#### Évolution du Ton

```python
class ToneManager:
    """
    Adapte ton selon évolution relation
    """
    
    def get_tone_instructions(
        self,
        relationship_level: str,
        total_messages: int,
        trust_score: int
    ) -> str:
        """
        Instructions ton selon relation
        
        Stranger (0-20 trust, <5 msgs):
        "Reste courtois et léger. Vouvoiement implicite dans 
        formulation. Pas de familiarités. Questions simples."
        
        Acquaintance (20-40 trust, 5-15 msgs):
        "Ton plus direct mais respectueux. Tu peux être légèrement 
        plus décontracté. Commence à partager un peu plus."
        
        Friend (40-70 trust, 15-30 msgs):
        "Ton naturel et chaleureux. Tu peux taquiner légèrement. 
        Partage plus personnel. Utilise prénom occasionnellement."
        
        Close Friend (70-90 trust, 30+ msgs):
        "Ton complice. Inside jokes possibles. Références à 
        éléments partagés. Utilise prénom régulièrement."
        
        Complicity (90-100 trust, 50+ msgs):
        "Ton authentique et intime. Vraie complicité établie. 
        Humour partagé. Références fréquentes au passé commun."
        """
    
    def detect_inside_jokes(
        self,
        conversation_history: list
    ) -> list:
        """
        Détecte inside jokes dans historique
        
        Patterns :
        - Répétition même blague/référence
        - Rires partagés sur sujet spécifique
        - Anecdote marquante mentionnée plusieurs fois
        
        Stocke dans bot_memory pour réutilisation
        """
```

#### Intégration

```python
# Dans build_prompt()

# Ajouter instructions ton adaptatif
tone_instructions = tone_manager.get_tone_instructions(
    memory['relationship_level'],
    memory['total_messages_exchanged'],
    memory['trust_score']
)

# Si inside jokes existent
inside_jokes = tone_manager.detect_inside_jokes(history)
if inside_jokes:
    tone_instructions += f"\n\nINSIDE JOKES: {inside_jokes}"
```

#### Tests

```bash
# Test tone manager
python -m app.test_tone_manager

# Vérifier évolution ton sur plusieurs conversations
```

#### Critères de Succès

- [ ] Ton formel au début
- [ ] Évolution progressive vers familiarité
- [ ] Utilisation prénom augmente avec relation
- [ ] Inside jokes détectés et réutilisés
- [ ] Ton cohérent avec trust_score

---

## 📊 Résumé des Priorités

### 🔴 HAUTE Priorité (Faire en premier)

1. **Phase 0 - Validation Base** ⭐
   - Tester Phase 1-2 existantes
   - Corriger bugs éventuels
   - Déployer sur Railway

2. **Phase 1 - Memory Manager**
   - Update automatique mémoire
   - Évolution trust_score
   - Détection topics/facts

3. **Phase 2 - Initiation**
   - Premier message post-match
   - Timing réaliste
   - Personnalisation profil

### 🟡 MOYENNE Priorité (Important mais pas critique)

4. **Phase 3 - Availability**
   - Horaires variables
   - Absences simulées
   - Délais selon heure

5. **Phase 4 - Engagement**
   - Adaptation engagement user
   - Ne pas avoir dernier mot
   - Abandon conversation

### 🟢 BASSE Priorité (Nice to have)

6. **Phase 5 - Relances**
   - Relances contextuelles
   - Scheduler messages

7. **Phase 6 - Profile Adapter**
   - Utilisation profil user
   - Références spots locaux

8. **Phase 7 - Tone Evolution**
   - Évolution ton naturelle
   - Inside jokes

---

## 🎯 Recommandation Immédiate

### Action #1 : Valider Phase 1-2 (Phase 0)

**Prochaine étape suggérée :**

```bash
cd /Users/anthony/Projects/randomatch-bot-service
source venv/bin/activate

# Test connexions
python -m app.test_all_connections

# Terminal 1
python -m app.bridge_intelligence

# Terminal 2
python -m app.worker_intelligence

# Observer logs, tester avec Flutter
```

**Si succès → Phase 1 (Memory Manager)**  
**Si échec → Debug et corriger**

---

## 📅 Timeline Estimée

| Phase | Durée | Cumul |
|-------|-------|-------|
| Phase 0 | 1-2h | 2h |
| Phase 1 | 2-3h | 5h |
| Phase 2 | 2-3h | 8h |
| Phase 3 | 3-4h | 12h |
| Phase 4 | 2-3h | 15h |
| Phase 5 | 2-3h | 18h |
| Phase 6 | 1-2h | 20h |
| Phase 7 | 1-2h | 22h |

**Total MVP (Phases 0-2) :** ~8h  
**Total Complet (Toutes phases) :** ~22h

---

## ✅ Checklist Validation Finale

### Bot Véritablement Intelligent

Lorsque toutes les phases sont complètes, le bot doit :

- [ ] Se souvenir de tout depuis le début
- [ ] Faire évoluer la relation naturellement
- [ ] Pouvoir initier conversations post-match
- [ ] Ne pas être toujours disponible instantanément
- [ ] Adapter engagement selon user
- [ ] Accepter silences et fins de conversation
- [ ] Relancer contextuellement après plusieurs jours
- [ ] Utiliser intelligemment données profil
- [ ] Évoluer son ton avec la relation

**Test ultime :** Un user ne peut pas déterminer si c'est un bot ou un humain.

---

**Prêt à commencer Phase 0 ? 🚀**