"""Whisper transcription module - converts audio to text."""

from faster_whisper import WhisperModel
from typing import Optional
import os


class Transcriber:
    """Transcribes audio using Whisper."""
    
    # Available models (smallest to largest):
    # tiny, base, small, medium, large-v2, large-v3
    # Smaller = faster, larger = more accurate
    
    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: str = "auto"
    ):
        """
        Initialize the Whisper transcriber.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v2, large-v3)
            device: Device to use (cpu, cuda, auto)
            compute_type: Computation type (int8, float16, float32, auto)
        """
        self.model_size = model_size
        self.model = None
        self.device = device
        self.compute_type = compute_type
        
    def load_model(self):
        """Load the Whisper model (lazy loading for faster startup)."""
        if self.model is None:
            print(f"Loading Whisper model '{self.model_size}'...")
            
            # Determine optimal settings
            if self.device == "auto":
                # Try CUDA first, fall back to CPU
                try:
                    import torch
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                except ImportError:
                    device = "cpu"
            else:
                device = self.device
            
            if self.compute_type == "auto":
                # int8 is fastest on CPU, float16 on GPU
                compute_type = "int8" if device == "cpu" else "float16"
            else:
                compute_type = self.compute_type
            
            print(f"Using device: {device}, compute type: {compute_type}")
            
            self.model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type
            )
            print("Model loaded!")
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe an audio file to text.
        
        Args:
            audio_path: Path to the audio file
            language: Language code (e.g., 'en', 'es', 'de') or None for auto-detect
            
        Returns:
            Transcribed text
        """
        self.load_model()
        
        print(f"Transcribing {audio_path}...")
        
        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,  # Filter out silence
            vad_parameters=dict(
                min_silence_duration_ms=500,
            )
        )
        
        # Combine all segments
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())
        
        full_text = " ".join(text_parts).strip()
        
        print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
        print(f"Transcription: {full_text}")
        
        return full_text
    
    def transcribe_and_cleanup(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio and delete the temporary file afterwards.
        
        Args:
            audio_path: Path to the audio file
            language: Language code or None for auto-detect
            
        Returns:
            Transcribed text
        """
        try:
            return self.transcribe(audio_path, language)
        finally:
            # Clean up the temporary audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)
                print(f"Cleaned up {audio_path}")
