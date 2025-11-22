import os
import re
import json
from typing import Dict, List, Any
import pandas as pd
import logging

logger = logging.getLogger(__name__)

try:
    from .gemini_client import parse_with_gemini, _providers_available
except Exception:
    parse_with_gemini = None
    _providers_available = lambda: False

try:
    from .text_chunker import get_chunker
except Exception:
    get_chunker = None

# Import document processing libraries
try:
    import docx
except ImportError:
    docx = None
    logger.warning("python-docx not installed. DOCX files will not be supported.")

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None
    logger.warning("pypdf not installed. PDF files will not be supported.")

def extract_text_from_file(file_path: str) -> str:
    """Extract text from various file formats"""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    
    elif ext == ".docx":
        if docx is None:
            raise RuntimeError("python-docx not installed. pip install python-docx")
        doc = docx.Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    
    elif ext == ".pdf":
        if PdfReader is None:
            raise RuntimeError("pypdf not installed. pip install pypdf")
        reader = PdfReader(file_path)
        texts = []
        for page in reader.pages:
            texts.append(page.extract_text() or "")
        return "\n".join(texts)
    
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def normalize_persian(text: str) -> str:
    """Normalize Persian text"""
    # Persian to English number conversion
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    
    for p, e in zip(persian_digits, english_digits):
        text = text.replace(p, e)
    
    # Common Persian trading terms normalization
    persian_terms = {
        'خرید': 'buy',
        'فروش': 'sell',
        'ورود': 'entry',
        'خروج': 'exit',
        'حد ضرر': 'stop loss',
        'حد سود': 'take profit',
        'ریسک': 'risk',
        'سود': 'profit',
        'ضرر': 'loss',
        'معامله': 'trade',
        'نمودار': 'chart',
        'قیمت': 'price',
        'باز': 'open',
        'بسته': 'close',
        'بالا': 'high',
        'پایین': 'low'
    }
    
    for persian, english in persian_terms.items():
        text = text.replace(persian, english)
    
    return text

def extract_indicators(text: str) -> List[str]:
    """Extract technical indicators from text"""
    indicators = []
    
    # Common indicators in Persian and English
    indicator_patterns = [
        r'RSI\s*\(?\s*(\d+)?\s*\)?',
        r'MACD\s*\(?\s*(\d+,\s*\d+,\s*\d+)?\s*\)?',
        r'Moving\s+Average\s*\(?\s*(\d+)?\s*\)?',
        r'میانگین\s+متحرک\s*\(?\s*(\d+)?\s*\)?',
        r'Bollinger\s+Bands',
        r'باند\s+بولینگر',
        r'Stochastic',
        r'استوکاستیک',
        r'Williams\s+%R',
        r'ADX',
        r'CCI',
        r'Parabolic\s+SAR',
        r'Fibonacci',
        r'فیبوناچی',
        r'Ichimoku',
        r'ایچیموکو'
    ]
    
    for pattern in indicator_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            indicators.extend(matches)
    
    return list(set(indicators))

def parse_strategy_text(text: str) -> Dict[str, Any]:
    """Parse strategy text and extract structured information
    
    Note: We preserve the original text for extracted conditions to show user's actual strategy
    """
    # Keep original text for extraction (to preserve Persian text)
    original_text = text
    # Use normalized text only for indicator extraction
    normalized_text = normalize_persian(text)
    
    logger.debug(f"Parsing strategy text: {len(original_text)} characters")
    
    parsed = {
        "entry_conditions": [],
        "exit_conditions": [],
        "risk_management": {},
        "timeframe": None,
        "symbol": None,
        "indicators": extract_indicators(normalized_text),
        "raw_excerpt": original_text[:2000],
        "confidence_score": 0.0
    }
    
    # Extract entry conditions - improved patterns to capture more variations
    # Use original text to preserve Persian text in extracted conditions
    entry_patterns = [
        # Persian patterns - more flexible spacing and variations
        r'شرایط\s+ورود[:\-]?\s*(.+?)(?=شرایط\s+خروج|خروج|فروش|exit|sell|$)', 
        r'ورود\s+زمانی[:\-]?\s*(.+?)(?=خروج|فروش|exit|sell|$)', 
        r'خرید\s+زمانی[:\-]?\s*(.+?)(?=فروش|sell|خروج|exit|$)', 
        r'زمان\s+خرید[:\-]?\s*(.+?)(?=زمان\s+فروش|فروش|sell|$)', 
        r'شرایط\s+خرید[:\-]?\s*(.+?)(?=شرایط\s+فروش|فروش|sell|$)', 
        # More generic Persian entry patterns
        r'(?:برای\s+)?ورود[:\-]?\s*(.+?)(?=برای\s+خروج|خروج|$)', 
        r'(?:برای\s+)?خرید[:\-]?\s*(.+?)(?=برای\s+فروش|فروش|$)', 
        r'ورود[:\-]\s*(.+?)(?=\n|خروج|$)', 
        r'خرید[:\-]\s*(.+?)(?=\n|فروش|$)', 
        # English patterns
        r'entry\s+when[:\-]?\s*(.+?)(?=exit|sell|$)', 
        r'buy\s+when[:\-]?\s*(.+?)(?=sell|exit|$)', 
        r'when\s+to\s+buy[:\-]?\s*(.+?)(?=when\s+to\s+sell|sell|exit|$)', 
        r'entry\s+condition[:\-]?\s*(.+?)(?=exit|sell|$)', 
        r'buy\s+signal[:\-]?\s*(.+?)(?=sell|exit|$)', 
        r'long\s+signal[:\-]?\s*(.+?)(?=short|exit|$)', 
        r'(?:^|\n)\s*(?:entry|buy|long)[:\-]?\s*(.+?)(?=\n|exit|sell|$)', 
        # Pattern for bullet points or numbered lists (Persian and English)
        r'(?:^|\n)[\-\*•\d+\.]\s*(?:ورود|خرید|entry|buy|long)[:\-]?\s*(.+?)(?=\n[\-\*•\d+\.]|\n|$)', 
        # Numbered list patterns (1., 2., etc.)
        r'(?:^|\n)\d+[\.\)]\s*(?:ورود|خرید|entry|buy)[:\-]?\s*(.+?)(?=\n\d+[\.\)]|\n|$)', 
        # Section headers followed by conditions
        r'(?:^|\n)#{1,3}\s*(?:ورود|خرید|entry|buy)[:\-]?\s*(.+?)(?=\n#{1,3}|\n|$)', 
    ]
    
    logger.debug(f"Searching for entry conditions with {len(entry_patterns)} patterns")
    matched_patterns = []
    
    for idx, pattern in enumerate(entry_patterns):
        matches = re.findall(pattern, original_text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        for match in matches:
            # Clean up extracted text
            cleaned = match.strip()
            if cleaned and len(cleaned) > 3:  # Ignore very short matches
                parsed["entry_conditions"].append(cleaned)
                matched_patterns.append(f"Pattern {idx+1}: {cleaned[:50]}...")
    
    if matched_patterns:
        logger.info(f"Found {len(parsed['entry_conditions'])} entry conditions using patterns: {matched_patterns[:3]}")
    else:
        logger.warning(f"No entry conditions found with regex patterns. Text length: {len(original_text)} chars")
        logger.debug(f"First 500 chars of text: {original_text[:500]}")
    
    # Extract exit conditions - improved patterns
    exit_patterns = [
        # Persian patterns - more flexible spacing
        r'شرایط\s+خروج[:\-]?\s*(.+?)(?=ریسک|مدیریت|risk|management|$)', 
        r'خروج\s+زمانی[:\-]?\s*(.+?)(?=ریسک|مدیریت|risk|management|$)', 
        r'فروش\s+زمانی[:\-]?\s*(.+?)(?=ریسک|مدیریت|risk|management|$)', 
        r'زمان\s+فروش[:\-]?\s*(.+?)(?=ریسک|مدیریت|risk|management|$)', 
        r'شرایط\s+فروش[:\-]?\s*(.+?)(?=ریسک|مدیریت|risk|management|$)', 
        # More generic Persian exit patterns
        r'(?:برای\s+)?خروج[:\-]?\s*(.+?)(?=برای\s+ریسک|ریسک|$)', 
        r'(?:برای\s+)?فروش[:\-]?\s*(.+?)(?=برای\s+ریسک|ریسک|$)', 
        r'خروج[:\-]\s*(.+?)(?=\n|ریسک|$)', 
        r'فروش[:\-]\s*(.+?)(?=\n|ریسک|$)', 
        # English patterns
        r'exit\s+when[:\-]?\s*(.+?)(?=risk|management|$)', 
        r'sell\s+when[:\-]?\s*(.+?)(?=risk|management|$)', 
        r'when\s+to\s+sell[:\-]?\s*(.+?)(?=risk|management|$)', 
        r'exit\s+condition[:\-]?\s*(.+?)(?=risk|management|$)', 
        r'sell\s+signal[:\-]?\s*(.+?)(?=risk|management|$)', 
        r'short\s+signal[:\-]?\s*(.+?)(?=risk|management|$)', 
        r'(?:^|\n)\s*(?:exit|sell|short)[:\-]?\s*(.+?)(?=\n|risk|management|$)', 
        # Pattern for bullet points or numbered lists (Persian and English)
        r'(?:^|\n)[\-\*•\d+\.]\s*(?:خروج|فروش|exit|sell|short)[:\-]?\s*(.+?)(?=\n[\-\*•\d+\.]|\n|$)', 
        # Numbered list patterns (1., 2., etc.)
        r'(?:^|\n)\d+[\.\)]\s*(?:خروج|فروش|exit|sell)[:\-]?\s*(.+?)(?=\n\d+[\.\)]|\n|$)', 
        # Section headers followed by conditions
        r'(?:^|\n)#{1,3}\s*(?:خروج|فروش|exit|sell)[:\-]?\s*(.+?)(?=\n#{1,3}|\n|$)', 
    ]
    
    logger.debug(f"Searching for exit conditions with {len(exit_patterns)} patterns")
    matched_exit_patterns = []
    
    for idx, pattern in enumerate(exit_patterns):
        matches = re.findall(pattern, original_text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        for match in matches:
            # Clean up extracted text
            cleaned = match.strip()
            if cleaned and len(cleaned) > 3:  # Ignore very short matches
                parsed["exit_conditions"].append(cleaned)
                matched_exit_patterns.append(f"Pattern {idx+1}: {cleaned[:50]}...")
    
    if matched_exit_patterns:
        logger.info(f"Found {len(parsed['exit_conditions'])} exit conditions using patterns: {matched_exit_patterns[:3]}")
    else:
        logger.warning(f"No exit conditions found with regex patterns. Text length: {len(original_text)} chars")
    
    # Extract risk management
    risk_patterns = [
        r'حد\s+ضرر[:\-]?\s*(\d+(?:\.\d+)?)', 
        r'stop\s+loss[:\-]?\s*(\d+(?:\.\d+)?)', 
        r'حد\s+سود[:\-]?\s*(\d+(?:\.\d+)?)', 
        r'take\s+profit[:\-]?\s*(\d+(?:\.\d+)?)', 
        r'ریسک\s+هر\s+معامله[:\-]?\s*(\d+(?:\.\d+)?)', 
        r'risk\s+per\s+trade[:\-]?\s*(\d+(?:\.\d+)?)', 
        r'position\s+size[:\-]?\s*(\d+(?:\.\d+)?)', 
    ]
    
    for pattern in risk_patterns:
        matches = re.findall(pattern, original_text, re.IGNORECASE)
        if matches:
            parsed["risk_management"][pattern.split('[')[0]] = matches[0]
    
    # Extract timeframe
    timeframe_patterns = [
        r'تایم\s+فریم[:\-]?\s*(\w+)', 
        r'timeframe[:\-]?\s*(\w+)', 
        r'بازه\s+زمانی[:\-]?\s*(\w+)', 
        r'(\d+)\s*minute',
        r'(\d+)\s*دقیقه',
        r'(\d+)\s*hour',
        r'(\d+)\s*ساعت',
        r'daily',
        r'روزانه',
        r'weekly',
        r'هفتگی'
    ]
    
    for pattern in timeframe_patterns:
        matches = re.findall(pattern, original_text, re.IGNORECASE)
        if matches:
            parsed["timeframe"] = matches[0]
    
    # Extract symbol
    symbol_patterns = [
        r'نماد[:\-]?\s*(\w+)', 
        r'symbol[:\-]?\s*(\w+)', 
        r'جفت\s+ارز[:\-]?\s*(\w+)', 
        r'currency\s+pair[:\-]?\s*(\w+)', 
        r'(EUR/USD|GBP/USD|USD/JPY|AUD/USD|USD/CAD|USD/CHF|NZD/USD)',
        r'(EURUSD|GBPUSD|USDJPY|AUDUSD|USDCAD|USDCHF|NZDUSD)',
    ]
    
    for pattern in symbol_patterns:
        matches = re.findall(pattern, original_text, re.IGNORECASE)
        if matches:
            parsed["symbol"] = matches[0]
    
    # Calculate confidence score
    confidence = 0.0
    if parsed["entry_conditions"]:
        confidence += 0.3
    if parsed["exit_conditions"]:
        confidence += 0.3
    if parsed["risk_management"]:
        confidence += 0.2
    if parsed["indicators"]:
        confidence += 0.1
    if parsed["timeframe"]:
        confidence += 0.1
    
    parsed["confidence_score"] = confidence
    
    return parsed

def parse_strategy_file(file_path: str, user=None) -> Dict[str, Any]:
    """
    Parse strategy file exclusively through ChatGPT/OpenAI.
    If the AI provider is unavailable or returns an error, the parsing fails.
    Automatically chunks large texts that exceed token limits.
    """
    try:
        text = extract_text_from_file(file_path)
        logger.debug(f"Extracted {len(text)} characters from file: {file_path}")

        if parse_with_gemini is None:
            raise RuntimeError("AI parser not available. ChatGPT integration is required.")

        if not _providers_available(user=user):
            logger.error("[NLP_PARSER] No ChatGPT providers available")
            raise RuntimeError("هیچ کلید ChatGPT فعالی پیکربندی نشده است.")

        logger.debug("[NLP_PARSER] Attempting AI parsing (ChatGPT only)...")
        logger.debug(f"[NLP_PARSER] Text length: {len(text)}, User: {user.username if user and user.is_authenticated else 'None'}")
        
        # Check if text needs chunking
        chunker = get_chunker() if get_chunker else None
        if chunker and chunker.should_chunk(text):
            logger.info(f"[NLP_PARSER] Text exceeds token limit, chunking into smaller pieces")
            chunks = chunker.chunk_text(text)
            logger.info(f"[NLP_PARSER] Text chunked into {len(chunks)} pieces")
            
            # Process each chunk and merge results
            all_entry_conditions = []
            all_exit_conditions = []
            all_indicators = []
            merged_risk_management = {}
            timeframe = None
            symbol = None
            
            for i, chunk in enumerate(chunks):
                logger.debug(f"[NLP_PARSER] Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
                chunk_result = parse_with_gemini(chunk, user=user)
                
                if chunk_result.get('ai_status') == 'ok':
                    # Merge results from this chunk
                    if chunk_result.get('entry_conditions'):
                        all_entry_conditions.extend(chunk_result.get('entry_conditions', []))
                    if chunk_result.get('exit_conditions'):
                        all_exit_conditions.extend(chunk_result.get('exit_conditions', []))
                    if chunk_result.get('indicators'):
                        all_indicators.extend(chunk_result.get('indicators', []))
                    if chunk_result.get('risk_management'):
                        merged_risk_management.update(chunk_result.get('risk_management', {}))
                    if chunk_result.get('timeframe') and not timeframe:
                        timeframe = chunk_result.get('timeframe')
                    if chunk_result.get('symbol') and not symbol:
                        symbol = chunk_result.get('symbol')
                else:
                    # If any chunk fails, return error
                    logger.warning(f"[NLP_PARSER] Chunk {i+1} failed: {chunk_result.get('message', 'Unknown error')}")
                    return {
                        "error": chunk_result.get('message', 'AI parsing failed for chunk'),
                        "error_type": "ai_parsing_failed",
                        "provider_attempts": chunk_result.get('provider_attempts', []),
                        "status_code": chunk_result.get('status_code'),
                        "entry_conditions": all_entry_conditions,
                        "exit_conditions": all_exit_conditions,
                        "risk_management": merged_risk_management,
                        "timeframe": timeframe,
                        "symbol": symbol,
                        "indicators": list(set(all_indicators)),
                        "raw_excerpt": text[:2000],
                        "confidence_score": 0.0,
                        "parsing_method": "chunked_error"
                    }
            
            # Return merged results
            final_result = {
                "entry_conditions": all_entry_conditions,
                "exit_conditions": all_exit_conditions,
                "risk_management": merged_risk_management,
                "timeframe": timeframe,
                "symbol": symbol,
                "indicators": list(set(all_indicators)),
                "raw_excerpt": text[:2000],
                "confidence_score": 0.0,
                "parsing_method": "ai_chunked"
            }
            
            # Calculate confidence
            confidence = 0.0
            if final_result["entry_conditions"]:
                confidence += 0.3
            if final_result["exit_conditions"]:
                confidence += 0.3
            if final_result["risk_management"]:
                confidence += 0.2
            if final_result["indicators"]:
                confidence += 0.1
            if final_result["timeframe"]:
                confidence += 0.1
            final_result["confidence_score"] = confidence
            
            logger.info(
                "AI parsing result (chunked): entry=%s, exit=%s, confidence=%.2f",
                len(final_result["entry_conditions"]),
                len(final_result["exit_conditions"]),
                final_result["confidence_score"],
            )
            
            return final_result
        
        # Process normally if no chunking needed
        ai_result = parse_with_gemini(text, user=user)
        
        logger.debug(f"[NLP_PARSER] AI result received: ai_status={ai_result.get('ai_status') if isinstance(ai_result, dict) else 'NOT_DICT'}")

        if not isinstance(ai_result, dict):
            logger.error(f"[NLP_PARSER] Invalid AI result type: {type(ai_result)}")
            raise RuntimeError("پاسخ نامعتبر از ChatGPT دریافت شد.")

        if ai_result.get('ai_status') != 'ok':
            message = ai_result.get('message') or ai_result.get('error') or 'AI parsing failed'
            error_details = ai_result.get('error', '')
            provider_attempts = ai_result.get('provider_attempts', [])
            
            # Log error only once - details are already logged in provider_manager and gemini_client
            # Only log a summary to avoid duplicate logs
            status_code = None
            if provider_attempts and len(provider_attempts) > 0:
                status_code = provider_attempts[0].get('status_code')
            
            # Log different levels based on error type
            if status_code == 429:
                # Rate Limit errors - log once with summary (avoid duplicate logs)
                logger.warning(f"[NLP_PARSER] Rate Limit (429) detected - Provider: {provider_attempts[0].get('provider') if provider_attempts else 'unknown'}")
            else:
                # Other errors - log summary only (truncate long messages)
                error_msg_truncated = message[:100] + "..." if len(message) > 100 else message
                logger.error(f"[NLP_PARSER] AI parsing failed: {error_msg_truncated}")
                # Log provider attempt details only if needed for debugging (use debug level)
                if provider_attempts:
                    logger.debug(f"[NLP_PARSER] Error details: {error_details[:200] if error_details else 'N/A'}")
                    for i, attempt in enumerate(provider_attempts, 1):
                        logger.debug(f"[NLP_PARSER] Provider attempt {i}: {attempt.get('provider')}, status={attempt.get('status_code')}")
            
            # به جای raise RuntimeError، یک dictionary با اطلاعات خطا برگردانیم
            # این باعث می‌شود که در api/views.py بتوانیم Rate Limit errors را به درستی handle کنیم
            
            return {
                "error": message,
                "error_type": "ai_parsing_failed",
                "provider_attempts": provider_attempts,
                "status_code": status_code,
                "entry_conditions": [],
                "exit_conditions": [],
                "risk_management": {},
                "timeframe": None,
                "symbol": None,
                "indicators": [],
                "raw_excerpt": "",
                "confidence_score": 0.0,
                "parsing_method": "error"
            }

        final_result = {
            "entry_conditions": ai_result.get('entry_conditions', []),
            "exit_conditions": ai_result.get('exit_conditions', []),
            "risk_management": ai_result.get('risk_management', {}),
            "timeframe": ai_result.get('timeframe'),
            "symbol": ai_result.get('symbol'),
            "indicators": ai_result.get('indicators', []),
            "raw_excerpt": text[:2000],
            "confidence_score": 0.0,
            "parsing_method": "ai"
        }

        confidence = 0.0
        if final_result["entry_conditions"]:
            confidence += 0.3
        if final_result["exit_conditions"]:
            confidence += 0.3
        if final_result["risk_management"]:
            confidence += 0.2
        if final_result["indicators"]:
            confidence += 0.1
        if final_result["timeframe"]:
            confidence += 0.1
        final_result["confidence_score"] = confidence

        logger.info(
            "AI parsing result: entry=%s, exit=%s, confidence=%.2f",
            len(final_result["entry_conditions"]),
            len(final_result["exit_conditions"]),
            final_result["confidence_score"],
        )

        return final_result

    except Exception as e:
        logger.error(f"Error parsing strategy file {file_path}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "error": str(e),
            "entry_conditions": [],
            "exit_conditions": [],
            "risk_management": {},
            "timeframe": None,
            "symbol": None,
            "indicators": [],
            "raw_excerpt": "",
            "confidence_score": 0.0,
            "parsing_method": "error"
        }

def validate_strategy(parsed_strategy: Dict[str, Any]) -> Dict[str, Any]:
    """Validate parsed strategy and provide suggestions"""
    validation = {
        "is_valid": True,
        "warnings": [],
        "suggestions": []
    }
    
    if not parsed_strategy.get("entry_conditions"):
        validation["warnings"].append("No entry conditions found")
        validation["is_valid"] = False
    
    if not parsed_strategy.get("exit_conditions"):
        validation["warnings"].append("No exit conditions found")
        validation["is_valid"] = False
    
    if not parsed_strategy.get("risk_management"):
        validation["suggestions"].append("Consider adding risk management rules")
    
    if not parsed_strategy.get("timeframe"):
        validation["suggestions"].append("Specify timeframe for better results")
    
    if not parsed_strategy.get("symbol"):
        validation["suggestions"].append("Specify trading symbol")
    
    if parsed_strategy.get("confidence_score", 0) < 0.5:
        validation["warnings"].append("Low confidence in strategy parsing")
    
    return validation

# Legacy functions for backward compatibility
def parse_strategy(text):
    """Legacy function for backward compatibility"""
    return parse_strategy_text(text)