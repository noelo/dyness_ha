"""Dyness Battery sensors."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DynessCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class DynessSensorDescription(SensorEntityDescription):
    """Sensor description with value extractor."""
    value_fn: Callable[[dict], Any] = lambda d: None


def _safe_float(val, scale=1.0):
    try:
        return round(float(val) * scale, 3) if val not in (None, "", "null") else None
    except (ValueError, TypeError):
        return None


def _power_status(data: dict) -> str:
    pwr = _safe_float(data.get("power", {}).get("realTimePower"))
    if pwr is None:
        return "Unknown"
    if pwr > 10:
        return "Charging"
    if pwr < -10:
        return "Discharging"
    return "Standby"


SENSORS: list[DynessSensorDescription] = [

    # ── Power & Energy ────────────────────────────────────────────────────────
    DynessSensorDescription(
        key="battery_power",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt",
        value_fn=lambda d: _safe_float(d.get("power", {}).get("realTimePower")),
    ),
    DynessSensorDescription(
        key="battery_current",
        name="Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
        value_fn=lambda d: _safe_float(d.get("power", {}).get("realTimeCurrent")),
    ),
    DynessSensorDescription(
        key="battery_status",
        name="Battery Status",
        icon="mdi:battery-charging",
        value_fn=_power_status,
    ),

    # ── SOC / SOH ─────────────────────────────────────────────────────────────
    DynessSensorDescription(
        key="battery_soc",
        name="Battery SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        value_fn=lambda d: _safe_float(d.get("power", {}).get("soc")),
    ),
    DynessSensorDescription(
        key="battery_soh",
        name="Battery SOH",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-heart",
        value_fn=lambda d: _safe_float(d.get("bms", {}).get("1200")),
    ),

    # ── Voltage ───────────────────────────────────────────────────────────────
    DynessSensorDescription(
        key="pack_voltage",
        name="Pack Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
        value_fn=lambda d: _safe_float(d.get("bms", {}).get("600")),
    ),
    DynessSensorDescription(
        key="cell_voltage_max",
        name="Cell Voltage Max",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-triangle",
        value_fn=lambda d: _safe_float(d.get("bms", {}).get("1300")),
    ),
    DynessSensorDescription(
        key="cell_voltage_min",
        name="Cell Voltage Min",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-outline",
        value_fn=lambda d: _safe_float(d.get("bms", {}).get("1500")),
    ),
    DynessSensorDescription(
        key="cell_voltage_spread",
        name="Cell Voltage Spread",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-expand-vertical",
        value_fn=lambda d: round(
            float(d["bms"]["1300"]) - float(d["bms"]["1500"]), 3
        ) if d.get("bms", {}).get("1300") and d.get("bms", {}).get("1500") else None,
    ),
    DynessSensorDescription(
        key="cell_voltage_max_cell_num",
        name="Max Voltage Cell #",
        icon="mdi:numeric",
        value_fn=lambda d: d.get("bms", {}).get("1402"),
    ),
    DynessSensorDescription(
        key="cell_voltage_min_cell_num",
        name="Min Voltage Cell #",
        icon="mdi:numeric",
        value_fn=lambda d: d.get("bms", {}).get("1602"),
    ),
    DynessSensorDescription(
        key="charge_voltage_upper",
        name="Charge Voltage Upper Limit",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-alert",
        value_fn=lambda d: _safe_float(d.get("bms", {}).get("3600")),
    ),
    DynessSensorDescription(
        key="charge_voltage_lower",
        name="Charge Voltage Lower Limit",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-alert-outline",
        value_fn=lambda d: _safe_float(d.get("bms", {}).get("3700")),
    ),

    # ── Temperature ───────────────────────────────────────────────────────────
    DynessSensorDescription(
        key="cell_temp_max",
        name="Cell Temperature Max",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer-chevron-up",
        value_fn=lambda d: _safe_float(d.get("bms", {}).get("1800")),
    ),
    DynessSensorDescription(
        key="cell_temp_min",
        name="Cell Temperature Min",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer-chevron-down",
        value_fn=lambda d: _safe_float(d.get("bms", {}).get("2000")),
    ),
    DynessSensorDescription(
        key="mosfet_temp_max",
        name="MOSFET Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        value_fn=lambda d: _safe_float(d.get("bms", {}).get("2300")),
    ),
    DynessSensorDescription(
        key="bms_temp_max",
        name="BMS Temperature Max",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        value_fn=lambda d: _safe_float(d.get("bms", {}).get("2800")),
    ),
    DynessSensorDescription(
        key="bms_temp_min",
        name="BMS Temperature Min",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        value_fn=lambda d: _safe_float(d.get("bms", {}).get("3000")),
    ),

    # ── Current limits ────────────────────────────────────────────────────────
    DynessSensorDescription(
        key="max_charge_current",
        name="Max Charge Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
        value_fn=lambda d: _safe_float(d.get("bms", {}).get("3800")),
    ),
    DynessSensorDescription(
        key="max_discharge_current",
        name="Max Discharge Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
        value_fn=lambda d: _safe_float(d.get("bms", {}).get("3900")),
    ),

    # ── Status flags ──────────────────────────────────────────────────────────
    DynessSensorDescription(
        key="charge_enable",
        name="Charge Enable",
        icon="mdi:battery-plus",
        value_fn=lambda d: "Enabled" if d.get("bms", {}).get("4008") == "1" else "Disabled",
    ),
    DynessSensorDescription(
        key="discharge_enable",
        name="Discharge Enable",
        icon="mdi:battery-minus",
        value_fn=lambda d: "Enabled" if d.get("bms", {}).get("4007") == "1" else "Disabled",
    ),
    DynessSensorDescription(
        key="alarm_status",
        name="Alarm Status",
        icon="mdi:bell-alert",
        value_fn=lambda d: "OK" if d.get("bms", {}).get("4100") == "0" else "ALARM",
    ),
    DynessSensorDescription(
        key="communication_status",
        name="Communication Status",
        icon="mdi:wifi",
        value_fn=lambda d: d.get("device", {}).get("deviceCommunicationStatus", "Unknown"),
    ),
    DynessSensorDescription(
        key="firmware_version",
        name="Firmware Version",
        icon="mdi:chip",
        value_fn=lambda d: d.get("device", {}).get("firmwareVersion"),
    ),
    DynessSensorDescription(
        key="signal_strength",
        name="Signal Strength",
        native_unit_of_measurement="dBm",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:signal",
        value_fn=lambda d: _safe_float(d.get("dongle", {}).get("800000")),
    ),
    DynessSensorDescription(
        key="last_update",
        name="Last Data Update",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline",
        value_fn=lambda d: d.get("device", {}).get("dataUpdateTime"),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dyness sensors from config entry."""
    coordinator: DynessCoordinator = hass.data[DOMAIN][entry.entry_id]

    device_data = coordinator.data.get("device", {}) if coordinator.data else {}
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.data["sn_bms"])},
        name=device_data.get("stationName") or f"Dyness {entry.data['sn_bms']}",
        manufacturer="Dyness Technology",
        model=device_data.get("deviceModelName") or device_data.get("deviceName") or "Dyness Battery",
        sw_version=device_data.get("firmwareVersion"),
        configuration_url="https://open-api.dyness.com/swagger-ui/index.html",
    )

    async_add_entities(
        DynessSensor(coordinator, description, device_info, entry)
        for description in SENSORS
    )


class DynessSensor(CoordinatorEntity, SensorEntity):
    """A single Dyness sensor."""

    entity_description: DynessSensorDescription

    def __init__(
        self,
        coordinator: DynessCoordinator,
        description: DynessSensorDescription,
        device_info: DeviceInfo,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id    = f"{entry.data['sn_bms']}_{description.key}"
        self._attr_device_info  = device_info
        self._entry             = entry

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        try:
            return self.entity_description.value_fn(self.coordinator.data)
        except Exception as e:  # noqa: BLE001
            _LOGGER.debug("Error getting value for %s: %s", self.entity_description.key, e)
            return None
