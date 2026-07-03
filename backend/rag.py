"""
RAG (Retrieval-Augmented Generation) Processor
Handles prompt construction, LLM calls, and response generation
"""

import requests
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class RAGProcessor:
    """
    Processes queries using retrieved context and LLM
    
    Pipeline:
    1. Build prompt with retrieved chunks
    2. Call Ollama API
    3. Parse and structure response
    4. Add source citations
    """
    
    def __init__(self, 
                 ollama_url: str = "http://localhost:11434/api/generate",
                 model_name: str = "phi3:mini"):
        """
        Initialize the RAG Processor
        
        Args:
            ollama_url (str): Ollama API endpoint
            model_name (str): Model to use for generation
        """
        self.ollama_url = ollama_url
        self.model_name = model_name
        
        # System prompt for consistent behavior
        self.system_prompt = """You are a helpful, accurate AI assistant. 
You must:
1. ONLY use information from the provided context
2. If the context doesn't contain the answer, clearly say so
3. Be concise but thorough
4. Use a professional, clear tone
5. Cite sources when possible"""
        
        logger.info(f"🚀 RAG Processor initialized with model: {model_name}")
        logger.info(f"🔗 Ollama endpoint: {ollama_url}")
    
    def check_ollama_status(self) -> bool:
        """
        Check if Ollama is running and responsive
        
        Returns:
            bool: True if Ollama is accessible
        """
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Ollama is running")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Ollama not accessible: {str(e)}")
            return False
    
    def build_prompt(self, query: str, context_chunks: List[str]) -> str:
        """
        Build a structured prompt with context
        
        Args:
            query (str): User's question
            context_chunks (List[str]): Retrieved text chunks
            
        Returns:
            str: Complete prompt for LLM
        """
        # Prepare context
        context = "\n\n---\n\n".join([
            f"Context {i+1}:\n{chunk}" 
            for i, chunk in enumerate(context_chunks)
        ])
        
        # Build the prompt
        prompt = f"""{self.system_prompt}

--- CONTEXT ---
{context}

--- QUESTION ---
{query}

--- INSTRUCTIONS ---
Based on the context provided above, answer the question.
If the context doesn't contain relevant information, say:
"I don't have enough information to answer this question based on the provided documents."

Your answer should be clear, accurate, and directly reference the context when possible.

--- ANSWER ---
"""
        
        logger.debug(f"📝 Prompt built (length: {len(prompt)} characters)")
        return prompt
    
    def generate_answer(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Generate answer using Ollama
        
        Args:
            prompt (str): Prompt to send to LLM
            temperature (float): Creativity parameter (0-1)
            
        Returns:
            str: Generated answer
        """
        try:
            logger.info(f"🤖 Calling Ollama with model: {self.model_name}")
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "num_ctx": 2048,  # Context window
                    "num_predict": 512  # Max tokens to generate
                }
            }
            
            # Call Ollama API
            start_time = datetime.now()
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=90  # 90 second timeout
            )
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "").strip()
                
                logger.info(f"✅ Answer generated in {elapsed:.2f}s ({len(generated_text)} chars)")
                return generated_text
            else:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                logger.error(f"❌ {error_msg}")
                return f"Error: {error_msg}"
                
        except requests.Timeout:
            logger.error("❌ Ollama request timed out")
            return "Error: Request timed out. Please try again."
        except requests.ConnectionError:
            logger.error("❌ Cannot connect to Ollama")
            return "Error: Cannot connect to Ollama. Make sure it's running with `ollama serve`"
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            return f"Error: {str(e)}"
    
    def process_query(self, query: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a query through the full RAG pipeline
        
        Args:
            query (str): User's question
            search_results (Dict): Results from vector search
            
        Returns:
            Dict: Answer with sources and metadata
        """
        logger.info(f"🔄 Processing query: '{query[:50]}...'")
        
        # Step 1: Extract documents from search results
        documents = search_results.get('documents', [[]])[0]
        metadatas = search_results.get('metadatas', [[]])[0]
        distances = search_results.get('distances', [[]])[0]
        
        # Step 2: Log retrieval metrics
        logger.info(f"📊 Retrieved {len(documents)} chunks")
        if distances:
            avg_distance = sum(distances) / len(distances)
            logger.info(f"📏 Average similarity distance: {avg_distance:.4f}")
        
        # Step 3: Build prompt with context
        prompt = self.build_prompt(query, documents)
        
        # Step 4: Generate answer
        answer = self.generate_answer(prompt)
        
        # Step 5: Prepare sources for citation
        sources = []
        for i, metadata in enumerate(metadatas):
            source = {
                "document": metadata.get('document', 'Unknown'),
                "chunk_index": metadata.get('chunk_index', 0),
                "chunk_total": metadata.get('chunk_total', 0),
                "distance": distances[i] if i < len(distances) else None,
                "relevance_score": 1 - distances[i] if i < len(distances) else None,
                "preview": documents[i][:200] + "..." if documents[i] and len(documents[i]) > 200 else documents[i] if documents[i] else ""
            }
            sources.append(source)
        
        # Step 6: Structure response
        response = {
            "answer": answer,
            "sources": sources,
            "chunks_used": len(documents),
            "model_used": self.model_name,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Query processed successfully (used {len(documents)} chunks)")
        return response
    
    def stream_answer(self, query: str, search_results: Dict[str, Any]):
        """
        Stream answer token by token (for real-time responses)
        
        Args:
            query (str): User's question
            search_results (Dict): Results from vector search
            
        Yields:
            str: Token chunks as they're generated
        """
        # Step 1: Extract documents
        documents = search_results.get('documents', [[]])[0]
        
        # Step 2: Build prompt
        prompt = self.build_prompt(query, documents)
        
        # Step 3: Stream from Ollama
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 512
                }
            }
            
            response = requests.post(
                self.ollama_url,
                json=payload,
                stream=True,
                timeout=90
            )
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if 'response' in data:
                            yield data['response']
                        if data.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Streaming error: {str(e)}")
            yield f"Error: {str(e)}"
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available Ollama models
        
        Returns:
            List[str]: Available model names
        """
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                logger.info(f"📚 Available models: {models}")
                return models
            return []
        except Exception as e:
            logger.error(f"❌ Error getting models: {str(e)}")
            return []