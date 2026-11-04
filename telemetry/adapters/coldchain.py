"""Biopharma Cold-Chain IoT Reefer Telemetry Adapter.
Simulates refrigerated container telemetry (thermal slope, compressor vibration, MKT drift)
for USP <1079> and FDA 21 CFR § 211.150 autonomous compliance monitoring.
"""
import math
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional
from pydantic import BaseModel, Field

from telemetry.adapters.base import (
    DataSourceType,
    ProvenanceMetadata,
    TelemetryAdapter,
    TelemetryEventSchema,
)


class ColdChainReading(BaseModel):
    equipment_id: str = "REEFER-TRK-9042"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    internal_temp_c: float
    ambient_temp_c: float = 32.5  # Summer ambient highway temp
    compressor_vibration_mm_s: float
    compressor_rpm: int = 1800
    door_sealed: bool = True
    gps_lat: float = 41.5250
    gps_lng: float = -88.0817  # I-80 corridor, Joliet logistics hub
    mean_kinetic_temp_c: float
    thermal_slope_c_per_min: float
    usp_1079_status: str  # "COMPLIANT", "WARNING", "EXCURSION_CRITICAL"
    cargo_manifest: str = "1,200 Vials Trastuzumab (Herceptin 440mg)"
    cargo_value_usd: float = 1400000.00
    minutes_until_irreversible_denaturation: float


class ColdChainTelemetryAdapter(TelemetryAdapter):
    """Adapter for IoT Smart Reefer Telemetry monitoring high-value biologic drugs."""

    def __init__(
        self,
        equipment_id: str = "REEFER-TRK-9042",
        activation_energy_kj_mol: float = 83.144,  # Standard Arrhenius constant for protein degradation
    ):
        self.equipment_id = equipment_id
        self.activation_energy_kj_mol = activation_energy_kj_mol  # dH in kJ/mol
        self.r_constant = 8.314472e-3  # kJ/(mol·K)
        self.step_index = 0

        # Provenance metadata
        self.provenance = ProvenanceMetadata(
            data_source_type="COLDCHAIN_IOT",
            dataset_name="Smart Reefer IoT BioPharma Benchmark",
            source_reference="USP <1079> Good Storage & Shipping Practices / FDA 21 CFR § 211.150",
            replay_mode=True,
            license="Open Telemetry Pharma Standard",
        )

    def get_source_type(self) -> DataSourceType:
        return DataSourceType.SYNTHETIC_GENERATOR

    def get_provenance_metadata(self) -> Dict[str, Any]:
        return self.provenance.model_dump()

    def calculate_mean_kinetic_temperature(self, temps_celsius: List[float]) -> float:
        """Calculate Mean Kinetic Temperature (MKT) according to USP <1151> & <1079>.
        
        MKT = (dH / R) / -ln( sum(exp(-dH / (R * T_k))) / n )
        where T_k is temperature in Kelvin.
        """
        if not temps_celsius:
            return 5.0

        dh_over_r = self.activation_energy_kj_mol / self.r_constant
        sum_exp = 0.0

        for t_c in temps_celsius:
            t_k = t_c + 273.15
            sum_exp += math.exp(-dh_over_r / t_k)

        mean_exp = sum_exp / len(temps_celsius)
        mkt_kelvin = -dh_over_r / math.log(mean_exp)
        return round(mkt_kelvin - 273.15, 2)

    def generate_step(self, step: Optional[int] = None) -> ColdChainReading:
        """Generate a progressive cold-chain excursion sequence simulating compressor failure."""
        if step is not None:
            self.step_index = step
        else:
            self.step_index += 1

        # Profile: Steps 0-2 Nominal, Step 3 Compressor Flutter, Step 4+ Thermal Excursion
        if self.step_index <= 2:
            internal_temp = 4.2 + (self.step_index * 0.2)
            vib = 1.8 + (self.step_index * 0.1)
            slope = 0.05
            usp_status = "COMPLIANT"
            minutes_to_spoilage = 180.0
        elif self.step_index == 3:
            # Compressor fluttering, refrigerant valve stuck
            internal_temp = 5.8
            vib = 4.9  # Mechanical flutter
            slope = 0.35
            usp_status = "WARNING"
            minutes_to_spoilage = 52.0
        elif self.step_index == 4:
            # Thermal boundary broken (> 8.0°C)
            internal_temp = 8.6
            vib = 6.2  # Severe vibration
            slope = 0.70
            usp_status = "EXCURSION_CRITICAL"
            minutes_to_spoilage = 28.5  # Critical 30-minute intervention window!
        else:
            internal_temp = min(12.4 + ((self.step_index - 5) * 1.5), 24.0)
            vib = 7.1
            slope = 1.10
            usp_status = "EXCURSION_CRITICAL"
            minutes_to_spoilage = max(5.0, 20.0 - ((self.step_index - 5) * 4.0))

        # Recent history for MKT
        history = [4.2, 4.5, 5.0, internal_temp]
        mkt = self.calculate_mean_kinetic_temperature(history)

        return ColdChainReading(
            equipment_id=self.equipment_id,
            internal_temp_c=round(internal_temp, 2),
            compressor_vibration_mm_s=round(vib, 2),
            mean_kinetic_temp_c=mkt,
            thermal_slope_c_per_min=round(slope, 2),
            usp_1079_status=usp_status,
            minutes_until_irreversible_denaturation=round(minutes_to_spoilage, 1),
        )

    def normalize_reading(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw incoming payload into standard telemetry event schema."""
        return {
            "equipment_id": raw_data.get("equipment_id", self.equipment_id),
            "sensor_id": "TEMP-REEFER-01",
            "vibration_mm_s": float(raw_data.get("compressor_vibration_mm_s", 1.8)),
            "bearing_temp_c": float(raw_data.get("internal_temp_c", 4.2)),
            "unit": "°C / mm/s",
            "is_anomaly": raw_data.get("usp_1079_status") == "EXCURSION_CRITICAL",
            "threshold_exceeded": float(raw_data.get("internal_temp_c", 4.2)) > 8.0,
            "stage": raw_data.get("usp_1079_status", "COMPLIANT"),
            "data_source_type": DataSourceType.SYNTHETIC_GENERATOR,
            "replay_mode": True,
            "provenance": self.get_provenance_metadata(),
            "raw_feature": f"MKT={raw_data.get('mean_kinetic_temp_c', 5.0)}°C",
        }

    def read_event(self, record_id: Optional[str] = None) -> Dict[str, Any]:
        """Read a single normalized cold-chain event."""
        reading = self.generate_step()
        return self.normalize_reading(reading.model_dump())

    def stream_events(self, max_steps: int = 6) -> List[Dict[str, Any]]:
        """Stream sequence of normalized time-series events in chronological order."""
        events = []
        for step in range(max_steps):
            reading = self.generate_step(step)
            events.append(self.normalize_reading(reading.model_dump()))
        return events
