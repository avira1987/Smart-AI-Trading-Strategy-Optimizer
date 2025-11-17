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

def parse_strategy_file(file_path: str) -> Dict[str, Any]:
    """
    Parse strategy file using AI-First approach with Regex fallback.
    
    Strategy:
    1. Try AI parsing first (with cache support)
    2. If AI fails or unavailable, fallback to regex
    3. Merge results: prefer AI results, fill gaps with regex
    """
    try:
        text = extract_text_from_file(file_path)
        logger.info(f"Extracted {len(text)} characters from file: {file_path}")
        
        # Initialize result structure
        final_result = {
            "entry_conditions": [],
            "exit_conditions": [],
            "risk_management": {},
            "timeframe": None,
            "symbol": None,
            "indicators": [],
            "raw_excerpt": text[:2000],
            "confidence_score": 0.0,
            "parsing_method": "unknown"
        }
        
        ai_result = None
        ai_success = False
        
        # ===== STEP 1: Try AI First (with automatic caching) =====
        if parse_with_gemini is not None and _providers_available():
            try:
                logger.info("Attempting AI parsing first (with cache support)...")
                ai_result = parse_with_gemini(text)
                
                if isinstance(ai_result, dict) and ai_result.get('ai_status') == 'ok':
                    # AI parsing successful
                    ai_success = True
                    logger.info(f"✅ AI parsing successful: "
                               f"{len(ai_result.get('entry_conditions', []))} entry conditions, "
                               f"{len(ai_result.get('exit_conditions', []))} exit conditions")
                    
                    # Extract AI results
                    final_result["entry_conditions"] = ai_result.get('entry_conditions', [])
                    final_result["exit_conditions"] = ai_result.get('exit_conditions', [])
                    final_result["risk_management"] = ai_result.get('risk_management', {})
                    final_result["indicators"] = ai_result.get('indicators', [])
                    final_result["timeframe"] = ai_result.get('timeframe')
                    final_result["symbol"] = ai_result.get('symbol')
                    final_result["parsing_method"] = "ai"
                    
                    # Calculate confidence from AI results
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
                    
                    # If AI provided complete results, return early
                    if (final_result["entry_conditions"] and 
                        final_result["exit_conditions"] and 
                        confidence >= 0.6):
                        logger.info(f"AI parsing complete - confidence: {confidence:.2f}")
                        return final_result
                    else:
                        logger.info(f"AI parsing partial - confidence: {confidence:.2f}, will merge with regex")
                        
                else:
                    # AI parsing failed or returned error
                    ai_status = ai_result.get('ai_status', 'unknown') if isinstance(ai_result, dict) else 'invalid'
                    error_msg = ai_result.get('message', 'Unknown error') if isinstance(ai_result, dict) else 'Invalid response'
                    logger.warning(f"AI parsing failed (status: {ai_status}): {error_msg}")
                    
            except Exception as ai_error:
                logger.warning(f"AI parsing exception: {str(ai_error)}, falling back to regex")
                import traceback
                logger.debug(f"AI error traceback: {traceback.format_exc()}")
        else:
            if parse_with_gemini is None:
                logger.info("AI parser not available (parse_with_gemini is None)")
            elif not _providers_available():
                logger.info("No AI providers configured - falling back to regex")
        
        # ===== STEP 2: Fallback to Regex Parsing =====
        logger.info("Running regex parsing as fallback/enhancement...")
        regex_result = parse_strategy_text(text)
        
        logger.info(f"Regex parsing results: {len(regex_result.get('entry_conditions', []))} entry conditions, "
                   f"{len(regex_result.get('exit_conditions', []))} exit conditions, "
                   f"confidence: {regex_result.get('confidence_score', 0.0):.2f}")
        
        # ===== STEP 3: Merge Results (AI-first, fill gaps with regex) =====
        if ai_success:
            # AI was successful - use AI as base, fill gaps with regex
            logger.info("Merging: AI results as base, regex for gaps")
            
            # Fill missing entry conditions from regex
            if not final_result["entry_conditions"] and regex_result.get("entry_conditions"):
                final_result["entry_conditions"] = regex_result["entry_conditions"]
                logger.info(f"Filled {len(regex_result['entry_conditions'])} entry conditions from regex")
            
            # Fill missing exit conditions from regex
            if not final_result["exit_conditions"] and regex_result.get("exit_conditions"):
                final_result["exit_conditions"] = regex_result["exit_conditions"]
                logger.info(f"Filled {len(regex_result['exit_conditions'])} exit conditions from regex")
            
            # Fill missing indicators from regex
            if not final_result["indicators"] and regex_result.get("indicators"):
                final_result["indicators"] = regex_result["indicators"]
                logger.info(f"Filled {len(regex_result['indicators'])} indicators from regex")
            
            # Fill missing risk management from regex
            if not final_result["risk_management"] and regex_result.get("risk_management"):
                final_result["risk_management"] = regex_result["risk_management"]
                logger.info("Filled risk_management from regex")
            
            # Fill missing timeframe from regex
            if not final_result["timeframe"] and regex_result.get("timeframe"):
                final_result["timeframe"] = regex_result["timeframe"]
                logger.info(f"Filled timeframe from regex: {regex_result['timeframe']}")
            
            # Fill missing symbol from regex
            if not final_result["symbol"] and regex_result.get("symbol"):
                final_result["symbol"] = regex_result["symbol"]
                logger.info(f"Filled symbol from regex: {regex_result['symbol']}")
            
            # Recalculate confidence after merge
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
            final_result["parsing_method"] = "ai_regex_merged"
            
        else:
            # AI failed or unavailable - use regex results
            logger.info("Using regex results (AI unavailable or failed)")
            final_result = regex_result
            final_result["parsing_method"] = "regex"
        
        logger.info(f"Final parsing result: method={final_result.get('parsing_method')}, "
                   f"entry={len(final_result.get('entry_conditions', []))}, "
                   f"exit={len(final_result.get('exit_conditions', []))}, "
                   f"confidence={final_result.get('confidence_score', 0.0):.2f}")
        
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