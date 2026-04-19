"""
Generic scenario interview command (AWS, Kubernetes, etc.)
"""

import json
import random
from typing import Dict, List

import click

from ..data.aws_scenarios import AWS_SCENARIO_QUESTIONS
from ..data.kubernetes_scenarios import KUBERNETES_SCENARIO_QUESTIONS

try:
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None


SCENARIO_DOMAINS = {
    "aws": {
        "label": "AWS",
        "aliases": ["amazon-web-services"],
        "questions": AWS_SCENARIO_QUESTIONS,
        "grading_guidance": (
            "Reward concrete AWS services, prioritization, realistic trade-offs, "
            "security, scalability, and operational thinking."
        ),
    },
    "kubernetes": {
        "label": "Kubernetes",
        "aliases": ["k8s"],
        "questions": KUBERNETES_SCENARIO_QUESTIONS,
        "grading_guidance": (
            "Reward Kubernetes troubleshooting logic, production-safe debugging, "
            "networking awareness, workload reliability, and realistic fixes."
        ),
    },
}


def resolve_domain(name: str):
    candidate = name.lower().strip()

    for key, cfg in SCENARIO_DOMAINS.items():
        names = [key] + cfg.get("aliases", [])
        if candidate in names:
            return key, cfg

    valid = ", ".join(sorted(SCENARIO_DOMAINS.keys()))
    raise click.BadParameter(
        f"Unknown scenario domain '{name}'. Choose from: {valid}"
    )


class LocalGrader:
    """Simple keyword-based fallback grader."""

    def grade(self, question: Dict[str, object], answer: str) -> Dict[str, object]:
        rubric = question.get("rubric", [])
        answer_lower = answer.lower()
        hits = []

        for item in rubric:
            item_lower = str(item).lower()
            if any(word in answer_lower for word in item_lower.split()):
                hits.append(item)

        score = int((len(hits) / max(len(rubric), 1)) * 100)

        verdict = (
            "Excellent"
            if score >= 80 else
            "Good"
            if score >= 60 else
            "Needs improvement"
        )

        return {
            "score": score,
            "verdict": verdict,
            "strengths": hits,
            "gaps": [item for item in rubric if item not in hits],
            "feedback": "Matched rubric keywords locally.",
            "rubric_hits": hits,
        }


class BedrockClaudeGrader:
    """Bedrock-based AI grader."""

    def __init__(
        self,
        region: str,
        model_id: str,
        domain_label: str,
        grading_guidance: str,
    ):
        if boto3 is None:
            raise RuntimeError(
                "boto3 is not installed. Install it or use --no-bedrock."
            )

        self.region = region
        self.model_id = model_id
        self.domain_label = domain_label
        self.grading_guidance = grading_guidance
        self.client = boto3.client("bedrock-runtime", region_name=region)

    def grade(self, question: Dict[str, object], answer: str) -> Dict[str, object]:
        rubric = question.get("rubric", [])

        prompt = (
            f"You are grading a {self.domain_label} interview answer.\n"
            "Return ONLY valid JSON with these exact keys:\n"
            'score (integer 0-100), verdict (string), strengths (array of strings), '
            'gaps (array of strings), feedback (string), rubric_hits (array of strings).\n\n'
            f"Scenario:\n{question['scenario']}\n\n"
            f"Candidate answer:\n{answer}\n\n"
            f"Reference answer:\n{question['reference_answer']}\n\n"
            "Rubric items (must be used for grading):\n"
            f"{json.dumps(rubric, indent=2)}\n\n"
            "Grading rules:\n"
            f"- {self.grading_guidance}\n"
            "- Reward structured troubleshooting or design thinking.\n"
            "- Penalize vague answers that miss key steps.\n"
            "- Keep feedback concise and practical.\n"
            "- rubric_hits must contain the rubric items the answer genuinely covered.\n"
        )

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 700,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        }
                    ],
                }
            ],
        }

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        raw_body = response["body"].read()
        payload = json.loads(raw_body)

        text_parts = []
        for item in payload.get("content", []):
            if item.get("type") == "text":
                text_parts.append(item.get("text", ""))

        text = "\n".join(text_parts).strip()

        if not text:
            raise ValueError("Bedrock returned an empty response.")

        parsed = self._extract_json(text)

        return {
            "score": int(parsed.get("score", 0)),
            "verdict": str(parsed.get("verdict", "Needs improvement")),
            "strengths": list(parsed.get("strengths", [])),
            "gaps": list(parsed.get("gaps", [])),
            "feedback": str(parsed.get("feedback", "")),
            "rubric_hits": list(parsed.get("rubric_hits", [])),
        }

    @staticmethod
    def _extract_json(text: str) -> Dict[str, object]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"Could not parse JSON from Bedrock response: {text}")

        return json.loads(text[start:end + 1])


@click.command("scenario")
@click.argument("domain")
@click.option("--count", default=3, show_default=True, help="Number of scenario questions")
@click.option("--topic", default=None, help="Filter by topic")
@click.option("--difficulty", default=None, help="Filter by difficulty")
@click.option(
    "--region",
    default="us-east-1",
    show_default=True,
    envvar="AWS_REGION",
    help="AWS region for Bedrock",
)
@click.option(
    "--model-id",
    "model_id",
    default="us.anthropic.claude-sonnet-4-6",
    show_default=True,
    envvar="MOCKOPS_BEDROCK_MODEL_ID",
    help="Bedrock model ID",
)
@click.option(
    "--no-bedrock",
    is_flag=True,
    help="Use local keyword grading instead of Bedrock AI grading",
)
@click.option("--export", default=None, help="Export results to JSON")
@click.pass_context
def scenario(ctx, domain, count, topic, difficulty, region, model_id, no_bedrock, export):
    """Run scenario-based interview questions for a given domain."""
    log = ctx.obj["LOGGER"]

    _, domain_cfg = resolve_domain(domain)
    domain_label = domain_cfg["label"]
    questions = domain_cfg["questions"]

    log.debug(
        "%s scenario called count=%s topic=%s difficulty=%s region=%s model_id=%s no_bedrock=%s",
        domain_label,
        count,
        topic,
        difficulty,
        region,
        model_id,
        no_bedrock,
    )

    if topic:
        questions = [
            q for q in questions
            if str(q["topic"]).lower() == topic.lower()
        ]

    if difficulty:
        questions = [
            q for q in questions
            if str(q["difficulty"]).lower() == difficulty.lower()
        ]

    if not questions:
        click.echo("No matching questions found.")
        return

    selected = random.sample(
        questions,
        k=min(count, len(questions))
    )

    if no_bedrock:
        grader = LocalGrader()
        click.echo("\nUsing local keyword grading.\n")
    else:
        try:
            grader = BedrockClaudeGrader(
                region=region,
                model_id=model_id,
                domain_label=domain_label,
                grading_guidance=domain_cfg["grading_guidance"],
            )
            click.echo(
                f"\nUsing Bedrock AI grading ({model_id} in {region}).\n"
            )
        except Exception as exc:
            click.echo(
                f"\nBedrock grader unavailable: {exc}\n"
                "Falling back to local keyword grading.\n"
            )
            grader = LocalGrader()

    results = []

    click.echo(f"=== {domain_label.upper()} SCENARIO PRACTICE ===\n")

    for index, question in enumerate(selected, start=1):
        click.echo(f"\nQuestion {index}")
        click.echo(question["scenario"])

        answer = click.prompt("\nYour answer", type=str)

        grade = grader.grade(question, answer)

        click.echo(f"\nScore: {grade['score']} ({grade['verdict']})")

        if grade.get("strengths"):
            click.echo("\nStrengths:")
            for item in grade["strengths"]:
                click.echo(f"- {item}")

        if grade.get("gaps"):
            click.echo("\nGaps:")
            for item in grade["gaps"]:
                click.echo(f"- {item}")

        if grade.get("feedback"):
            click.echo(f"\nFeedback: {grade['feedback']}")

        results.append({
            "id": question["id"],
            "topic": question["topic"],
            "difficulty": question["difficulty"],
            "score": grade["score"],
            "verdict": grade["verdict"],
            "strengths": grade.get("strengths", []),
            "gaps": grade.get("gaps", []),
            "feedback": grade.get("feedback", ""),
            "rubric_hits": grade.get("rubric_hits", []),
        })

    avg = sum(r["score"] for r in results) / len(results)
    click.echo(f"\nAverage score: {avg:.1f}")

    if export:
        with open(export, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        click.echo(f"Saved results to {export}")