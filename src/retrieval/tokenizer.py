"""
Custom Tokenizer and Text Preprocessing for BM25 and Lexical Information Retrieval.
Implemented from scratch without external BM25 library dependencies.
"""

import re
import string
from typing import List, Set

# Standard English stop words curated for IR
STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", 
    "but", "by", "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", 
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had", 
    "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", 
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", 
    "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", 
    "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", 
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", 
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", 
    "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these", 
    "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under", 
    "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", 
    "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", 
    "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", 
    "your", "yours", "yourself", "yourselves"
}


def clean_text(text: str) -> str:
    """Lowercases text, removes punctuation, and normalizes whitespace."""
    if not text:
        return ""
    text = text.lower()
    # Replace punctuation with spaces
    text = re.sub(r'[' + re.escape(string.punctuation) + r']', ' ', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def simple_stem(word: str) -> str:
    """
    Lightweight rule-based suffix stemmer to conflate common plurals and inflections
    (e.g., networks -> network, trained -> train).
    """
    if len(word) <= 3:
        return word
    
    # Common deep learning / general suffixes
    if word.endswith("sses"):
        return word[:-2]
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("ss"):
        return word
    if word.endswith("s") and not word.endswith("us") and not word.endswith("is"):
        return word[:-1]
    
    if word.endswith("ing") and len(word) > 5:
        stem = word[:-3]
        if stem.endswith("ll") or stem.endswith("nn") or stem.endswith("tt") or stem.endswith("pp"):
            stem = stem[:-1]
        return stem
    
    if word.endswith("ed") and len(word) > 4:
        stem = word[:-2]
        if stem.endswith("ll") or stem.endswith("nn") or stem.endswith("tt") or stem.endswith("pp"):
            stem = stem[:-1]
        return stem
    
    if word.endswith("ational") and len(word) > 8:
        return word[:-7] + "ation"
    if word.endswith("tional") and len(word) > 7:
        return word[:-2]
    if word.endswith("ization") and len(word) > 7:
        return word[:-5] + "e"
    
    return word


def tokenize(text: str, remove_stopwords: bool = True, stem: bool = True) -> List[str]:
    """
    Tokenizes raw text into clean term tokens.
    
    Args:
        text: Raw document or query string.
        remove_stopwords: If True, filters out frequent non-discriminative stop words.
        stem: If True, applies lightweight stemming.
        
    Returns:
        List of processed term tokens.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []
    
    tokens = cleaned.split()
    
    result = []
    for token in tokens:
        # Ignore purely single-character tokens unless digits
        if len(token) < 2 and not token.isdigit():
            continue
        if remove_stopwords and token in STOP_WORDS:
            continue
        if stem:
            token = simple_stem(token)
        result.append(token)
        
    return result
