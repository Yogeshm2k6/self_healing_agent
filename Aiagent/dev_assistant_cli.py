import click

@click.group()
def cli():
    pass

@cli.command()
def run():
    # Run the dev assistant
    dev_assistant = DevAssistant()
    dev_assistant.run()

if __name__ == "__main__":
    cli()
