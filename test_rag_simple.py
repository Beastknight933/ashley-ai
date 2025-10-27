#!/usr/bin/env python3
"""
Simple test for RAG-enhanced OpenRouter GPT 5 Pro integration
"""

import requests
import json
from rag_system import assistant_rag

def test_openrouter_with_rag_simple():
    """Test OpenRouter API with RAG context directly"""
    print("Testing OpenRouter API with RAG context...")
    
    # Test query
    test_query = "What is your name?"
    
    # API key from medusa-ai(llm).py
    api_key = "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"
    
    try:
        # Retrieve relevant context from knowledge base
        context = assistant_rag.retrieve_context(test_query)
        
        # Create system message with identity context
        system_message = assistant_rag.get_identity_context()
        
        # Build the prompt with context
        if context:
            enhanced_prompt = f"""Context about me: {system_message}

Relevant information: {context}

User query: {test_query}

Please respond as Ashley, the AI assistant, using the context provided. Be helpful, professional, and address the user as "sir" when appropriate."""
        else:
            enhanced_prompt = f"""Context about me: {system_message}

User query: {test_query}

Please respond as Ashley, the AI assistant. Be helpful, professional, and address the user as "sir" when appropriate."""
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://medusa-ai.local",
                "X-Title": "medusa--ai",
            },
            data=json.dumps({
                "model": "openai/gpt-5-pro",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Ashley, a helpful AI assistant. Use the provided context to maintain your identity and respond appropriately."
                    },
                    {
                        "role": "user",
                        "content": enhanced_prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            })
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data["choices"][0]["message"]["content"].strip()
            
            print(f"SUCCESS! GPT 5 Pro responded with RAG context:")
            print(f"Query: {test_query}")
            print(f"Response: {response_text}")
            print(f"\nContext used: {context[:200]}...")
            return True
        else:
            print(f"API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error testing OpenRouter with RAG: {e}")
        return False

def main():
    """Run the test"""
    print("Testing RAG-enhanced OpenRouter GPT 5 Pro integration...")
    print("=" * 60)
    
    # Test RAG system first
    print("Testing RAG system...")
    print(f"Knowledge base loaded with {len(assistant_rag.knowledge_sections)} sections")
    
    test_query = "What is your name?"
    context = assistant_rag.retrieve_context(test_query)
    print(f"Context retrieved: {context[:100]}...")
    
    identity = assistant_rag.get_identity_context()
    print(f"Identity context: {identity[:100]}...")
    
    print("\nTesting OpenRouter API with RAG...")
    success = test_openrouter_with_rag_simple()
    
    if success:
        print("\nAll tests passed! RAG-enhanced OpenRouter integration is working!")
        print("\nKey features:")
        print("- Knowledge base loaded successfully")
        print("- Context retrieval working")
        print("- Identity context available")
        print("- OpenRouter API responding with RAG context")
        print("\nYour AI assistant will now remember its identity when using GPT 5 Pro!")
    else:
        print("\nThere might be an issue with the OpenRouter integration.")
        print("Please check your API key and internet connection.")

if __name__ == "__main__":
    main()
