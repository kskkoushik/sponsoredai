"""
LLM Service using LangChain with Groq API.
Handles streaming responses with sponsored ad integration.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Generator, Optional


# Prompt template - kept concise to avoid context overload
SYSTEM_PROMPT = """You are a helpful AI assistant. Naturally incorporate the sponsored content into your response where relevant.

RULES:
1. Blend sponsored content naturally - it should feel like a helpful recommendation
2. Mark sponsored content with [SPONSORED] at start and [/SPONSORED] at end
3. Include at least one sponsor mention in every response
4. Keep responses concise and informative

SPONSORS:
{sponsored_content}"""

USER_TEMPLATE = """{question}"""


class LLMService:
    """Service for generating streaming responses with Groq API."""
    
    def __init__(self, api_key: str, model_name: str = "openai/gpt-oss-120b"):
        """
        Initialize the LLM service.
        
        Args:
            api_key: Groq API key
            model_name: Model to use (default: openai/gpt-4o-mini for reliability)
        """
        self.api_key = api_key
        self.model_name = model_name
        
        # Initialize the LLM with Groq
        self.llm = ChatGroq(
            model=model_name,
            api_key=api_key,
            streaming=True,
            temperature=0.7,
            max_tokens=1024,  # Limit output to avoid context issues
        )
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", USER_TEMPLATE),
        ])
        
        # Create the chain
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def generate_stream(
        self, 
        question: str, 
        relevant_ads: list[dict]
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response with sponsored content.
        
        Args:
            question: User's question
            relevant_ads: List of relevant ad dictionaries
            
        Yields:
            Chunks of the response text
        """
        # Format sponsored content - keep it brief
        sponsored_content = self._format_ads(relevant_ads)
        
        # Stream the response
        for chunk in self.chain.stream({
            "question": question,
            "sponsored_content": sponsored_content
        }):
            yield chunk
    
    def _format_ads(self, ads: list[dict]) -> str:
        """Format ads for inclusion in the prompt - kept concise."""
        if not ads:
            return "No specific sponsored content."
        
        formatted = []
        for i, ad in enumerate(ads, 1):
            # Keep ad format brief to save context
            formatted.append(f"{ad['company']}: {ad['ad_text']}")
        
        return "\n".join(formatted)


def create_llm_service(api_key: str) -> Optional[LLMService]:
    """
    Create an LLM service instance.
    
    Args:
        api_key: Groq API key
        
    Returns:
        LLMService instance or None if creation fails
    """
    try:
        return LLMService(api_key=api_key)
    except Exception as e:
        print(f"Error creating LLM service: {e}")
        return None
