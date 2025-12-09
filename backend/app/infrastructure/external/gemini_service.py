"""Google Gemini API integration for embeddings and similarity detection."""
import asyncio
import logging
import hashlib
from typing import List, Optional
import numpy as np
from google import genai
from google.genai import types
from app.core.config import settings
from app.infrastructure.cache.redis_cache import cache
import httpx
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class GeminiService:
    """Google Gemini service for embeddings and similarity detection."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.text_model = settings.GEMINI_TEXT_MODEL
        self.vision_model = settings.GEMINI_VISION_MODEL
        self.timeout = 30.0
        self.max_retries = 3
        self.retry_delay = 1.0
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        """Get or create Gemini client."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Gemini API call failed after {self.max_retries} attempts: {e}")
                    raise
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"Gemini API call failed (attempt {attempt + 1}/{self.max_retries}), retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
        return None

    def _generate_cache_key(self, prefix: str, content: str) -> str:
        """Generate a stable cache key using SHA256 hash."""
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        return f"gemini:{prefix}:{content_hash}"

    async def generate_text_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text content."""
        if not text or not text.strip():
            return None

        # Limit text length to prevent API errors
        text = text.strip()[:10000]  # Limit to 10k characters

        # Check cache first
        cache_key = self._generate_cache_key("text_embed", text)
        try:
            cached = await cache.get(cache_key)
            if cached:
                return cached
        except Exception:
            pass  # Cache miss, continue

        try:
            client = self._get_client()
            
            # Run in thread pool since genai client is synchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.embed_content(
                    model=self.text_model,
                    contents=text
                )
            )

            if response and response.embeddings and len(response.embeddings) > 0:
                embedding = list(response.embeddings[0].values)
                # Cache for 7 days
                await cache.set(cache_key, embedding, ttl=604800)
                return embedding
        except ValueError as e:
            if "GEMINI_API_KEY" in str(e):
                logger.error("Gemini API key not configured")
            else:
                logger.error(f"Error generating text embedding: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating text embedding: {e}")
            return None

        return None

    def _validate_image_url(self, url: str) -> bool:
        """Validate image URL format."""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ['http', 'https'] and parsed.netloc
        except Exception:
            return False

    async def generate_image_embedding(self, image_url: str) -> Optional[List[float]]:
        """Generate embedding for image using multimodal model."""
        if not image_url or not self._validate_image_url(image_url):
            logger.warning(f"Invalid image URL: {image_url}")
            return None

        # Check cache first
        cache_key = self._generate_cache_key("image_embed", image_url)
        try:
            cached = await cache.get(cache_key)
            if cached:
                return cached
        except Exception:
            pass  # Cache miss, continue

        try:
            # Download image and convert to base64 or use URI
            # For now, we'll use the vision model to describe the image
            # and then embed the description
            description = await self.describe_image(image_url)
            if description:
                return await self.generate_text_embedding(description)
        except Exception as e:
            logger.error(f"Error generating image embedding for {image_url}: {e}")
            return None

        return None

    def _detect_mime_type(self, image_data: bytes, url: str) -> str:
        """Detect MIME type from image data or URL extension."""
        # Check magic bytes
        if image_data.startswith(b'\xff\xd8\xff'):
            return "image/jpeg"
        elif image_data.startswith(b'\x89PNG\r\n\x1a\n'):
            return "image/png"
        elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):
            return "image/gif"
        elif image_data.startswith(b'WEBP', 8):
            return "image/webp"
        
        # Fallback to URL extension
        parsed = urlparse(url)
        ext = parsed.path.lower().split('.')[-1]
        mime_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        return mime_map.get(ext, 'image/jpeg')

    async def describe_image(self, image_url: str) -> Optional[str]:
        """Generate text description of image content."""
        if not image_url or not self._validate_image_url(image_url):
            return None

        # Check cache first
        cache_key = self._generate_cache_key("image_desc", image_url)
        try:
            cached = await cache.get(cache_key)
            if cached:
                return cached
        except Exception:
            pass  # Cache miss, continue

        try:
            # Download image with size limit (10MB)
            max_size = 10 * 1024 * 1024
            async with httpx.AsyncClient(timeout=self.timeout, max_redirects=5) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                
                # Check content length
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > max_size:
                    logger.warning(f"Image too large: {image_url} ({content_length} bytes)")
                    return None
                
                image_data = response.content
                if len(image_data) > max_size:
                    logger.warning(f"Image too large: {image_url} ({len(image_data)} bytes)")
                    return None

            # Detect MIME type
            mime_type = self._detect_mime_type(image_data, image_url)

            client = self._get_client()
            
            # Run in thread pool since genai client is synchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=self.vision_model,
                    contents=[
                        "Describe this image in detail, focusing on any damage, issues, or problems visible. Be specific about what you see.",
                        types.Part.from_bytes(image_data, mime_type=mime_type)
                    ]
                )
            )

            if response and response.text:
                description = response.text.strip()
                # Cache for 7 days
                await cache.set(cache_key, description, ttl=604800)
                return description
        except httpx.HTTPError as e:
            logger.error(f"HTTP error describing image {image_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error describing image {image_url}: {e}")
            return None

        return None

    async def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts."""
        if not text1 or not text2:
            return 0.0

        emb1 = await self.generate_text_embedding(text1)
        emb2 = await self.generate_text_embedding(text2)

        if not emb1 or not emb2:
            return 0.0

        return self._cosine_similarity(emb1, emb2)

    async def calculate_image_similarity(self, image_url1: str, image_url2: str) -> float:
        """Calculate cosine similarity between two images."""
        if not image_url1 or not image_url2:
            return 0.0

        emb1 = await self.generate_image_embedding(image_url1)
        emb2 = await self.generate_image_embedding(image_url2)

        if not emb1 or not emb2:
            return 0.0

        return self._cosine_similarity(emb1, emb2)

    async def calculate_multimodal_similarity(
        self,
        text1: str,
        images1: List[str],
        text2: str,
        images2: List[str]
    ) -> float:
        """Calculate combined similarity score using text and images."""
        text_weight = settings.DUPLICATE_TEXT_WEIGHT
        image_weight = settings.DUPLICATE_IMAGE_WEIGHT

        # Calculate text similarity
        text_score = await self.calculate_text_similarity(text1, text2)

        # Calculate image similarity if both have images
        image_score = 0.0
        if images1 and images2:
            # Compare all images and take the highest similarity
            max_image_similarity = 0.0
            for img1 in images1[:settings.GEMINI_MAX_IMAGES_PER_INCIDENT]:
                for img2 in images2[:settings.GEMINI_MAX_IMAGES_PER_INCIDENT]:
                    similarity = await self.calculate_image_similarity(img1, img2)
                    max_image_similarity = max(max_image_similarity, similarity)
            image_score = max_image_similarity
        elif images1 or images2:
            # If only one has images, slightly penalize
            text_weight = 0.8
            image_weight = 0.2

        # Combined score
        combined_score = (text_score * text_weight) + (image_score * image_weight)
        return combined_score

    async def batch_embed_text(self, contents: List[str]) -> List[Optional[List[float]]]:
        """Batch generate text embeddings."""
        results = []
        for content in contents:
            embedding = await self.generate_text_embedding(content)
            results.append(embedding)
        return results

    async def batch_embed_images(self, image_urls: List[str]) -> List[Optional[List[float]]]:
        """Batch generate image embeddings."""
        results = []
        for url in image_urls:
            embedding = await self.generate_image_embedding(url)
            results.append(embedding)
        return results

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(np.clip(similarity, -1.0, 1.0))
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

