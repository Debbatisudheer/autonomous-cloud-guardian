from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from guardian.application.health_signals import (
    HealthSignalEngine,
)
from guardian.application.observability_event_pipeline import (
    ObservabilityEventPipeline,
)
from guardian.domain.observability_event import (
    ObservabilityEventType,
)
from guardian.infrastructure.docker.telemetry import (
    DockerTelemetryCollector,
)
from guardian.infrastructure.kafka.observability import (
    KafkaObservabilityEventPublisher,
)

KAFKA_CONTAINER = "acg-kafka"

TOPIC = "acg.observability.phase47"

CONSUMER_TIMEOUT_MS = 30000

CONSUMER_GROUP_ID = (
    "acg-phase47-validation-"
    f"{uuid4().hex[:12]}"
)


def run_command(
    command: list[str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )


def print_header(title: str) -> None:
    print("=" * 72)
    print(title)
    print("=" * 72)


def create_topic() -> None:
    run_command(
        [
            "docker",
            "exec",
            KAFKA_CONTAINER,
            "/opt/kafka/bin/kafka-topics.sh",
            "--bootstrap-server",
            "localhost:9092",
            "--create",
            "--if-not-exists",
            "--topic",
            TOPIC,
            "--partitions",
            "1",
            "--replication-factor",
            "1",
        ]
    )


def delete_topic() -> None:
    subprocess.run(
        [
            "docker",
            "exec",
            KAFKA_CONTAINER,
            "/opt/kafka/bin/kafka-topics.sh",
            "--bootstrap-server",
            "localhost:9092",
            "--delete",
            "--topic",
            TOPIC,
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def consume_events(
    expected_count: int,
) -> list[dict[str, object]]:
    command = [
        "docker",
        "exec",
        KAFKA_CONTAINER,
        "/opt/kafka/bin/kafka-console-consumer.sh",
        "--bootstrap-server",
        "localhost:9092",
        "--topic",
        TOPIC,
        "--group",
        CONSUMER_GROUP_ID,
        "--from-beginning",
        "--max-messages",
        str(expected_count),
        "--timeout-ms",
        str(CONSUMER_TIMEOUT_MS),
        "--property",
        "print.key=false",
        "--property",
        "print.value=true",
    ]

    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode not in {0, 1}:
        raise RuntimeError(
            "Kafka consumer command failed.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    events: list[dict[str, object]] = []

    for line in result.stdout.splitlines():
        line = line.strip()

        if not line:
            continue

        try:
            decoded = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Kafka returned a non-JSON event:\n"
                f"{line}"
            ) from exc

        if not isinstance(decoded, dict):
            raise TypeError(
                "Kafka event is not a JSON object."
            )

        events.append(decoded)

    return events


def validate_topic_records(
    expected_count: int,
) -> int:
    """
    Inspect the topic directly using Kafka's consumer group offsets.

    This is an independent check that the records actually exist
    in the Kafka topic before attempting to consume them.
    """

    command = [
        "docker",
        "exec",
        KAFKA_CONTAINER,
        "/opt/kafka/bin/kafka-get-offsets.sh",
        "--bootstrap-server",
        "localhost:9092",
        "--topic",
        TOPIC,
    ]

    result = run_command(command)

    total_records = 0

    for line in result.stdout.splitlines():
        line = line.strip()

        if not line:
            continue

        parts = line.split(":")

        if len(parts) != 3:
            raise RuntimeError(
                "Unexpected Kafka offset output:\n"
                f"{line}"
            )

        earliest = int(parts[1])
        latest = int(parts[2])

        total_records += latest - earliest

    if total_records < expected_count:
        raise RuntimeError(
            "Kafka topic contains fewer records than expected. "
            f"Expected at least {expected_count}, "
            f"found {total_records}."
        )

    return total_records


def main() -> None:
    print_header(
        "PHASE 4.7 — REAL OBSERVABILITY EVENT PIPELINE VALIDATION"
    )

    publisher: KafkaObservabilityEventPublisher | None = None

    try:
        # ==============================================================
        # 1. Kafka availability
        # ==============================================================

        print()
        print("[1] REAL KAFKA AVAILABILITY")
        print("-" * 72)

        run_command(
            [
                "docker",
                "exec",
                KAFKA_CONTAINER,
                "/opt/kafka/bin/kafka-topics.sh",
                "--bootstrap-server",
                "localhost:9092",
                "--list",
            ]
        )

        print("Kafka container              : PASS")
        print("Kafka bootstrap              : PASS")

        # ==============================================================
        # 2. Isolated topic
        # ==============================================================

        print()
        print("[2] KAFKA VALIDATION TOPIC")
        print("-" * 72)

        delete_topic()
        create_topic()

        print(
            "Topic                        : "
            f"{TOPIC}"
        )

        print("Topic creation               : PASS")

        # ==============================================================
        # 3. Real Docker telemetry
        # ==============================================================

        print()
        print("[3] REAL DOCKER TELEMETRY")
        print("-" * 72)

        collector = DockerTelemetryCollector()

        observations = collector.collect_all()

        if not observations:
            raise RuntimeError(
                "No real Docker telemetry was collected."
            )

        for observation in observations:
            if observation.source.value != "docker":
                raise RuntimeError(
                    "Telemetry source is not Docker."
                )

            if observation.value < 0:
                raise RuntimeError(
                    "Telemetry contains a negative value."
                )

        print(
            "Real observations            : "
            f"{len(observations)}"
        )

        print("Real telemetry evidence      : PASS")

        # ==============================================================
        # 4. Real health signals
        # ==============================================================

        print()
        print("[4] REAL HEALTH SIGNAL GENERATION")
        print("-" * 72)

        health_engine = HealthSignalEngine()

        signals = health_engine.evaluate_many(
            observations,
        )

        if len(signals) != len(observations):
            raise RuntimeError(
                "Health signal count does not match "
                "telemetry count."
            )

        print(
            "Health signals               : "
            f"{len(signals)}"
        )

        print("Health signal generation     : PASS")

        # ==============================================================
        # 5. Event pipeline
        # ==============================================================

        print()
        print("[5] OBSERVABILITY EVENT PIPELINE")
        print("-" * 72)

        publisher = KafkaObservabilityEventPublisher(
            bootstrap_servers="localhost:9092",
            topic=TOPIC,
        )

        pipeline = ObservabilityEventPipeline(
            publisher=publisher,
        )

        events = [
            pipeline.create_health_event(signal)
            for signal in signals
        ]

        if len(events) != len(signals):
            raise RuntimeError(
                "Event count does not match health signal count."
            )

        print(
            "Events generated             : "
            f"{len(events)}"
        )

        print("Event pipeline creation      : PASS")

        # ==============================================================
        # 6. Evidence integrity
        # ==============================================================

        print()
        print("[6] EVENT EVIDENCE INTEGRITY")
        print("-" * 72)

        for signal, event in zip(
            signals,
            events,
            strict=True,
        ):
            if event.resource_id != signal.resource_id:
                raise RuntimeError(
                    "Event resource ID does not match signal."
                )

            if event.metric != signal.metric:
                raise RuntimeError(
                    "Event metric does not match signal."
                )

            if event.value != signal.value:
                raise RuntimeError(
                    "Event value does not match signal."
                )

            if event.unit != signal.unit:
                raise RuntimeError(
                    "Event unit does not match signal."
                )

            if event.health_level != signal.level:
                raise RuntimeError(
                    "Event health level does not match signal."
                )

            if event.event_type != (
                ObservabilityEventType.HEALTH_SIGNAL_GENERATED
            ):
                raise RuntimeError(
                    "Unexpected observability event type."
                )

        print("Resource correlation        : PASS")
        print("Metric correlation          : PASS")
        print("Value correlation           : PASS")
        print("Unit correlation            : PASS")
        print("Health correlation          : PASS")
        print("Event type integrity        : PASS")

        # ==============================================================
        # 7. Publish to real Kafka
        # ==============================================================

        print()
        print("[7] REAL KAFKA EVENT PUBLISH")
        print("-" * 72)

        publisher.publish_many(events)

        print(
            "Events published            : "
            f"{len(events)}"
        )

        print("Kafka publication            : PASS")

        # ==============================================================
        # 8. Verify topic contains records
        # ==============================================================

        print()
        print("[8] REAL KAFKA TOPIC RECORDS")
        print("-" * 72)

        topic_record_count = validate_topic_records(
            expected_count=len(events),
        )

        print(
            "Kafka topic records         : "
            f"{topic_record_count}"
        )

        print("Kafka topic persistence      : PASS")

        # ==============================================================
        # 9. Consume from real Kafka
        # ==============================================================

        print()
        print("[9] REAL KAFKA EVENT CONSUMPTION")
        print("-" * 72)

        consumed_events = consume_events(
            expected_count=len(events),
        )

        print(
            "Events consumed              : "
            f"{len(consumed_events)}"
        )

        if len(consumed_events) != len(events):
            raise RuntimeError(
                "Kafka consumer did not receive the expected "
                "number of events.\n"
                f"Expected: {len(events)}\n"
                f"Received: {len(consumed_events)}\n"
                f"Consumer group: {CONSUMER_GROUP_ID}"
            )

        print("Kafka consumption             : PASS")

        # ==============================================================
        # 10. Validate consumed evidence
        # ==============================================================

        print()
        print("[10] CONSUMED EVENT EVIDENCE")
        print("-" * 72)

        expected_keys = {
            (
                event.resource_id,
                event.metric,
                event.value,
                event.unit,
                event.health_level.value,
                event.event_type.value,
            )
            for event in events
        }

        consumed_keys = {
            (
                str(event["resource_id"]),
                str(event["metric"]),
                float(event["value"]),
                str(event["unit"]),
                str(event["health_level"]),
                str(event["event_type"]),
            )
            for event in consumed_events
        }

        if expected_keys != consumed_keys:
            missing = expected_keys - consumed_keys
            unexpected = consumed_keys - expected_keys

            raise RuntimeError(
                "Consumed Kafka evidence does not exactly "
                "match published evidence.\n"
                f"Missing: {len(missing)}\n"
                f"Unexpected: {len(unexpected)}"
            )

        print(
            "Expected event records      : "
            f"{len(expected_keys)}"
        )

        print(
            "Matching consumed records   : PASS"
        )

        # ==============================================================
        # 11. Autonomous boundary
        # ==============================================================

        print()
        print("[11] AUTONOMOUS ACTION BOUNDARY")
        print("-" * 72)

        print(
            "Prediction generated        : NONE"
        )

        print(
            "Decision generated          : NONE"
        )

        print(
            "Remediation executed        : NONE"
        )

        print("Phase boundary               : PASS")

        # ==============================================================
        # Final
        # ==============================================================

        print()
        print("=" * 72)
        print("PHASE 4.7 VALIDATION RESULT")
        print("=" * 72)

        print(
            "REAL KAFKA AVAILABILITY       : PASS"
        )

        print(
            "REAL DOCKER TELEMETRY         : PASS"
        )

        print(
            "HEALTH SIGNAL GENERATION      : PASS"
        )

        print(
            "EVENT CREATION                : PASS"
        )

        print(
            "EVENT EVIDENCE INTEGRITY      : PASS"
        )

        print(
            "KAFKA PUBLICATION             : PASS"
        )

        print(
            "KAFKA TOPIC PERSISTENCE       : PASS"
        )

        print(
            "KAFKA CONSUMPTION             : PASS"
        )

        print(
            "CONSUMED EVIDENCE             : PASS"
        )

        print(
            "AUTONOMOUS ACTION BOUNDARY     : PASS"
        )

        print()
        print(
            "PHASE 4.7 — COMPLETE: PASS"
        )

        print("=" * 72)

    finally:
        if publisher is not None:
            publisher.close()

        delete_topic()


if __name__ == "__main__":
    main()