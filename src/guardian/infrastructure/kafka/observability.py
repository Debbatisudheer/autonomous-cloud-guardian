from __future__ import annotations

import json
import os
from typing import Any

from kafka import KafkaProducer  # type: ignore[import-untyped]

from guardian.application.observability_event_publisher import (
    ObservabilityEventPublisher,
)
from guardian.domain.observability_event import (
    ObservabilityEvent,
)


class KafkaObservabilityEventPublisher(
    ObservabilityEventPublisher,
):
    """
    Real Kafka publisher for observability events.

    This class publishes only events supplied by the caller.
    It does not fabricate telemetry or health signals.
    """

    DEFAULT_BOOTSTRAP_SERVERS = "localhost:9092"
    DEFAULT_TOPIC = "acg.observability"

    def __init__(
        self,
        bootstrap_servers: str | None = None,
        topic: str | None = None,
    ) -> None:
        self.bootstrap_servers = (
            bootstrap_servers
            or os.getenv(
                "ACG_KAFKA_BOOTSTRAP_SERVERS",
                self.DEFAULT_BOOTSTRAP_SERVERS,
            )
        )

        self.topic = (
            topic
            or os.getenv(
                "ACG_KAFKA_OBSERVABILITY_TOPIC",
                self.DEFAULT_TOPIC,
            )
        )

        self._producer: KafkaProducer | None = None

    def initialize(self) -> None:
        """
        Initialize the real Kafka producer.
        """

        if self._producer is not None:
            return

        self._producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=self._serialize,
            key_serializer=lambda value: (
                value.encode("utf-8")
                if value is not None
                else None
            ),
        )

    def publish(
        self,
        event: ObservabilityEvent,
    ) -> None:
        """
        Publish one observability event to Kafka.
        """

        self.initialize()

        if self._producer is None:
            raise RuntimeError(
                "Kafka producer was not initialized."
            )

        future = self._producer.send(
            self.topic,
            key=event.resource_id,
            value=event.model_dump(mode="json"),
        )

        future.get(timeout=10)

    def publish_many(
        self,
        events: list[ObservabilityEvent],
    ) -> None:
        """
        Publish multiple observability events.
        """

        self.initialize()

        if self._producer is None:
            raise RuntimeError(
                "Kafka producer was not initialized."
            )

        futures = [
            self._producer.send(
                self.topic,
                key=event.resource_id,
                value=event.model_dump(mode="json"),
            )
            for event in events
        ]

        for future in futures:
            future.get(timeout=10)

    def close(self) -> None:
        """
        Flush and close the Kafka producer.
        """

        if self._producer is None:
            return

        self._producer.flush()
        self._producer.close()
        self._producer = None

    @staticmethod
    def _serialize(
        value: dict[str, Any],
    ) -> bytes:
        return json.dumps(
            value,
            separators=(",", ":"),
        ).encode("utf-8")