from __future__ import annotations

from guardian.application.observability_event_publisher import (
    ObservabilityEventPublisher,
)
from guardian.domain.health_signal import (
    HealthSignal,
    HealthSignalLevel,
)
from guardian.domain.observability_event import (
    ObservabilityEvent,
    ObservabilityEventType,
)
from guardian.domain.telemetry import (
    TelemetryObservation,
)


class ObservabilityEventPipeline:
    """
    Converts evidence-backed telemetry and health signals into
    observability events and publishes them through the configured
    event publisher.

    The pipeline does not predict, decide, or remediate.
    """

    def __init__(
        self,
        publisher: ObservabilityEventPublisher,
    ) -> None:
        self._publisher = publisher

    def create_telemetry_event(
        self,
        observation: TelemetryObservation,
    ) -> ObservabilityEvent:
        """
        Create an event representing a real telemetry observation.
        """

        return ObservabilityEvent(
            event_type=(
                ObservabilityEventType.TELEMETRY_OBSERVED
            ),
            resource_id=observation.resource_id,
            metric=observation.metric.value,
            value=observation.value,
            unit=observation.unit,
            health_level=self._default_health_level(),
            observed_at=observation.observed_at,
            source=observation.source.value,
            metadata=observation.metadata,
        )

    def create_health_event(
        self,
        signal: HealthSignal,
    ) -> ObservabilityEvent:
        """
        Create an event representing an already-derived
        health signal.
        """

        if signal.value is None:
            raise ValueError(
                "Health signal must contain a value "
                "before it can be published."
            )

        if signal.unit is None:
            raise ValueError(
                "Health signal must contain a unit "
                "before it can be published."
            )

        return ObservabilityEvent(
            event_type=(
                ObservabilityEventType.HEALTH_SIGNAL_GENERATED
            ),
            resource_id=signal.resource_id,
            metric=signal.metric,
            value=signal.value,
            unit=signal.unit,
            health_level=signal.level,
            source="health_signal_engine",
            metadata={
                "reason": signal.reason,
            },
        )

    def publish_telemetry(
        self,
        observation: TelemetryObservation,
    ) -> ObservabilityEvent:
        """
        Create and publish one telemetry event.
        """

        event = self.create_telemetry_event(
            observation,
        )

        self._publisher.publish(event)

        return event

    def publish_health_signal(
        self,
        signal: HealthSignal,
    ) -> ObservabilityEvent:
        """
        Create and publish one health signal event.
        """

        event = self.create_health_event(
            signal,
        )

        self._publisher.publish(event)

        return event

    def publish_health_signals(
        self,
        signals: list[HealthSignal],
    ) -> list[ObservabilityEvent]:
        """
        Create and publish multiple health signal events.
        """

        events = [
            self.create_health_event(signal)
            for signal in signals
        ]

        self._publisher.publish_many(events)

        return events

    @staticmethod
    def _default_health_level() -> HealthSignalLevel:
        """
        Return the transport-level default for a raw telemetry event.

        Raw telemetry is a measurement and has not yet been classified
        by the health signal engine. The actual operational health
        classification belongs to HealthSignalEngine.
        """

        return HealthSignalLevel.HEALTHY