from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from guardian.application.security_assessment import (
    SecurityAssessmentEngine,
)
from guardian.application.security_recommendation import (
    SecurityRecommendationEngine,
)
from guardian.application.security_risk import (
    SecurityRiskSignalEngine,
)
from guardian.domain.security import SecurityEvidence
from guardian.infrastructure.docker.security import (
    DockerSecurityEvidenceProvider,
)
from guardian.infrastructure.postgres.security_storage import (
    PostgreSQLSecurityStorage,
)


def main() -> None:
    print(
        "PHASE 7.7 — SECURITY INTELLIGENCE "
        "INTEGRATION VALIDATION"
    )
    print("=" * 70)

    provider = DockerSecurityEvidenceProvider()
    storage = PostgreSQLSecurityStorage()

    assessment_engine = SecurityAssessmentEngine()
    risk_engine = SecurityRiskSignalEngine()
    recommendation_engine = SecurityRecommendationEngine()

    validation_resource_id = (
        f"phase-7-7-validation-{uuid4().hex}"
    )

    stored_evidence: list[SecurityEvidence] = []

    try:
        # =========================================================
        # 1. REAL DOCKER DISCOVERY
        # =========================================================

        containers = provider._client.containers.list(
            all=True
        )

        if not containers:
            raise RuntimeError(
                "No Docker containers were discovered."
            )

        print(
            "REAL DOCKER DISCOVERY PASS "
            f"({len(containers)} containers)"
        )

        running_container = next(
            (
                container
                for container in containers
                if container.status == "running"
            ),
            None,
        )

        if running_container is None:
            raise RuntimeError(
                "No running Docker container was "
                "available for validation."
            )

        resource_id = str(running_container.name)

        print(
            "INTEGRATION RESOURCE: "
            f"{resource_id}"
        )

        # =========================================================
        # 2. REAL SECURITY EVIDENCE COLLECTION
        # =========================================================

        evidence_result = (
            provider.collect_for_resource(
                resource_id
            )
        )

        if not evidence_result.evidence_available:
            raise RuntimeError(
                "Real Docker security evidence "
                "was unavailable."
            )

        evidence = evidence_result.evidence

        if not evidence:
            raise RuntimeError(
                "Real Docker security evidence "
                "collection returned no observations."
            )

        print(
            "REAL SECURITY EVIDENCE COLLECTION PASS "
            f"({len(evidence)} observations)"
        )

        # =========================================================
        # 3. SECURITY EVIDENCE INTEGRITY
        # =========================================================

        for item in evidence:
            if item.resource_id != resource_id:
                raise RuntimeError(
                    "Security evidence resource "
                    "correlation failed."
                )

            if not item.evidence_id:
                raise RuntimeError(
                    "Security evidence is missing "
                    "evidence_id."
                )

            if not item.evidence_type:
                raise RuntimeError(
                    "Security evidence is missing "
                    "evidence_type."
                )

            if not item.details:
                raise RuntimeError(
                    "Security evidence contains "
                    "no details."
                )

            if not item.evidence_available:
                raise RuntimeError(
                    "Expected collected security "
                    "evidence to be available."
                )

        print(
            "SECURITY EVIDENCE INTEGRITY PASS"
        )

        # =========================================================
        # 4. CONTROLLED PERSISTENCE COPY
        #
        # The evidence itself originates from the real Docker
        # container above.
        #
        # A separate validation resource ID is used only so that
        # the PostgreSQL validation records can be safely removed
        # afterward.
        # =========================================================

        observed_base = datetime.now(UTC)

        for index, item in enumerate(evidence):
            stored_item = SecurityEvidence(
                evidence_id=(
                    f"phase-7-7-{uuid4().hex}"
                ),
                resource_id=validation_resource_id,
                category=item.category,
                source=item.source,
                evidence_type=item.evidence_type,
                observed_at=(
                    observed_base
                    + timedelta(seconds=index)
                ),
                evidence_available=item.evidence_available,
                details=dict(item.details),
            )

            stored_evidence.append(
                stored_item
            )

        # =========================================================
        # 5. POSTGRESQL STORAGE
        # =========================================================

        storage.initialize()

        storage.save_many(
            stored_evidence
        )

        print(
            "POSTGRESQL SECURITY EVIDENCE "
            "PERSISTENCE PASS "
            f"({len(stored_evidence)} records)"
        )

        # =========================================================
        # 6. POSTGRESQL RETRIEVAL
        # =========================================================

        retrieved = storage.get_for_resource(
            validation_resource_id
        )

        if len(retrieved) != len(
            stored_evidence
        ):
            raise RuntimeError(
                "Persisted security evidence count "
                "does not match submitted evidence."
            )

        retrieved_ids = {
            item.evidence_id
            for item in retrieved
        }

        expected_ids = {
            item.evidence_id
            for item in stored_evidence
        }

        if retrieved_ids != expected_ids:
            raise RuntimeError(
                "Persisted security evidence IDs "
                "do not match submitted evidence."
            )

        print(
            "POSTGRESQL SECURITY EVIDENCE "
            "RETRIEVAL PASS"
        )

        # =========================================================
        # 7. TIME-RANGE RETRIEVAL
        # =========================================================

        start_time = (
            observed_base
            - timedelta(seconds=1)
        )

        end_time = (
            observed_base
            + timedelta(
                seconds=len(evidence) + 1
            )
        )

        ranged = storage.get_between(
            start_time,
            end_time,
        )

        ranged_validation_records = [
            item
            for item in ranged
            if item.resource_id
            == validation_resource_id
        ]

        if len(
            ranged_validation_records
        ) != len(stored_evidence):
            raise RuntimeError(
                "Time-range retrieval did not "
                "return all validation evidence."
            )

        print(
            "SECURITY EVIDENCE TIME-RANGE "
            "RETRIEVAL PASS"
        )

        # =========================================================
        # 8. SECURITY ASSESSMENT
        #
        # Assessment is performed against the real Docker
        # evidence collected in step 2.
        # =========================================================

        findings = assessment_engine.assess(
            evidence
        )

        print(
            "SECURITY ASSESSMENT PASS "
            f"({len(findings)} findings)"
        )

        # =========================================================
        # 9. FINDING CORRELATION
        # =========================================================

        evidence_ids = {
            item.evidence_id
            for item in evidence
        }

        for finding in findings:
            if finding.resource_id != resource_id:
                raise RuntimeError(
                    "Finding resource does not "
                    "match the real Docker resource."
                )

            if (
                finding.evidence_id is not None
                and finding.evidence_id
                not in evidence_ids
            ):
                raise RuntimeError(
                    "Finding references evidence "
                    "that was not collected."
                )

            if not finding.title:
                raise RuntimeError(
                    "Finding has no title."
                )

            if not finding.description:
                raise RuntimeError(
                    "Finding has no description."
                )

        print(
            "SECURITY FINDING CORRELATION PASS"
        )

        # =========================================================
        # 10. SECURITY RISK SIGNAL GENERATION
        # =========================================================

        signals = risk_engine.generate(
            findings
        )

        if len(signals) != len(findings):
            raise RuntimeError(
                "Risk signal count does not "
                "match finding count."
            )

        print(
            "SECURITY RISK SIGNAL PASS "
            f"({len(signals)} signals)"
        )

        # =========================================================
        # 11. RISK SIGNAL CORRELATION
        # =========================================================

        finding_ids = {
            finding.finding_id
            for finding in findings
        }

        for signal in signals:
            if signal.finding_id not in finding_ids:
                raise RuntimeError(
                    "Risk signal references "
                    "an unknown finding."
                )

            if signal.evidence_id not in evidence_ids:
                raise RuntimeError(
                    "Risk signal references evidence "
                    "that was not collected."
                )

            if signal.resource_id != resource_id:
                raise RuntimeError(
                    "Risk signal resource "
                    "correlation failed."
                )

        print(
            "SECURITY RISK SIGNAL CORRELATION PASS"
        )

        # =========================================================
        # 12. SECURITY RECOMMENDATION GENERATION
        # =========================================================

        recommendations = []

        for finding, signal in zip(
            findings,
            signals,
        ):
            recommendation = (
                recommendation_engine.generate(
                    finding,
                    signal,
                )
            )

            recommendations.append(
                recommendation
            )

        if len(recommendations) != len(
            findings
        ):
            raise RuntimeError(
                "Recommendation count does not "
                "match finding count."
            )

        print(
            "SECURITY RECOMMENDATION PASS "
            f"({len(recommendations)} recommendations)"
        )

        # =========================================================
        # 13. END-TO-END EVIDENCE CORRELATION
        # =========================================================

        for finding, signal, recommendation in zip(
            findings,
            signals,
            recommendations,
        ):
            if (
                signal.finding_id
                != finding.finding_id
            ):
                raise RuntimeError(
                    "Finding → signal "
                    "correlation failed."
                )

            if (
                recommendation.finding_id
                != finding.finding_id
            ):
                raise RuntimeError(
                    "Finding → recommendation "
                    "correlation failed."
                )

            if (
                recommendation.signal_id
                != signal.signal_id
            ):
                raise RuntimeError(
                    "Signal → recommendation "
                    "correlation failed."
                )

            expected_evidence_id = (
                finding.evidence_id
            )

            if (
                expected_evidence_id is not None
                and recommendation.evidence_id
                != expected_evidence_id
            ):
                raise RuntimeError(
                    "Evidence → recommendation "
                    "correlation failed."
                )

            if (
                recommendation.resource_id
                != finding.resource_id
            ):
                raise RuntimeError(
                    "Resource correlation failed."
                )

        print(
            "END-TO-END EVIDENCE CHAIN PASS"
        )

        # =========================================================
        # 14. NO INFRASTRUCTURE EXECUTION
        # =========================================================

        forbidden_terms = (
            "restart the container",
            "restart container",
            "delete the container",
            "delete container",
            "terminate the container",
            "terminate container",
            "automatically remediate",
            "automatic remediation",
        )

        for recommendation in recommendations:
            recommendation_text = (
                recommendation.recommendation.lower()
            )

            if any(
                term in recommendation_text
                for term in forbidden_terms
            ):
                raise RuntimeError(
                    "Recommendation contains "
                    "infrastructure execution logic."
                )

        print(
            "NO INFRASTRUCTURE EXECUTION PASS"
        )

        # =========================================================
        # 15. NO UNSUPPORTED VULNERABILITY CLAIMS
        # =========================================================

        for finding in findings:
            combined_text = (
                f"{finding.title} "
                f"{finding.description}"
            ).lower()

            if "confirmed vulnerability" in (
                combined_text
            ):
                raise RuntimeError(
                    "Unsupported confirmed "
                    "vulnerability claim detected."
                )

        print(
            "NO UNSUPPORTED VULNERABILITY CLAIMS PASS"
        )

        # =========================================================
        # 16. FINAL PHASE 7.7 BOUNDARY
        # =========================================================

        print()
        print(
            "PHASE 7.7 BOUNDARY CHECK"
        )
        print(
            "------------------------"
        )

        print(
            "Real Docker evidence:        AVAILABLE"
        )
        print(
            "PostgreSQL evidence storage: VERIFIED"
        )
        print(
            "Security assessment:         EXECUTED"
        )
        print(
            "Security risk signals:       EXECUTED"
        )
        print(
            "Recommendations:             EXECUTED"
        )
        print(
            "Infrastructure action:       NONE"
        )
        print(
            "Automatic remediation:       NONE"
        )
        print(
            "Security configuration change: NONE"
        )

        print()
        print(
            "PHASE 7.7 — COMPLETE: PASS"
        )
        print(
            "PHASE 7 — SECURITY INTELLIGENCE: COMPLETE"
        )

    finally:
        # =========================================================
        # CLEANUP
        #
        # PostgreSQLSecurityStorage intentionally does not expose
        # a delete_for_resource() production API.
        #
        # Therefore cleanup is performed directly against the
        # validation records using the storage connection.
        # =========================================================

        if stored_evidence:
            cleanup_ids = [
                item.evidence_id
                for item in stored_evidence
            ]

            with storage._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM security_evidence
                        WHERE evidence_id = ANY(%s)
                        """,
                        (
                            cleanup_ids,
                        ),
                    )

                connection.commit()

            print(
                "CLEANUP PASS — removed "
                f"{len(stored_evidence)} "
                "controlled validation records."
            )

        provider.close()


if __name__ == "__main__":
    main()