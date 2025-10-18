"""CLI entrypoint for Prompt Paladin MCP server."""
import typer

app = typer.Typer(
    name="prompt-paladin",
    help="Prompt Paladin MCP Server - Prompt quality assessment"
)


@app.command()
def serve():
    """Start the MCP server (stdio mode)."""
    from .server import mcp
    from .config import load_config
    
    typer.echo("🏰 Starting Prompt Paladin MCP Server...")
    
    try:
        # Load and validate config before starting
        config = load_config()
        typer.echo("✅ Configuration loaded")
        typer.echo(f"   Default Provider: {config.default_provider}")
        typer.echo(f"   Auto-cast Heal: {config.auto_cast_heal}")
        typer.echo(f"   Anger Translator: {config.anger_translator}")
        typer.echo("")
        typer.echo("🚀 Server running on stdio...")
        typer.echo("   Press Ctrl+C to stop")
        typer.echo("")
        
        # Run the MCP server
        mcp.run()
        
    except KeyboardInterrupt:
        typer.echo("\n👋 Server stopped")
    except Exception as e:
        typer.echo(f"❌ Server error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def doctor():
    """Check system health and configuration."""
    from .config import load_config
    
    typer.echo("🏥 Running health check...")
    
    try:
        config = load_config()
        typer.echo("✅ Configuration loaded successfully")
        typer.echo(f"   Default Provider: {config.default_provider}")
        typer.echo(f"   Default Model: {config.default_model}")
        typer.echo(f"   Auto-cast Heal: {config.auto_cast_heal}")
        typer.echo(f"   Anger Translator: {config.anger_translator}")
        
        # Check API keys
        if config.anthropic_api_key:
            typer.echo("✅ Anthropic API key configured")
        if config.openai_api_key:
            typer.echo("✅ OpenAI API key configured")
        if config.groq_api_key:
            typer.echo("✅ Groq API key configured")
        
        typer.echo("\n✅ All checks passed!")
        
    except Exception as e:
        typer.echo(f"❌ Configuration error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

