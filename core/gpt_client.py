from openai import AsyncOpenAI
from typing import Dict, List
from config.settings import settings

class GPTClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4-turbo-preview"
    

    async def analyze_market(self, market_data: Dict, research_data: str) -> Dict:
        """
        Analyze market data and research to generate trading insights and recommendations.
        Now optimized for more active trading while maintaining risk management.
        
        Args:
            market_data: Dictionary containing market information
            research_data: String containing research findings
            
        Returns:
            Dictionary containing analysis and recommendations
        """
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
        
        Provide your analysis with numerical probability estimates when possible.
        Even with limited information, if you identify an edge, express it quantitatively.
        Think step-by-step about your reasoning, focusing on finding actionable opportunities.
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "system",
                "content": "You are an active prediction market trader. While you maintain rigorous analysis, "
                          "you look for trading opportunities and are willing to make calculated bets when "
                          "you identify even small edges. You always provide specific probability estimates."
            },
            {"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=settings.MAX_TOKENS
        )
        
        analysis = response.choices[0].message.content
        return self._parse_analysis(analysis)
    
    def _parse_analysis(self, analysis: str) -> Dict:
        """Parse the GPT analysis into a structured format with enhanced trading focus."""
        lines = analysis.split('\n')
        result = {
            "estimated_probability": None,
            "key_factors": [],
            "confidence_level": None,
            "reasoning": analysis
        }
        
        # Enhanced parsing to capture trading-specific insights
        for line in lines:
            line = line.strip().lower()
            
            # Look for probability estimates
            if "probability:" in line or "likelihood:" in line:
                try:
                    # Extract probability percentage and convert to float
                    prob_text = line.split(":")[-1].strip()
                    # Handle percentage or decimal format
                    if "%" in prob_text:
                        prob = float(prob_text.rstrip("%")) / 100
                    else:
                        prob = float(prob_text)
                    result["estimated_probability"] = prob
                except ValueError:
                    continue
            
            # Extract confidence level
            elif "confidence:" in line:
                try:
                    conf_text = line.split(":")[-1].strip()
                    if "%" in conf_text:
                        conf = float(conf_text.rstrip("%")) / 100
                    else:
                        conf = float(conf_text)
                    result["confidence_level"] = conf
                except ValueError:
                    continue
            
            # Capture key factors
            elif "factor:" in line or "• " in line:
                factor = line.split(":")[-1].strip() if ":" in line else line.replace("•", "").strip()
                if factor:
                    result["key_factors"].append(factor)
            
            # Look for edge identification
            elif "edge:" in line:
                try:
                    edge_text = line.split(":")[-1].strip()
                    if "%" in edge_text:
                        edge = float(edge_text.rstrip("%")) / 100
                    else:
                        edge = float(edge_text)
                    result["edge"] = edge
                except ValueError:
                    continue
        
        # Default to more active trading stance when probability is identified
        if result["estimated_probability"] is not None:
            result["recommended_position"] = "YES" if result["estimated_probability"] > 0.55 else "NO"
            
            # Calculate basic edge if market probability available
            market_prob = float(market_data.get("probability", 0))
            if market_prob:
                result["edge"] = abs(result["estimated_probability"] - market_prob)
        
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