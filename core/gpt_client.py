import json
from openai import AsyncOpenAI
from typing import Dict, List, Optional
from config.settings import settings
from utils.logger import get_logger
import re
from pydantic import BaseModel, ConfigDict

logger = get_logger(__name__)

class GPTClient(BaseModel):
    """Enhanced GPT client utilizing native search capabilities."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    client: AsyncOpenAI = None
    model: str = "gpt-4-turbo-preview"
    max_retries: int = settings.MAX_RETRIES
    
    def __init__(self, **data):
        super().__init__(**data)
        # Initialize OpenAI client after parent initialization
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._retry_count = 0  # Private attributes don't need to be in model fields



    
    async def analyze_market(self, market_data: Dict) -> Dict:
        """Comprehensive market analysis with enhanced error handling."""
        try:
            # Create analysis prompt
            prompt = self._create_market_analysis_prompt(market_data)
            
            # Get GPT completion
            completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": """You are a prediction market expert.
                    Return analysis as JSON with probability estimates and specific bet recommendations.
                    Consider market dynamics and provide concrete trading advice."""},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=settings.MAX_TOKENS
            )
            
            # Extract and parse response
            response = completion.choices[0].message.content
            logger.debug(f"Raw GPT response: {response}")
            
            try:
                # Clean response to ensure valid JSON
                cleaned_response = self._clean_json_response(response)
                analysis = json.loads(cleaned_response)
                logger.debug(f"Parsed analysis: {analysis}")
                
                # Validate and enhance analysis
                validated_analysis = self._validate_analysis(analysis)
                
                # Mark analysis as successful if we have valid probability estimates
                validated_analysis['success'] = (
                    validated_analysis.get('estimated_probability') is not None and
                    validated_analysis.get('confidence_level') is not None
                )
                
                if validated_analysis['success']:
                    validated_analysis['bet_recommendation'] = self._generate_bet_recommendation(
                        validated_analysis['estimated_probability'],
                        validated_analysis['confidence_level'],
                        market_data
                    )
                    
                return validated_analysis
                
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse GPT response: {str(e)}"
                logger.error(f"JSON parsing error: {error_msg}")
                return self._create_default_analysis(error=error_msg)
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in analyze_market: {error_msg}")
            return self._create_default_analysis(error=error_msg)
        
        
    def _clean_json_response(self, response: str) -> str:
        """Clean GPT response to ensure valid JSON."""
        # Find JSON content between curly braces
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            json_str = match.group()
            # Remove any markdown code block markers
            json_str = re.sub(r'```json\s*|\s*```', '', json_str)
            return json_str
        raise ValueError("No valid JSON object found in response")

    def _create_default_analysis(self, error: str = None) -> Dict:
        """Create a safe default analysis structure with error information."""
        return {
            'estimated_probability': None,
            'confidence_level': None,
            'research_findings': [],
            'key_factors': [],
            'reasoning': error if error else "Analysis failed to complete",
            'sources': [],
            'error': error if error else "Unknown error in analysis",
            'success': False
        }
    


    async def get_market_news(self, query: str) -> Dict:
        """Focused search for recent news about a market topic."""
        prompt = f"""Search for recent news about: {query}
        Focus on articles from the past week that could affect this market.
        Include source URLs and publication dates."""
        
        try:
            completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a research assistant focused on finding recent, relevant news."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model
            )
            
            return self._parse_news_response(completion.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error getting market news: {str(e)}")
            raise

    async def validate_sources(self, sources: List[str]) -> Dict:
        """Validate and rate the credibility of sources."""
        prompt = f"""Evaluate the credibility of these sources:
        {sources}
        
        For each source, provide:
        1. Credibility rating (1-5)
        2. Known biases or limitations
        3. Recommendation for use in analysis"""
        
        try:
            completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert at evaluating source credibility and bias."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model
            )
            
            return self._parse_validation_response(completion.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error validating sources: {str(e)}")
            raise

    
    def _parse_analysis_response(self, response: str) -> Dict:
        """Parse the GPT analysis response into a structured format.
        
        Args:
            response: Raw response string from GPT
            
        Returns:
            Dictionary containing parsed analysis fields
        """
        try:
            # Initialize default structure
            analysis = {
                'estimated_probability': None,
                'confidence_level': None,
                'research_findings': [],
                'sources': [],
                'key_factors': []
            }
            
            # Split response into sections
            sections = response.split('\n\n')
            
            for section in sections:
                if 'SEARCH FINDINGS:' in section:
                    # Extract research findings
                    findings = section.split('SEARCH FINDINGS:')[1].strip().split('\n')
                    analysis['research_findings'] = [f.strip('- ') for f in findings if f.strip()]
                    
                elif 'FINAL ESTIMATES:' in section:
                    # Parse probability estimates
                    for line in section.split('\n'):
                        if 'Estimated Probability:' in line:
                            prob = float(line.split(':')[1].strip().strip('[]%'))/100
                            analysis['estimated_probability'] = prob
                        elif 'Confidence Level:' in line:
                            conf = float(line.split(':')[1].strip().strip('[]%'))/100
                            analysis['confidence_level'] = conf
                            
                elif 'KEY FACTORS:' in section:
                    # Extract key factors
                    factors = section.split('KEY FACTORS:')[1].strip().split('\n')
                    analysis['key_factors'] = [f.strip('123. ') for f in factors if f.strip()]
                    
                elif 'SOURCES:' in section:
                    # Extract sources
                    sources = section.split('SOURCES:')[1].strip().split('\n')
                    analysis['sources'] = [{'url': s.strip('- '), 'credibility': 0.8} 
                                        for s in sources if s.strip()]
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}")
            raise ValueError(f"Failed to parse GPT response: {str(e)}")

    def _parse_validation_response(self, response: str) -> Dict:
        """Parse the source validation response into a structured format.
        
        Args:
            response: Raw response string from GPT
            
        Returns:
            Dictionary containing validation results
        """
        try:
            # Initialize validation results
            validation = {
                'validated_sources': []
            }
            
            # Split response by source
            source_sections = response.split('\n\n')
            
            for section in source_sections:
                if not section.strip():
                    continue
                    
                source_data = {
                    'credibility': None,
                    'recommendation': None
                }
                
                # Parse rating and recommendation
                for line in section.split('\n'):
                    if 'Credibility rating' in line.lower():
                        try:
                            rating = float(line.split(':')[1].strip().split('/')[0])
                            source_data['credibility'] = rating / 5.0  # Normalize to 0-1
                        except:
                            continue
                            
                    if 'Recommendation' in line:
                        source_data['recommendation'] = line.split(':')[1].strip()
                
                if source_data['credibility'] is not None:
                    validation['validated_sources'].append(source_data)
            
            return validation
            
        except Exception as e:
            logger.error(f"Error parsing validation response: {str(e)}")
            raise ValueError(f"Failed to parse validation response: {str(e)}")


    def _validate_analysis(self, analysis: Dict) -> Dict:
        """Validate and clean analysis output with enhanced betting logic."""
        # Ensure all required fields exist
        required_fields = {
            'estimated_probability': float,
            'confidence_level': float,
            'research_findings': list,
            'key_factors': list,
            'reasoning': str,
            'sources': list
        }
        
        for field, field_type in required_fields.items():
            if field not in analysis or not isinstance(analysis[field], field_type):
                logger.warning(f"Missing or invalid field: {field}")
                analysis[field] = field_type()
        
        # Ensure probabilities are between 0 and 1
        analysis['estimated_probability'] = max(0, min(1, float(analysis.get('estimated_probability', 0))))
        analysis['confidence_level'] = max(0, min(1, float(analysis.get('confidence_level', 0))))
        
        return analysis


    def _create_default_analysis(self) -> Dict:
        """Create a safe default analysis structure."""
        return {
            'estimated_probability': None,
            'confidence_level': None,
            'research_findings': [],
            'key_factors': [],
            'reasoning': "Analysis failed to complete",
            'sources': []
        }
    

    
    def _generate_bet_recommendation(self, 
                                   estimated_prob: float, 
                                   confidence: float,
                                   market_data: Dict) -> Dict:
        """Generate betting recommendation based on analysis."""
        market_prob = float(market_data.get('probability', 0))
        edge = abs(estimated_prob - market_prob)
        
        # More aggressive edge requirement
        min_edge = 0.01  # Reduced from 0.02
        
        if edge >= min_edge and confidence >= 0.6:  # Reduced confidence threshold
            # Calculate bet size based on edge and confidence
            base_amount = settings.MIN_BET_AMOUNT
            scaling_factor = min(edge * confidence * 10, 1.0)  # More aggressive scaling
            bet_amount = base_amount + (
                (settings.MAX_BET_AMOUNT - base_amount) * scaling_factor
            )
            
            return {
                'amount': round(bet_amount, 2),
                'probability': estimated_prob,
                'edge': edge,
                'confidence': confidence
            }
        return None



    
    def _create_market_analysis_prompt(self, market_data: Dict) -> str:
        """Enhanced prompt for market analysis with explicit trading guidance."""
        return f"""Analyze this prediction market for trading opportunities:

        MARKET DETAILS
        Question: {market_data.get('question')}
        Current Probability: {market_data.get('probability')}
        Close Time: {market_data.get('closeTime')}
        Description: {market_data.get('textDescription', '')}

        Provide analysis in this EXACT JSON format:
        {{
            "estimated_probability": <float between 0-1>,
            "confidence_level": <float between 0-1>,
            "research_findings": [<list of key findings>],
            "key_factors": [<list of decision factors>],
            "reasoning": "<detailed explanation of probability estimate>",
            "sources": [
                {{
                    "url": "<source url>",
                    "credibility": <float between 0-1>,
                    "type": "<NEWS|ACADEMIC|SOCIAL|BLOG|OFFICIAL>"
                }}
            ]
        }}

        IMPORTANT: 
        - Be decisive in probability estimates
        - Consider recent news and developments
        - Focus on actionable insights
        - Return ONLY the JSON object"""