# src/main.py
import logging
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional

# Internal module imports
from src.agent import DeepResearchAgent, AgentConfig
from src.planning import PlanningStrategy

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Typer app and Rich console
app = typer.Typer(
    help="CLI entry point for the Deep Research Agent.",
    add_completion=False
)
console = Console()

@app.command()
def main(
    query: str = typer.Argument(
        ..., 
        help="The research query or topic to investigate."
    ),
    strategy: PlanningStrategy = typer.Option(
        PlanningStrategy.SEQUENTIAL,
        "--strategy", "-s",
        help="The planning topology to use (e.g., sequential, parallel)."
    ),
    max_subtasks: int = typer.Option(
        5,
        "--max-subtasks", "-m",
        help="Maximum number of sub-tasks to execute per query."
    ),
    timeout: int = typer.Option(
        300,
        "--timeout", "-t",
        help="Global execution timeout in seconds."
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose logging output for debugging."
    ),
) -> None:
    """
    Run the Deep Research Agent on a specific user query.
    
    This tool orchestrates the research process by planning sub-tasks, 
    acquiring information, managing memory, and generating a final report.
    """
    # Configure logging verbosity
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled.")
    else:
        # Suppress external library logs unless verbose
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Display startup banner
    console.print(Panel.fit(
        f"[bold blue]Deep Research Agent[/bold blue]\n"
        f"Query: [italic]{query}[/italic]\n"
        f"Strategy: [cyan]{strategy.value}[/cyan] | Max Subtasks: [cyan]{max_subtasks}[/cyan]",
        border_style="blue"
    ))

    # Initialize Configuration
    try:
        config = AgentConfig(
            planning_strategy=strategy,
            max_subtasks=max_subtasks,
            timeout=timeout
        )
        logger.debug(f"Agent configuration initialized: {config}")
    except Exception as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Initialize and Run Agent
    try:
        agent = DeepResearchAgent(config=config)
        
        result: str = ""
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console
        ) as progress:
            task_id = progress.add_task(description="[cyan]Initializing research workflow...[/cyan]", total=None)
            
            # Execute the research workflow
            # The agent handles planning, acquisition, memory, and generation internally
            result = agent.run(query)
            
            progress.update(task_id, completed=True)

        # Output the Final Report
        console.print("\n[bold green]Research Complete![/bold green]")
        console.print(Panel(
            Markdown(result),
            title="Final Research Report",
            border_style="green",
            expand=True
        ))

    except KeyboardInterrupt:
        console.print("\n[bold yellow]Operation cancelled by user.[/bold yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"\n[bold red]Execution Error:[/bold red] {str(e)}")
        if verbose:
            logger.exception("Detailed traceback:")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()