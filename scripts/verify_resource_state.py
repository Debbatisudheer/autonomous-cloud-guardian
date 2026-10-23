from guardian.application.resource_state import ResourceStateManager
from guardian.infrastructure.docker.discovery import DockerDiscovery

resources = DockerDiscovery().discover()
states = ResourceStateManager().observe_all(resources)

print(f"Resources discovered: {len(resources)}")
print(f"States observed: {len(states)}")

for state in states:
    print(
        f"{state.resource_id} | "
        f"{state.attributes['provider']} | "
        f"{state.attributes['resource_type']} | "
        f"{state.status.value} | "
        f"{state.health.value} | "
        f"observed={state.observed_at.isoformat()}"
    )