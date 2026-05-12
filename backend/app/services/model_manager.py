"""Model management and recommendation engine"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from app.config import config
from app.models.schemas import ModelRecommendation, DeviceInfo
from app.utils.hardware_detect import detector

logger = logging.getLogger(__name__)

@dataclass
class ModelCatalogEntry:
    id: str
    name: str
    params_million: int
    min_ram_gb: float
    min_vram_gb: Optional[float]
    recommended_precision: str
    huggingface_id: Optional[str]
    description: str
    tags: List[str]
    onnx_url: Optional[str] = None

class ModelManager:
    """Manages available models and recommends based on hardware"""

    def __init__(self):
        self._catalog: Dict[str, ModelCatalogEntry] = {}
        self._load_catalog()

    def _load_catalog(self):
        """Load built-in model catalog"""
        builtin_models = [
            ModelCatalogEntry(
                id="phi-2",
                name="Microsoft Phi-2",
                params_million=2700,
                min_ram_gb=8,
                min_vram_gb=4,
                recommended_precision="fp16",
                huggingface_id="microsoft/phi-2",
                description="2.7B parameter model with strong reasoning capabilities",
                tags=["small", "reasoning", "microsoft"]
            ),
            ModelCatalogEntry(
                id="llama2-7b-chat",
                name="Llama-2-7B-Chat",
                params_million=7000,
                min_ram_gb=16,
                min_vram_gb=8,
                recommended_precision="fp16",
                huggingface_id="meta-llama/Llama-2-7b-chat-hf",
                description="Meta's 7B parameter chat model",
                tags=["chat", "meta", "popular"]
            ),
            ModelCatalogEntry(
                id="mistral-7b",
                name="Mistral-7B-Instruct",
                params_million=7000,
                min_ram_gb=16,
                min_vram_gb=8,
                recommended_precision="fp16",
                huggingface_id="mistralai/Mistral-7B-Instruct-v0.2",
                description="High-performing 7B model with sliding window attention",
                tags=["chat", "mistral", "efficient"]
            ),
            ModelCatalogEntry(
                id="gemma-2b",
                name="Gemma-2B",
                params_million=2000,
                min_ram_gb=6,
                min_vram_gb=3,
                recommended_precision="fp16",
                huggingface_id="google/gemma-2b",
                description="Google's lightweight 2B parameter model",
                tags=["small", "google", "edge"]
            ),
            ModelCatalogEntry(
                id="qwen2-0.5b",
                name="Qwen2-0.5B",
                params_million=500,
                min_ram_gb=4,
                min_vram_gb=2,
                recommended_precision="fp16",
                huggingface_id="Qwen/Qwen2-0.5B-Instruct",
                description="Ultra-small 0.5B model for edge devices",
                tags=["tiny", "edge", "multilingual"]
            ),
            ModelCatalogEntry(
                id="llama3-8b",
                name="Llama-3-8B-Instruct",
                params_million=8000,
                min_ram_gb=16,
                min_vram_gb=10,
                recommended_precision="fp16",
                huggingface_id="meta-llama/Meta-Llama-3-8B-Instruct",
                description="Latest Meta 8B model with improved capabilities",
                tags=["chat", "meta", "latest"]
            )
        ]

        for model in builtin_models:
            self._catalog[model.id] = model

    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models"""
        return [
            {
                "id": m.id,
                "name": m.name,
                "params_million": m.params_million,
                "min_ram_gb": m.min_ram_gb,
                "min_vram_gb": m.min_vram_gb,
                "recommended_precision": m.recommended_precision,
                "description": m.description,
                "tags": m.tags,
                "installed": self._is_installed(m.id)
            }
            for m in self._catalog.values()
        ]

    def get_model(self, model_id: str) -> Optional[ModelCatalogEntry]:
        """Get model by ID"""
        return self._catalog.get(model_id)

    def recommend_models(self, device: Optional[DeviceInfo] = None) -> List[ModelRecommendation]:
        """Recommend models based on current hardware"""
        if device is None:
            profile = detector.get_full_system_profile()
            device = DeviceInfo(
                os=profile["os"],
                os_build=profile["os_build"],
                cpu=profile["cpu"]["name"],
                cpu_cores=profile["cpu"]["cores"],
                cpu_threads=profile["cpu"]["threads"],
                gpu=profile["gpus"][0]["name"] if profile["gpus"] else None,
                gpu_vram_gb=profile["gpus"][0]["vram_gb"] if profile["gpus"] else None,
                npu=profile["npu"]["name"] if profile["npu"] else None,
                ram_gb=profile["ram"]["total_gb"],
                driver_versions={},
                power_plan=profile["power_plan"],
                bios_version=""
            )

        recommendations = []

        for model in self._catalog.values():
            # Check compatibility
            compatible = True
            reasons = []

            if device.ram_gb < model.min_ram_gb:
                compatible = False
                reasons.append(f"Insufficient RAM: {device.ram_gb}GB < {model.min_ram_gb}GB required")

            if model.min_vram_gb and device.gpu_vram_gb and device.gpu_vram_gb < model.min_vram_gb:
                compatible = False
                reasons.append(f"Insufficient VRAM: {device.gpu_vram_gb}GB < {model.min_vram_gb}GB required")

            # Calculate confidence score
            confidence = 1.0
            if device.gpu:
                # GPU available - good for larger models
                if model.params_million > 5000:
                    confidence = 0.95
                else:
                    confidence = 0.8
            else:
                # CPU only
                if model.params_million < 3000:
                    confidence = 0.7
                else:
                    confidence = 0.3

            # Adjust for RAM headroom
            ram_headroom = device.ram_gb / model.min_ram_gb
            confidence *= min(ram_headroom, 1.5) / 1.5

            # Estimate performance
            if device.gpu:
                est_tps = model.params_million * 0.01  # Rough estimate
                est_vram = model.params_million * 0.0015
            else:
                est_tps = model.params_million * 0.001
                est_vram = 0

            reason = "Compatible with your system" if compatible else "; ".join(reasons)
            if compatible and not reasons:
                if device.gpu:
                    reason = f"GPU acceleration available. Estimated {est_tps:.1f} tokens/sec"
                else:
                    reason = f"CPU-only mode. Estimated {est_tps:.1f} tokens/sec"

            recommendations.append(ModelRecommendation(
                ai_model_id=model.id,
                ai_model_name=model.name,
                confidence=round(confidence, 2),
                reason=reason,
                estimated_tokens_per_sec=round(est_tps, 2),
                estimated_vram_gb=round(est_vram, 2),
                compatible=compatible
            ))

        # Sort by confidence descending
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        return recommendations

    def _is_installed(self, model_id: str) -> bool:
        """Check if model is locally installed"""
        model_dir = config.models_dir / model_id
        return model_dir.exists() and any(model_dir.iterdir())

    def get_install_path(self, model_id: str) -> Path:
        """Get installation path for model"""
        return config.models_dir / model_id

    def add_custom_model(self, model_id: str, name: str, onnx_path: str, 
                        params_million: int, precision: str = "fp16") -> bool:
        """Add a custom local model"""
        try:
            entry = ModelCatalogEntry(
                id=model_id,
                name=name,
                params_million=params_million,
                min_ram_gb=params_million * 0.002,
                min_vram_gb=None,
                recommended_precision=precision,
                huggingface_id=None,
                description=f"Custom model: {name}",
                tags=["custom"],
                onnx_url=None
            )
            self._catalog[model_id] = entry
            return True
        except Exception as e:
            logger.error(f"Failed to add custom model: {e}")
            return False

# Global instance
model_manager = ModelManager()
