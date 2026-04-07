from click.testing import CliRunner

from devops_interview_prep.cli import cli


def test_aws_scenario_command_no_bedrock_runs():
    runner = CliRunner()

    # One free-text answer followed by blank line to submit
    result = runner.invoke(
        cli,
        ["aws-scenario", "--count", "1", "--no-bedrock"],
        input=(
            "Use IAM Identity Center and federation.\n"
            "Disable and rotate long-lived keys and enforce MFA.\n"
            "Use CloudTrail and Access Analyzer to tighten permissions.\n"
            "\n"
        ),
    )

    assert result.exit_code == 0
    assert "AWS SCENARIO INTERVIEW PREP" in result.output
    assert "SESSION SUMMARY" in result.output
    assert "Average score" in result.output


def test_aws_scenario_topic_filter_no_results():
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["aws-scenario", "--topic", "does-not-exist", "--no-bedrock"],
    )

    assert result.exit_code == 0
    assert "No scenario questions found" in result.output
