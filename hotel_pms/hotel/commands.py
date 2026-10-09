"""
hotel_pms.hotel.commands
~~~~~~~~~~~~~~~~~~~~~~~~
bench CLI commands for Hotel PMS.

Usage:
    bench --site <site> hotel-seed-data
    bench --site <site> hotel-reset-data
"""
import click
from frappe.commands import pass_context


@click.command("hotel-seed-data")
@pass_context
def seed_data(context):
    """Create Hotel PMS demo/test data (rooms, customers, reservations)."""
    import frappe

    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if not site:
        click.echo("Error: no site specified. Use bench --site <site> hotel-seed-data")
        return

    frappe.init(site=site)
    frappe.connect()

    try:
        from hotel_pms.setup.seed_demo_data import seed
        result = seed()
        for line in (result or {}).get("log", []):
            click.echo(line)
        click.echo("✓ Hotel PMS test data created.")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise
    finally:
        frappe.destroy()


@click.command("hotel-reset-data")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@pass_context
def reset_data(context, yes):
    """Delete all Hotel PMS test data, then recreate it."""
    import frappe

    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if not site:
        click.echo("Error: no site specified.")
        return

    if not yes:
        click.confirm(
            "This will DELETE all test data and recreate it. Continue?",
            abort=True,
        )

    frappe.init(site=site)
    frappe.connect()

    try:
        from hotel_pms.setup.seed_demo_data import delete_test_data, seed

        click.echo("Deleting existing test data…")
        result = delete_test_data()
        for line in (result or {}).get("log", []):
            click.echo("  " + line)

        click.echo("Creating fresh test data…")
        result = seed()
        for line in (result or {}).get("log", []):
            click.echo("  " + line)

        click.echo("✓ Hotel PMS test data reset complete.")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise
    finally:
        frappe.destroy()


commands = [seed_data, reset_data]
