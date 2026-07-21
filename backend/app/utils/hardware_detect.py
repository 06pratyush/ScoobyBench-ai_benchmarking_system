"""Hardware detection for Windows systems"""
import platform
import subprocess
import re
import threading
import time
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
import logging
import psutil

logger = logging.getLogger(__name__)

@dataclass
class GPUInfo:
    name: str
    vendor: str
    vram_gb: float
    driver_version: str
    compute_capability: Optional[str] = None

@dataclass
class CPUInfo:
    name: str
    vendor: str
    cores: int
    threads: int
    base_clock_ghz: float
    max_clock_ghz: float
    features: List[str]

@dataclass
class NPUInfo:
    name: str
    vendor: str
    compute_tops: Optional[float] = None

class HardwareDetector:
    """Detects system hardware capabilities.

    CPU/GPU/NPU/BIOS identity doesn't change while the app runs, but the WMI
    and powercfg queries behind it are expensive and the UI polls the profile
    every few seconds — so static parts are cached with a long TTL.
    """

    STATIC_CACHE_TTL = 300.0  # seconds

    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self._static_cache: Optional[Dict] = None
        self._static_cache_time = 0.0
        self._cache_lock = threading.Lock()

    def get_cpu_info(self) -> CPUInfo:
        try:
            if self.is_windows:
                return self._get_cpu_windows()
            return self._get_cpu_generic()
        except Exception as e:
            logger.error(f"CPU detection failed: {e}")
            return CPUInfo(
                name=platform.processor() or "Unknown",
                vendor="Unknown",
                cores=psutil.cpu_count(logical=False) or 4,
                threads=psutil.cpu_count(logical=True) or 8,
                base_clock_ghz=2.0,
                max_clock_ghz=3.0,
                features=[]
            )

    def _get_cpu_windows(self) -> CPUInfo:
        try:
            import wmi
            c = wmi.WMI()
            proc = c.Win32_Processor()[0]

            features = []
            if hasattr(proc, 'VirtualizationFirmwareEnabled') and proc.VirtualizationFirmwareEnabled:
                features.append("VT-x/AMD-V")

            try:
                import cpuinfo
                info = cpuinfo.get_cpu_info()
                flags = info.get('flags', [])
                if 'avx2' in flags:
                    features.append('AVX2')
                elif 'avx' in flags:
                    features.append('AVX')
                if 'fma' in flags:
                    features.append('FMA')
            except ImportError:
                pass

            return CPUInfo(
                name=proc.Name.strip(),
                vendor=proc.Manufacturer,
                cores=proc.NumberOfCores,
                threads=proc.NumberOfLogicalProcessors,
                base_clock_ghz=proc.MaxClockSpeed / 1000.0,
                max_clock_ghz=proc.MaxClockSpeed / 1000.0 * 1.2,
                features=features
            )
        except Exception as e:
            logger.warning(f"WMI CPU detection failed: {e}")
            return self._get_cpu_generic()

    def _get_cpu_generic(self) -> CPUInfo:
        return CPUInfo(
            name=platform.processor() or "Unknown",
            vendor="Unknown",
            cores=psutil.cpu_count(logical=False) or 4,
            threads=psutil.cpu_count(logical=True) or 8,
            base_clock_ghz=2.0,
            max_clock_ghz=3.0,
            features=[]
        )

    def get_gpu_info(self) -> List[GPUInfo]:
        gpus = []

        try:
            gpus.extend(self._get_nvidia_gpus())
        except Exception as e:
            logger.debug(f"NVML detection failed: {e}")

        if not gpus:
            try:
                gpus.extend(self._get_amd_gpus())
            except Exception as e:
                logger.debug(f"ADL detection failed: {e}")

        if not gpus and self.is_windows:
            try:
                gpus.extend(self._get_gpu_wmi())
            except Exception as e:
                logger.debug(f"WMI GPU detection failed: {e}")

        return gpus

    def _get_nvidia_gpus(self) -> List[GPUInfo]:
        try:
            from pynvml import nvmlInit, nvmlDeviceGetCount, nvmlDeviceGetHandleByIndex
            from pynvml import nvmlDeviceGetName, nvmlDeviceGetMemoryInfo, nvmlDeviceGetDriverVersion

            nvmlInit()
            count = nvmlDeviceGetCount()
            gpus = []

            for i in range(count):
                handle = nvmlDeviceGetHandleByIndex(i)
                name = nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                mem = nvmlDeviceGetMemoryInfo(handle)
                driver = nvmlDeviceGetDriverVersion(handle)
                if isinstance(driver, bytes):
                    driver = driver.decode('utf-8')

                gpus.append(GPUInfo(
                    name=name,
                    vendor="NVIDIA",
                    vram_gb=mem.total / (1024**3),
                    driver_version=driver,
                    compute_capability=None
                ))
            return gpus
        except ImportError:
            return []
        except Exception as e:
            logger.debug(f"NVML error: {e}")
            return []

    def _get_amd_gpus(self) -> List[GPUInfo]:
        return []

    def _get_gpu_wmi(self) -> List[GPUInfo]:
        try:
            import wmi
            c = wmi.WMI()
            gpus = []

            for gpu in c.Win32_VideoController():
                if gpu.AdapterRAM:
                    vram_gb = int(gpu.AdapterRAM) / (1024**3)
                else:
                    vram_gb = 0

                vendor = "Unknown"
                if "NVIDIA" in gpu.Name.upper():
                    vendor = "NVIDIA"
                elif "AMD" in gpu.Name.upper() or "RADEON" in gpu.Name.upper():
                    vendor = "AMD"
                elif "INTEL" in gpu.Name.upper():
                    vendor = "Intel"

                gpus.append(GPUInfo(
                    name=gpu.Name.strip(),
                    vendor=vendor,
                    vram_gb=vram_gb,
                    driver_version=gpu.DriverVersion or "Unknown"
                ))
            return gpus
        except Exception as e:
            logger.debug(f"WMI GPU error: {e}")
            return []

    def get_npu_info(self) -> Optional[NPUInfo]:
        if not self.is_windows:
            return None

        try:
            import wmi
            c = wmi.WMI()

            # Single pass over PnP devices; enumerating them is slow.
            qualcomm_match = None
            for device in c.Win32_PnPEntity():
                if not device.Name:
                    continue
                upper = device.Name.upper()
                if "NPU" in upper:
                    return NPUInfo(name=device.Name, vendor="Intel", compute_tops=None)
                if qualcomm_match is None and any(x in upper for x in ["QUALCOMM", "SNAPDRAGON", "HEXAGON"]):
                    qualcomm_match = device.Name
            if qualcomm_match:
                return NPUInfo(name=qualcomm_match, vendor="Qualcomm", compute_tops=None)
        except Exception as e:
            logger.debug(f"NPU detection failed: {e}")

        return None

    def get_ram_info(self) -> Tuple[float, float]:
        mem = psutil.virtual_memory()
        return mem.total / (1024**3), mem.available / (1024**3)

    def get_power_plan(self) -> str:
        if not self.is_windows:
            return "Unknown"

        try:
            result = subprocess.run(
                ["powercfg", "/getactivescheme"],
                capture_output=True,
                text=True
            )
            output = result.stdout
            match = re.search(r"\((.*?)\)", output)
            if match:
                return match.group(1)
            return "Unknown"
        except Exception as e:
            logger.debug(f"Power plan detection failed: {e}")
            return "Unknown"

    def get_bios_info(self) -> Dict[str, str]:
        if not self.is_windows:
            return {}

        try:
            import wmi
            c = wmi.WMI()
            bios = c.Win32_BIOS()[0]
            return {
                "version": bios.Version,
                "manufacturer": bios.Manufacturer,
                "release_date": bios.ReleaseDate
            }
        except Exception as e:
            logger.debug(f"BIOS detection failed: {e}")
            return {}

    def _get_static_profile(self) -> Dict:
        """Hardware identity that doesn't change at runtime (cached)."""
        now = time.monotonic()
        with self._cache_lock:
            if self._static_cache and (now - self._static_cache_time) < self.STATIC_CACHE_TTL:
                return self._static_cache

        cpu = self.get_cpu_info()
        gpus = self.get_gpu_info()
        npu = self.get_npu_info()

        static = {
            "os": f"{platform.system()} {platform.release()}",
            "os_build": platform.version(),
            "cpu": {
                "name": cpu.name,
                "vendor": cpu.vendor,
                "cores": cpu.cores,
                "threads": cpu.threads,
                "features": cpu.features
            },
            "gpus": [
                {
                    "name": g.name,
                    "vendor": g.vendor,
                    "vram_gb": round(g.vram_gb, 2),
                    "driver": g.driver_version
                } for g in gpus
            ],
            "npu": {
                "name": npu.name,
                "vendor": npu.vendor
            } if npu else None,
            "bios": self.get_bios_info()
        }

        with self._cache_lock:
            self._static_cache = static
            self._static_cache_time = now
        return static

    def invalidate_cache(self):
        """Force re-detection on next profile request (e.g. after driver update)."""
        with self._cache_lock:
            self._static_cache = None

    def get_full_system_profile(self) -> Dict[str, any]:
        try:
            profile = dict(self._get_static_profile())
            total_ram, available_ram = self.get_ram_info()

            profile["ram"] = {
                "total_gb": round(total_ram, 2),
                "available_gb": round(available_ram, 2)
            }
            profile["power_plan"] = self.get_power_plan()
            return profile
        except Exception as e:
            logger.error(f"System profile failed: {e}")
            # Return minimal profile so app doesn't crash
            return {
                "os": f"{platform.system()} {platform.release()}",
                "os_build": platform.version(),
                "cpu": {"name": platform.processor() or "Unknown", "vendor": "Unknown", "cores": 4, "threads": 8, "features": []},
                "gpus": [],
                "npu": None,
                "ram": {"total_gb": 8, "available_gb": 4},
                "power_plan": "Unknown",
                "bios": {}
            }

detector = HardwareDetector()
