#!/usr/bin/env python3
"""
Apple-inspired launch script for TaskForge
Demonstrates the beautiful CLI and web interfaces
"""

import subprocess
import sys
import webbrowser
from pathlib import Path

from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

# Apple-inspired theme
apple_theme = Theme(
    {
        "primary": "#007AFF",  # SF Blue
        "success": "#34C759",  # SF Green
        "warning": "#FF9500",  # SF Orange
        "error": "#FF3B30",  # SF Red
        "secondary": "#5856D6",  # SF Purple
        "muted": "#8E8E93",  # SF Gray
        "accent": "#AF52DE",  # SF Purple variant
        "info": "#00C7BE",  # SF Teal
    }
)

console = Console(theme=apple_theme)


def print_welcome():
    """Display Apple-style welcome message"""

    # TaskForge logo/title
    logo = Text("⚡ TaskForge", style="bold primary")
    logo.stylize("bold", 0, 2)  # Make the lightning bolt bold

    subtitle = Text("Beautifully designed task management", style="muted")

    # Center align
    centered_logo = Align.center(logo)
    centered_subtitle = Align.center(subtitle)

    console.print()
    console.print(centered_logo)
    console.print(centered_subtitle)
    console.print()

    # Feature showcase
    features = [
        "[primary]⚡[/primary] Lightning fast CLI",
        "[success]🎨[/success] Apple-inspired design",
        "[secondary]📊[/secondary] Beautiful dashboards",
        "[accent]🚀[/accent] Modern web interface",
    ]

    feature_panels = []
    for feature in features:
        feature_panels.append(
            Panel(feature, border_style="primary", padding=(0, 1), width=25)
        )

    console.print(Columns(feature_panels, equal=True, expand=True))
    console.print()


def show_menu():
    """Display interactive menu"""

    menu_items = [
        "1. 📱 Launch CLI Demo",
        "2. 🌐 Start Web Dashboard",
        "3. 📖 View API Documentation",
        "4. 🎭 Create Demo Data",
        "5. ❌ Exit",
    ]

    menu_content = "\n".join([f"  {item}" for item in menu_items])

    console.print(
        Panel(
            menu_content,
            title="[bold primary]Choose an Experience[/bold primary]",
            border_style="primary",
            padding=(1, 2),
        )
    )


def launch_cli_demo():
    """Launch CLI with demo data"""
    console.print("🚀 Launching CLI demo...", style="primary")

    try:
        # Create demo data first
        subprocess.run([sys.executable, "examples/simple_cli.py", "demo"], check=True)

        # Show task list
        console.print("\n📋 Here are your demo tasks:", style="accent")
        subprocess.run([sys.executable, "examples/simple_cli.py", "list"], check=True)

        console.print(f"\n✨ Try these commands:", style="success")
        console.print(
            f'  [primary]python examples/simple_cli.py add "Your new task"[/primary]'
        )
        console.print(
            f"  [primary]python examples/simple_cli.py complete <task-id>[/primary]"
        )
        console.print(f"  [primary]python examples/simple_cli.py stats[/primary]")

    except subprocess.CalledProcessError as e:
        console.print(f"❌ Error launching CLI: {e}", style="error")


def launch_web_dashboard():
    """Launch web dashboard"""
    console.print("🌐 Starting web dashboard...", style="primary")

    try:
        # Try to start the Apple-inspired dashboard
        console.print(
            "📱 Starting Apple-inspired dashboard at http://localhost:8501",
            style="info",
        )
        console.print("💡 Opening in your browser in 3 seconds...", style="muted")

        # Open browser after short delay
        import threading
        import time

        def open_browser():
            time.sleep(3)
            webbrowser.open("http://localhost:8501")

        threading.Thread(target=open_browser).start()

        # Start Streamlit dashboard
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "taskforge/web/apple_dashboard.py",
                "--server.port=8501",
                "--server.headless=true",
            ],
            check=True,
        )

    except subprocess.CalledProcessError as e:
        console.print(f"❌ Error starting dashboard: {e}", style="error")
        console.print(
            "💡 Make sure Streamlit is installed: pip install streamlit", style="muted"
        )


def launch_api_docs():
    """Launch API documentation"""
    console.print("📖 Starting API server...", style="primary")

    try:
        console.print(
            "🚀 API docs will be available at http://localhost:8000/docs", style="info"
        )
        console.print("💡 Opening in your browser in 3 seconds...", style="muted")

        # Open browser after short delay
        import threading
        import time

        def open_browser():
            time.sleep(3)
            webbrowser.open("http://localhost:8000/docs")

        threading.Thread(target=open_browser).start()

        # Start API server
        subprocess.run([sys.executable, "examples/simple_api.py"], check=True)

    except subprocess.CalledProcessError as e:
        console.print(f"❌ Error starting API: {e}", style="error")


def create_demo_data():
    """Create demo data"""
    console.print("🎭 Creating demo data...", style="primary")

    try:
        subprocess.run([sys.executable, "examples/simple_cli.py", "demo"], check=True)
        console.print("✅ Demo data created successfully!", style="success")
        console.print("💡 Use option 1 to see the CLI demo with data", style="muted")

    except subprocess.CalledProcessError as e:
        console.print(f"❌ Error creating demo data: {e}", style="error")


def main():
    """Main application loop"""
    print_welcome()

    while True:
        show_menu()

        try:
            choice = console.input(
                "\n[primary]Choose an option (1-5):[/primary] "
            ).strip()

            if choice == "1":
                launch_cli_demo()
            elif choice == "2":
                launch_web_dashboard()
            elif choice == "3":
                launch_api_docs()
            elif choice == "4":
                create_demo_data()
            elif choice == "5":
                console.print("👋 Thank you for using TaskForge!", style="success")
                break
            else:
                console.print("❌ Invalid choice. Please select 1-5.", style="error")

        except KeyboardInterrupt:
            console.print("\n\n👋 Goodbye!", style="muted")
            break
        except Exception as e:
            console.print(f"❌ An error occurred: {e}", style="error")

        console.print()  # Add spacing


if __name__ == "__main__":
    main()
