"""Build static HTML site from directory of HTML templates and plain files."""
import pathlib
import json
import os
import sys
from pathlib import Path
from shutil import copytree
import click
import jinja2


def file_not_found(filename):
    """File not found error message."""
    click.echo(f"ERROR: {filename} not found")
    sys.exit(1)


@click.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output directory.')
@click.option('-v', '--verbose', is_flag=True, help='Print more output.')
def main(input_dir, output, verbose):
    """Templated static website generator."""
    # input_dir = hello, output = myout/None
    input_dir = pathlib.Path(input_dir)
    output_dir = input_dir/"html"
    static_dir = input_dir/"static"
    json_file = input_dir/"config.json"

    # check output option
    if output:
        output_dir = Path(output)

    try:
        data = json.load(json_file.open('r'))
    # ERROR: json exception
    except FileNotFoundError:
        file_not_found("json file")

    except json.JSONDecodeError:
        click.echo("ERROR: JSONDecodeError exception")
        sys.exit(2)

    # copy static if exists
    if os.path.exists(static_dir):
        copytree(str(static_dir), str(output_dir), dirs_exist_ok=True)
        if verbose:
            click.echo(f"Copied {static_dir} -> {output_dir}")

    # loop through json
    for elmt in data:
        url = elmt["url"].lstrip("/")
        tplt = elmt["template"]

        # ERROR: templates file not found
        if not os.path.exists(input_dir/"templates"):
            file_not_found("templates")

        template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(input_dir/"templates")),
            autoescape=jinja2.select_autoescape(['html']),
        )

        try:
            template = template_env.get_template(tplt)
            output_html = template.render(elmt["context"])
        except jinja2.exceptions.TemplateNotFound:
            click.echo("ERROR: TemplateNotFound jinja exception")
            sys.exit(2)

        output_path = output_dir/url/"index.html"

        # ERROR: output directory already exists
        if os.path.exists(output_path):
            click.echo("ERROR: output directory already exists")
            sys.exit(3)

        try:
            output_path.parent.mkdir(exist_ok=True, parents=True)
            output_path.open('w').write(output_html)
        except FileNotFoundError:
            file_not_found("output file")

        # check verbose option
        if verbose:
            click.echo(f"Rendered {tplt} -> {output_path}")


if __name__ == "__main__":
    main()
