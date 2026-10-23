from unittest.mock import Mock, patch

from guardian.domain.health_signal import (
    HealthSignalLevel,
)
from guardian.domain.observability_event import (
    ObservabilityEvent,
    ObservabilityEventType,
)
from guardian.infrastructure.kafka.observability import (
    KafkaObservabilityEventPublisher,
)


def make_event() -> ObservabilityEvent:
    return ObservabilityEvent(
        event_type=(
            ObservabilityEventType.HEALTH_SIGNAL_GENERATED
        ),
        resource_id="resource-a",
        metric="cpu_usage_percent",
        value=42.0,
        unit="percent",
        health_level=HealthSignalLevel.HEALTHY,
        source="health_signal_engine",
    )


@patch(
    "guardian.infrastructure.kafka.observability.KafkaProducer"
)
def test_initialize_creates_kafka_producer(
    kafka_producer: Mock,
) -> None:
    publisher = KafkaObservabilityEventPublisher(
        bootstrap_servers="localhost:9092",
        topic="acg.test",
    )

    publisher.initialize()

    kafka_producer.assert_called_once()


@patch(
    "guardian.infrastructure.kafka.observability.KafkaProducer"
)
def test_publish_sends_event(
    kafka_producer: Mock,
) -> None:
    producer = kafka_producer.return_value

    future = Mock()

    producer.send.return_value = future

    publisher = KafkaObservabilityEventPublisher(
        bootstrap_servers="localhost:9092",
        topic="acg.test",
    )

    event = make_event()

    publisher.publish(event)

    producer.send.assert_called_once()

    future.get.assert_called_once_with(
        timeout=10,
    )


@patch(
    "guardian.infrastructure.kafka.observability.KafkaProducer"
)
def test_publish_many_sends_all_events(
    kafka_producer: Mock,
) -> None:
    producer = kafka_producer.return_value

    future = Mock()

    producer.send.return_value = future

    publisher = KafkaObservabilityEventPublisher(
        bootstrap_servers="localhost:9092",
        topic="acg.test",
    )

    events = [
        make_event(),
        make_event(),
        make_event(),
    ]

    publisher.publish_many(events)

    assert producer.send.call_count == 3
    assert future.get.call_count == 3


@patch(
    "guardian.infrastructure.kafka.observability.KafkaProducer"
)
def test_close_flushes_and_closes_producer(
    kafka_producer: Mock,
) -> None:
    producer = kafka_producer.return_value

    publisher = KafkaObservabilityEventPublisher()

    publisher.initialize()
    publisher.close()

    producer.flush.assert_called_once()
    producer.close.assert_called_once()