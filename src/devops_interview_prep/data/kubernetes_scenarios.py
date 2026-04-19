"""
Kubernetes scenario-based interview questions.
"""

from typing import Dict, List


KUBERNETES_SCENARIO_QUESTIONS: List[Dict[str, object]] = [

    {
        "id": "k8s-troubleshooting-001",
        "topic": "troubleshooting",
        "difficulty": "medium",
        "scenario": "A pod is stuck in CrashLoopBackOff. How do you investigate?",
        "reference_answer": (
            "Check pod logs using kubectl logs, inspect events with kubectl describe pod, "
            "verify container image and startup command, check environment variables, "
            "review liveness and readiness probes, and confirm resource limits are not causing restarts."
        ),
        "rubric": [
            "kubectl logs",
            "kubectl describe pod",
            "container image",
            "startup command",
            "environment variable",
            "liveness probe",
            "readiness probe",
            "resource limit"
        ]
    },

    {
        "id": "k8s-networking-001",
        "topic": "networking",
        "difficulty": "medium",
        "scenario": "A service cannot reach another service inside the cluster. How do you debug?",
        "reference_answer": (
            "Check service selectors match pod labels, verify endpoints exist, "
            "confirm cluster DNS resolution works, inspect network policies, "
            "and ensure the target pod is running and listening on the expected port."
        ),
        "rubric": [
            "service selector",
            "pod label",
            "endpoint",
            "cluster dns",
            "network policy",
            "target port",
            "pod running"
        ]
    }

]