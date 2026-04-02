"""
Practice command implementation
"""
import click
from ..core.question_bank import question_bank
from ..models.session import InterviewSession

@click.command(context_settings={"ignore_unknown_options": True})
@click.argument('topic', required=False)
@click.option('--difficulty', '-d', help='Difficulty level (easy, medium, hard)')
@click.option('--count', '-c', default=5, help='Number of questions')
@click.option('--company-type', help='Company type (faang, startup, enterprise)')
@click.option('--interview-mode', '-i', is_flag=True, help='Interview simulation mode')
@click.option('--export', help='Export results to JSON file')
@click.pass_context
def practice(ctx, topic, difficulty, count, company_type, interview_mode, export):
    """Practice interview questions by topic"""
    log = ctx.obj['LOGGER']
    log.debug(f"Practice called with topic={topic}, difficulty={difficulty}, count={count}, company_type={company_type}, interview_mode={interview_mode}")
    
    if not question_bank.questions:
        click.echo("Error: No questions available")
        return

    topics = question_bank.get_topics()
    lcase_topics = {t.lower(): t for t in topics}

    if topic:
        if topic.lower() not in lcase_topics:
            click.echo(f"Error: Unknown topic '{topic}'\n")
            click.echo("Available topics:")
            for t in topics:
                topic_question_count = question_bank.get_topic_count(t)
                click.echo(f"{t} ({topic_question_count} questions)")
            topic = click.prompt(
                "\nSelect a topic",
                type=click.Choice(topics, case_sensitive=False)
            )
        else:
            topic = lcase_topics[topic.lower()]
    else:
        click.echo("Available topics:")
        for t in topics:
            topic_count = question_bank.get_topic_count(t)
            click.echo(f"{t} ({topic_count} questions)")
        topic = click.prompt(
            "\nSelect a topic",
            type=click.Choice(topics, case_sensitive=False)
        )

    if company_type and not question_bank.get_company_types():
        click.echo("Warning: --company-type filtering is not yet supported (no questions are tagged). Ignoring filter.")
        company_type = None

    questions = question_bank.get_questions(topic, difficulty, count, company_type)
    if not questions:
        click.echo("No questions found for the specified criteria")
        return
    
    click.echo(f"\n🎯 Starting practice: {topic.upper()}")
    if difficulty:
        click.echo(f"📊 Difficulty: {difficulty}")
    if company_type:
        click.echo(f"🏢 Company type: {company_type}")
    click.echo(f"📝 Questions: {len(questions)}")
    
    session = InterviewSession()

    for i, question in enumerate(questions, 1):
        click.echo(f"\nQuestion {i}/{len(questions)} | {question.difficulty.upper()}")

        completed = session.ask_question(question)
        if completed is False:
            click.echo("\nPractice session cancelled.")
            break

        if interview_mode and i < len(questions):
            if not click.confirm("\nContinue to next question?", default=True):
                break

    session.show_summary()
    if export:
        session.export_results(export)
