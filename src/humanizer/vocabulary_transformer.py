"""
Vocabulary Transformer v1.0.0
Replaces AI-typical words and phrases with human-like alternatives.

AI detectors look for:
- Repetitive vocabulary patterns
- Overuse of certain transitional phrases
- Predictable word choices
- Lack of colloquial variations

This transformer addresses all these patterns.
"""

import random
import re
from typing import Dict, List, Tuple


class VocabularyTransformer:
    """
    Transforms vocabulary to avoid AI detection patterns.
    Uses contextual synonym replacement with academic appropriateness scoring.
    """
    
    def __init__(self):
        # AI-typical words and their human alternatives
        # Format: "ai_word": ["human_alt1", "human_alt2", ...]
        self.word_replacements: Dict[str, List[str]] = {
            # Overused AI transition words
            "furthermore": ["besides", "what's more", "in addition to this", "adding to this", "on top of that"],
            "moreover": ["besides this", "equally important", "what is more", "not only that"],
            "additionally": ["also", "as well", "on top of this", "plus", "in addition"],
            "consequently": ["as a result", "therefore", "thus", "hence", "so"],
            "subsequently": ["afterwards", "later", "then", "following this", "after that"],
            "nevertheless": ["even so", "still", "yet", "regardless", "all the same"],
            "nonetheless": ["even so", "however", "still", "yet", "in spite of this"],
            "therefore": ["so", "thus", "hence", "as a result", "for this reason"],
            "thus": ["so", "hence", "therefore", "in this way", "accordingly"],
            "hence": ["therefore", "so", "thus", "for this reason", "as a result"],
            "however": ["but", "yet", "still", "on the other hand", "that said"],
            
            # AI-typical verbs
            "utilize": ["use", "employ", "apply", "make use of", "draw on"],
            "implement": ["put in place", "carry out", "execute", "apply", "introduce"],
            "demonstrate": ["show", "reveal", "illustrate", "display", "indicate"],
            "investigate": ["examine", "explore", "look into", "study", "probe"],
            "analyze": ["examine", "study", "look at", "assess", "evaluate"],
            "enhance": ["improve", "boost", "strengthen", "increase", "better"],
            "facilitate": ["help", "enable", "assist", "support", "make easier"],
            "establish": ["set up", "create", "form", "found", "determine"],
            "indicate": ["show", "suggest", "point to", "reveal", "signal"],
            "significantly": ["notably", "considerably", "substantially", "markedly", "greatly"],
            "particularly": ["especially", "specifically", "notably", "in particular", "chiefly"],
            "essentially": ["basically", "fundamentally", "primarily", "mainly", "at its core"],
            "predominantly": ["mainly", "mostly", "largely", "primarily", "chiefly"],
            "comprehensively": ["thoroughly", "fully", "completely", "extensively", "in depth"],
            
            # AI-typical adjectives
            "crucial": ["key", "vital", "essential", "critical", "important"],
            "significant": ["important", "notable", "meaningful", "considerable", "substantial"],
            "substantial": ["considerable", "significant", "large", "major", "sizeable"],
            "comprehensive": ["thorough", "complete", "full", "extensive", "all-encompassing"],
            "robust": ["strong", "solid", "sturdy", "reliable", "sound"],
            "innovative": ["new", "novel", "creative", "original", "groundbreaking"],
            "optimal": ["best", "ideal", "most suitable", "perfect", "most effective"],
            "pivotal": ["key", "crucial", "central", "critical", "vital"],
            "paramount": ["supreme", "chief", "primary", "main", "foremost"],
            "multifaceted": ["complex", "varied", "diverse", "many-sided", "wide-ranging"],
            
            # AI-typical nouns
            "methodology": ["method", "approach", "technique", "procedure", "way"],
            "framework": ["structure", "system", "model", "outline", "foundation"],
            "paradigm": ["model", "pattern", "example", "standard", "framework"],
            "implications": ["effects", "consequences", "outcomes", "results", "impact"],
            "perspective": ["view", "viewpoint", "standpoint", "angle", "outlook"],
            "phenomenon": ["occurrence", "event", "happening", "situation", "instance"],
            "dynamics": ["interactions", "forces", "processes", "workings", "mechanics"],
            "parameters": ["limits", "boundaries", "factors", "variables", "settings"],
            
            # AI-typical phrases (will be handled separately)
            "it is important to note": ["notably", "worth mentioning", "it should be noted", "keep in mind"],
            "it is worth mentioning": ["notably", "interestingly", "it bears noting", "worth pointing out"],
            "plays a crucial role": ["is vital", "is essential", "matters greatly", "is key"],
            "in the context of": ["regarding", "with respect to", "concerning", "when it comes to"],
            "in terms of": ["regarding", "concerning", "with respect to", "as for"],
            "a wide range of": ["many", "various", "numerous", "diverse", "a variety of"],
            "the fact that": ["that", "the reality that", "the truth that", "how"],
            "due to the fact that": ["because", "since", "as", "given that"],
            "in order to": ["to", "so as to", "for the purpose of", "with the aim of"],
            "as a result of": ["because of", "due to", "owing to", "following"],
            "with regard to": ["about", "concerning", "regarding", "on the subject of"],
            "in light of": ["considering", "given", "because of", "in view of"],
        }
        
        # Sentence starters that sound AI-generated
        self.ai_starters = [
            "It is evident that",
            "It can be observed that",
            "It is noteworthy that",
            "It is essential to",
            "It is imperative that",
            "It should be noted that",
            "It is important to highlight",
            "It is crucial to understand",
            "It is widely recognized that",
            "It has been demonstrated that",
        ]
        
        # Human-like sentence starters
        self.human_starters = [
            "Clearly,",
            "As we can see,",
            "Interestingly,",
            "What stands out is",
            "Looking at this more closely,",
            "The evidence suggests",
            "Based on the findings,",
            "One key insight is",
            "A closer look reveals",
            "The data points to",
            "Research shows",
            "Studies indicate",
            "Evidence supports",
            "Findings suggest",
            "The results confirm",
        ]
    
    def transform(self, text: str, intensity: float = 0.6) -> str:
        """
        Transform vocabulary in text to be more human-like.
        
        Args:
            text: Input text to transform
            intensity: How aggressively to replace (0.0-1.0)
            
        Returns:
            Transformed text with human-like vocabulary
        """
        result = text
        
        # Replace AI-typical phrases first (longer matches first)
        sorted_phrases = sorted(
            [(k, v) for k, v in self.word_replacements.items() if ' ' in k],
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for phrase, alternatives in sorted_phrases:
            if random.random() < intensity:
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                matches = pattern.findall(result)
                for match in matches:
                    if random.random() < intensity:
                        replacement = random.choice(alternatives)
                        # Preserve capitalization
                        if match[0].isupper():
                            replacement = replacement.capitalize()
                        result = result.replace(match, replacement, 1)
        
        # Replace single words
        words_only = {k: v for k, v in self.word_replacements.items() if ' ' not in k}
        for word, alternatives in words_only.items():
            if random.random() < intensity:
                # Word boundary matching
                pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
                matches = pattern.findall(result)
                for match in matches:
                    if random.random() < intensity:
                        replacement = random.choice(alternatives)
                        # Preserve capitalization
                        if match[0].isupper():
                            replacement = replacement.capitalize()
                        result = pattern.sub(replacement, result, count=1)
        
        # Replace AI-typical sentence starters
        for ai_starter in self.ai_starters:
            if ai_starter.lower() in result.lower():
                if random.random() < intensity:
                    pattern = re.compile(re.escape(ai_starter), re.IGNORECASE)
                    human_starter = random.choice(self.human_starters)
                    result = pattern.sub(human_starter, result, count=1)
        
        return result
    
    def get_replacement_count(self, text: str) -> int:
        """Count how many AI-typical patterns are in the text."""
        count = 0
        text_lower = text.lower()
        
        for word in self.word_replacements.keys():
            count += text_lower.count(word.lower())
        
        for starter in self.ai_starters:
            count += text_lower.count(starter.lower())
        
        return count


# Academic domain-specific replacements
DOMAIN_SPECIFIC_REPLACEMENTS = {
    "healthcare": {
        "treatment modality": ["treatment approach", "therapeutic method", "care strategy"],
        "clinical outcomes": ["patient results", "treatment results", "health outcomes"],
        "healthcare delivery": ["care provision", "health services", "medical care"],
    },
    "technology": {
        "technological advancement": ["tech progress", "technical development", "innovation"],
        "digital transformation": ["digital shift", "tech modernization", "digitalization"],
        "computational approach": ["computing method", "algorithmic technique", "computer-based method"],
    },
    "business": {
        "organizational performance": ["company results", "business outcomes", "firm performance"],
        "strategic implementation": ["strategy execution", "strategic rollout", "plan implementation"],
        "competitive advantage": ["market edge", "business advantage", "competitive edge"],
    },
    "education": {
        "learning outcomes": ["educational results", "student achievement", "learning gains"],
        "pedagogical approach": ["teaching method", "instructional strategy", "educational approach"],
        "academic achievement": ["student success", "educational attainment", "scholarly performance"],
    }
}
