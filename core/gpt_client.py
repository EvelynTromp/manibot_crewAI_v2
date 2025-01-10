# core/gpt_client.py

from openai import AsyncOpenAI
from typing import Dict, Optional
from datetime import datetime
from utils.logger import get_logger
import asyncio
import re

logger = get_logger(__name__)

class GPTClient:
    """
    Enhanced GPT client with improved parsing and range handling.
    """
    
    def __init__(self, api_key: str):
        """Initialize OpenAI client with API key."""
        self.client = AsyncOpenAI(api_key=api_key)
        self.max_retries = 3

    async def analyze_market(self, market_data: Dict) -> Dict:
        """Main method for analyzing markets - this is the primary entry point."""
        try:
            logger.info(f"Starting analysis for market: {market_data.get('id')}")
            
            # Stage 1: Get free-form analysis with retries
            for attempt in range(self.max_retries):
                try:
                    analysis = await self._get_market_analysis(market_data)
                    logger.debug(f"Raw analysis obtained: {analysis[:200]}...")  # Log first 200 chars
                    break
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise
                    logger.warning(f"Analysis attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(1)
            
            # Stage 2: Parse the analysis into structured format
            parsed_result = await self._parse_analysis(analysis)
            logger.info(f"Analysis completed for market {market_data.get('id')}")
            
            # Validate the result
            if not self._validate_analysis_result(parsed_result):
                raise ValueError("Invalid analysis result")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
            return self._create_error_response(str(e))
    
    async def _get_market_analysis(self, market_data: Dict) -> str:
        """Stage 1: Get free-form analysis from GPT with explicit instructions for single values."""
        thinking_prompt = f"""You are an expert prediction market analyst. 
        Think through this market carefully and explain your reasoning:

        MARKET QUESTION: {market_data.get('question', '')}
        CURRENT PROBABILITY: {market_data.get('probability', '')}
        CLOSE TIME: {self._format_timestamp(market_data.get('closeTime'))}
        DESCRIPTION: {market_data.get('description', '')}

        Think through:
        1. What factors influence this outcome?
        2. What is your estimated probability? (Must be a single number, not a range)
        3. How confident are you in this estimate? (Must be a single number)
        4. Should we make a trade? Why or why not?

        IMPORTANT RULES:
        - Your probability must be a single number between 0 and 1 (e.g., 0.65)
        - Your confidence must be a single number between 0 and 1 (e.g., 0.8)
        - Do NOT give ranges - pick your best single estimate

        Example good format:
        "After analysis, I estimate a probability of 0.65 with a confidence level of 0.8"

        Explain your thinking step by step."""

        completion = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert prediction market analyst. Always give single numerical values, never ranges."},
                {"role": "user", "content": thinking_prompt}
            ],
            temperature=0.7
        )
        
        if not completion.choices:
            raise ValueError("No completion choices returned from GPT")
            
        return completion.choices[0].message.content

    async def _parse_analysis(self, analysis_text: str) -> Dict:
        """Stage 2: Parse free-form analysis into structured format."""
        parsing_prompt = f"""Parse the following market analysis into a clear, structured format.
        CRITICAL: Extract or calculate SINGLE numerical values for probability and confidence.
        If you see a range, use the midpoint.

        Format exactly like this:

        PROBABILITY: (single number between 0-1, if given a range use the midpoint)
        CONFIDENCE: (single number between 0-1, if given a range use the midpoint)
        TRADE_RECOMMENDATION: (YES or NO)
        REASONING: (brief explanation)
        KEY_FACTORS: (comma-separated list)

        Here's the analysis to parse:

        {analysis_text}"""

        completion = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a precise analysis parser. Always convert ranges to single numbers by using the midpoint."},
                {"role": "user", "content": parsing_prompt}
            ],
            temperature=0
        )
        
        parsed_text = completion.choices[0].message.content
        logger.debug(f"Parsed analysis: {parsed_text}")
        
        return self._extract_structured_data(parsed_text)

    def _extract_structured_data(self, parsed_text: str) -> Dict:
        """Extract structured data with enhanced range handling."""
        try:
            lines = parsed_text.strip().split('\n')
            result = {
                'estimated_probability': None,
                'confidence_level': None,
                'should_trade': False,
                'reasoning': '',
                'key_factors': []
            }
            
            for line in lines:
                if ':' not in line:
                    continue
                    
                key, value = line.split(':', 1)
                key = key.strip().upper()
                value = value.strip()
                
                if key in ['PROBABILITY', 'CONFIDENCE']:
                    try:
                        # Handle potential ranges (e.g., "0.20-0.25" or "0.20 to 0.25")
                        range_match = re.search(r'(\d*\.?\d+)\s*[-–—to]\s*(\d*\.?\d+)', value)
                        if range_match:
                            low = float(range_match.group(1))
                            high = float(range_match.group(2))
                            value = str((low + high) / 2)
                            logger.debug(f"Converted range {low}-{high} to midpoint {value}")
                        
                        # Now try to convert to float
                        num_value = float(value)
                        num_value = min(max(num_value, 0), 1)
                        
                        if key == 'PROBABILITY':
                            result['estimated_probability'] = num_value
                        else:  # CONFIDENCE
                            result['confidence_level'] = num_value
                            
                    except ValueError as e:
                        logger.warning(f"Error parsing {key}: {value} - {str(e)}")
                        
                elif key == 'TRADE_RECOMMENDATION':
                    result['should_trade'] = value.upper().strip() == 'YES'
                    
                elif key == 'REASONING':
                    result['reasoning'] = value
                    
                elif key == 'KEY_FACTORS':
                    result['key_factors'] = [f.strip() for f in value.split(',') if f.strip()]
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
            raise

    def _validate_analysis_result(self, result: Dict) -> bool:
        """Validate that the analysis result contains all required fields."""
        required_fields = {
            'estimated_probability': float,
            'confidence_level': float,
            'should_trade': bool,
            'reasoning': str,
            'key_factors': list
        }
        
        for field, field_type in required_fields.items():
            if field not in result:
                logger.error(f"Missing required field: {field}")
                return False
            if result[field] is not None and not isinstance(result[field], field_type):
                logger.error(f"Invalid type for {field}: expected {field_type}, got {type(result[field])}")
                return False
                
        return True

    def _format_timestamp(self, timestamp: Optional[int]) -> str:
        """Format timestamp for prompt if available."""
        if not timestamp:
            return "Not specified"
        try:
            dt = datetime.fromtimestamp(timestamp / 1000)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception:
            return "Invalid timestamp"

    def _create_error_response(self, error_message: str) -> Dict:
        """Create a standardized error response."""
        return {
            'estimated_probability': None,
            'confidence_level': None,
            'should_trade': False,
            'reasoning': f"Analysis failed: {error_message}",
            'key_factors': [],
            'error': error_message
        }