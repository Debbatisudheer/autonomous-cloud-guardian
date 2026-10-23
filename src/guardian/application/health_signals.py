from __future__ import annotations

from guardian.domain.health_signal import (
    HealthSignal,
    HealthSignalLevel,
)
from guardian.domain.telemetry import (
    TelemetryMetric,
    TelemetryObservation,
)


class HealthSignalEngine:
    """
    Derives deterministic operational health signals from telemetry.

    This engine does not predict future conditions and does not
    perform remediation.
    """

    CPU_WARNING_THRESHOLD = 70.0
    CPU_CRITICAL_THRESHOLD = 90.0

    MEMORY_WARNING_THRESHOLD = 75.0
    MEMORY_CRITICAL_THRESHOLD = 90.0

    NETWORK_BYTES_HEALTHY_THRESHOLD = 0.0

    def evaluate(
        self,
        observation: TelemetryObservation,
    ) -> HealthSignal:
        """
        Convert one telemetry observation into a health signal.
        """

        if observation.metric == (
            TelemetryMetric.CPU_USAGE_PERCENT
        ):
            return self._evaluate_percentage_metric(
                observation=observation,
                warning_threshold=(
                    self.CPU_WARNING_THRESHOLD
                ),
                critical_threshold=(
                    self.CPU_CRITICAL_THRESHOLD
                ),
                metric_name="CPU usage",
            )

        if observation.metric == (
            TelemetryMetric.MEMORY_USAGE_PERCENT
        ):
            return self._evaluate_percentage_metric(
                observation=observation,
                warning_threshold=(
                    self.MEMORY_WARNING_THRESHOLD
                ),
                critical_threshold=(
                    self.MEMORY_CRITICAL_THRESHOLD
                ),
                metric_name="Memory usage",
            )

        if observation.metric in {
            TelemetryMetric.NETWORK_RX_BYTES,
            TelemetryMetric.NETWORK_TX_BYTES,
        }:
            return self._evaluate_network_metric(
                observation,
            )

        if observation.metric == (
            TelemetryMetric.MEMORY_USAGE_BYTES
        ):
            return HealthSignal(
                resource_id=observation.resource_id,
                metric=observation.metric.value,
                level=HealthSignalLevel.HEALTHY,
                value=observation.value,
                unit=observation.unit,
                reason=(
                    "Memory usage is available as a "
                    "measured byte value."
                ),
                evidence_available=True,
            )

        return HealthSignal(
            resource_id=observation.resource_id,
            metric=observation.metric.value,
            level=HealthSignalLevel.UNKNOWN,
            value=observation.value,
            unit=observation.unit,
            reason=(
                "No health evaluation rule exists "
                "for this metric."
            ),
            evidence_available=True,
        )

    def evaluate_many(
        self,
        observations: list[TelemetryObservation],
    ) -> list[HealthSignal]:
        """
        Evaluate multiple telemetry observations.
        """

        return [
            self.evaluate(observation)
            for observation in observations
        ]

    @staticmethod
    def _evaluate_percentage_metric(
        observation: TelemetryObservation,
        warning_threshold: float,
        critical_threshold: float,
        metric_name: str,
    ) -> HealthSignal:
        if observation.value >= critical_threshold:
            level = HealthSignalLevel.CRITICAL

            reason = (
                f"{metric_name} is at or above the "
                f"critical threshold of "
                f"{critical_threshold:.1f}%."
            )

        elif observation.value >= warning_threshold:
            level = HealthSignalLevel.WARNING

            reason = (
                f"{metric_name} is at or above the "
                f"warning threshold of "
                f"{warning_threshold:.1f}%."
            )

        else:
            level = HealthSignalLevel.HEALTHY

            reason = (
                f"{metric_name} is below the "
                f"warning threshold of "
                f"{warning_threshold:.1f}%."
            )

        return HealthSignal(
            resource_id=observation.resource_id,
            metric=observation.metric.value,
            level=level,
            value=observation.value,
            unit=observation.unit,
            reason=reason,
            evidence_available=True,
        )

    def _evaluate_network_metric(
        self,
        observation: TelemetryObservation,
    ) -> HealthSignal:
        """
        Network byte counters are measurements, not inherently
        healthy/unhealthy conditions.

        Therefore the engine reports them as healthy when real
        evidence exists, without pretending that network volume
        represents service health.
        """

        if observation.value < (
            self.NETWORK_BYTES_HEALTHY_THRESHOLD
        ):
            return HealthSignal(
                resource_id=observation.resource_id,
                metric=observation.metric.value,
                level=HealthSignalLevel.UNKNOWN,
                value=observation.value,
                unit=observation.unit,
                reason=(
                    "Network telemetry contains an "
                    "unexpected negative value."
                ),
                evidence_available=True,
            )

        return HealthSignal(
            resource_id=observation.resource_id,
            metric=observation.metric.value,
            level=HealthSignalLevel.HEALTHY,
            value=observation.value,
            unit=observation.unit,
            reason=(
                "Network telemetry is available as "
                "a measured byte counter. No health "
                "threshold is inferred from traffic "
                "volume alone."
            ),
            evidence_available=True,
        )