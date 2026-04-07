"""
AWS scenario-based interview command with Bedrock grading.
"""
import json
from typing import Dict, List, Optional

import click
from colorama import Fore, Back, Style, init

from ..data.aws_scenarios import AWS_SCENARIO_QUESTIONS

# Initialize colorama
init(autoreset=True)


def _prompt_multiline_answer() -> Optional[str]:
    """Collect free-text answer from user until empty line."""
    click.echo()
    click.echo(f"{Fore.CYAN}📝 Your Answer:{Style.RESET_ALL}")
    click.echo(f"{Fore.LIGHTBLACK_EX}(Press ENTER twice when done, or type 'q' to skip){Style.RESET_ALL}")
    click.echo()
    lines: List[str] = []

    while True:
        line = click.prompt(f"{Fore.LIGHTBLACK_EX}> {Style.RESET_ALL}", prompt_suffix="", default="", show_default=False)
        if not lines and line.strip().lower() == "q":
            return None

        if line.strip() == "":
            break

        lines.append(line)

    answer = "\n".join(lines).strip()
    if not answer:
        click.echo(f"{Fore.YELLOW}⚠  Please provide at least one line.{Style.RESET_ALL}")
        return _prompt_multiline_answer()

    return answer


def _extract_json_object(text: str) -> Dict[str, object]:
    """Extract first JSON object from model output."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Model response does not contain a JSON object")
    return json.loads(text[start : end + 1])


def _heuristic_grade(question: Dict[str, object], answer: str) -> Dict[str, object]:
    """Fallback grading that checks rubric coverage using keyword overlap."""
    rubric = question.get("rubric", []) or []
    answer_l = answer.lower()

    rubric_hits: List[str] = []
    gaps: List[str] = []

    for item in rubric:
        token_hits = 0
        tokens = [t.strip("(),./").lower() for t in item.split() if len(t) > 3]
        for token in tokens:
            if token in answer_l:
                token_hits += 1

        if token_hits >= max(1, len(tokens) // 4):
            rubric_hits.append(str(item))
        else:
            gaps.append(str(item))

    total = len(rubric)
    score = int((len(rubric_hits) / total) * 100) if total else 0

    if score >= 85:
        verdict = "strong"
    elif score >= 65:
        verdict = "good"
    elif score >= 45:
        verdict = "partial"
    else:
        verdict = "weak"

    return {
        "score": score,
        "verdict": verdict,
        "strengths": rubric_hits[:3],
        "gaps": gaps[:3],
        "feedback": "💡 Tip: Cover immediate actions and longer-term architecture, then map each point to AWS-native controls.",
        "rubric_hits": rubric_hits,
        "grader": "heuristic",
    }


class BedrockClaudeGrader:
    """Grades free-text answers using Claude on Amazon Bedrock."""

    def __init__(self, region: str, model_id: str):
        self.region = region
        self.model_id = model_id

    def _invoke_claude(self, prompt: str) -> str:
        try:
            import boto3  # Imported lazily so CLI still works without Bedrock mode
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "boto3 is required for Bedrock grading. Install it with: pip install boto3"
            ) from exc

        client = boto3.client("bedrock-runtime", region_name=self.region)
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 600,
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

        response = client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        payload = json.loads(response["body"].read())
        content = payload.get("content", [])
        if not content:
            raise RuntimeError("Empty Bedrock response")

        return content[0].get("text", "")

    def grade(self, question: Dict[str, object], answer: str) -> Dict[str, object]:
        rubric = question.get("rubric", [])
        prompt = (
            "You are grading an AWS interview answer. Return ONLY valid JSON with keys: "
            "score (0-100 int), verdict (string), strengths (array of strings), "
            "gaps (array of strings), feedback (string), rubric_hits (array of strings).\n\n"
            f"Scenario:\n{question['scenario']}\n\n"
            f"Candidate answer:\n{answer}\n\n"
            f"Reference answer:\n{question['reference_answer']}\n\n"
            "Rubric items (must be used for grading):\n"
            f"{json.dumps(rubric, indent=2)}\n\n"
            "Scoring guidance: Reward concrete AWS services, prioritization, and realistic trade-offs."
        )

        raw_text = self._invoke_claude(prompt)
        graded = _extract_json_object(raw_text)
        graded["grader"] = "bedrock-claude"
        return graded


@click.command("aws-scenario", context_settings={"ignore_unknown_options": True})
@click.option("--count", "count", default=3, show_default=True, help="Number of AWS scenario questions")
@click.option("--topic", "topic", type=str, help="Filter by topic (iam, networking, cost-optimization)")
@click.option("--difficulty", "difficulty", type=click.Choice(["medium", "hard"], case_sensitive=False), help="Filter by difficulty")
@click.option("--region", "region", default="us-east-1", show_default=True, envvar="AWS_REGION", help="AWS region for Bedrock")
@click.option("--model-id", "model_id", default="anthropic.claude-3-5-sonnet-20241022-v2:0", show_default=True, envvar="MOCKOPS_BEDROCK_MODEL_ID", help="Bedrock model ID")
@click.option("--no-bedrock", "no_bedrock", is_flag=True, help="Use local heuristic grading instead of Bedrock")
@click.option("--export", "export", type=str, help="Export results JSON path")
@click.pass_context
def aws_scenario(ctx, count, topic, difficulty, region, model_id, no_bedrock, export):
    """Practice AWS scenario interviews with free-text answers and Bedrock grading."""
    log = ctx.obj["LOGGER"]
    log.debug(
        "AWS scenario called with count=%s, topic=%s, difficulty=%s, region=%s, model_id=%s, no_bedrock=%s",
        count,
        topic,
        difficulty,
        region,
        model_id,
        no_bedrock,
    )

    questions = AWS_SCENARIO_QUESTIONS

    if topic:
        questions = [q for q in questions if str(q["topic"]).lower() == topic.lower()]

    if difficulty:
        questions = [q for q in questions if str(q["difficulty"]).lower() == difficulty.lower()]

    if not questions:
        click.echo(f"{Fore.YELLOW}ℹ  No scenario questions found with the selected filters.{Style.RESET_ALL}")
        return

    selected = questions[: min(count, len(questions))]
    if count > len(questions):
        click.echo(f"{Fore.YELLOW}ℹ  Requested {count}, using {len(selected)} available questions.{Style.RESET_ALL}")

    click.echo()
    click.echo(f"{Back.CYAN}{Fore.BLACK}  🚀 AWS SCENARIO INTERVIEW PREP  {Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}{'─' * 70}{Style.RESET_ALL}")
    click.echo(f"{Fore.WHITE}Questions: {len(selected)} | Grading: {'Bedrock Claude' if not no_bedrock else 'Local Heuristic'}{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}{'─' * 70}{Style.RESET_ALL}")
    click.echo()

    grader = BedrockClaudeGrader(region=region, model_id=model_id)
    results = []

    for idx, question in enumerate(selected, start=1):
        click.echo("\n" + "-" * 70)
        click.echo(
            f"Question {idx}/{len(selected)} | Topic: {question['topic']} | Difficulty: {question['difficulty']}"
        )
        click.echo(f"\nScenario:\n{question['scenario']}\n")

        answer = _prompt_multiline_answer()
        if answer is None:
            click.echo(f"{Fore.YELLOW}⏭  Skipping this question.{Style.RESET_ALL}")
            continue

        click.echo(f"{Fore.LIGHTBLACK_EX}⏳ Grading your answer...{Style.RESET_ALL}")

        if no_bedrock:
            grade = _heuristic_grade(question, answer)
        else:
            try:
                grade = grader.grade(question, answer)
            except Exception as exc:
                click.echo(f"{Fore.YELLOW}⚠  Bedrock grading failed: {exc}{Style.RESET_ALL}")
                click.echo(f"{Fore.LIGHTBLACK_EX}📊 Falling back to local heuristic grading...{Style.RESET_ALL}")
                grade = _heuristic_grade(question, answer)

        score = int(grade.get("score", 0))
        verdict = str(grade.get("verdict", "n/a"))

        # Color-code the score
        if score >= 80:
            score_color = Fore.GREEN
            emoji = "🌟"
        elif score >= 60:
            score_color = Fore.YELLOW
            emoji = "✨"
        else:
            score_color = Fore.RED
            emoji = "📊"

        click.echo()
        click.echo(f"{emoji} {score_color}Score: {score}/100 ({verdict}){Style.RESET_ALL}")

        strengths = grade.get("strengths", []) or []
        gaps = grade.get("gaps", []) or []
        feedback = str(grade.get("feedback", ""))

        if strengths:
            click.echo(f"\n{Fore.GREEN}✅ Strengths:{Style.RESET_ALL}")
            for item in strengths:
                click.echo(f"   {Fore.GREEN}• {item}{Style.RESET_ALL}")

        if gaps:
            click.echo(f"\n{Fore.MAGENTA}🔧 Areas to Improve:{Style.RESET_ALL}")
            for item in gaps:
                click.echo(f"   {Fore.MAGENTA}• {item}{Style.RESET_ALL}")

        if feedback:
            click.echo(f"\n{Fore.CYAN}{feedback}{Style.RESET_ALL}")

        results.append(
            {
                "question": question,
                "answer": answer,
                "grade": grade,
            }
        )

    if not results:
        click.echo(f"{Fore.YELLOW}ℹ  No answers graded.{Style.RESET_ALL}")
        return

    avg_score = sum(int(r["grade"].get("score", 0)) for r in results) / len(results)

    click.echo()
    click.echo(f"{Fore.CYAN}{'─' * 70}{Style.RESET_ALL}")
    click.echo(f"{Back.CYAN}{Fore.BLACK}  📊 SESSION SUMMARY  {Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}{'─' * 70}{Style.RESET_ALL}")
    click.echo()
    click.echo(f"  {Fore.WHITE}Questions Answered: {len(results)}{Style.RESET_ALL}")

    # Color-code average score
    if avg_score >= 80:
        avg_color = Fore.GREEN
    elif avg_score >= 60:
        avg_color = Fore.YELLOW
    else:
        avg_color = Fore.RED

    click.echo(f"  {avg_color}Average Score: {avg_score:.1f}/100{Style.RESET_ALL}")

    # Topic breakdown
    topic_scores = {}
    for r in results:
        topic = r["question"]["topic"]
        score = int(r["grade"].get("score", 0))
        if topic not in topic_scores:
            topic_scores[topic] = []
        topic_scores[topic].append(score)

    if topic_scores:
        click.echo(f"\n  {Fore.CYAN}By Topic:{Style.RESET_ALL}")
        for topic, scores in sorted(topic_scores.items()):
            avg_topic = sum(scores) / len(scores)
            topic_color = Fore.GREEN if avg_topic >= 70 else Fore.YELLOW if avg_topic >= 50 else Fore.RED
            click.echo(f"    {topic_color}• {topic.replace('_', ' ').title()}: {avg_topic:.0f}%{Style.RESET_ALL}")

    click.echo()
    click.echo(f"{Fore.CYAN}{'─' * 70}{Style.RESET_ALL}")

    if export:
        try:
            with open(export, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "session": {
                            "question_count": len(results),
                            "average_score": avg_score,
                            "grading_mode": "bedrock" if not no_bedrock else "heuristic",
                            "region": region,
                            "model_id": model_id,
                        },
                        "results": results,
                    },
                    f,
                    indent=2,
                )
            click.echo(f"\n{Fore.GREEN}✅ Results exported to {export}{Style.RESET_ALL}\n")
        except Exception as exc:
            click.echo(f"\n{Fore.RED}❌ Failed to export results: {exc}{Style.RESET_ALL}\n")
