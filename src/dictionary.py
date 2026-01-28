"""Smart dictionary module - phonetic/fuzzy matching for brand names and custom terms."""

import json
import os
import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
from .paths import get_config_path


class Dictionary:
    """
    Smart dictionary that matches similar-sounding words.
    
    Just add your brand names/terms, and it will automatically
    match phonetically similar transcriptions.
    """
    
    def __init__(self, dictionary_path: Optional[str] = None):
        """
        Initialize the dictionary.
        
        Args:
            dictionary_path: Path to dictionary.json file
        """
        if dictionary_path is None:
            self.dictionary_path = get_config_path("dictionary.json")
        else:
            self.dictionary_path = dictionary_path
        
        self.terms: List[str] = []
        self._phonetic_cache: Dict[str, str] = {}
        self.load()
    
    def load(self):
        """Load terms from the dictionary file."""
        if not os.path.exists(self.dictionary_path):
            print(f"No dictionary file found at {self.dictionary_path}")
            self.terms = []
            return
        
        try:
            with open(self.dictionary_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.terms = data.get("terms", [])
            
            # Build phonetic cache for all terms
            self._phonetic_cache = {}
            for term in self.terms:
                self._phonetic_cache[term] = self._to_phonetic(term)
            
            print(f"Loaded {len(self.terms)} terms from dictionary")
            
        except Exception as e:
            print(f"Error loading dictionary: {e}")
            self.terms = []
    
    def _to_phonetic(self, text: str) -> str:
        """
        Convert text to a phonetic representation.
        
        This normalizes the text to make phonetic comparison easier:
        - Lowercase
        - Remove non-alphanumeric
        - Apply phonetic substitutions
        """
        # Normalize
        text = text.lower()
        
        # Remove spaces for comparison
        text = text.replace(' ', '')
        
        # Common phonetic equivalents - order matters!
        substitutions = [
            # FX/effects equivalence - do this FIRST
            (r'effects', 'fx'),
            (r'efects', 'fx'),
            (r'efx', 'fx'),
            
            # Vowel sounds that often get confused
            (r'ea', 'e'),      # mean -> men
            (r'ee', 'e'),      # meet -> met
            (r'ai', 'a'),      # main -> man
            (r'ay', 'a'),      # may -> ma
            (r'oo', 'u'),      # moon -> mun
            (r'ou', 'o'),      # out -> ot
            (r'oi', 'oy'),
            (r'ie', 'i'),
            
            # Consonant equivalents
            (r'ph', 'f'),
            (r'ck', 'k'),
            (r'x', 'ks'),
            (r'qu', 'kw'),
            (r'ce', 'se'),
            (r'ci', 'si'),
            (r'cy', 'sy'),
            (r'tion', 'shun'),
            (r'sion', 'zhun'),
            (r'ght', 't'),
            (r'wh', 'w'),
            (r'wr', 'r'),
            (r'kn', 'n'),
            (r'gn', 'n'),
            (r'mb$', 'm'),
            (r'mn', 'n'),
            
            # Double letters to single
            (r'(.)\1+', r'\1'),
            
            # Ending patterns
            (r'e$', ''),       # Remove silent e at end
            (r'ed$', 'd'),     # jumped -> jumpd
            (r'ing$', 'n'),    # running -> runn
        ]
        
        result = text
        for pattern, replacement in substitutions:
            result = re.sub(pattern, replacement, result)
        
        # Remove remaining non-alphanumeric
        result = re.sub(r'[^a-z0-9]', '', result)
        
        return result
    
    def _similarity(self, a: str, b: str) -> float:
        """Calculate similarity ratio between two strings (0.0 to 1.0)."""
        return SequenceMatcher(None, a, b).ratio()
    
    def _phonetic_similarity(self, text: str, term: str) -> float:
        """
        Calculate phonetic similarity between transcribed text and a dictionary term.
        
        Returns a score from 0.0 to 1.0
        """
        text_phonetic = self._to_phonetic(text)
        term_phonetic = self._phonetic_cache.get(term, self._to_phonetic(term))
        
        # Direct phonetic comparison
        phonetic_sim = self._similarity(text_phonetic, term_phonetic)
        
        # Also check raw similarity (helps with exact matches)
        raw_sim = self._similarity(text.lower().replace(' ', ''), term.lower())
        
        
        # Return the better of phonetic or raw match
        return max(phonetic_sim, raw_sim)
    
    def _find_matches_in_text(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Find all potential matches in the transcribed text.
        
        Returns list of (original_text, replacement, start_pos, end_pos)
        """
        matches = []
        words = text.split()
        
        if not words or not self.terms:
            return matches
        
        # Common words to ignore (too short/generic to match reliably)
        ignore_words = {
            'the', 'a', 'an', 'to', 'of', 'in', 'on', 'at', 'by', 'for',
            'is', 'it', 'be', 'as', 'or', 'and', 'but', 'if', 'so', 'no',
            'out', 'up', 'do', 'my', 'me', 'we', 'he', 'she', 'you', 'i',
            'was', 'has', 'had', 'are', 'were', 'been', 'have', 'get', 'got'
        }
        
        # Try matching sequences of 1-4 words against each term
        for term in self.terms:
            term_word_count = len(term.split())
            # Check window sizes from 1 to max(4, term_word_count + 1)
            max_window = max(4, term_word_count + 1)
            
            for window_size in range(1, min(max_window + 1, len(words) + 1)):
                for i in range(len(words) - window_size + 1):
                    phrase = ' '.join(words[i:i + window_size])
                    
                    # Skip if phrase is just common words
                    phrase_words = set(phrase.lower().split())
                    if phrase_words.issubset(ignore_words):
                        continue
                    
                    # Skip very short phrases for long terms (likely false positives)
                    if len(phrase.replace(' ', '')) < len(term) * 0.4:
                        continue
                    
                    similarity = self._phonetic_similarity(phrase, term)
                    
                    # Threshold for matching (tuned for good results)
                    threshold = 0.75
                    
                    # Adjust threshold based on term length (shorter = stricter)
                    if len(term) <= 4:
                        threshold = 0.90
                    elif len(term) <= 6:
                        threshold = 0.80
                    
                    # Single words need higher threshold to avoid false positives
                    if len(phrase.split()) == 1:
                        threshold = max(threshold, 0.85)
                    
                    # Require higher threshold if phrase is much longer than term
                    if len(phrase.replace(' ', '')) > len(term) * 1.5:
                        threshold = max(threshold, 0.90)
                    
                    if similarity >= threshold:
                        # Find position in original text
                        start = text.lower().find(phrase.lower())
                        if start >= 0:
                            matches.append((phrase, term, similarity, start, start + len(phrase)))
        
        return matches
    
    def apply(self, text: str) -> str:
        """
        Apply smart dictionary replacements to text.
        
        Args:
            text: The transcribed text
            
        Returns:
            Text with similar-sounding words replaced by dictionary terms
        """
        if not self.terms or not text:
            return text
        
        matches = self._find_matches_in_text(text)
        
        if not matches:
            return text
        
        # Sort by: highest similarity first, then prefer matches closer to term length
        def match_score(m):
            original, replacement, similarity, start, end = m
            # Calculate how close the original is in length to the replacement
            len_ratio = len(original.replace(' ', '')) / max(len(replacement), 1)
            # Ideal ratio is around 1.0-1.5 (original slightly longer due to spaces/variations)
            len_score = 1.0 - min(abs(len_ratio - 1.2), 1.0)
            # Combined score: primarily similarity, with length as tiebreaker
            return -(similarity * 10 + len_score)
        
        matches.sort(key=match_score)
        
        # Apply replacements, avoiding overlaps
        result = text
        applied = []
        
        for original, replacement, similarity, start, end in matches:
            # Skip if original is already exactly the replacement (case-insensitive but keep formatting)
            if original.lower() == replacement.lower():
                continue
            
            # Skip phrases that contain extra common words + the exact term
            # e.g., don't match "to GitHub" or "out ChatGPT" when the term itself is there
            original_words = original.lower().split()
            skip_this = False
            if len(original_words) > 1:
                # Check if any single word is the term itself
                for word in original_words:
                    if word == replacement.lower():
                        # The term is already in the phrase - skip this match
                        skip_this = True
                        break
            if skip_this:
                continue
            
            # Check for overlap with already applied replacements
            overlaps = False
            for applied_start, applied_end in applied:
                if not (end <= applied_start or start >= applied_end):
                    overlaps = True
                    break
            
            if not overlaps:
                # Case-preserving replacement
                pattern = re.compile(re.escape(original), re.IGNORECASE)
                new_result = pattern.sub(replacement, result, count=1)
                
                if new_result != result:
                    print(f"Dictionary match: '{original}' -> '{replacement}' (similarity: {similarity:.2f})")
                    result = new_result
                    applied.append((start, end))
        
        return result
    
    def reload(self):
        """Reload the dictionary from file."""
        print("Reloading dictionary...")
        self.load()
    
    @property
    def replacements(self) -> Dict[str, str]:
        """For backwards compatibility - return terms count."""
        return {term: term for term in self.terms}
