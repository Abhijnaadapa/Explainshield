import io
import os
import logging
from typing import Union, Optional
import numpy as np

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF not installed. PDF extraction will be limited.")

try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    logger.warning("pytesseract/PIL not installed. Image OCR will be unavailable.")

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False
    logger.warning("sentence-transformers not installed.")


class DocumentExtractor:
    SUPPORTED_IMAGES = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp'}
    SUPPORTED_PDF = {'.pdf'}
    
    def __init__(self):
        self._embedder = None
        
    def _get_embedder(self):
        if self._embedder is None and ST_AVAILABLE:
            logger.info("Loading sentence-transformer model for embeddings...")
            self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
        return self._embedder
    
    def extract_text(self, file_bytes: bytes, filename: str) -> dict:
        """
        Extract text from PDF or image file.
        
        Returns:
            {
                "text": str,
                "embeddings": list[float],
                "source_type": "pdf" | "image",
                "page_count": int (for PDF)
            }
        """
        ext = os.path.splitext(filename.lower())[1]
        
        if ext in self.SUPPORTED_PDF:
            return self._extract_from_pdf(file_bytes)
        elif ext in self.SUPPORTED_IMAGES:
            return self._extract_from_image(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def _extract_from_pdf(self, file_bytes: bytes) -> dict:
        if not PYMUPDF_AVAILABLE:
            return {
                "text": "[PDF extraction unavailable - PyMuPDF not installed]",
                "embeddings": [],
                "source_type": "pdf",
                "page_count": 0
            }
        
        text_parts = []
        page_count = 0
        
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            page_count = len(doc)
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(page_text)
                else:
                    # Try OCR on scanned pages
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_bytes = pix.tobytes("png")
                    ocr_text = self._ocr_image_bytes(img_bytes)
                    if ocr_text.strip():
                        text_parts.append(ocr_text)
                        logger.info(f"OCR extracted from PDF page {page_num + 1}")
        
        full_text = "\n\n".join(text_parts)
        embeddings = self._generate_embeddings(full_text)
        
        return {
            "text": full_text,
            "embeddings": embeddings,
            "source_type": "pdf",
            "page_count": page_count
        }
    
    def _extract_from_image(self, file_bytes: bytes) -> dict:
        if not PYTESSERACT_AVAILABLE:
            return {
                "text": "[Image OCR unavailable - pytesseract not installed]",
                "embeddings": [],
                "source_type": "image",
                "page_count": 1
            }
        
        text = self._ocr_image_bytes(file_bytes)
        embeddings = self._generate_embeddings(text)
        
        return {
            "text": text,
            "embeddings": embeddings,
            "source_type": "image",
            "page_count": 1
        }
    
    def _ocr_image_bytes(self, image_bytes: bytes) -> str:
        if not PYTESSERACT_AVAILABLE:
            return ""
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Convert to grayscale for better OCR
            if image.mode != 'L':
                image = image.convert('L')
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""
    
    def _generate_embeddings(self, text: str) -> list:
        if not text.strip() or not ST_AVAILABLE:
            return []
        
        embedder = self._get_embedder()
        if embedder is None:
            return []
        
        try:
            # Truncate very long texts to avoid memory issues
            max_chars = 10000
            if len(text) > max_chars:
                text = text[:max_chars]
            
            embedding = embedder.encode([text], convert_to_numpy=True)
            return embedding[0].tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []


def extract_document(file_bytes: bytes, filename: str) -> dict:
    """
    Convenience function for document extraction.
    """
    extractor = DocumentExtractor()
    return extractor.extract_text(file_bytes, filename)


if __name__ == "__main__":
    print("Document Extractor module loaded.")
    print(f"PyMuPDF available: {PYMUPDF_AVAILABLE}")
    print(f"pytesseract available: {PYTESSERACT_AVAILABLE}")
    print(f"sentence-transformers available: {ST_AVAILABLE}")