"""
Interview simulation command
"""
import click
import random as py_random
from ..core.question_bank import question_bank
from ..models.session import InterviewSession


@click.command(context_settings={"ignore_unknown_options": True})
@click.option('--count', '-c', default=15, help='Number of questions')
@click.option('--company-type', help='Focus on specific company type')
@click.option('--duration', help='Time limit (e.g., 45min)')
@click.option('--export', help='Export interview results to JSON file')
@click.pass_context
def interview(ctx, count, company_type, duration, export):
    """Full interview simulation with mixed topics"""
    log = ctx.obj['LOGGER']
    log.debug(
        f"Interview called with count={count}, company_type={company_type}, duration={duration}"
    )
    if not question_bank.questions:
        click.echo("Error: No questions available")
        return

    all_questions = question_bank.questions
    if company_type:
        tagged = [
            q for q in all_questions if company_type.lower() in
            [tag.lower() for tag in (q.company_tags or [])]
        ]
        if not tagged:
            click.echo(
                f"Warning: No questions tagged for '{company_type}'. Using all questions instead."
            )
        else:
            all_questions = tagged

    if len(all_questions) < count:
        count = len(all_questions)
        click.echo(f"Adjusted to {count} questions (all available)")

    selected_questions = py_random.sample(all_questions, count)

    click.echo("🎭 INTERVIEW SIMULATION")
    click.echo("=" * 30)
    click.echo(f"📝 Questions: {count}")
    if company_type:
        click.echo(f"🏢 Company type: {company_type}")
    if duration:
        click.echo(f"⏱️  Time limit: {duration}")

    # Show question distribution
    topic_dist = {}
    for q in selected_questions:
        topic_dist[q.topic] = topic_dist.get(q.topic, 0) + 1

    click.echo(f"\n📊 Question distribution:")
    for topic, cnt in sorted(topic_dist.items()):
        click.echo(f"  {topic}: {cnt}")

    if not click.confirm("\nReady to begin your interview?"):
        return

    session = InterviewSession()

    for i, question in enumerate(selected_questions, 1):
        click.echo(f"\nInterview Question {i}/{count}")
        click.echo(f"Topic: {question.topic} | Difficulty: {question.difficulty}")

        completed = session.ask_question(question)

        if completed is False:
            click.echo("\nInterview cancelled.")
            break

    session.show_summary()

    if export:
        session.export_results(export)