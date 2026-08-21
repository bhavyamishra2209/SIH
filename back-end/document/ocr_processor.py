"""
Enhanced OCR processor with swappable engines and page-level tracking.
Implements P1 requirements: Tesseract/EasyOCR support, confidence scoring, page metadata.
"""

import os
import logging
from typing import List, Tuple, Dict, Any, Optional
from abc import ABC, abstractmethod
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class OCREngine(ABC):
    """Abstract base class for OCR engines - swappable implementation."""
    
    @abstractmethod
    def extract_text(self, image: Image.Image) -> Tuple[str, float]:
        """
        Extract text from an image.
        
        Args:
            image: PIL Image object
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        pass
    
    @abstractmethod
    def extract_text_with_boxes(self, image: Image.Image) -> List[Dict[str, Any]]:
        """
        Extract text with bounding boxes and word-level confidence.
        
        Args:
            image: PIL Image object
            
        Returns:
            List of dicts with {text, confidence, bbox: (x, y, w, h)}
        """
        pass


class TesseractOCR(OCREngine):
    """Tesseract OCR engine implementation."""
    
    def __init__(self, language: str = "eng", tesseract_cmd: Optional[str] = None):
        """
        Initialize Tesseract OCR.
        
        Args:
            language: OCR language code (default: eng)
            tesseract_cmd: Path to tesseract binary (optional)
        """
        try:
            import pytesseract
            self.pytesseract = pytesseract
            
            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
            self.language = language
            logger.info(f"Initialized TesseractOCR with language: {language}")
        except ImportError:
            raise ImportError(
                "pytesseract not installed. Install with: pip install pytesseract"
            )
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: Original PIL Image
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            from PIL import ImageEnhance, ImageFilter
            
            # Convert to grayscale if not already
            if image.mode != 'L':
                image = image.convert('L')
            
            # Increase contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Sharpen the image
            image = image.filter(ImageFilter.SHARPEN)
            
            # Remove noise
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            logger.debug("Image preprocessing completed")
            return image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using original")
            return image
    
    def extract_text(self, image: Image.Image) -> Tuple[str, float]:
        """Extract text with average confidence."""
        try:
            # Preprocess image for better OCR
            image = self._preprocess_image(image)
            
            # Get detailed data with confidence scores
            data = self.pytesseract.image_to_data(
                image, 
                lang=self.language, 
                output_type=self.pytesseract.Output.DICT
            )
            
            # Extract text and calculate average confidence
            text_parts = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if conf > 0:  # Filter out low confidence/empty
                    text = data['text'][i].strip()
                    if text:
                        text_parts.append(text)
                        confidences.append(conf)
            
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Normalize confidence to 0-1 range (Tesseract uses 0-100)
            avg_confidence = avg_confidence / 100.0
            
            return full_text, avg_confidence
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return "", 0.0
    
    def extract_text_with_boxes(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Extract text with bounding boxes."""
        try:
            data = self.pytesseract.image_to_data(
                image,
                lang=self.language,
                output_type=self.pytesseract.Output.DICT
            )
            
            results = []
            for i in range(len(data['text'])):
                conf = data['conf'][i]
                if conf > 0:
                    text = data['text'][i].strip()
                    if text:
                        results.append({
                            'text': text,
                            'confidence': conf / 100.0,
                            'bbox': (
                                data['left'][i],
                                data['top'][i],
                                data['width'][i],
                                data['height'][i]
                            )
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"Tesseract box extraction failed: {e}")
            return []


class EasyOCREngine(OCREngine):
    """EasyOCR engine implementation."""
    
    def __init__(self, languages: List[str] = None, gpu: bool = False):
        """
        Initialize EasyOCR.
        
        Args:
            languages: List of language codes (default: ['en'])
            gpu: Whether to use GPU acceleration
        """
        try:
            import easyocr
            self.languages = languages or ['en']
            self.gpu = gpu
            
            logger.info(f"Initializing EasyOCR with languages: {self.languages}")
            self.reader = easyocr.Reader(self.languages, gpu=self.gpu)
            logger.info("EasyOCR initialized successfully")
            
        except ImportError:
            raise ImportError(
                "easyocr not installed. Install with: pip install easyocr"
            )
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results."""
        try:
            from PIL import ImageEnhance, ImageFilter
            
            if image.mode != 'L':
                image = image.convert('L')
            
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            image = image.filter(ImageFilter.SHARPEN)
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            return image
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image
    
    def extract_text(self, image: Image.Image) -> Tuple[str, float]:
        """Extract text with average confidence."""
        try:
            # Preprocess image
            image = self._preprocess_image(image)
            
            # Convert PIL Image to numpy array
            image_np = np.array(image)
            
            # Perform OCR
            results = self.reader.readtext(image_np)
            
            # Extract text and confidence
            text_parts = []
            confidences = []
            
            for bbox, text, conf in results:
                text_parts.append(text)
                confidences.append(conf)
            
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return full_text, avg_confidence
            
        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
            return "", 0.0
    
    def extract_text_with_boxes(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Extract text with bounding boxes."""
        try:
            image_np = np.array(image)
            results = self.reader.readtext(image_np)
            
            extracted = []
            for bbox, text, conf in results:
                # bbox is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                
                x = min(x_coords)
                y = min(y_coords)
                w = max(x_coords) - x
                h = max(y_coords) - y
                
                extracted.append({
                    'text': text,
                    'confidence': conf,
                    'bbox': (x, y, w, h)
                })
            
            return extracted
            
        except Exception as e:
            logger.error(f"EasyOCR box extraction failed: {e}")
            return []


class OCRProcessor:
    """
    Main OCR processor with swappable engines.
    Implements P1 requirement: modular OCR with page tracking.
    """
    
    def __init__(self, engine: Optional[OCREngine] = None):
        """
        Initialize OCR processor.
        
        Args:
            engine: OCR engine to use (defaults to Tesseract)
        """
        if engine is None:
            # Default to Tesseract
            try:
                self.engine = TesseractOCR()
            except ImportError:
                logger.warning("Tesseract not available, falling back to EasyOCR")
                self.engine = EasyOCREngine()
        else:
            self.engine = engine
    
    def extract_from_image(
        self, 
        image: Image.Image, 
        page_number: int = 1
    ) -> Dict[str, Any]:
        """
        Extract text from a single image with metadata.
        
        Args:
            image: PIL Image object
            page_number: Page number for tracking
            
        Returns:
            Dict with text, confidence, page_number, and metadata
        """
        text, confidence = self.engine.extract_text(image)
        
        return {
            "text": text,
            "confidence": confidence,
            "page_number": page_number,
            "word_count": len(text.split()),
            "char_count": len(text)
        }
    
    def extract_from_images(
        self, 
        images: List[Image.Image]
    ) -> List[Dict[str, Any]]:
        """
        Extract text from multiple images (pages).
        
        Args:
            images: List of PIL Image objects
            
        Returns:
            List of extraction results with page-level metadata
        """
        results = []
        
        for page_num, image in enumerate(images, start=1):
            logger.info(f"Processing page {page_num}/{len(images)}")
            result = self.extract_from_image(image, page_number=page_num)
            results.append(result)
        
        return results
    
    def extract_with_boxes(
        self, 
        image: Image.Image, 
        page_number: int = 1
    ) -> Dict[str, Any]:
        """
        Extract text with bounding boxes for detailed analysis.
        
        Args:
            image: PIL Image object
            page_number: Page number for tracking
            
        Returns:
            Dict with boxes, page_number, and aggregated metadata
        """
        boxes = self.engine.extract_text_with_boxes(image)
        
        full_text = ' '.join([b['text'] for b in boxes])
        avg_confidence = (
            sum(b['confidence'] for b in boxes) / len(boxes) 
            if boxes else 0.0
        )
        
        return {
            "text": full_text,
            "confidence": avg_confidence,
            "page_number": page_number,
            "boxes": boxes,
            "box_count": len(boxes)
        }


def extract_text_from_image(image: Image.Image) -> tuple[str, float]:
    """
    Legacy function for backward compatibility.
    Extracts text from a single image.
    
    Args:
        image: PIL Image object
        
    Returns:
        Tuple of (text, confidence)
    """
    processor = OCRProcessor()
    result = processor.extract_from_image(image)
    return result["text"], result["confidence"]


def create_ocr_processor(engine_type: str = "tesseract", **kwargs) -> OCRProcessor:
    """
    Factory function to create OCR processor with specified engine.
    
    Args:
        engine_type: Type of OCR engine ('tesseract' or 'easyocr')
        **kwargs: Additional arguments for the engine
        
    Returns:
        Configured OCRProcessor
    """
    if engine_type.lower() == "tesseract":
        engine = TesseractOCR(**kwargs)
    elif engine_type.lower() == "easyocr":
        engine = EasyOCREngine(**kwargs)
    else:
        raise ValueError(f"Unknown OCR engine type: {engine_type}")
    
    return OCRProcessor(engine=engine)