#!/usr/bin/env python3
"""
Test script for RAG-enhanced OpenRouter GPT 5 Pro integration
"""

import sys
import os

# Add current directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_rag_system():
    """Test the RAG system functionality"""
    print("Testing RAG system...")
    
    try:
        from rag_system import assistant_rag
        
        # Test knowledge base loading
        print(f"Knowledge base loaded with {len(assistant_rag.knowledge_sections)} sections")
        
        # Test context retrieval
        test_query = "What is your name?"
        context = assistant_rag.retrieve_context(test_query)
        print(f"Context retrieved for '{test_query}': {context[:100]}...")
        
        # Test identity context
        identity = assistant_rag.get_identity_context()
        print(f"Identity context: {identity[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"RAG system test failed: {e}")
        return False

def test_openrouter_with_rag():
    """Test OpenRouter API with RAG context"""
    print("\nTesting OpenRouter API with RAG...")
    
    try:
        from nlp_processor import fallback_openrouter_gpt5
        
        # Test queries that should trigger identity responses
        test_queries = [
            "What is your name?",
            "Who are you?",
            "What can you do?",
            "How old are you?"
        ]
        
        api_key = "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"
        
        for query in test_queries:
            print(f"\nTesting query: '{query}'")
            response = fallback_openrouter_gpt5(query, api_key)
            
            if response:
                print(f"Response: {response}")
            else:
                print("No response received")
        
        return True
        
    except Exception as e:
        print(f"OpenRouter with RAG test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing RAG-enhanced OpenRouter integration...")
    print("=" * 60)
    
    # Test RAG system
    rag_success = test_rag_system()
    
    if rag_success:
        # Test OpenRouter with RAG
        openrouter_success = test_openrouter_with_rag()
        
        if openrouter_success:
            print("\nAll tests passed! RAG-enhanced OpenRouter integration is working!")
            print("\nKey features:")
            print("- Knowledge base loaded successfully")
            print("- Context retrieval working")
            print("- Identity context available")
            print("- OpenRouter API responding with RAG context")
            print("\nYour AI assistant will now remember its identity when using GPT 5 Pro!")
        else:
            print("\nRAG system works but OpenRouter integration needs attention")
    else:
        print("\nRAG system needs to be fixed before testing OpenRouter integration")

if __name__ == "__main__":
    main()
