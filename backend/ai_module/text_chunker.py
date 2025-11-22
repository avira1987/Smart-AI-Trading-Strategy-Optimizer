"""
Intelligent text chunking for large inputs that exceed token limits.
Splits text by paragraphs/sentences to maintain context.
"""

import re
import logging
from typing import List, Tuple, Optional
from django.conf import settings

logger = logging.getLogger("ai.text_chunker")


class TextChunker:
    """
    Intelligently chunks text by paragraphs and sentences.
    """
    
    def __init__(self, max_tokens_per_chunk: int = None):
        self.max_tokens_per_chunk = max_tokens_per_chunk or getattr(
            settings, 'AI_MAX_TOKENS_PER_CHUNK', 1500
        )
        self.max_chars_per_chunk = self.max_tokens_per_chunk * 4  # Rough estimate: 4 chars = 1 token
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough: 4 chars = 1 token)."""
        return len(text) // 4
    
    def should_chunk(self, text: str) -> bool:
        """Check if text should be chunked."""
        return self.estimate_tokens(text) > self.max_tokens_per_chunk
    
    def split_by_paragraphs(self, text: str) -> List[str]:
        """Split text by paragraphs (double newlines)."""
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences (periods, exclamation, question marks)."""
        # Pattern for sentence endings (Persian and English)
        sentence_pattern = r'([.!?؟]\s+|\.\s*$)'
        sentences = re.split(sentence_pattern, text)
        # Recombine sentences with their punctuation
        result = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            if sentence.strip():
                result.append(sentence.strip())
        # Handle last sentence if odd number
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            result.append(sentences[-1].strip())
        return result
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Intelligently chunk text into smaller pieces.
        Tries to maintain context by splitting at paragraph boundaries first,
        then sentence boundaries if needed.
        """
        if not self.should_chunk(text):
            return [text]
        
        logger.info(
            f"Chunking text: {len(text)} chars, "
            f"estimated {self.estimate_tokens(text)} tokens, "
            f"max per chunk: {self.max_tokens_per_chunk}"
        )
        
        chunks = []
        
        # First, try splitting by paragraphs
        paragraphs = self.split_by_paragraphs(text)
        
        current_chunk = ""
        for paragraph in paragraphs:
            # Check if adding this paragraph would exceed limit
            test_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            test_tokens = self.estimate_tokens(test_chunk)
            
            if test_tokens <= self.max_tokens_per_chunk:
                # Safe to add paragraph
                current_chunk = test_chunk
            else:
                # Current chunk is full, save it and start new one
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph
                
                # If single paragraph is too large, split by sentences
                if self.estimate_tokens(paragraph) > self.max_tokens_per_chunk:
                    sentences = self.split_by_sentences(paragraph)
                    for sentence in sentences:
                        test_chunk = current_chunk + " " + sentence if current_chunk else sentence
                        test_tokens = self.estimate_tokens(test_chunk)
                        
                        if test_tokens <= self.max_tokens_per_chunk:
                            current_chunk = test_chunk
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sentence
                            
                            # If single sentence is still too large, force split
                            if self.estimate_tokens(sentence) > self.max_tokens_per_chunk:
                                # Split by character count as last resort
                                char_limit = self.max_chars_per_chunk
                                for i in range(0, len(sentence), char_limit):
                                    chunks.append(sentence[i:i + char_limit])
                                current_chunk = ""
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        logger.info(f"Text chunked into {len(chunks)} pieces")
        return chunks
    
    def merge_chunked_responses(self, responses: List[str], separator: str = "\n\n") -> str:
        """
        Merge chunked responses back into a single text.
        """
        return separator.join(responses)


# Global chunker instance
_global_chunker: Optional[TextChunker] = None


def get_chunker() -> TextChunker:
    """Get or create the global text chunker instance."""
    global _global_chunker
    if _global_chunker is None:
        max_tokens = getattr(settings, 'AI_MAX_TOKENS_PER_CHUNK', 1500)
        _global_chunker = TextChunker(max_tokens_per_chunk=max_tokens)
    return _global_chunker

