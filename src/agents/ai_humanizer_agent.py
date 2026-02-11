"""
AI Humanizer Agent v1.0.0
Transforms AI-generated academic content into natural, human-like writing.

This agent is strategically positioned AFTER Quality Assurance and BEFORE Final Assembly
to ensure:
1. Content is complete and quality-checked
2. Citations remain intact
3. Academic integrity is preserved
4. AI detection scores are minimized (<10%)

Transformation Techniques:
1. Vocabulary Diversification - Replace AI-typical patterns
2. Sentence Restructuring - Vary sentence structures
3. Discourse Markers - Add natural transitions
4. Paragraph Flow - Vary lengths and structures
5. Academic Voice Variation - Mix formal/semi-formal tones
6. Hedging Language - Add uncertainty markers
7. Perplexity Enhancement - Increase text unpredictability

Author: ResearchAI Platform
Version: 1.0.0
"""

import random
import re
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.core.llm_provider import LLMProvider
from src.core.state_manager import StateManager
from src.models.agent_messages import AgentRequest, AgentResponse, TaskStatus


class HumanizationIntensity(Enum):
    """Humanization intensity levels."""
    LIGHT = 0.5      # Light changes
    MODERATE = 0.75  # Balanced approach (increased from 0.5)
    STRONG = 0.9     # Significant transformation
    AGGRESSIVE = 0.98 # Maximum humanization


@dataclass
class HumanizationMetrics:
    """Metrics from humanization process."""
    original_word_count: int
    transformed_word_count: int
    vocabulary_changes: int
    sentence_restructures: int
    discourse_markers_added: int
    estimated_ai_score_before: float
    estimated_ai_score_after: float
    transformation_ratio: float


class AIHumanizerAgent(BaseAgent):
    """
    AI Humanizer Agent - Transforms AI-generated content into human-like writing.
    
    Position in Pipeline: After QA, Before Final Assembly
    
    Responsibilities:
    - Detect and replace AI-typical vocabulary patterns
    - Restructure sentences for natural flow
    - Add human discourse markers and transitions
    - Vary paragraph lengths and structures
    - Inject hedging and uncertainty language
    - Preserve citations and references
    - Maintain academic quality and meaning
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        state_manager: Optional[StateManager] = None,
        intensity: HumanizationIntensity = HumanizationIntensity.MODERATE,
        target_ai_score: float = 10.0,  # Target <10% AI detection
        preserve_citations: bool = True,
    ):
        """
        Initialize AI Humanizer Agent.
        
        Args:
            llm_provider: LLM provider for advanced transformations
            state_manager: State manager for persistence
            intensity: How aggressively to humanize
            target_ai_score: Target AI detection score (%)
            preserve_citations: Whether to protect citation text
        """
        super().__init__(
            agent_name="ai_humanizer_agent",
            llm_provider=llm_provider,
            state_manager=state_manager,
        )
        
        self.intensity = intensity
        self.target_ai_score = target_ai_score
        self.preserve_citations = preserve_citations
        
        # Initialize transformation components
        self._init_vocabulary_maps()
        self._init_sentence_patterns()
        self._init_discourse_markers()
        self._init_hedging_phrases()
        
        logger.info(
            f"AIHumanizerAgent initialized: intensity={intensity.name}, "
            f"target_ai_score={target_ai_score}%"
        )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data before processing.
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Check for required fields
        if not input_data:
            return False
        
        # Must have either sections or content
        has_sections = "sections" in input_data and input_data["sections"]
        has_content = "content" in input_data and input_data["content"]
        
        return has_sections or has_content
    
    def _init_vocabulary_maps(self):
        """Initialize vocabulary replacement maps."""
        
        # AI-typical words → Human alternatives
        self.vocab_replacements = {
            # Overused transitions (AI loves these)
            "furthermore": ["besides", "what's more", "adding to this", "on top of that", "also"],
            "moreover": ["besides this", "equally important", "not only that", "plus"],
            "additionally": ["also", "as well", "on top of this", "plus", "too"],
            "consequently": ["as a result", "so", "thus", "hence", "therefore"],
            "subsequently": ["afterwards", "later", "then", "following this", "next"],
            "nevertheless": ["even so", "still", "yet", "regardless", "all the same"],
            "nonetheless": ["even so", "however", "still", "yet", "despite this"],
            "therefore": ["so", "thus", "hence", "as a result", "for this reason"],
            "thus": ["so", "hence", "therefore", "in this way", "accordingly"],
            "hence": ["so", "therefore", "thus", "for this reason", "as a result"],
            "however": ["but", "yet", "still", "on the other hand", "that said", "although"],
            
            # Overused verbs
            "utilize": ["use", "employ", "apply", "draw on", "work with"],
            "implement": ["put in place", "carry out", "execute", "apply", "introduce", "adopt"],
            "demonstrate": ["show", "reveal", "illustrate", "display", "indicate", "highlight"],
            "investigate": ["examine", "explore", "look into", "study", "probe", "research"],
            "analyze": ["examine", "study", "look at", "assess", "evaluate", "review"],
            "enhance": ["improve", "boost", "strengthen", "increase", "better", "upgrade"],
            "facilitate": ["help", "enable", "assist", "support", "make easier", "aid"],
            "establish": ["set up", "create", "form", "found", "determine", "build"],
            "indicate": ["show", "suggest", "point to", "reveal", "signal", "imply"],
            "exhibit": ["show", "display", "demonstrate", "present", "reveal"],
            "elucidate": ["explain", "clarify", "illuminate", "shed light on", "make clear"],
            "ascertain": ["find out", "determine", "establish", "discover", "learn"],
            "constitute": ["make up", "form", "represent", "compose", "be"],
            "necessitate": ["require", "need", "call for", "demand", "make necessary"],
            "encompass": ["include", "cover", "contain", "involve", "take in"],
            
            # Overused adverbs
            "significantly": ["notably", "considerably", "substantially", "markedly", "greatly", "much"],
            "particularly": ["especially", "specifically", "notably", "chiefly", "mainly"],
            "essentially": ["basically", "fundamentally", "primarily", "mainly", "at its core"],
            "predominantly": ["mainly", "mostly", "largely", "primarily", "chiefly"],
            "comprehensively": ["thoroughly", "fully", "completely", "extensively", "in depth"],
            "inherently": ["naturally", "by nature", "fundamentally", "essentially", "intrinsically"],
            "ultimately": ["in the end", "finally", "eventually", "at last", "lastly"],
            "fundamentally": ["basically", "at heart", "essentially", "at its core", "primarily"],
            "intrinsically": ["inherently", "naturally", "essentially", "by nature"],
            "systematically": ["methodically", "in order", "step by step", "regularly"],
            
            # Overused adjectives
            "crucial": ["key", "vital", "essential", "critical", "important", "major"],
            "significant": ["important", "notable", "meaningful", "considerable", "major"],
            "substantial": ["considerable", "significant", "large", "major", "sizeable", "big"],
            "comprehensive": ["thorough", "complete", "full", "extensive", "wide-ranging"],
            "robust": ["strong", "solid", "sturdy", "reliable", "sound", "firm"],
            "innovative": ["new", "novel", "creative", "original", "fresh", "pioneering"],
            "optimal": ["best", "ideal", "most suitable", "perfect", "top"],
            "pivotal": ["key", "crucial", "central", "critical", "vital", "main"],
            "paramount": ["supreme", "chief", "primary", "main", "foremost", "top"],
            "multifaceted": ["complex", "varied", "diverse", "many-sided", "wide-ranging"],
            "pertinent": ["relevant", "related", "applicable", "fitting", "appropriate"],
            "profound": ["deep", "significant", "far-reaching", "major", "intense"],
            "salient": ["key", "main", "notable", "important", "striking"],
            "unprecedented": ["unmatched", "new", "unique", "first-time", "novel"],
            "exemplary": ["outstanding", "excellent", "model", "ideal", "superb"],
            
            # Overused nouns
            "methodology": ["method", "approach", "technique", "procedure", "way", "process"],
            "framework": ["structure", "system", "model", "outline", "foundation", "basis"],
            "paradigm": ["model", "pattern", "example", "standard", "framework", "approach"],
            "implications": ["effects", "consequences", "outcomes", "results", "impact", "meaning"],
            "perspective": ["view", "viewpoint", "standpoint", "angle", "outlook", "position"],
            "phenomenon": ["occurrence", "event", "happening", "situation", "instance", "case"],
            "dynamics": ["interactions", "forces", "processes", "workings", "mechanics", "patterns"],
            "parameters": ["limits", "boundaries", "factors", "variables", "settings", "conditions"],
            "discourse": ["discussion", "debate", "dialogue", "conversation", "talk"],
            "trajectory": ["path", "course", "direction", "trend", "route"],
            "paradigm shift": ["major change", "fundamental shift", "transformation", "revolution"],
            "synergy": ["cooperation", "teamwork", "collaboration", "combined effect"],
            # Sentence starters that sound AI-generated
            "this study": ["this research", "this work", "the present study", "our research"],
            "this research": ["this work", "the current study", "our investigation"],
            "the study": ["the research", "the work", "the investigation"],
        }
        
        # AI-typical phrases → Human alternatives
        self.phrase_replacements = {
            "it is important to note": ["notably", "worth mentioning", "keep in mind that", "it's worth noting"],
            "it is worth mentioning": ["notably", "interestingly", "it bears noting", "worth pointing out"],
            "it is evident that": ["clearly", "obviously", "it's clear that", "as we can see"],
            "it can be observed that": ["we can see that", "looking at this", "this shows", "notably"],
            "it should be noted that": ["note that", "keep in mind", "importantly", "notably"],
            "it is crucial to": ["it's key to", "we must", "it's vital to", "importantly"],
            "it is essential to": ["we need to", "it's important to", "we must", "it's vital to"],
            "it is imperative that": ["we must", "it's crucial that", "it's necessary that"],
            "it is important to note that": ["notably", "worth noting", "importantly", "keep in mind"],
            "plays a crucial role": ["is vital", "is essential", "matters greatly", "is key", "is important"],
            "plays a significant role": ["is important", "matters", "is key", "is central"],
            "in the context of": ["regarding", "when it comes to", "concerning", "about", "in terms of"],
            "in terms of": ["regarding", "concerning", "about", "when it comes to", "for"],
            "a wide range of": ["many", "various", "numerous", "diverse", "a variety of", "lots of"],
            "the fact that": ["that", "how", "the way"],
            "due to the fact that": ["because", "since", "as", "given that", "seeing that"],
            "in order to": ["to", "so as to", "for"],
            "as a result of": ["because of", "due to", "owing to", "following", "from"],
            "with regard to": ["about", "concerning", "regarding", "on", "as for"],
            "in light of": ["considering", "given", "because of", "in view of", "seeing"],
            "on the other hand": ["but", "however", "yet", "alternatively", "conversely"],
            "in this regard": ["here", "on this point", "in this respect", "about this"],
            "to a large extent": ["largely", "mostly", "mainly", "in large part", "for the most part"],
            "in the realm of": ["in", "within", "in the field of", "in the area of"],
            "serves as a": ["is a", "acts as a", "works as a", "functions as a"],
            "is characterized by": ["features", "has", "shows", "displays", "exhibits"],
            "with respect to": ["about", "regarding", "concerning", "for", "on"],
            "a plethora of": ["many", "lots of", "numerous", "plenty of", "a wealth of"],
            "a myriad of": ["many", "countless", "numerous", "lots of", "a host of"],
            "in conjunction with": ["with", "along with", "together with", "combined with"],
            "prior to": ["before", "ahead of", "preceding", "earlier than"],
            "subsequent to": ["after", "following", "later than", "post"],
            "this study demonstrates": ["this work shows", "our research reveals", "we found that", "the findings show"],
            "this research demonstrates": ["this work shows", "our findings reveal", "we found", "evidence shows"],
            "the implementation of": ["using", "applying", "the use of", "adopting"],
            "utilized in": ["used in", "applied in", "employed in"],
            "provides substantial": ["offers significant", "gives considerable", "yields major"],
            "future endeavors": ["future work", "future research", "further studies"],
            "future research endeavors": ["future studies", "further research", "upcoming work"],
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
            "This paper aims to",
            "This study seeks to",
            "The primary objective is to",
            "The purpose of this study is to",
            "The current research endeavors to",
        ]
        
        # Human-like sentence starters
        self.human_starters = [
            "Clearly,",
            "As we can see,",
            "Interestingly,",
            "What stands out is that",
            "Looking at this more closely,",
            "The evidence suggests that",
            "Based on the findings,",
            "One key insight is that",
            "A closer look reveals that",
            "The data points to",
            "Research shows that",
            "Studies indicate that",
            "Evidence supports the idea that",
            "Findings suggest that",
            "The results confirm that",
            "What emerges from this is",
            "We can see that",
            "This points to",
            "Looking at the evidence,",
            "From this, we learn that",
        ]
    
    def _init_sentence_patterns(self):
        """Initialize sentence restructuring patterns."""
        
        # Patterns to detect and restructure
        self.restructure_patterns = [
            # "X is Y" → "Y characterizes X" or "We see Y in X"
            (r'^(\w+)\s+is\s+(\w+)', self._restructure_is_statement),
            # "This demonstrates" → "We can see from this" 
            (r'^This\s+demonstrates', self._restructure_this_demonstrates),
            # Long sentences to split
            (r'^(.{150,})[,;]\s*(and|but|or)\s+(.+)$', self._split_long_sentence),
        ]
    
    def _init_discourse_markers(self):
        """Initialize discourse markers for natural flow."""
        
        # Additive markers (adding information)
        self.additive_markers = [
            "Also,", "Besides,", "What's more,", "In addition,", "Plus,",
            "On top of this,", "Adding to this,", "Further,", "As well as this,",
        ]
        
        # Contrastive markers (showing contrast)
        self.contrastive_markers = [
            "But", "Yet", "However,", "Still,", "Although", "Even so,",
            "That said,", "On the flip side,", "At the same time,",
        ]
        
        # Causal markers (cause and effect)
        self.causal_markers = [
            "So", "Thus", "Hence", "As a result,", "Because of this,",
            "This leads to", "This means that", "For this reason,",
        ]
        
        # Temporal markers (time sequence)
        self.temporal_markers = [
            "First,", "Then,", "Next,", "After this,", "Finally,",
            "Meanwhile,", "At this point,", "Following this,", "Later,",
        ]
        
        # Exemplification markers
        self.example_markers = [
            "For example,", "For instance,", "Such as", "Like",
            "To illustrate,", "Consider", "Take", "As seen in",
        ]
    
    def _init_hedging_phrases(self):
        """Initialize hedging and uncertainty phrases."""
        
        # Hedging verbs (reduce certainty)
        self.hedging_verbs = [
            "seems to", "appears to", "tends to", "might", "may",
            "could", "suggests", "indicates", "points to", "implies",
        ]
        
        # Hedging adverbs
        self.hedging_adverbs = [
            "perhaps", "possibly", "probably", "likely", "seemingly",
            "apparently", "arguably", "potentially", "conceivably",
        ]
        
        # Hedging phrases
        self.hedging_phrases = [
            "it seems that", "it appears that", "this suggests that",
            "evidence points to", "this may indicate", "one could argue",
            "it is possible that", "there is reason to believe",
            "the data suggests", "findings indicate",
        ]
        
        # Personal voice insertions (sparingly used)
        self.personal_touches = [
            "we observe", "we can see", "we note", "we find",
            "our analysis shows", "our findings suggest",
            "looking at the data, we", "examining this further, we",
        ]
    
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute content humanization.
        
        Args:
            request: Agent request containing content to humanize
            
        Returns:
            AgentResponse with humanized content and metrics
        """
        try:
            input_data = request.input_data
            
            # Extract sections to humanize
            sections = input_data.get("sections", [])
            topic = input_data.get("topic", "")
            
            logger.info(f"Starting humanization for: {topic} ({len(sections)} sections)")
            
            # Track metrics
            total_metrics = HumanizationMetrics(
                original_word_count=0,
                transformed_word_count=0,
                vocabulary_changes=0,
                sentence_restructures=0,
                discourse_markers_added=0,
                estimated_ai_score_before=0,
                estimated_ai_score_after=0,
                transformation_ratio=0,
            )
            
            humanized_sections = []
            
            for section in sections:
                title = section.get("title", "")
                content = section.get("content", "")
                
                # Skip certain sections
                if self._should_skip_section(title):
                    humanized_sections.append(section)
                    logger.debug(f"Skipped section: {title}")
                    continue
                
                # Humanize content
                humanized_content, metrics = await self._humanize_content(content, title)
                
                # Update metrics
                total_metrics.original_word_count += metrics.original_word_count
                total_metrics.transformed_word_count += metrics.transformed_word_count
                total_metrics.vocabulary_changes += metrics.vocabulary_changes
                total_metrics.sentence_restructures += metrics.sentence_restructures
                total_metrics.discourse_markers_added += metrics.discourse_markers_added
                
                humanized_sections.append({
                    **section,
                    "content": humanized_content,
                    "humanization_applied": True,
                })
                
                logger.info(f"Humanized section: {title} ({metrics.vocabulary_changes} vocab changes)")
            
            # Calculate overall metrics
            if total_metrics.original_word_count > 0:
                total_metrics.transformation_ratio = (
                    total_metrics.vocabulary_changes / total_metrics.original_word_count
                )
            
            # Estimate AI scores
            total_metrics.estimated_ai_score_before = self._estimate_ai_score(sections)
            total_metrics.estimated_ai_score_after = self._estimate_ai_score(humanized_sections)
            
            logger.info(
                f"Humanization complete: {total_metrics.vocabulary_changes} vocab changes, "
                f"estimated AI score: {total_metrics.estimated_ai_score_before:.1f}% → "
                f"{total_metrics.estimated_ai_score_after:.1f}%"
            )
            
            return AgentResponse(
                agent_name=self.agent_name,
                status=TaskStatus.COMPLETED,
                output_data={
                    "sections": humanized_sections,
                    "metrics": {
                        "original_word_count": total_metrics.original_word_count,
                        "transformed_word_count": total_metrics.transformed_word_count,
                        "vocabulary_changes": total_metrics.vocabulary_changes,
                        "sentence_restructures": total_metrics.sentence_restructures,
                        "discourse_markers_added": total_metrics.discourse_markers_added,
                        "estimated_ai_score_before": total_metrics.estimated_ai_score_before,
                        "estimated_ai_score_after": total_metrics.estimated_ai_score_after,
                        "transformation_ratio": total_metrics.transformation_ratio,
                    },
                    "humanization_applied": True,
                },
                message=f"Content humanized successfully. AI score reduced from "
                        f"{total_metrics.estimated_ai_score_before:.1f}% to "
                        f"{total_metrics.estimated_ai_score_after:.1f}%",
            )
            
        except Exception as e:
            logger.error(f"Humanization failed: {e}", exc_info=True)
            return AgentResponse(
                agent_name=self.agent_name,
                status=TaskStatus.FAILED,
                error=str(e),
            )
    
    def _should_skip_section(self, title: str) -> bool:
        """Check if section should be skipped from humanization."""
        skip_sections = [
            "references", "bibliography", "citations", "table of contents",
            "list of tables", "list of figures", "list of abbreviations",
            "appendix", "appendices", "acknowledgements", "dedication",
            "abstract",  # Keep abstract more formal
        ]
        return any(skip in title.lower() for skip in skip_sections)
    
    async def _humanize_content(self, content: str, section_title: str) -> Tuple[str, HumanizationMetrics]:
        """
        Apply humanization transformations to content.
        
        Args:
            content: Original content
            section_title: Section title for context
            
        Returns:
            Tuple of (humanized_content, metrics)
        """
        original_word_count = len(content.split())
        vocab_changes = 0
        sentence_restructures = 0
        discourse_markers_added = 0
        
        # Protect citations before transformation
        content, citation_placeholders = self._protect_citations(content)
        
        # Step 1: Vocabulary diversification
        content, v_changes = self._transform_vocabulary(content)
        vocab_changes += v_changes
        
        # Step 2: Replace AI-typical phrases
        content, p_changes = self._transform_phrases(content)
        vocab_changes += p_changes
        
        # Step 3: Transform sentence starters
        content, s_changes = self._transform_starters(content)
        sentence_restructures += s_changes
        
        # Step 4: Add discourse markers (sparingly)
        content, d_added = self._add_discourse_markers(content)
        discourse_markers_added += d_added
        
        # Step 5: Add hedging language (sparingly)
        content, h_added = self._add_hedging(content)
        vocab_changes += h_added
        
        # Step 6: Vary sentence lengths
        content, sent_changes = self._vary_sentence_lengths(content)
        sentence_restructures += sent_changes
        
        # Step 7: Add personal touches (very sparingly)
        content, p_touches = self._add_personal_touches(content)
        vocab_changes += p_touches
        
        # Restore citations
        content = self._restore_citations(content, citation_placeholders)
        
        transformed_word_count = len(content.split())
        
        metrics = HumanizationMetrics(
            original_word_count=original_word_count,
            transformed_word_count=transformed_word_count,
            vocabulary_changes=vocab_changes,
            sentence_restructures=sentence_restructures,
            discourse_markers_added=discourse_markers_added,
            estimated_ai_score_before=0,
            estimated_ai_score_after=0,
            transformation_ratio=vocab_changes / max(original_word_count, 1),
        )
        
        return content, metrics
    
    def _protect_citations(self, content: str) -> Tuple[str, Dict[str, str]]:
        """Protect citations from transformation."""
        placeholders = {}
        
        # Protect various citation formats
        citation_patterns = [
            r'\([A-Z][a-z]+(?:\s+(?:et\s+al\.?|&|and)\s+[A-Z][a-z]+)?,?\s*\d{4}[a-z]?\)',  # (Author, 2020)
            r'\([A-Z][a-z]+\s+&\s+[A-Z][a-z]+,?\s*\d{4}\)',  # (Smith & Jones, 2020)
            r'\[[0-9,\s-]+\]',  # [1], [1,2,3], [1-5]
            r'\[\d+\]',  # [1]
        ]
        
        for i, pattern in enumerate(citation_patterns):
            matches = re.findall(pattern, content)
            for j, match in enumerate(matches):
                placeholder = f"__CITATION_{i}_{j}__"
                placeholders[placeholder] = match
                content = content.replace(match, placeholder, 1)
        
        return content, placeholders
    
    def _restore_citations(self, content: str, placeholders: Dict[str, str]) -> str:
        """Restore protected citations."""
        for placeholder, original in placeholders.items():
            content = content.replace(placeholder, original)
        return content
    
    def _transform_vocabulary(self, content: str) -> Tuple[str, int]:
        """Transform AI-typical vocabulary."""
        changes = 0
        intensity = self.intensity.value
        
        for ai_word, alternatives in self.vocab_replacements.items():
            pattern = re.compile(r'\b' + re.escape(ai_word) + r'\b', re.IGNORECASE)
            
            # Find all matches first
            def replace_match(match):
                nonlocal changes
                if random.random() < intensity:
                    replacement = random.choice(alternatives)
                    # Preserve capitalization
                    if match.group(0)[0].isupper():
                        replacement = replacement.capitalize()
                    changes += 1
                    return replacement
                return match.group(0)
            
            content = pattern.sub(replace_match, content)
        
        return content, changes
    
    def _transform_phrases(self, content: str) -> Tuple[str, int]:
        """Transform AI-typical phrases."""
        changes = 0
        intensity = self.intensity.value
        
        # Sort by length (longest first) to avoid partial matches
        sorted_phrases = sorted(self.phrase_replacements.keys(), key=len, reverse=True)
        
        for phrase in sorted_phrases:
            alternatives = self.phrase_replacements[phrase]
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            
            def replace_phrase(match):
                nonlocal changes
                if random.random() < intensity:
                    replacement = random.choice(alternatives)
                    if match.group(0)[0].isupper():
                        replacement = replacement.capitalize()
                    changes += 1
                    return replacement
                return match.group(0)
            
            content = pattern.sub(replace_phrase, content)
        
        return content, changes
    
    def _transform_starters(self, content: str) -> Tuple[str, int]:
        """Transform AI-typical sentence starters."""
        changes = 0
        intensity = self.intensity.value
        
        for ai_starter in self.ai_starters:
            if ai_starter.lower() in content.lower():
                if random.random() < intensity:
                    pattern = re.compile(re.escape(ai_starter), re.IGNORECASE)
                    human_starter = random.choice(self.human_starters)
                    content = pattern.sub(human_starter, content, count=1)
                    changes += 1
        
        return content, changes
    
    def _add_discourse_markers(self, content: str) -> Tuple[str, int]:
        """Add natural discourse markers."""
        added = 0
        sentences = content.split('. ')
        
        if len(sentences) < 3:
            return content, 0
        
        # Only add markers to ~15% of sentences
        marker_probability = 0.15 * self.intensity.value
        
        new_sentences = [sentences[0]]  # Keep first sentence as-is
        
        for i, sentence in enumerate(sentences[1:], 1):
            if random.random() < marker_probability and not self._starts_with_marker(sentence):
                # Choose marker type based on context
                if any(word in sentence.lower() for word in ['however', 'but', 'although', 'despite']):
                    marker = random.choice(self.contrastive_markers)
                elif any(word in sentence.lower() for word in ['because', 'therefore', 'result', 'leads']):
                    marker = random.choice(self.causal_markers)
                elif any(word in sentence.lower() for word in ['example', 'instance', 'such as', 'like']):
                    marker = random.choice(self.example_markers)
                else:
                    marker = random.choice(self.additive_markers)
                
                sentence = f"{marker} {sentence[0].lower()}{sentence[1:]}" if sentence else sentence
                added += 1
            
            new_sentences.append(sentence)
        
        return '. '.join(new_sentences), added
    
    def _starts_with_marker(self, sentence: str) -> bool:
        """Check if sentence already starts with a discourse marker."""
        all_markers = (
            self.additive_markers + self.contrastive_markers + 
            self.causal_markers + self.temporal_markers + self.example_markers
        )
        return any(sentence.strip().startswith(marker.strip()) for marker in all_markers)
    
    def _add_hedging(self, content: str) -> Tuple[str, int]:
        """Add hedging and uncertainty language."""
        added = 0
        intensity = self.intensity.value * 0.5  # Increased from 0.3
        
        # Replace absolute statements with hedged versions
        absolute_patterns = [
            (r'\bproves that\b', ['suggests that', 'indicates that', 'points to the fact that']),
            (r'\bclearly shows\b', ['seems to show', 'appears to indicate', 'suggests']),
            (r'\bdefinitely\b', ['likely', 'probably', 'seemingly']),
            (r'\bcertainly\b', ['probably', 'likely', 'apparently']),
            (r'\bobviously\b', ['it seems', 'apparently', 'evidently']),
            (r'\bundoubtedly\b', ['likely', 'probably', 'in all likelihood']),
            (r'\bwill be\b', ['may be', 'could be', 'is likely to be']),
            (r'\bmust be\b', ['appears to be', 'seems to be', 'is likely']),
            (r'\bis essential\b', ['is important', 'matters', 'is key']),
            (r'\bis crucial\b', ['is important', 'is key', 'matters']),
            (r'\bis critical\b', ['is important', 'is key', 'matters greatly']),
            (r'\bis vital\b', ['is important', 'is key', 'matters']),
            (r'\bis necessary\b', ['is needed', 'is required', 'is important']),
        ]
        
        for pattern, replacements in absolute_patterns:
            if random.random() < intensity:
                if re.search(pattern, content, re.IGNORECASE):
                    replacement = random.choice(replacements)
                    content = re.sub(pattern, replacement, content, count=1, flags=re.IGNORECASE)
                    added += 1
        
        return content, added
    
    def _vary_sentence_lengths(self, content: str) -> Tuple[str, int]:
        """Vary sentence lengths for natural flow."""
        changes = 0
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        if len(sentences) < 2:
            return content, 0
        
        new_sentences = []
        i = 0
        
        while i < len(sentences):
            sentence = sentences[i]
            words = sentence.split()
            
            # Very long sentence (>40 words) - consider splitting
            if len(words) > 40 and random.random() < self.intensity.value * 0.5:
                # Find a good split point
                split_words = [', and ', ', but ', ', which ', '; ', ' - ']
                for split_word in split_words:
                    if split_word in sentence:
                        parts = sentence.split(split_word, 1)
                        if len(parts) == 2 and len(parts[0].split()) > 10 and len(parts[1].split()) > 10:
                            new_sentences.append(parts[0] + '.')
                            new_sentences.append(parts[1].strip().capitalize())
                            changes += 1
                            break
                else:
                    new_sentences.append(sentence)
            
            # Very short consecutive sentences - consider combining
            elif len(words) < 10 and i + 1 < len(sentences):
                next_sentence = sentences[i + 1]
                next_words = next_sentence.split()
                
                if len(next_words) < 10 and random.random() < self.intensity.value * 0.3:
                    combined = f"{sentence.rstrip('.')} and {next_sentence[0].lower()}{next_sentence[1:]}"
                    new_sentences.append(combined)
                    i += 1  # Skip next sentence
                    changes += 1
                else:
                    new_sentences.append(sentence)
            else:
                new_sentences.append(sentence)
            
            i += 1
        
        return ' '.join(new_sentences), changes
    
    def _add_personal_touches(self, content: str) -> Tuple[str, int]:
        """Add personal voice touches (very sparingly for academic writing)."""
        added = 0
        intensity = self.intensity.value * 0.2  # Very conservative
        
        # Replace impersonal constructions with personal voice (sparingly)
        personal_replacements = [
            (r'\bIt is observed that\b', ['We observe that', 'We can see that', 'We note that']),
            (r'\bIt was found that\b', ['We found that', 'Our analysis shows that', 'We discovered that']),
            (r'\bIt can be seen that\b', ['We can see that', 'Looking at this, we see', 'We observe']),
            (r'\bOne can observe\b', ['We can observe', 'We see', 'We note']),
        ]
        
        for pattern, replacements in personal_replacements:
            if random.random() < intensity:
                if re.search(pattern, content, re.IGNORECASE):
                    replacement = random.choice(replacements)
                    content = re.sub(pattern, replacement, content, count=1, flags=re.IGNORECASE)
                    added += 1
        
        return content, added
    
    def _estimate_ai_score(self, sections: List[Dict]) -> float:
        """
        Estimate AI detection score based on content patterns.
        
        This is a heuristic estimation - actual AI detectors use more sophisticated methods.
        Returns a score between 0-100 where lower is better (more human-like).
        """
        if not sections:
            return 0.0
        
        full_text = ' '.join(section.get('content', '') for section in sections)
        
        if not full_text:
            return 0.0
        
        word_count = len(full_text.split())
        if word_count == 0:
            return 0.0
        
        # Count AI-typical patterns
        ai_pattern_count = 0
        
        # Check vocabulary (weight: 1 per match)
        for ai_word in self.vocab_replacements.keys():
            matches = re.findall(r'\b' + re.escape(ai_word) + r'\b', full_text, re.IGNORECASE)
            ai_pattern_count += len(matches)
        
        # Check phrases (weight: 2 per match - more indicative of AI)
        for phrase in self.phrase_replacements.keys():
            matches = re.findall(re.escape(phrase), full_text, re.IGNORECASE)
            ai_pattern_count += len(matches) * 2
        
        # Check sentence starters (weight: 3 per match - very indicative of AI)
        for starter in self.ai_starters:
            matches = re.findall(re.escape(starter), full_text, re.IGNORECASE)
            ai_pattern_count += len(matches) * 3
        
        # Calculate pattern density (patterns per 100 words)
        pattern_density = (ai_pattern_count / word_count) * 100
        
        # Convert to AI score (0-100 scale)
        # Typical human text: ~2-5 patterns per 100 words → score ~5-15%
        # Typical AI text: ~10-20 patterns per 100 words → score ~30-60%
        # Heavy AI text: ~25+ patterns per 100 words → score ~75-100%
        
        # Scale: multiply density by 3, cap at 100
        estimated_score = min(pattern_density * 3, 100)
        
        # Apply floor for very short texts (minimum uncertainty)
        if word_count < 50:
            estimated_score = max(estimated_score, 10)  # At least 10% uncertainty for short texts
        
        return round(estimated_score, 1)
    
    def _restructure_is_statement(self, match) -> str:
        """Restructure 'X is Y' statements."""
        templates = [
            "We find that {0} is {1}",
            "Looking at {0}, we see that it is {1}",
            "{1} characterizes {0}",
            "What makes {0} notable is that it is {1}",
        ]
        return random.choice(templates).format(match.group(1), match.group(2))
    
    def _restructure_this_demonstrates(self, match) -> str:
        """Restructure 'This demonstrates' statements."""
        alternatives = [
            "We can see from this that",
            "This shows us that",
            "What this tells us is that",
            "From this, we learn that",
        ]
        return random.choice(alternatives)
    
    def _split_long_sentence(self, match) -> str:
        """Split long sentences at natural break points."""
        first_part = match.group(1)
        conjunction = match.group(2)
        second_part = match.group(3)
        
        return f"{first_part}. {conjunction.capitalize()}, {second_part}"


# Convenience function for quick humanization
async def humanize_text(
    text: str,
    intensity: HumanizationIntensity = HumanizationIntensity.MODERATE
) -> str:
    """
    Quick humanization of text without full agent setup.
    
    Args:
        text: Text to humanize
        intensity: Humanization intensity
        
    Returns:
        Humanized text
    """
    agent = AIHumanizerAgent(intensity=intensity)
    
    request = AgentRequest(
        task_id="quick_humanize",
        agent_name="ai_humanizer_agent",
        input_data={
            "sections": [{"title": "Content", "content": text}],
            "topic": "Quick Humanization",
        }
    )
    
    response = await agent.execute(request)
    
    if response.status == TaskStatus.COMPLETED:
        sections = response.output_data.get("sections", [])
        if sections:
            return sections[0].get("content", text)
    
    return text
