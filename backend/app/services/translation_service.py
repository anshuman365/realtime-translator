"""
Machine Translation service using Hugging Face Transformers.
"""
import asyncio
from typing import Optional
from transformers import MarianMTModel, MarianTokenizer, M2M100ForConditionalGeneration, M2M100Tokenizer
from loguru import logger
from app.config import get_translation_model, TRANSLATION_MODELS, settings
import os


class TranslationService:
    """Machine Translation service with model caching."""
    
    def __init__(self):
        self.models = {}  # Cache loaded models
        self.tokenizers = {}  # Cache tokenizers
        self.cache_dir = settings.hf_cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_model_and_tokenizer(self, source_lang: str, target_lang: str):
        """Get or load model and tokenizer for a language pair."""
        model_name = get_translation_model(source_lang, target_lang)
        
        if model_name not in self.models:
            logger.info(f"Loading translation model: {model_name}")
            try:
                # Check if it's M2M100 (multilingual model)
                if "m2m100" in model_name.lower():
                    tokenizer = M2M100Tokenizer.from_pretrained(
                        model_name,
                        cache_dir=self.cache_dir
                    )
                    model = M2M100ForConditionalGeneration.from_pretrained(
                        model_name,
                        cache_dir=self.cache_dir
                    )
                else:
                    # MarianMT models
                    tokenizer = MarianTokenizer.from_pretrained(
                        model_name,
                        cache_dir=self.cache_dir
                    )
                    model = MarianMTModel.from_pretrained(
                        model_name,
                        cache_dir=self.cache_dir
                    )
                
                self.models[model_name] = model
                self.tokenizers[model_name] = tokenizer
                logger.success(f"Model loaded: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                raise
        
        return self.models[model_name], self.tokenizers[model_name]
    
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str,
        max_length: int = 512
    ) -> Optional[str]:
        """
        Translate text from source to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            max_length: Maximum length of generated translation
        
        Returns:
            Translated text or None if error
        """
        if not text or not text.strip():
            return ""
        
        model_name = get_translation_model(source_lang, target_lang)
        
        def _translate():
            model, tokenizer = self._get_model_and_tokenizer(source_lang, target_lang)
            
            # For M2M100, set source and target languages
            if "m2m100" in model_name.lower():
                # M2M100 uses language codes like "en", "hi", etc.
                tokenizer.src_lang = source_lang
                encoded = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=max_length)
                generated_tokens = model.generate(
                    **encoded,
                    forced_bos_token_id=tokenizer.get_lang_id(target_lang),
                    max_length=max_length
                )
            else:
                # MarianMT models
                encoded = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=max_length)
                generated_tokens = model.generate(**encoded, max_length=max_length)
            
            translated = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
            return translated
        
        try:
            loop = asyncio.get_event_loop()
            translated_text = await loop.run_in_executor(None, _translate)
            logger.debug(f"MT ({source_lang}->{target_lang}): '{text}' -> '{translated_text}'")
            return translated_text
        except Exception as e:
            logger.error(f"Translation error ({source_lang}->{target_lang}): {e}")
            return None
    
    async def translate_batch(
        self,
        texts: list[str],
        source_lang: str,
        target_lang: str,
        max_length: int = 512
    ) -> list[Optional[str]]:
        """
        Translate multiple texts in batch (more efficient).
        
        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            max_length: Maximum length of generated translations
        
        Returns:
            List of translated texts
        """
        if not texts:
            return []
        
        model_name = get_translation_model(source_lang, target_lang)
        
        def _translate_batch():
            model, tokenizer = self._get_model_and_tokenizer(source_lang, target_lang)
            
            # For M2M100
            if "m2m100" in model_name.lower():
                tokenizer.src_lang = source_lang
                encoded = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=max_length)
                generated_tokens = model.generate(
                    **encoded,
                    forced_bos_token_id=tokenizer.get_lang_id(target_lang),
                    max_length=max_length
                )
            else:
                # MarianMT
                encoded = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=max_length)
                generated_tokens = model.generate(**encoded, max_length=max_length)
            
            translated = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
            return translated
        
        try:
            loop = asyncio.get_event_loop()
            translated_texts = await loop.run_in_executor(None, _translate_batch)
            logger.debug(f"MT batch ({source_lang}->{target_lang}): {len(texts)} texts translated")
            return translated_texts
        except Exception as e:
            logger.error(f"Batch translation error ({source_lang}->{target_lang}): {e}")
            return [None] * len(texts)
    
    def preload_models(self, language_pairs: list[tuple[str, str]]):
        """
        Preload models for specified language pairs.
        
        Args:
            language_pairs: List of (source_lang, target_lang) tuples
        """
        logger.info(f"Preloading {len(language_pairs)} translation models...")
        for source_lang, target_lang in language_pairs:
            try:
                self._get_model_and_tokenizer(source_lang, target_lang)
            except Exception as e:
                logger.error(f"Failed to preload model for {source_lang}->{target_lang}: {e}")
        logger.success("Model preloading complete")


# Global translation service instance
translation_service = TranslationService()
