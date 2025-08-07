"""Command-line interface for claude-cli-auth module.

Provides a simple CLI for testing and basic operations with the Claude CLI Auth module.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click

from . import ClaudeAuthManager, __version__


@click.group()
@click.version_option(version=__version__)
@click.option('--debug', is_flag=True, help='Enable debug logging')
def main(debug: bool):
    """Claude CLI Authentication Module - Command Line Interface."""
    if debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)


@main.command()
@click.option('--working-dir', '-w', type=click.Path(exists=True, path_type=Path), 
              default=Path.cwd(), help='Working directory')
@click.option('--session-id', '-s', help='Session ID for conversation continuity')
@click.option('--continue-session', '-c', is_flag=True, help='Continue existing session')
@click.option('--timeout', '-t', type=float, help='Query timeout in seconds')
@click.argument('prompt')
def query(
    prompt: str,
    working_dir: Path,
    session_id: Optional[str],
    continue_session: bool,
    timeout: Optional[float]
):
    """Execute a Claude query with the given prompt."""
    async def _query():
        try:
            claude = ClaudeAuthManager()
            
            response = await claude.query(
                prompt=prompt,
                working_directory=working_dir,
                session_id=session_id,
                continue_session=continue_session,
                timeout=timeout,
            )
            
            click.echo(response.content)
            
            if response.cost > 0:
                click.echo(f"\nCost: ${response.cost:.4f}", err=True)
            if response.tools_used:
                click.echo(f"Tools used: {len(response.tools_used)}", err=True)
                
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            sys.exit(1)
    
    asyncio.run(_query())


@main.command()
def status():
    """Show authentication and system status."""
    try:
        claude = ClaudeAuthManager()
        
        # Get authentication status
        auth_info = claude.auth_manager.get_authentication_info()
        click.echo("🔐 Authentication Status:")
        click.echo(f"  Authenticated: {'✅' if auth_info['authenticated'] else '❌'}")
        if auth_info.get('claude_cli_version'):
            click.echo(f"  Claude CLI Version: {auth_info['claude_cli_version']}")
        if auth_info.get('user_info'):
            click.echo(f"  User: {auth_info['user_info']}")
        if auth_info.get('error'):
            click.echo(f"  Error: {auth_info['error']}")
        
        # Get system health
        click.echo(f"\n🏥 System Health: {'✅ Healthy' if claude.is_healthy() else '❌ Unhealthy'}")
        
        # Get configuration
        config = claude.get_config()
        click.echo("\n⚙️  Configuration:")
        click.echo(f"  Prefer SDK: {config['prefer_sdk']}")
        click.echo(f"  Enable Fallback: {config['enable_fallback']}")
        click.echo(f"  SDK Available: {config['sdk_available']}")
        click.echo(f"  SDK Interface: {'✅' if config['sdk_interface_initialized'] else '❌'}")
        click.echo(f"  CLI Interface: {'✅' if config['cli_interface_initialized'] else '❌'}")
        
        # Get statistics
        stats = claude.get_stats()
        if stats['total_requests'] > 0:
            click.echo("\n📊 Statistics:")
            click.echo(f"  Total Requests: {stats['total_requests']}")
            click.echo(f"  Success Rate: {stats['success_rate']:.1%}")
            click.echo(f"  Total Cost: ${stats['total_cost']:.4f}")
            click.echo(f"  Avg Cost/Request: ${stats['avg_cost_per_request']:.4f}")
            click.echo(f"  Avg Duration: {stats['avg_duration_ms']:.0f}ms")
            
        asyncio.run(claude.shutdown())
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@main.command()
@click.option('--user-id', '-u', help='Filter by user ID')
@click.option('--include-expired', '-e', is_flag=True, help='Include expired sessions')
def sessions(user_id: Optional[str], include_expired: bool):
    """List Claude sessions."""
    try:
        claude = ClaudeAuthManager()
        
        sessions = claude.list_sessions(
            user_id=user_id,
            include_expired=include_expired
        )
        
        if not sessions:
            click.echo("No sessions found.")
            return
        
        click.echo(f"Found {len(sessions)} session(s):\n")
        
        for session in sessions:
            status_emoji = "✅" if session.status.value == "active" else "❌"
            click.echo(f"{status_emoji} {session.session_id}")
            if session.user_id:
                click.echo(f"   User: {session.user_id}")
            click.echo(f"   Directory: {session.working_directory}")
            click.echo(f"   Created: {session.created_at}")
            click.echo(f"   Cost: ${session.total_cost:.4f}")
            click.echo(f"   Turns: {session.total_turns}")
            click.echo(f"   Status: {session.status.value}")
            if session.is_expired(claude.config.session_timeout_hours):
                click.echo("   ⚠️  Expired")
            click.echo()
            
        asyncio.run(claude.shutdown())
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@main.command()
@click.confirmation_option(prompt='Are you sure you want to cleanup expired sessions?')
def cleanup():
    """Clean up expired sessions."""
    async def _cleanup():
        try:
            claude = ClaudeAuthManager()
            
            count = await claude.cleanup_sessions()
            click.echo(f"Cleaned up {count} expired session(s).")
            
            await claude.shutdown()
            
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            sys.exit(1)
    
    asyncio.run(_cleanup())


@main.command()
@click.option('--output', '-o', type=click.File('w'), default='-', help='Output file (default: stdout)')
@click.option('--pretty', '-p', is_flag=True, help='Pretty print JSON')
def config(output, pretty: bool):
    """Show current configuration as JSON."""
    try:
        claude = ClaudeAuthManager()
        config_dict = claude.get_config()
        
        if pretty:
            json.dump(config_dict, output, indent=2, default=str)
        else:
            json.dump(config_dict, output, default=str)
        
        output.write('\n')
        
        asyncio.run(claude.shutdown())
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@main.command()
def test():
    """Run a simple test to verify the module is working."""
    async def _test():
        try:
            click.echo("🧪 Testing Claude CLI Auth module...\n")
            
            # Initialize
            click.echo("1️⃣  Initializing ClaudeAuthManager...")
            claude = ClaudeAuthManager()
            click.echo("   ✅ Initialized successfully")
            
            # Check health
            click.echo("2️⃣  Checking system health...")
            if claude.is_healthy():
                click.echo("   ✅ System is healthy")
            else:
                click.echo("   ⚠️  System health check failed")
                
            # Test simple query
            click.echo("3️⃣  Testing simple query...")
            response = await claude.query(
                "Say hello briefly",
                timeout=30
            )
            click.echo("   ✅ Query successful")
            click.echo(f"   Response: {response.content[:50]}...")
            if response.cost > 0:
                click.echo(f"   Cost: ${response.cost:.4f}")
            
            # Show final stats
            click.echo("4️⃣  Final statistics:")
            stats = claude.get_stats()
            click.echo(f"   Requests: {stats['total_requests']}")
            click.echo(f"   Success Rate: {stats['success_rate']:.1%}")
            click.echo(f"   Total Cost: ${stats['total_cost']:.4f}")
            
            # Cleanup
            await claude.shutdown()
            
            click.echo("\n🎉 All tests passed!")
            
        except Exception as e:
            click.echo(f"\n❌ Test failed: {str(e)}", err=True)
            sys.exit(1)
    
    asyncio.run(_test())


if __name__ == '__main__':
    main()