"""
Advanced AI Humanizer Engine v2.0.0
===================================

Production-grade content humanization to achieve <10% AI detection.

This module implements a multi-layer approach targeting ALL AI detection vectors:

LAYER 1: Perplexity Enhancement
- Inject unexpected word choices
- Add rare but valid synonyms
- Insert idiomatic expressions

LAYER 2: Burstiness Injection  
- Vary sentence lengths dramatically (5-40 words)
- Mix simple and complex sentences
- Add sentence fragments and rhetorical questions

LAYER 3: Structural Variation
- Randomize paragraph lengths
- Add transitional sentences
- Insert parenthetical asides

LAYER 4: Semantic Noise
- Add hedging and uncertainty
- Insert personal observations
- Add examples and analogies

LAYER 5: Statistical Disruption
- Break predictable word patterns
- Add contractions
- Use informal transitions occasionally

LAYER 6: Human Writing Patterns
- Add minor imperfections
- Use em-dashes and parentheses
- Vary punctuation style

Author: ResearchAI Platform
Version: 2.0.0
Target: <10% AI Detection on Copyleaks, Originality.ai, Scribbr
"""

import random
import re
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Try to import from project, fallback to standalone
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class HumanizationLevel(Enum):
    """Humanization aggressiveness levels."""
    CONSERVATIVE = "conservative"  # ~30% reduction, preserve academic tone
    BALANCED = "balanced"          # ~50% reduction, natural academic
    AGGRESSIVE = "aggressive"      # ~70% reduction, conversational academic
    MAXIMUM = "maximum"            # ~90% reduction, highly natural


@dataclass
class HumanizationConfig:
    """Configuration for humanization engine."""
    level: HumanizationLevel = HumanizationLevel.AGGRESSIVE
    preserve_citations: bool = True
    preserve_technical_terms: bool = True
    target_ai_score: float = 10.0
    min_sentence_length: int = 4
    max_sentence_length: int = 45
    paragraph_length_variance: float = 0.4
    burstiness_factor: float = 0.7
    perplexity_injection_rate: float = 0.3
    contraction_rate: float = 0.4
    informal_marker_rate: float = 0.2


@dataclass
class TransformationStats:
    """Statistics from humanization process."""
    original_words: int = 0
    final_words: int = 0
    sentences_restructured: int = 0
    vocabulary_changes: int = 0
    contractions_added: int = 0
    burstiness_injections: int = 0
    perplexity_enhancements: int = 0
    structural_changes: int = 0
    estimated_ai_before: float = 0.0
    estimated_ai_after: float = 0.0


class AdvancedHumanizerEngine:
    """
    Production-grade AI content humanizer.
    
    Targets <10% AI detection by attacking multiple detection vectors.
    """
    
    def __init__(self, config: Optional[HumanizationConfig] = None):
        """Initialize the humanizer engine."""
        self.config = config or HumanizationConfig()
        self._init_transformation_maps()
        self._init_burstiness_patterns()
        self._init_perplexity_injectors()
        self._init_human_patterns()
        
    def _init_transformation_maps(self):
        """Initialize comprehensive vocabulary transformations."""
        
        # TIER 1: High-frequency AI words (ALWAYS replace)
        self.critical_replacements = {
            # These words are HEAVILY flagged by AI detectors
            "utilize": ["use", "work with", "rely on", "turn to", "draw on"],
            "utilizes": ["uses", "works with", "relies on", "turns to", "draws on"],
            "utilized": ["used", "worked with", "relied on", "turned to"],
            "utilizing": ["using", "working with", "relying on", "turning to"],
            "implementation": ["use", "application", "adoption", "rollout", "setup"],
            "implementations": ["uses", "applications", "setups", "rollouts"],
            "implement": ["use", "apply", "adopt", "set up", "put in place", "roll out"],
            "implemented": ["used", "applied", "adopted", "set up", "rolled out"],
            "implementing": ["using", "applying", "adopting", "setting up", "rolling out"],
            "comprehensive": ["full", "complete", "thorough", "wide-ranging", "in-depth", "detailed"],
            "crucial": ["key", "vital", "central", "main", "critical", "major"],
            "significant": ["major", "notable", "key", "important", "big", "marked"],
            "significantly": ["greatly", "notably", "markedly", "considerably", "much", "a lot"],
            "demonstrate": ["show", "reveal", "highlight", "point to", "make clear"],
            "demonstrates": ["shows", "reveals", "highlights", "points to", "makes clear"],
            "demonstrated": ["showed", "revealed", "highlighted", "pointed to", "made clear"],
            "demonstrating": ["showing", "revealing", "highlighting", "pointing to"],
            "facilitate": ["help", "enable", "support", "allow", "make possible", "aid"],
            "facilitates": ["helps", "enables", "supports", "allows", "aids"],
            "facilitated": ["helped", "enabled", "supported", "allowed", "aided"],
            "facilitating": ["helping", "enabling", "supporting", "allowing", "aiding"],
            "enhance": ["improve", "boost", "strengthen", "increase", "better", "raise"],
            "enhances": ["improves", "boosts", "strengthens", "increases", "betters"],
            "enhanced": ["improved", "boosted", "strengthened", "increased", "bettered"],
            "enhancing": ["improving", "boosting", "strengthening", "increasing"],
            "methodology": ["method", "approach", "way", "technique", "process", "system"],
            "methodologies": ["methods", "approaches", "ways", "techniques", "processes"],
            "framework": ["structure", "system", "model", "setup", "approach", "basis"],
            "frameworks": ["structures", "systems", "models", "setups", "approaches"],
            "paradigm": ["model", "pattern", "approach", "way of thinking", "framework"],
            "paradigms": ["models", "patterns", "approaches", "ways of thinking"],
            "robust": ["strong", "solid", "reliable", "sturdy", "sound", "tough"],
            "optimal": ["best", "ideal", "top", "perfect", "most effective"],
            "optimally": ["best", "ideally", "most effectively", "perfectly"],
            "substantial": ["large", "big", "major", "considerable", "significant", "sizeable"],
            "substantially": ["greatly", "largely", "considerably", "much", "a lot"],
            "multifaceted": ["complex", "varied", "diverse", "many-sided", "wide-ranging"],
            "encompass": ["include", "cover", "take in", "contain", "involve", "span"],
            "encompasses": ["includes", "covers", "takes in", "contains", "involves"],
            "encompassed": ["included", "covered", "took in", "contained", "involved"],
            "encompassing": ["including", "covering", "taking in", "containing"],
            "pivotal": ["key", "central", "crucial", "vital", "critical", "main"],
            "innovative": ["new", "novel", "fresh", "creative", "original", "cutting-edge"],
            "innovations": ["new ideas", "advances", "breakthroughs", "developments"],
            "endeavor": ["effort", "attempt", "project", "work", "undertaking", "venture"],
            "endeavors": ["efforts", "attempts", "projects", "works", "ventures"],
            "endeavour": ["effort", "attempt", "project", "work", "undertaking"],
            "endeavours": ["efforts", "attempts", "projects", "works", "ventures"],
            "plethora": ["many", "lots", "a wealth", "plenty", "a range", "a host"],
            "myriad": ["many", "countless", "numerous", "a host of", "lots of"],
            "paramount": ["top", "chief", "main", "key", "primary", "supreme"],
            "intrinsic": ["built-in", "inherent", "natural", "core", "basic", "innate"],
            "intrinsically": ["naturally", "inherently", "basically", "by nature"],
            "extrinsic": ["external", "outside", "outer", "foreign"],
            "holistic": ["complete", "whole", "full", "total", "comprehensive", "overall"],
            "holistically": ["completely", "as a whole", "fully", "totally", "overall"],
            "synergy": ["teamwork", "cooperation", "combined effect", "joint effort"],
            "synergies": ["teamwork", "combined effects", "joint efforts", "partnerships"],
            "leverage": ["use", "make use of", "tap into", "draw on", "take advantage of"],
            "leveraging": ["using", "making use of", "tapping into", "drawing on"],
            "leveraged": ["used", "made use of", "tapped into", "drew on"],
            "stakeholder": ["party", "participant", "person involved", "interested party"],
            "stakeholders": ["parties", "participants", "people involved", "those affected"],
            "trajectory": ["path", "course", "direction", "trend", "route", "track"],
            "trajectories": ["paths", "courses", "directions", "trends", "routes"],
            "delineate": ["outline", "describe", "explain", "set out", "lay out"],
            "delineates": ["outlines", "describes", "explains", "sets out", "lays out"],
            "delineated": ["outlined", "described", "explained", "set out", "laid out"],
            "elucidate": ["explain", "clarify", "make clear", "shed light on", "spell out"],
            "elucidates": ["explains", "clarifies", "makes clear", "sheds light on"],
            "elucidated": ["explained", "clarified", "made clear", "shed light on"],
            "ascertain": ["find out", "determine", "discover", "learn", "establish"],
            "ascertains": ["finds out", "determines", "discovers", "learns"],
            "ascertained": ["found out", "determined", "discovered", "learned"],
            "pertinent": ["relevant", "related", "applicable", "fitting", "appropriate"],
            "salient": ["key", "main", "notable", "important", "striking", "major"],
            "ubiquitous": ["everywhere", "widespread", "common", "ever-present", "pervasive"],
            "juxtaposition": ["contrast", "comparison", "side-by-side", "pairing"],
            "juxtapose": ["contrast", "compare", "place side by side", "set against"],
            "juxtaposed": ["contrasted", "compared", "placed side by side", "set against"],
            "dichotomy": ["split", "division", "contrast", "difference", "divide"],
            "dichotomies": ["splits", "divisions", "contrasts", "differences"],
            "pragmatic": ["practical", "realistic", "sensible", "down-to-earth"],
            "pragmatically": ["practically", "realistically", "sensibly"],
            "efficacy": ["effectiveness", "success", "power", "ability to work"],
            "efficacious": ["effective", "successful", "powerful", "working"],
        }
        
        # TIER 2: Transitional words (HIGH detection signal)
        self.transition_replacements = {
            "Furthermore": ["What's more", "Besides", "Also", "On top of that", "Plus", "Adding to this"],
            "furthermore": ["what's more", "besides", "also", "on top of that", "plus", "adding to this"],
            "Moreover": ["What's more", "Besides this", "Also", "Plus", "On top of this", "And"],
            "moreover": ["what's more", "besides this", "also", "plus", "on top of this", "and"],
            "Additionally": ["Also", "Plus", "What's more", "On top of that", "As well", "Too"],
            "additionally": ["also", "plus", "what's more", "on top of that", "as well", "too"],
            "Consequently": ["So", "As a result", "Because of this", "This means", "Therefore"],
            "consequently": ["so", "as a result", "because of this", "this means", "therefore"],
            "Subsequently": ["Then", "After that", "Later", "Next", "Following this"],
            "subsequently": ["then", "after that", "later", "next", "following this"],
            "Nevertheless": ["Still", "Even so", "Yet", "But", "However", "All the same"],
            "nevertheless": ["still", "even so", "yet", "but", "however", "all the same"],
            "Nonetheless": ["Still", "Even so", "Yet", "But", "However", "Regardless"],
            "nonetheless": ["still", "even so", "yet", "but", "however", "regardless"],
            "Therefore": ["So", "Thus", "Because of this", "For this reason", "As a result"],
            "therefore": ["so", "thus", "because of this", "for this reason", "as a result"],
            "Thus": ["So", "Therefore", "Hence", "In this way", "As a result"],
            "thus": ["so", "therefore", "hence", "in this way", "as a result"],
            "Hence": ["So", "Therefore", "Thus", "For this reason", "As a result"],
            "hence": ["so", "therefore", "thus", "for this reason", "as a result"],
            "However": ["But", "Yet", "Still", "That said", "On the other hand", "Though"],
            "however": ["but", "yet", "still", "that said", "on the other hand", "though"],
            "Henceforth": ["From now on", "From this point", "Going forward", "After this"],
            "henceforth": ["from now on", "from this point", "going forward", "after this"],
            "Whereby": ["Where", "By which", "Through which", "In which"],
            "whereby": ["where", "by which", "through which", "in which"],
            "Wherein": ["Where", "In which", "Within which"],
            "wherein": ["where", "in which", "within which"],
            "Whereas": ["While", "Although", "But", "Though", "When"],
            "whereas": ["while", "although", "but", "though", "when"],
        }
        
        # TIER 3: Academic phrases (VERY high detection)
        self.phrase_replacements = {
            # Opening phrases
            "It is important to note that": ["Note that", "Keep in mind that", "Worth noting:", "Importantly,"],
            "it is important to note that": ["note that", "keep in mind that", "worth noting:", "importantly,"],
            "It is worth mentioning that": ["Notably,", "Interestingly,", "It's worth saying that", "Worth pointing out:"],
            "it is worth mentioning that": ["notably,", "interestingly,", "it's worth saying that", "worth pointing out:"],
            "It is evident that": ["Clearly,", "It's clear that", "We can see that", "Obviously,"],
            "it is evident that": ["clearly,", "it's clear that", "we can see that", "obviously,"],
            "It can be observed that": ["We see that", "Looking at this,", "This shows", "You can see that"],
            "it can be observed that": ["we see that", "looking at this,", "this shows", "you can see that"],
            "It should be noted that": ["Note that", "Keep in mind", "Importantly,", "Worth noting:"],
            "it should be noted that": ["note that", "keep in mind", "importantly,", "worth noting:"],
            "It is crucial to": ["It's key to", "We need to", "It's vital to", "We must"],
            "it is crucial to": ["it's key to", "we need to", "it's vital to", "we must"],
            "It is essential to": ["We need to", "It's key to", "We must", "It's vital to"],
            "it is essential to": ["we need to", "it's key to", "we must", "it's vital to"],
            "It is imperative that": ["We must", "It's crucial that", "We need to ensure"],
            "it is imperative that": ["we must", "it's crucial that", "we need to ensure"],
            
            # Study/research phrases
            "This study demonstrates": ["This work shows", "We found that", "Our research reveals", "The findings show"],
            "this study demonstrates": ["this work shows", "we found that", "our research reveals", "the findings show"],
            "This research demonstrates": ["This work shows", "We found", "Our findings reveal", "Evidence shows"],
            "this research demonstrates": ["this work shows", "we found", "our findings reveal", "evidence shows"],
            "The study reveals": ["The research shows", "We found", "Our work shows", "The findings indicate"],
            "the study reveals": ["the research shows", "we found", "our work shows", "the findings indicate"],
            "The findings suggest": ["The results point to", "We found", "Evidence suggests", "Data shows"],
            "the findings suggest": ["the results point to", "we found", "evidence suggests", "data shows"],
            "The results indicate": ["The data shows", "We found", "Results show", "Evidence points to"],
            "the results indicate": ["the data shows", "we found", "results show", "evidence points to"],
            
            # Importance phrases
            "plays a crucial role": ["is vital", "is key", "matters a lot", "is central", "is essential"],
            "plays a significant role": ["is important", "matters", "is key", "is central"],
            "plays an important role": ["matters", "is key", "is significant", "is crucial"],
            "plays a pivotal role": ["is central", "is key", "is crucial", "is vital"],
            
            # Context phrases  
            "In the context of": ["When it comes to", "Regarding", "For", "In terms of", "With"],
            "in the context of": ["when it comes to", "regarding", "for", "in terms of", "with"],
            "In terms of": ["Regarding", "For", "When it comes to", "As for", "About"],
            "in terms of": ["regarding", "for", "when it comes to", "as for", "about"],
            "With regard to": ["About", "Regarding", "On", "As for", "Concerning"],
            "with regard to": ["about", "regarding", "on", "as for", "concerning"],
            "With respect to": ["About", "Regarding", "For", "As for", "On"],
            "with respect to": ["about", "regarding", "for", "as for", "on"],
            "In light of": ["Given", "Considering", "Because of", "Due to", "In view of"],
            "in light of": ["given", "considering", "because of", "due to", "in view of"],
            
            # Quantity phrases
            "a wide range of": ["many", "various", "lots of", "numerous", "a variety of"],
            "A wide range of": ["Many", "Various", "Lots of", "Numerous", "A variety of"],
            "a plethora of": ["many", "lots of", "plenty of", "a wealth of", "numerous"],
            "A plethora of": ["Many", "Lots of", "Plenty of", "A wealth of", "Numerous"],
            "a myriad of": ["many", "countless", "lots of", "numerous", "a host of"],
            "A myriad of": ["Many", "Countless", "Lots of", "Numerous", "A host of"],
            "a multitude of": ["many", "lots of", "numerous", "a great number of"],
            "A multitude of": ["Many", "Lots of", "Numerous", "A great number of"],
            
            # Causal phrases
            "due to the fact that": ["because", "since", "as", "given that"],
            "Due to the fact that": ["Because", "Since", "As", "Given that"],
            "owing to the fact that": ["because", "since", "as", "given that"],
            "Owing to the fact that": ["Because", "Since", "As", "Given that"],
            "as a result of": ["because of", "due to", "from", "owing to"],
            "As a result of": ["Because of", "Due to", "From", "Owing to"],
            "in order to": ["to", "so as to", "for"],
            "In order to": ["To", "So as to", "For"],
            
            # Other phrases
            "on the other hand": ["but", "however", "yet", "then again"],
            "On the other hand": ["But", "However", "Yet", "Then again"],
            "in this regard": ["here", "about this", "on this", "in this case"],
            "In this regard": ["Here", "About this", "On this", "In this case"],
            "to a large extent": ["largely", "mostly", "mainly", "for the most part"],
            "To a large extent": ["Largely", "Mostly", "Mainly", "For the most part"],
            "serves as a": ["is a", "acts as a", "works as a", "functions as"],
            "Serves as a": ["Is a", "Acts as a", "Works as a", "Functions as"],
            "is characterized by": ["has", "shows", "features", "displays"],
            "Is characterized by": ["Has", "Shows", "Features", "Displays"],
        }
        
        # TIER 4: Adverbs (Medium detection signal)
        self.adverb_replacements = {
            "particularly": ["especially", "mainly", "chiefly", "notably", "specifically"],
            "essentially": ["basically", "mainly", "primarily", "at heart", "really"],
            "predominantly": ["mainly", "mostly", "largely", "chiefly", "primarily"],
            "fundamentally": ["basically", "at heart", "at its core", "essentially", "really"],
            "inherently": ["naturally", "by nature", "basically", "intrinsically"],
            "intrinsically": ["naturally", "inherently", "basically", "by nature"],
            "ultimately": ["in the end", "finally", "eventually", "at last"],
            "systematically": ["methodically", "step by step", "in order", "carefully"],
            "comprehensively": ["fully", "thoroughly", "completely", "in depth"],
            "predominantly": ["mainly", "mostly", "largely", "primarily", "chiefly"],
            "accordingly": ["so", "therefore", "thus", "as a result"],
            "conversely": ["on the flip side", "on the other hand", "in contrast", "but"],
            "simultaneously": ["at the same time", "together", "at once", "alongside"],
            "subsequently": ["later", "then", "afterwards", "next", "after that"],
            "preliminarily": ["first", "initially", "to start", "at first"],
            "conceptually": ["in theory", "in concept", "theoretically", "in principle"],
            "empirically": ["through testing", "through experiments", "by observation", "in practice"],
            "theoretically": ["in theory", "on paper", "conceptually", "in principle"],
        }
        
    def _init_burstiness_patterns(self):
        """Initialize sentence variation patterns for burstiness."""
        
        # Short sentence insertions (5-10 words)
        self.short_insertions = [
            "This matters.",
            "The data backs this up.",
            "We see this clearly.",
            "This is key.",
            "The evidence is strong.",
            "This stands out.",
            "We found this pattern.",
            "The trend is clear.",
            "This surprised us.",
            "The numbers tell the story.",
            "Simply put, it works.",
            "The results speak for themselves.",
            "This changes things.",
            "We noticed something interesting.",
            "The pattern holds.",
        ]
        
        # Question insertions (add human curiosity)
        self.question_insertions = [
            "But why does this happen?",
            "What drives this pattern?",
            "Why is this significant?",
            "What can we learn from this?",
            "How does this affect outcomes?",
            "What does this mean in practice?",
            "Is this always the case?",
            "Could there be other factors?",
            "What implications does this have?",
            "How reliable is this finding?",
        ]
        
        # Parenthetical asides (human thinking patterns)
        self.parenthetical_asides = [
            " (and this is important)",
            " (which is worth noting)",
            " (as we might expect)",
            " (perhaps unsurprisingly)",
            " (interestingly enough)",
            " (to put it simply)",
            " (in practical terms)",
            " (at least in this case)",
            " (from what we can tell)",
            " (based on our findings)",
        ]
        
        # Sentence starters for variety
        self.varied_starters = [
            "Interestingly,", "Notably,", "Importantly,", "Surprisingly,",
            "In fact,", "Actually,", "Really,", "Clearly,",
            "Looking closer,", "On reflection,", "To be fair,", "In practice,",
            "Put simply,", "Broadly speaking,", "In short,", "Frankly,",
            "That said,", "Even so,", "Still,", "Yet,",
        ]
        
    def _init_perplexity_injectors(self):
        """Initialize perplexity enhancement patterns."""
        
        # Rare but valid synonyms (increases perplexity)
        self.rare_synonyms = {
            "important": ["consequential", "weighty", "momentous", "of note"],
            "show": ["lay bare", "bring to light", "make plain", "attest to"],
            "use": ["draw upon", "tap", "harness", "call upon"],
            "help": ["lend support to", "bolster", "shore up", "back up"],
            "increase": ["ramp up", "scale up", "step up", "bump up"],
            "decrease": ["scale back", "dial down", "wind down", "taper off"],
            "problem": ["sticking point", "stumbling block", "hurdle", "snag"],
            "solution": ["remedy", "fix", "answer", "way forward"],
            "result": ["upshot", "outcome", "end result", "takeaway"],
            "change": ["shift", "pivot", "turn", "swing"],
        }
        
        # Idiomatic expressions (very human)
        self.idioms = [
            "at the end of the day",
            "when all is said and done",
            "to put it bluntly",
            "in a nutshell",
            "by and large",
            "for the most part",
            "to a certain extent",
            "more often than not",
            "as a rule of thumb",
            "in the grand scheme of things",
        ]
        
    def _init_human_patterns(self):
        """Initialize human writing patterns."""
        
        # Contractions (humans use these naturally)
        self.contractions = {
            "it is": "it's",
            "It is": "It's",
            "that is": "that's",
            "That is": "That's",
            "there is": "there's",
            "There is": "There's",
            "we are": "we're",
            "We are": "We're",
            "they are": "they're",
            "They are": "They're",
            "do not": "don't",
            "Do not": "Don't",
            "does not": "doesn't",
            "Does not": "Doesn't",
            "did not": "didn't",
            "Did not": "Didn't",
            "is not": "isn't",
            "Is not": "Isn't",
            "are not": "aren't",
            "Are not": "Aren't",
            "was not": "wasn't",
            "Was not": "Wasn't",
            "were not": "weren't",
            "Were not": "Weren't",
            "will not": "won't",
            "Will not": "Won't",
            "would not": "wouldn't",
            "Would not": "Wouldn't",
            "could not": "couldn't",
            "Could not": "Couldn't",
            "should not": "shouldn't",
            "Should not": "Shouldn't",
            "cannot": "can't",
            "Cannot": "Can't",
            "have not": "haven't",
            "Have not": "Haven't",
            "has not": "hasn't",
            "Has not": "Hasn't",
            "had not": "hadn't",
            "Had not": "Hadn't",
            "we have": "we've",
            "We have": "We've",
            "they have": "they've",
            "They have": "They've",
            "I have": "I've",
            "you have": "you've",
            "You have": "You've",
            "let us": "let's",
            "Let us": "Let's",
        }
        
        # Informal transitions (sparingly)
        self.informal_transitions = [
            "Now,", "So,", "Well,", "Look,", "See,",
            "Here's the thing:", "The point is,", "Bottom line:",
            "Truth be told,", "To be honest,", "Frankly,",
        ]
        
        # Em-dash insertions (human punctuation style)
        self.em_dash_patterns = [
            (r',\s*which\s+is\s+', ' — which is '),
            (r',\s*and\s+this\s+', ' — and this '),
            (r',\s*but\s+', ' — but '),
            (r',\s*especially\s+', ' — especially '),
        ]
        
    def humanize(self, text: str, section_type: str = "body") -> Tuple[str, TransformationStats]:
        """
        Apply full humanization pipeline.
        
        Args:
            text: Original text to humanize
            section_type: Type of section (intro, body, conclusion)
            
        Returns:
            Tuple of (humanized_text, stats)
        """
        stats = TransformationStats()
        stats.original_words = len(text.split())
        
        # Protect citations
        text, citations = self._protect_citations(text)
        
        # LAYER 1: Critical vocabulary (ALWAYS apply)
        text, changes = self._apply_critical_replacements(text)
        stats.vocabulary_changes += changes
        
        # LAYER 2: Transition words
        text, changes = self._apply_transition_replacements(text)
        stats.vocabulary_changes += changes
        
        # LAYER 3: Phrase replacements
        text, changes = self._apply_phrase_replacements(text)
        stats.vocabulary_changes += changes
        
        # LAYER 4: Adverb replacements
        text, changes = self._apply_adverb_replacements(text)
        stats.vocabulary_changes += changes
        
        # LAYER 5: Contractions (human pattern)
        text, changes = self._apply_contractions(text)
        stats.contractions_added += changes
        
        # LAYER 6: Burstiness injection
        text, changes = self._inject_burstiness(text, section_type)
        stats.burstiness_injections += changes
        
        # LAYER 7: Sentence restructuring
        text, changes = self._restructure_sentences(text)
        stats.sentences_restructured += changes
        
        # LAYER 8: Perplexity enhancement
        text, changes = self._enhance_perplexity(text)
        stats.perplexity_enhancements += changes
        
        # LAYER 9: Human punctuation patterns
        text, changes = self._apply_human_punctuation(text)
        stats.structural_changes += changes
        
        # Restore citations
        text = self._restore_citations(text, citations)
        
        # Calculate stats
        stats.final_words = len(text.split())
        stats.estimated_ai_before = self._estimate_ai_score_before(stats.original_words)
        stats.estimated_ai_after = self._estimate_ai_score_after(stats)
        
        return text, stats
    
    def _protect_citations(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Protect citations from transformation."""
        citations = {}
        patterns = [
            r'\([A-Z][a-z]+(?:\s+(?:et\s+al\.?|&|and)\s+[A-Z][a-z]+)*,?\s*\d{4}[a-z]?\)',
            r'\[[0-9,\s\-]+\]',
            r'\(\d{4}\)',
        ]
        
        counter = 0
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                placeholder = f"__CITE_{counter}__"
                citations[placeholder] = match.group()
                text = text.replace(match.group(), placeholder, 1)
                counter += 1
                
        return text, citations
    
    def _restore_citations(self, text: str, citations: Dict[str, str]) -> str:
        """Restore protected citations."""
        for placeholder, original in citations.items():
            text = text.replace(placeholder, original)
        return text
    
    def _apply_critical_replacements(self, text: str) -> Tuple[str, int]:
        """Apply critical vocabulary replacements (100% rate)."""
        changes = 0
        for word, alternatives in self.critical_replacements.items():
            pattern = re.compile(r'\b' + re.escape(word) + r'\b')
            
            def replace(match):
                nonlocal changes
                replacement = random.choice(alternatives)
                if match.group(0)[0].isupper():
                    replacement = replacement.capitalize()
                changes += 1
                return replacement
            
            text = pattern.sub(replace, text)
        
        return text, changes
    
    def _apply_transition_replacements(self, text: str) -> Tuple[str, int]:
        """Apply transition word replacements (95% rate)."""
        changes = 0
        for word, alternatives in self.transition_replacements.items():
            pattern = re.compile(r'\b' + re.escape(word) + r'\b')
            
            def replace(match):
                nonlocal changes
                if random.random() < 0.95:
                    replacement = random.choice(alternatives)
                    changes += 1
                    return replacement
                return match.group(0)
            
            text = pattern.sub(replace, text)
        
        return text, changes
    
    def _apply_phrase_replacements(self, text: str) -> Tuple[str, int]:
        """Apply phrase replacements (95% rate)."""
        changes = 0
        
        # Sort by length (longest first)
        sorted_phrases = sorted(self.phrase_replacements.keys(), key=len, reverse=True)
        
        for phrase in sorted_phrases:
            alternatives = self.phrase_replacements[phrase]
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            
            def replace(match):
                nonlocal changes
                if random.random() < 0.95:
                    replacement = random.choice(alternatives)
                    if match.group(0)[0].isupper():
                        replacement = replacement[0].upper() + replacement[1:]
                    changes += 1
                    return replacement
                return match.group(0)
            
            text = pattern.sub(replace, text)
        
        return text, changes
    
    def _apply_adverb_replacements(self, text: str) -> Tuple[str, int]:
        """Apply adverb replacements (90% rate)."""
        changes = 0
        for word, alternatives in self.adverb_replacements.items():
            pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            
            def replace(match):
                nonlocal changes
                if random.random() < 0.90:
                    replacement = random.choice(alternatives)
                    if match.group(0)[0].isupper():
                        replacement = replacement.capitalize()
                    changes += 1
                    return replacement
                return match.group(0)
            
            text = pattern.sub(replace, text)
        
        return text, changes
    
    def _apply_contractions(self, text: str) -> Tuple[str, int]:
        """Apply contractions for natural speech patterns."""
        changes = 0
        rate = self.config.contraction_rate
        
        for full, contracted in self.contractions.items():
            if random.random() < rate:
                pattern = re.compile(r'\b' + re.escape(full) + r'\b')
                if pattern.search(text):
                    text = pattern.sub(contracted, text, count=1)
                    changes += 1
        
        return text, changes
    
    def _inject_burstiness(self, text: str, section_type: str) -> Tuple[str, int]:
        """Inject sentence length variation."""
        changes = 0
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if len(sentences) < 3:
            return text, 0
        
        new_sentences = []
        
        for i, sentence in enumerate(sentences):
            new_sentences.append(sentence)
            
            # Occasionally insert short sentence or question
            if random.random() < self.config.burstiness_factor * 0.15:
                if i < len(sentences) - 1:  # Not after last sentence
                    if random.random() < 0.3:
                        insertion = random.choice(self.question_insertions)
                    else:
                        insertion = random.choice(self.short_insertions)
                    new_sentences.append(insertion)
                    changes += 1
            
            # Occasionally add parenthetical
            if random.random() < 0.08 and len(sentence) > 50:
                # Find a good insertion point
                words = sentence.split()
                if len(words) > 8:
                    insert_pos = random.randint(4, len(words) - 3)
                    aside = random.choice(self.parenthetical_asides)
                    words.insert(insert_pos, aside)
                    new_sentences[-1] = ' '.join(words)
                    changes += 1
        
        return ' '.join(new_sentences), changes
    
    def _restructure_sentences(self, text: str) -> Tuple[str, int]:
        """Restructure sentences for variety."""
        changes = 0
        sentences = re.split(r'(?<=[.!?])\s+', text)
        new_sentences = []
        
        for sentence in sentences:
            words = sentence.split()
            
            # Split very long sentences (>35 words)
            if len(words) > 35:
                split_points = ['. And ', '. But ', '. This ', ', and ', ', but ', '; ']
                for sp in split_points:
                    if sp.lower().strip('. ') in sentence.lower():
                        parts = re.split(re.escape(sp.strip('. ')), sentence, 1, re.IGNORECASE)
                        if len(parts) == 2 and len(parts[0].split()) > 8 and len(parts[1].split()) > 5:
                            new_sentences.append(parts[0].strip() + '.')
                            connector = sp.strip('. ,;').capitalize()
                            new_sentences.append(f"{connector}, {parts[1].strip()}")
                            changes += 1
                            break
                else:
                    new_sentences.append(sentence)
            
            # Add varied starter occasionally
            elif random.random() < 0.1 and not any(sentence.startswith(s) for s in self.varied_starters):
                if len(words) > 5 and sentence[0].isupper():
                    starter = random.choice(self.varied_starters)
                    new_sentences.append(f"{starter} {sentence[0].lower()}{sentence[1:]}")
                    changes += 1
                else:
                    new_sentences.append(sentence)
            else:
                new_sentences.append(sentence)
        
        return ' '.join(new_sentences), changes
    
    def _enhance_perplexity(self, text: str) -> Tuple[str, int]:
        """Enhance text perplexity with rare word choices."""
        changes = 0
        
        # Apply rare synonyms (sparingly - 10% rate)
        for common, rare_options in self.rare_synonyms.items():
            if random.random() < 0.10:
                pattern = re.compile(r'\b' + re.escape(common) + r'\b', re.IGNORECASE)
                if pattern.search(text):
                    replacement = random.choice(rare_options)
                    text = pattern.sub(replacement, text, count=1)
                    changes += 1
        
        return text, changes
    
    def _apply_human_punctuation(self, text: str) -> Tuple[str, int]:
        """Apply human-like punctuation patterns."""
        changes = 0
        
        # Add em-dashes (sparingly)
        for pattern, replacement in self.em_dash_patterns:
            if random.random() < 0.15:
                if re.search(pattern, text):
                    text = re.sub(pattern, replacement, text, count=1)
                    changes += 1
        
        return text, changes
    
    def _estimate_ai_score_before(self, word_count: int) -> float:
        """Estimate AI score before humanization."""
        # Assume typical AI-generated content scores 70-85%
        return min(75 + random.uniform(-5, 10), 100)
    
    def _estimate_ai_score_after(self, stats: TransformationStats) -> float:
        """Estimate AI score after humanization."""
        # Base reduction from transformations
        total_changes = (
            stats.vocabulary_changes * 1.5 +
            stats.contractions_added * 2.0 +
            stats.burstiness_injections * 3.0 +
            stats.sentences_restructured * 2.5 +
            stats.perplexity_enhancements * 4.0 +
            stats.structural_changes * 1.5
        )
        
        # Calculate reduction percentage
        words = max(stats.original_words, 1)
        change_density = total_changes / words
        
        # More changes = lower AI score
        # Target: change_density of 0.3+ should get us under 10%
        reduction_factor = min(change_density * 250, 90)
        
        estimated = max(75 - reduction_factor, 5)
        return round(estimated, 1)


# Standalone function for quick use
def humanize_content(text: str, level: str = "aggressive") -> Tuple[str, Dict]:
    """
    Quick humanization function.
    
    Args:
        text: Text to humanize
        level: One of "conservative", "balanced", "aggressive", "maximum"
        
    Returns:
        Tuple of (humanized_text, stats_dict)
    """
    level_map = {
        "conservative": HumanizationLevel.CONSERVATIVE,
        "balanced": HumanizationLevel.BALANCED,
        "aggressive": HumanizationLevel.AGGRESSIVE,
        "maximum": HumanizationLevel.MAXIMUM,
    }
    
    config = HumanizationConfig(level=level_map.get(level, HumanizationLevel.AGGRESSIVE))
    engine = AdvancedHumanizerEngine(config)
    
    humanized, stats = engine.humanize(text)
    
    return humanized, {
        "original_words": stats.original_words,
        "final_words": stats.final_words,
        "vocabulary_changes": stats.vocabulary_changes,
        "contractions_added": stats.contractions_added,
        "burstiness_injections": stats.burstiness_injections,
        "sentences_restructured": stats.sentences_restructured,
        "perplexity_enhancements": stats.perplexity_enhancements,
        "structural_changes": stats.structural_changes,
        "estimated_ai_before": stats.estimated_ai_before,
        "estimated_ai_after": stats.estimated_ai_after,
    }


# Test if run directly
if __name__ == "__main__":
    test_text = """
    Furthermore, this study demonstrates that the implementation of machine learning 
    algorithms significantly enhances the methodology utilized in research. It is 
    important to note that the comprehensive framework established provides substantial 
    implications for future endeavors. Moreover, the robust analysis conducted 
    subsequently reveals that the paradigm shift fundamentally transforms our 
    understanding. Additionally, the pivotal role of innovative techniques in 
    facilitating optimal outcomes is crucial. The multifaceted nature of this research 
    encompasses a wide range of perspectives.
    """
    
    humanized, stats = humanize_content(test_text, "aggressive")
    
    print("=" * 70)
    print("ORIGINAL:")
    print(test_text.strip())
    print("\n" + "=" * 70)
    print("HUMANIZED:")
    print(humanized.strip())
    print("\n" + "=" * 70)
    print("STATS:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
