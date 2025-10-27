"""
Persistent conversation memory and context management system for Ashley AI
"""

import sqlite3
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enhanced_logging import get_enhanced_logger
from enhanced_config import get_config

@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation"""
    id: Optional[int] = None
    timestamp: datetime = None
    user_input: str = ""
    intent: str = ""
    confidence: float = 0.0
    entities: Dict[str, Any] = None
    response: str = ""
    success: bool = True
    session_id: str = ""
    context_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.entities is None:
            self.entities = {}
        if self.context_data is None:
            self.context_data = {}

@dataclass
class UserPreference:
    """Represents a user preference"""
    id: Optional[int] = None
    key: str = ""
    value: str = ""
    category: str = "general"
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class ContextMemory:
    """Represents contextual memory for a session"""
    session_id: str = ""
    last_intent: str = ""
    last_entities: Dict[str, Any] = None
    conversation_topic: str = ""
    user_mood: str = "neutral"
    interaction_count: int = 0
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.last_entities is None:
            self.last_entities = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

class ConversationMemory:
    """Persistent conversation memory and context management"""
    
    def __init__(self, db_path: str = "ashley_ai.db"):
        self.config = get_config()
        self.logger = get_enhanced_logger("conversation_memory")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Memory settings
        self.retention_days = self.config.conversation_retention_days
        self.max_context_history = self.config.max_conversation_history
        
        self.logger.info("Conversation memory initialized", 
                        db_path=str(self.db_path),
                        retention_days=self.retention_days)
    
    def _init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Conversations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        user_input TEXT NOT NULL,
                        intent TEXT,
                        confidence REAL,
                        entities TEXT,
                        response TEXT,
                        success BOOLEAN,
                        session_id TEXT,
                        context_data TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # User preferences table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE NOT NULL,
                        value TEXT NOT NULL,
                        category TEXT DEFAULT 'general',
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Context memory table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS context_memory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        last_intent TEXT,
                        last_entities TEXT,
                        conversation_topic TEXT,
                        user_mood TEXT DEFAULT 'neutral',
                        interaction_count INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_intent ON conversations(intent)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_preferences_key ON user_preferences(key)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_context_session ON context_memory(session_id)')
                
                conn.commit()
                
        except Exception as e:
            self.logger.error("Failed to initialize database", exception=e)
            raise
    
    def save_conversation_turn(self, turn: ConversationTurn) -> bool:
        """Save a conversation turn to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO conversations 
                    (timestamp, user_input, intent, confidence, entities, response, success, session_id, context_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    turn.timestamp.isoformat(),
                    turn.user_input,
                    turn.intent,
                    turn.confidence,
                    json.dumps(turn.entities),
                    turn.response,
                    turn.success,
                    turn.session_id,
                    json.dumps(turn.context_data)
                ))
                
                turn.id = cursor.lastrowid
                conn.commit()
                
                self.logger.debug("Conversation turn saved", 
                                turn_id=turn.id,
                                session_id=turn.session_id,
                                intent=turn.intent)
                
                return True
                
        except Exception as e:
            self.logger.error("Failed to save conversation turn", 
                            session_id=turn.session_id, 
                            exception=e)
            return False
    
    def get_conversation_history(self, session_id: str, limit: int = None) -> List[ConversationTurn]:
        """Get conversation history for a session"""
        try:
            limit = limit or self.max_context_history
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, timestamp, user_input, intent, confidence, entities, 
                           response, success, session_id, context_data
                    FROM conversations 
                    WHERE session_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (session_id, limit))
                
                turns = []
                for row in cursor.fetchall():
                    turn = ConversationTurn(
                        id=row[0],
                        timestamp=datetime.fromisoformat(row[1]),
                        user_input=row[2],
                        intent=row[3],
                        confidence=row[4],
                        entities=json.loads(row[5]) if row[5] else {},
                        response=row[6],
                        success=bool(row[7]),
                        session_id=row[8],
                        context_data=json.loads(row[9]) if row[9] else {}
                    )
                    turns.append(turn)
                
                self.logger.debug("Conversation history retrieved", 
                                session_id=session_id,
                                count=len(turns))
                
                return turns
                
        except Exception as e:
            self.logger.error("Failed to get conversation history", 
                            session_id=session_id, 
                            exception=e)
            return []
    
    def get_recent_conversations(self, limit: int = 10) -> List[ConversationTurn]:
        """Get recent conversations across all sessions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, timestamp, user_input, intent, confidence, entities, 
                           response, success, session_id, context_data
                    FROM conversations 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                
                turns = []
                for row in cursor.fetchall():
                    turn = ConversationTurn(
                        id=row[0],
                        timestamp=datetime.fromisoformat(row[1]),
                        user_input=row[2],
                        intent=row[3],
                        confidence=row[4],
                        entities=json.loads(row[5]) if row[5] else {},
                        response=row[6],
                        success=bool(row[7]),
                        session_id=row[8],
                        context_data=json.loads(row[9]) if row[9] else {}
                    )
                    turns.append(turn)
                
                return turns
                
        except Exception as e:
            self.logger.error("Failed to get recent conversations", exception=e)
            return []
    
    def save_user_preference(self, preference: UserPreference) -> bool:
        """Save or update a user preference"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO user_preferences (key, value, category, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    preference.key,
                    preference.value,
                    preference.category,
                    preference.updated_at.isoformat()
                ))
                
                conn.commit()
                
                self.logger.debug("User preference saved", 
                                key=preference.key,
                                value=preference.value,
                                category=preference.category)
                
                return True
                
        except Exception as e:
            self.logger.error("Failed to save user preference", 
                            key=preference.key, 
                            exception=e)
            return False
    
    def get_user_preference(self, key: str) -> Optional[str]:
        """Get a user preference value"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT value FROM user_preferences WHERE key = ?', (key,))
                result = cursor.fetchone()
                
                if result:
                    self.logger.debug("User preference retrieved", key=key)
                    return result[0]
                else:
                    self.logger.debug("User preference not found", key=key)
                    return None
                    
        except Exception as e:
            self.logger.error("Failed to get user preference", 
                            key=key, 
                            exception=e)
            return None
    
    def get_all_preferences(self, category: str = None) -> Dict[str, str]:
        """Get all user preferences, optionally filtered by category"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if category:
                    cursor.execute('''
                        SELECT key, value FROM user_preferences 
                        WHERE category = ? 
                        ORDER BY updated_at DESC
                    ''', (category,))
                else:
                    cursor.execute('''
                        SELECT key, value FROM user_preferences 
                        ORDER BY updated_at DESC
                    ''')
                
                preferences = {row[0]: row[1] for row in cursor.fetchall()}
                
                self.logger.debug("User preferences retrieved", 
                                category=category,
                                count=len(preferences))
                
                return preferences
                
        except Exception as e:
            self.logger.error("Failed to get user preferences", 
                            category=category, 
                            exception=e)
            return {}
    
    def update_context_memory(self, session_id: str, context: ContextMemory) -> bool:
        """Update or create context memory for a session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if context exists
                cursor.execute('SELECT id FROM context_memory WHERE session_id = ?', (session_id,))
                exists = cursor.fetchone() is not None
                
                if exists:
                    cursor.execute('''
                        UPDATE context_memory 
                        SET last_intent = ?, last_entities = ?, conversation_topic = ?, 
                            user_mood = ?, interaction_count = ?, updated_at = ?
                        WHERE session_id = ?
                    ''', (
                        context.last_intent,
                        json.dumps(context.last_entities),
                        context.conversation_topic,
                        context.user_mood,
                        context.interaction_count,
                        context.updated_at.isoformat(),
                        session_id
                    ))
                else:
                    cursor.execute('''
                        INSERT INTO context_memory 
                        (session_id, last_intent, last_entities, conversation_topic, 
                         user_mood, interaction_count, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        session_id,
                        context.last_intent,
                        json.dumps(context.last_entities),
                        context.conversation_topic,
                        context.user_mood,
                        context.interaction_count,
                        context.created_at.isoformat(),
                        context.updated_at.isoformat()
                    ))
                
                conn.commit()
                
                self.logger.debug("Context memory updated", 
                                session_id=session_id,
                                intent=context.last_intent,
                                topic=context.conversation_topic)
                
                return True
                
        except Exception as e:
            self.logger.error("Failed to update context memory", 
                            session_id=session_id, 
                            exception=e)
            return False
    
    def get_context_memory(self, session_id: str) -> Optional[ContextMemory]:
        """Get context memory for a session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT last_intent, last_entities, conversation_topic, 
                           user_mood, interaction_count, created_at, updated_at
                    FROM context_memory 
                    WHERE session_id = ?
                ''', (session_id,))
                
                row = cursor.fetchone()
                if row:
                    context = ContextMemory(
                        session_id=session_id,
                        last_intent=row[0],
                        last_entities=json.loads(row[1]) if row[1] else {},
                        conversation_topic=row[2],
                        user_mood=row[3],
                        interaction_count=row[4],
                        created_at=datetime.fromisoformat(row[5]),
                        updated_at=datetime.fromisoformat(row[6])
                    )
                    
                    self.logger.debug("Context memory retrieved", session_id=session_id)
                    return context
                else:
                    self.logger.debug("Context memory not found", session_id=session_id)
                    return None
                    
        except Exception as e:
            self.logger.error("Failed to get context memory", 
                            session_id=session_id, 
                            exception=e)
            return None
    
    def get_conversation_context(self, session_id: str, limit: int = None) -> Dict[str, Any]:
        """Get comprehensive conversation context for a session"""
        try:
            # Get conversation history
            history = self.get_conversation_history(session_id, limit)
            
            # Get context memory
            context_memory = self.get_context_memory(session_id)
            
            # Analyze conversation patterns
            intents = [turn.intent for turn in history if turn.intent]
            entities = {}
            for turn in history:
                for key, value in turn.entities.items():
                    if key not in entities:
                        entities[key] = []
                    entities[key].extend(value if isinstance(value, list) else [value])
            
            # Determine conversation topic
            topic = self._analyze_conversation_topic(history)
            
            # Determine user mood
            mood = self._analyze_user_mood(history)
            
            context = {
                "session_id": session_id,
                "conversation_count": len(history),
                "recent_intents": intents[:5],  # Last 5 intents
                "common_entities": {k: list(set(v))[:3] for k, v in entities.items()},  # Top 3 per entity type
                "conversation_topic": topic,
                "user_mood": mood,
                "last_interaction": history[0].timestamp if history else None,
                "context_memory": asdict(context_memory) if context_memory else None,
                "conversation_history": [asdict(turn) for turn in history]
            }
            
            self.logger.debug("Conversation context generated", 
                            session_id=session_id,
                            topic=topic,
                            mood=mood)
            
            return context
            
        except Exception as e:
            self.logger.error("Failed to get conversation context", 
                            session_id=session_id, 
                            exception=e)
            return {}
    
    def _analyze_conversation_topic(self, history: List[ConversationTurn]) -> str:
        """Analyze conversation history to determine the main topic"""
        if not history:
            return "general"
        
        # Simple topic analysis based on intents and entities
        topic_keywords = {
            "weather": ["weather", "temperature", "forecast", "rain", "sunny"],
            "work": ["work", "meeting", "project", "deadline", "office"],
            "entertainment": ["music", "movie", "game", "fun", "entertainment"],
            "shopping": ["buy", "purchase", "shop", "store", "price"],
            "travel": ["travel", "trip", "flight", "hotel", "vacation"],
            "health": ["health", "doctor", "medicine", "exercise", "fitness"],
            "technology": ["computer", "software", "app", "tech", "programming"]
        }
        
        # Count topic mentions
        topic_scores = {topic: 0 for topic in topic_keywords}
        
        for turn in history:
            text = (turn.user_input + " " + turn.response).lower()
            for topic, keywords in topic_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        topic_scores[topic] += 1
        
        # Return the topic with the highest score
        if topic_scores:
            best_topic = max(topic_scores, key=topic_scores.get)
            if topic_scores[best_topic] > 0:
                return best_topic
        
        return "general"
    
    def _analyze_user_mood(self, history: List[ConversationTurn]) -> str:
        """Analyze conversation history to determine user mood"""
        if not history:
            return "neutral"
        
        mood_keywords = {
            "happy": ["happy", "great", "awesome", "excellent", "wonderful", "amazing"],
            "sad": ["sad", "depressed", "down", "upset", "disappointed"],
            "angry": ["angry", "mad", "frustrated", "annoyed", "irritated"],
            "excited": ["excited", "thrilled", "pumped", "energetic"],
            "calm": ["calm", "relaxed", "peaceful", "serene"],
            "confused": ["confused", "lost", "unclear", "don't understand"]
        }
        
        mood_scores = {mood: 0 for mood in mood_keywords}
        
        for turn in history:
            text = turn.user_input.lower()
            for mood, keywords in mood_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        mood_scores[mood] += 1
        
        # Return the mood with the highest score
        if mood_scores:
            best_mood = max(mood_scores, key=mood_scores.get)
            if mood_scores[best_mood] > 0:
                return best_mood
        
        return "neutral"
    
    def cleanup_old_data(self) -> int:
        """Clean up old conversation data based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete old conversations
                cursor.execute('''
                    DELETE FROM conversations 
                    WHERE timestamp < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_conversations = cursor.rowcount
                
                # Delete old context memory for sessions with no recent conversations
                cursor.execute('''
                    DELETE FROM context_memory 
                    WHERE session_id NOT IN (
                        SELECT DISTINCT session_id 
                        FROM conversations 
                        WHERE timestamp >= ?
                    )
                ''', (cutoff_date.isoformat(),))
                
                deleted_contexts = cursor.rowcount
                
                conn.commit()
                
                total_deleted = deleted_conversations + deleted_contexts
                
                self.logger.info("Old data cleaned up", 
                               deleted_conversations=deleted_conversations,
                               deleted_contexts=deleted_contexts,
                               total_deleted=total_deleted)
                
                return total_deleted
                
        except Exception as e:
            self.logger.error("Failed to cleanup old data", exception=e)
            return 0
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count conversations
                cursor.execute('SELECT COUNT(*) FROM conversations')
                conversation_count = cursor.fetchone()[0]
                
                # Count preferences
                cursor.execute('SELECT COUNT(*) FROM user_preferences')
                preference_count = cursor.fetchone()[0]
                
                # Count context memories
                cursor.execute('SELECT COUNT(*) FROM context_memory')
                context_count = cursor.fetchone()[0]
                
                # Count unique sessions
                cursor.execute('SELECT COUNT(DISTINCT session_id) FROM conversations')
                session_count = cursor.fetchone()[0]
                
                # Get database size
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    "conversation_count": conversation_count,
                    "preference_count": preference_count,
                    "context_count": context_count,
                    "session_count": session_count,
                    "database_size_mb": db_size / (1024 * 1024),
                    "retention_days": self.retention_days,
                    "max_context_history": self.max_context_history
                }
                
        except Exception as e:
            self.logger.error("Failed to get memory stats", exception=e)
            return {}

# Global memory instance
conversation_memory = ConversationMemory()

# Convenience functions
def save_conversation(user_input: str, intent: str, confidence: float, 
                     entities: Dict[str, Any], response: str, 
                     success: bool = True, session_id: str = "default") -> bool:
    """Save a conversation turn"""
    turn = ConversationTurn(
        user_input=user_input,
        intent=intent,
        confidence=confidence,
        entities=entities,
        response=response,
        success=success,
        session_id=session_id
    )
    return conversation_memory.save_conversation_turn(turn)

def get_conversation_history(session_id: str = "default", limit: int = None) -> List[Dict[str, Any]]:
    """Get conversation history for a session"""
    history = conversation_memory.get_conversation_history(session_id, limit)
    return [asdict(turn) for turn in history]

def get_user_preference(key: str) -> Optional[str]:
    """Get a user preference"""
    return conversation_memory.get_user_preference(key)

def set_user_preference(key: str, value: str, category: str = "general") -> bool:
    """Set a user preference"""
    preference = UserPreference(key=key, value=value, category=category)
    return conversation_memory.save_user_preference(preference)

def get_conversation_context(session_id: str = "default") -> Dict[str, Any]:
    """Get comprehensive conversation context"""
    return conversation_memory.get_conversation_context(session_id)

# Example usage and testing
if __name__ == "__main__":
    print("Testing Conversation Memory System")
    print("=" * 50)
    
    # Test saving conversation turns
    print("Testing conversation saving...")
    
    test_turns = [
        ConversationTurn(
            user_input="Hello Ashley",
            intent="greet",
            confidence=0.95,
            entities={},
            response="Hello! How can I help you today?",
            session_id="test_session_1"
        ),
        ConversationTurn(
            user_input="What's the weather like?",
            intent="weather",
            confidence=0.88,
            entities={"location": ["here"]},
            response="Let me check the weather for you.",
            session_id="test_session_1"
        ),
        ConversationTurn(
            user_input="Thank you",
            intent="thanks",
            confidence=0.92,
            entities={},
            response="You're welcome!",
            session_id="test_session_1"
        )
    ]
    
    for turn in test_turns:
        success = conversation_memory.save_conversation_turn(turn)
        print(f"Saved turn: {turn.user_input} -> {'Success' if success else 'Failed'}")
    
    # Test retrieving conversation history
    print("\nTesting conversation history retrieval...")
    history = conversation_memory.get_conversation_history("test_session_1")
    print(f"Retrieved {len(history)} conversation turns")
    
    for turn in history:
        print(f"  {turn.timestamp}: {turn.user_input} -> {turn.intent}")
    
    # Test user preferences
    print("\nTesting user preferences...")
    
    preferences = [
        UserPreference(key="favorite_voice", value="en-GB-LibbyNeural", category="voice"),
        UserPreference(key="wake_word", value="hey ashley", category="interaction"),
        UserPreference(key="response_style", value="friendly", category="personality")
    ]
    
    for pref in preferences:
        success = conversation_memory.save_user_preference(pref)
        print(f"Saved preference {pref.key}: {'Success' if success else 'Failed'}")
    
    # Test retrieving preferences
    all_prefs = conversation_memory.get_all_preferences()
    print(f"Retrieved {len(all_prefs)} preferences:")
    for key, value in all_prefs.items():
        print(f"  {key}: {value}")
    
    # Test conversation context
    print("\nTesting conversation context...")
    context = conversation_memory.get_conversation_context("test_session_1")
    print(f"Conversation topic: {context.get('conversation_topic', 'unknown')}")
    print(f"User mood: {context.get('user_mood', 'unknown')}")
    print(f"Recent intents: {context.get('recent_intents', [])}")
    
    # Test memory stats
    print("\nMemory statistics:")
    stats = conversation_memory.get_memory_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nConversation memory testing completed!")


