"""Test script for Sponsored AI functionality."""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GROQ_API_KEY')
print(f'API Key loaded: {bool(api_key)}')
print(f'Key prefix: {api_key[:10]}...' if api_key else 'No key')

from vector_store import search_ads
ads = search_ads('best laptop for work', 2)
print(f'Found ads: {[a["company"] for a in ads]}')

from llm_service import create_llm_service
service = create_llm_service(api_key)
print(f'LLM Service created: {bool(service)}')

# Test streaming
print('Testing LLM response...')
print('-' * 50)
response = ''
for chunk in service.generate_stream('What laptop should I buy?', ads):
    response += chunk
    print(chunk, end='', flush=True)
print()
print('-' * 50)
print(f'Response length: {len(response)} chars')
print(f'Contains [SPONSORED]: {"[SPONSORED]" in response}')
