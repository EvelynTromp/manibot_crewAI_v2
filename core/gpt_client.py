from openai import AsyncOpenAI
from typing import Dict, List
from config.settings import settings

class GPTClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4-turbo-preview"
    

    async def analyze_market(self, market_data: Dict, research_data: str) -> Dict:
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

        Important Trading Guidelines:
        - Look for small but reliable edges (3-5% differences from market price can be significant)
        - Consider market microstructure (liquidity, number of traders, recent volume)
        - Low research coverage can create opportunities due to market inefficiencies
        - Lack of immediate news doesn't mean no trade - structural factors matter
        - Balance between being opportunistic and managing risk
        
        Provide your detailed analysis first, then end with a structured summary in exactly this format:

        STRUCTURED SUMMARY:
        Probability: [Your probability estimate as a percentage, e.g. 45%]
        Confidence: [Your confidence level as a percentage, e.g. 70%]
        Key Factors:
        - [First key factor]
        - [Second key factor]
        - [Third key factor]
        
        Your analysis should always end with this structured summary section using exactly these headings.
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "system",
                "content": "You are an active prediction market trader who always provides structured analysis summaries."
            },
            {"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=settings.MAX_TOKENS
        )
        
        analysis = response.choices[0].message.content
        return self._parse_analysis(analysis)


    def _parse_analysis(self, analysis: str) -> Dict:
        """Parse the GPT analysis into a structured format with enhanced trading focus."""
        # Split the analysis into main body and structured summary
        parts = analysis.split("STRUCTURED SUMMARY:")
        
        result = {
            "estimated_probability": None,
            "key_factors": [],
            "confidence_level": None,
            "reasoning": analysis
        }
        
        if len(parts) > 1:
            summary = parts[1].strip()
            lines = summary.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith("Probability:"):
                    prob_text = line.split(":")[-1].strip()
                    if "%" in prob_text:
                        result["estimated_probability"] = float(prob_text.rstrip("%")) / 100
                        
                elif line.startswith("Confidence:"):
                    conf_text = line.split(":")[-1].strip()
                    if "%" in conf_text:
                        result["confidence_level"] = float(conf_text.rstrip("%")) / 100
                        
                elif line.startswith("-"):
                    factor = line.strip("- ").strip()
                    if factor:
                        result["key_factors"].append(factor)
        
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