from __future__ import annotations

import typer
import requests


API_URL = "http://127.0.0.1:8000"
cli = typer.Typer(help="Trigger demo agents and inspect wallet control decisions.")


@cli.callback()
def main() -> None:
    """CLI entrypoint for the demo app."""


@cli.command()
def run(
    agent_name: str,
    task: str = typer.Option(..., "--task", help="Task assigned to the agent."),
) -> None:
    """Run a demo agent task and show the wallet-control decision."""
    response = requests.post(
        f"{API_URL}/run",
        json={"agent_id": agent_name, "task": task},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    typer.echo(f"[agent] Task started: {task}")

    payment_intent = data.get("payment_intent")
    if payment_intent:
        typer.echo(
            "[agent] Need paid access: "
            f"{payment_intent['vendor']} (${payment_intent['amount']:.2f})"
        )
    else:
        typer.echo("[agent] No payment required")

    typer.echo(f"[wallet-control] {data['decision']}")
    for reason in data.get("reasons", []):
        typer.echo(f"[wallet-control] Reason: {reason}")
    if data.get("risk_score") is not None:
        typer.echo(f"[wallet-control] Risk score: {data['risk_score']}")


if __name__ == "__main__":
    cli()
