from openai import AsyncOpenAI
from typing import Dict, List
from config.settings import settings
from utils.logger import get_logger

# Initialize module-level logger
logger = get_logger(__name__)

class GPTClient:
    def __init__(self):
        # Initialize the OpenAI client with our API key
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4-turbo-preview"
        logger.info("GPTClient initialized successfully")

    async def analyze_market(self, market_data: Dict, research_data: str, research_findings: List[Dict]) -> Dict:
        """
        Analyze market data and research to determine trading opportunities.
        Uses GPT-4 to evaluate probabilities and identify key factors.
        """
        try:
            # Compile research details for a comprehensive analysis
            research_details = "\n\nDetailed Research Findings:\n"
            for finding in research_findings:
                research_details += f"\nQuery: {finding['query']}\n"
                research_details += f"Results: {finding['results']}\n"
            
            prompt = f"""
            You are an experienced prediction market trader with a track record of identifying profitable opportunities.
            Your goal is to find trading edges while managing risk appropriately.
            
            Analyze this prediction market and research data to determine:
            1. The probability of each possible outcome
            2. Whether there are any trading edges (differences between your probability estimate and market prices)
            3. Key factors influencing the outcome
            4. Your confidence level in the analysis
            
            Market Information:
            {market_data}

            Research Data:
            {research_data}

            {research_details}

            Important Trading Guidelines:
            - Look for small but reliable edges (3-5% differences from market price can be significant)
            - Consider market microstructure (liquidity, number of traders, recent volume)
            - Low research coverage can create opportunities due to market inefficiencies
            - Lack of immediate news doesn't mean no trade - structural factors matter
            - Balance between being opportunistic and managing risk
            
            Provide your detailed analysis first, then end with a structured summary in exactly this format:

            STRUCTURED SUMMARY:
            Probability: [Your probability estimate as a percentage, e.g. 45%]
            Confidence: [Your confidence level as a percentage]
            Key Factors:
            - [First key factor]
            - [Second key factor]
            - [Third key factor]
            """

            completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an active prediction market trader who always provides structured analysis summaries."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=settings.MAX_TOKENS
            )

            return self._parse_analysis(completion.choices[0].message.content)

        except Exception as e:
            logger.error(f"Error in analyze_market: {str(e)}")
            raise

    async def generate_search_queries(self, market_data: Dict) -> List[str]:
        """
        Generate relevant search queries for market research.
        Returns clean, targeted queries ready for search engine use.
        """
        try:
            prompt = f"""
            You are an expert researcher helping to analyze a prediction market.
            Based on the market question and context, generate 2-3 specific,
            targeted search queries that would help evaluate the probability.

            Market Question: {market_data.get('question', '')}
            Description: {market_data.get('textDescription', '')}
            Current Probability: {market_data.get('probability', 0)}
            Close Time: {market_data.get('closeTime', 'Unknown')}

            Generate queries that:
            - Are specific and targeted rather than broad
            - Focus on quantitative data when relevant
            - Include temporal context when timing matters
            - Look for expert analysis in the relevant domain

            Just write each query on a new line, with no prefixes or formatting.
            Each query should be direct and clean, ready to be used in a search engine.
            """

            completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert researcher who generates precise, targeted search queries."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.7
            )

            # Process and clean the queries
            queries = []
            for line in completion.choices[0].message.content.split('\n'):
                cleaned_query = line.strip()
                if cleaned_query and len(cleaned_query) > 5:
                    # Remove any quotes or special characters
                    cleaned_query = cleaned_query.replace('"', '').replace("'", '')
                    queries.append(cleaned_query)

            logger.info(f"Generated {len(queries)} search queries")
            for query in queries:
                logger.info(f"Generated query: {query}")

            return queries[:3]  # Return top 3 queries

        except Exception as e:
            logger.error(f"Error generating search queries: {str(e)}")
            # Return a basic query based on the market question as fallback
            return [market_data.get('question', '')]

    async def validate_decision(self, market_data: Dict, analysis: Dict, proposed_bet: Dict) -> bool:
        """
        Validate a proposed trading decision using GPT-4 as a risk management check.
        Returns True if the trade passes validation checks.
        """
        try:
            prompt = f"""
            You are a risk management expert. Validate this proposed prediction market bet:

            Market: {market_data}
            Analysis: {analysis}
            Proposed Bet: {proposed_bet}

            Consider:
            1. Is the bet size appropriate given the uncertainty?
            2. Are there any red flags in the analysis?
            3. Is the probability estimate well-justified?

            After explaining your reasoning in depth, end with either "YES WE SHOULD TRADE" or "NO WE SHOULD NOT TRADE"
            """

            completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.3  # Lower temperature for more conservative validation
            )

            return "YES WE SHOULD TRADE" in completion.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in validate_decision: {str(e)}")
            return False

    def _parse_analysis(self, analysis: str) -> Dict:
        """
        Parse GPT's analysis into structured data.
        Returns a dictionary containing probability estimates and key factors.
        """
        try:
            # Initialize result structure
            result = {
                "estimated_probability": None,
                "confidence_level": None,
                "key_factors": [],
                "reasoning": analysis
            }
            
            # Look for the structured summary section
            if "STRUCTURED SUMMARY:" in analysis:
                summary_section = analysis.split("STRUCTURED SUMMARY:")[1].strip()
                
                # Extract probability
                if "Probability:" in summary_section:
                    prob_text = summary_section.split("Probability:")[1].split('\n')[0]
                    # Convert percentage to decimal (e.g., "45%" -> 0.45)
                    prob_value = float(prob_text.strip().replace('%', '')) / 100
                    result["estimated_probability"] = prob_value
                
                # Extract confidence
                if "Confidence:" in summary_section:
                    conf_text = summary_section.split("Confidence:")[1].split('\n')[0]
                    # Convert percentage to decimal
                    conf_value = float(conf_text.strip().replace('%', '')) / 100
                    result["confidence_level"] = conf_value
                
                # Extract key factors
                if "Key Factors:" in summary_section:
                    factors_section = summary_section.split("Key Factors:")[1].strip()
                    # Get all lines starting with a dash
                    factors = [
                        line.strip('- ').strip()  # Remove dash and whitespace
                        for line in factors_section.split('\n')
                        if line.strip().startswith('-')
                    ]
                    result["key_factors"] = factors
            
                logger.info(f"Parsed analysis: prob={result['estimated_probability']}, "
                           f"conf={result['confidence_level']}, "
                           f"factors={len(result['key_factors'])}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error parsing analysis: {str(e)}")
            # Return safe defaults if parsing fails
            return {
                "estimated_probability": None,
                "key_factors": ["Error parsing analysis"],
                "confidence_level": None,
                "reasoning": str(e)
            }