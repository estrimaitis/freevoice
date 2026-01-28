"""Audio recorder module - captures microphone input."""

import numpy as np
import sounddevice as sd
from scipy.io import wavfile
import tempfile
import os
from typing import Optional
import threading


class AudioRecorder:
    """Records audio from the microphone."""
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize the recorder.
        
        Args:
            sample_rate: Sample rate for recording (16000 is optimal for Whisper)
        """
        self.sample_rate = sample_rate
        self.recording = False
        self.audio_data = []
        self._lock = threading.Lock()
        self.last_duration = 0.0  # Duration of last recording in seconds
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback for sounddevice stream."""
        if status:
            print(f"Audio status: {status}")
        if self.recording:
            with self._lock:
                self.audio_data.append(indata.copy())
    
    def start(self):
        """Start recording audio."""
        with self._lock:
            self.audio_data = []
        self.recording = True
        
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            callback=self._audio_callback
        )
        self.stream.start()
        print("Recording started...")
    
    def stop(self) -> Optional[str]:
        """
        Stop recording and save to a temporary WAV file.
        
        Returns:
            Path to the temporary WAV file, or None if no audio was recorded.
        """
        self.recording = False
        
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        with self._lock:
            if not self.audio_data:
                print("No audio data recorded")
                self.last_duration = 0.0
                return None
            
            # Concatenate all audio chunks
            audio = np.concatenate(self.audio_data, axis=0)
        
        # Calculate duration
        self.last_duration = len(audio) / self.sample_rate
        
        # Convert to int16 for WAV file
        audio_int16 = (audio * 32767).astype(np.int16)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(
            suffix='.wav',
            delete=False
        )
        temp_path = temp_file.name
        temp_file.close()
        
        wavfile.write(temp_path, self.sample_rate, audio_int16)
        print(f"Recording saved to {temp_path}")
        
        return temp_path
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self.recording
    
    @staticmethod
    def list_devices():
        """List available audio input devices."""
        print("Available audio devices:")
        print(sd.query_devices())
        return sd.query_devices()
