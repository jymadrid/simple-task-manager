"""
CLI测试模块
"""

from typer.testing import CliRunner

from taskforge.cli import app

runner = CliRunner()


def test_app_help():
    """测试CLI的--help命令"""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "TaskForge" in result.stdout
    assert "task management" in result.stdout


def test_task_command_help():
    """测试task子命令的help"""
    result = runner.invoke(app, ["task", "--help"])
    assert result.exit_code == 0
    assert "add" in result.stdout
    assert "list" in result.stdout
    assert "show" in result.stdout


def test_project_command_help():
    """测试project子命令的help"""
    result = runner.invoke(app, ["project", "--help"])
    assert result.exit_code == 0
    assert "create" in result.stdout


def test_stats_command_help():
    """测试stats命令的help"""
    result = runner.invoke(app, ["stats", "--help"])
    assert result.exit_code == 0
    assert "statistics" in result.stdout


def test_dashboard_command_help():
    """测试dashboard命令的help"""
    result = runner.invoke(app, ["dashboard", "--help"])
    assert result.exit_code == 0
    assert "dashboard" in result.stdout


def test_task_list_command_exists():
    """测试task list命令是否存在且可执行"""
    # 由于需要实际的数据存储，我们只测试命令是否可以正常调用
    # 不要求有实际数据返回
    try:
        result = runner.invoke(app, ["task", "list"])
        # 命令可能因为没有数据文件而失败，但exit_code应该不是2（命令不存在）
        assert result.exit_code != 2
    except SystemExit:
        # CLI可能会调用sys.exit()，这是正常行为
        pass
