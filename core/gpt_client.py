from openai import AsyncOpenAI
from typing import Dict, List
from config.settings import settings

class GPTClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4-turbo-preview"
    
    async def analyze_market(self, market_data: Dict, research_data: str) -> Dict:
        """
        Analyze market data and research to generate insights and recommendations.
        
        Args:
            market_data: Dictionary containing market information
            research_data: String containing research findings
            
        Returns:
            Dictionary containing analysis and recommendations
        """
        prompt = f"""
        You are an expert market analyst. Analyze this prediction market and research data to determine:
        1. The likelihood of the event occurring
        2. Key factors influencing the outcome
        3. Recommended position (probability and bet size)
        4. Confidence level in the analysis

        Market Information:
        {market_data}

        Research Data:
        {research_data}

        Provide your analysis in a structured format.
        Think step-by-step about your reasoning.
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )
        
        analysis = response.choices[0].message.content
        return self._parse_analysis(analysis)
    
    def _parse_analysis(self, analysis: str) -> Dict:
        """Parse the GPT analysis into a structured format."""
        # This is a simple implementation - could be made more robust
        lines = analysis.split('\n')
        result = {
            "estimated_probability": None,
            "key_factors": [],
            "recommended_position": None,
            "confidence_level": None,
            "reasoning": analysis
        }
        
        for line in lines:
            line = line.strip().lower()
            if "probability:" in line or "likelihood:" in line:
                try:
                    # Extract probability percentage
                    prob = float(line.split(":")[-1].strip().rstrip("%")) / 100
                    result["estimated_probability"] = prob
                except ValueError:
                    pass
            elif "confidence:" in line:
                try:
                    # Extract confidence level
                    conf = float(line.split(":")[-1].strip().rstrip("%")) / 100
                    result["confidence_level"] = conf
                except ValueError:
                    pass
            elif "recommend" in line and "position" in line:
                result["recommended_position"] = line.split(":")[-1].strip()
            elif "factor:" in line:
                result["key_factors"].append(line.split(":")[-1].strip())
        
        return result
    
    async def validate_decision(self, market_data: Dict, analysis: Dict, proposed_bet: Dict) -> bool:
        """
        Double-check the betting decision for safety and rationality.
        
        Args:
            market_data: Dictionary containing market information
            analysis: Dictionary containing market analysis
            proposed_bet: Dictionary containing proposed bet details
            
        Returns:
            Boolean indicating whether the bet should proceed
        """
        prompt = f"""
        You are a risk management expert. Validate this proposed prediction market bet:

        Market: {market_data}
        Analysis: {analysis}
        Proposed Bet: {proposed_bet}

        Consider:
        1. Is the bet size appropriate given the uncertainty?
        2. Are there any red flags in the analysis?
        3. Is the probability estimate well-justified?

        Respond with a clear YES or NO and explanation.
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower temperature for more conservative validation
            max_tokens=settings.MAX_TOKENS
        )
        
        validation = response.choices[0].message.content.strip().upper()
        return validation.startswith("YES")