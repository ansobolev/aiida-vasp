"""Commandline util for dealing with potcar files"""
import click
from aiida.cmdline.commands import data_cmd

from aiida_vasp.utils.aiida_utils import get_data_class


@data_cmd.group('vasp-potcar')
def potcar():
    """Top level command for handling VASP POTCAR files."""


def try_grab_description(ctx, param, value):
    """
    Try to get the description from an existing group if it's not given.

    This is a click parameter callback.
    """
    potcar_data_cls = get_data_class('vasp.potcar')
    group_name = ctx.params['name']
    existing_groups = potcar_data_cls.get_potcar_groups()
    existing_group_names = [group.name for group in existing_groups]
    if not value:
        if group_name in existing_group_names:
            return potcar_data_cls.get_potcar_group(group_name).description
        else:
            raise click.MissingParameter('A new group must be given a description.', param=param)
    return value


@potcar.command()
@click.option('--path', default='.', type=click.Path(exists=True), help='Path to a folder or archive containing the POTCAR files')
@click.option('--name', required=True, help='The name of the family')
@click.option('--desc', help='A description for the family', callback=try_grab_description)
@click.option('--stop-if-existing', is_flag=True, help='Abort when encountering a previously uploaded POTCAR file')
def uploadfamily(path, name, desc, stop_if_existing):
    """Upload a family of VASP potcar files."""

    potcar_data_cls = get_data_class('vasp.potcar')
    num_found, num_uploaded = potcar_data_cls.upload_potcar_family(path, name, desc, stop_if_existing=stop_if_existing)

    click.echo('POTCAR files found: {}. New files uploaded: {}'.format(num_found, num_uploaded))
