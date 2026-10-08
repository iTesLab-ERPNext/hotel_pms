"""
hotel_pms.commands
~~~~~~~~~~~~~~~~~~
CLI commands available via 'bench hotel-demo <subcommand>'.
Mirrors the erpnext_lmd/commands.py pattern with a click group.

Usage:
    bench hotel-demo seed     # Insert demo rooms, customers, reservations
    bench hotel-demo status   # Show counts of Hotel PMS records
    bench hotel-demo remove   # Delete all demo data
"""
import click


def _connect(context):
    """Initialise a Frappe site context from the bench CLI context."""
    import frappe
    site = context.obj.get("sites", [None])[0]
    if not site:
        raise click.ClickException("Pass --site <site>")
    frappe.init(site=site)
    frappe.connect()
    return frappe


@click.group("hotel-demo")
def hotel_demo():
    """Hotel PMS demo-data commands."""


@hotel_demo.command("seed")
@click.pass_context
def seed(ctx):
    """Seed demo rooms, customers, and reservations."""
    frappe = _connect(ctx)
    try:
        from hotel_pms.demo.hotel import seed_demo_data
        result = seed_demo_data()
        click.echo("✓ Demo data seeded")
        for key, val in result.items():
            click.echo(f"  {key}: {val}")
    finally:
        frappe.destroy()


@hotel_demo.command("status")
@click.pass_context
def status(ctx):
    """Show record counts for all Hotel PMS DocTypes."""
    frappe = _connect(ctx)
    try:
        doctypes = [
            "Hotel Room", "Hotel Customer", "Hotel Reservation",
            "Hotel Stay", "Hotel Folio", "Hotel Payment", "Hotel Housekeeping",
        ]
        click.echo("Hotel PMS record counts:")
        for dt in doctypes:
            try:
                count = frappe.db.count(dt)
            except Exception:
                count = "—"
            click.echo(f"  {dt:<30} {count}")
    finally:
        frappe.destroy()


@hotel_demo.command("remove")
@click.pass_context
@click.confirmation_option(prompt="This will delete ALL Hotel PMS records. Continue?")
def remove(ctx):
    """Delete all Hotel PMS demo data."""
    frappe = _connect(ctx)
    try:
        from hotel_pms.demo.hotel import remove_demo_data
        remove_demo_data()
        click.echo("✓ Demo data removed")
    finally:
        frappe.destroy()


commands = [hotel_demo]
