import re
import json
from typing import List, Dict, Optional

class AssistantRAG:
    """RAG system for retrieving relevant context about the AI assistant"""
    
    def __init__(self, knowledge_base_path: str = "assistant_knowledge_base.txt"):
        self.knowledge_base_path = knowledge_base_path
        self.knowledge_sections = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> Dict[str, List[str]]:
        """Load and parse the knowledge base file"""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Parse sections from markdown-style headers
            sections = {}
            current_section = None
            current_content = []
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('## '):
                    # Save previous section
                    if current_section and current_content:
                        sections[current_section] = current_content.copy()
                    
                    # Start new section
                    current_section = line[3:].strip()
                    current_content = []
                elif line.startswith('- ') and current_section:
                    # Add bullet point to current section
                    current_content.append(line[2:].strip())
                elif line and not line.startswith('#') and current_section:
                    # Add regular content to current section
                    current_content.append(line)
            
            # Save last section
            if current_section and current_content:
                sections[current_section] = current_content.copy()
            
            return sections
        except FileNotFoundError:
            print(f"Warning: Knowledge base file {self.knowledge_base_path} not found")
            return {}
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
            return {}
    
    def _calculate_relevance_score(self, query: str, content: str) -> float:
        """Calculate relevance score between query and content"""
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        content_words = set(re.findall(r'\b\w+\b', content.lower()))
        
        if not query_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = query_words.intersection(content_words)
        union = query_words.union(content_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def retrieve_context(self, query: str, max_context_length: int = 500) -> str:
        """Retrieve relevant context for a given query"""
        if not self.knowledge_sections:
            return ""
        
        # Calculate relevance scores for all content
        scored_content = []
        
        for section_name, content_list in self.knowledge_sections.items():
            section_content = " ".join(content_list)
            score = self._calculate_relevance_score(query, section_content)
            
            if score > 0:
                scored_content.append({
                    'section': section_name,
                    'content': section_content,
                    'score': score
                })
        
        # Sort by relevance score
        scored_content.sort(key=lambda x: x['score'], reverse=True)
        
        # Build context string
        context_parts = []
        current_length = 0
        
        for item in scored_content:
            section_text = f"{item['section']}: {item['content']}"
            
            if current_length + len(section_text) <= max_context_length:
                context_parts.append(section_text)
                current_length += len(section_text)
            else:
                # Truncate if needed
                remaining_space = max_context_length - current_length
                if remaining_space > 50:  # Only add if there's meaningful space
                    truncated_text = section_text[:remaining_space] + "..."
                    context_parts.append(truncated_text)
                break
        
        return " | ".join(context_parts)
    
    def get_identity_context(self) -> str:
        """Get core identity information"""
        identity_sections = ['Identity Information', 'Communication Style', 'Core Functions']
        context_parts = []
        
        for section in identity_sections:
            if section in self.knowledge_sections:
                content = " ".join(self.knowledge_sections[section])
                context_parts.append(f"{section}: {content}")
        
        return " | ".join(context_parts)
    
    def update_knowledge_base(self, new_content: str, section: str = "Additional Information"):
        """Add new content to the knowledge base"""
        try:
            with open(self.knowledge_base_path, 'a', encoding='utf-8') as file:
                file.write(f"\n\n## {section}\n")
                file.write(f"- {new_content}\n")
            
            # Reload knowledge base
            self.knowledge_sections = self._load_knowledge_base()
        except Exception as e:
            print(f"Error updating knowledge base: {e}")

# Global RAG instance
assistant_rag = AssistantRAG()
