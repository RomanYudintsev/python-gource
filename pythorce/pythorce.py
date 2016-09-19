#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import os

import logging
import click

import gettext
import platform


if platform.system().lower() == 'windows':
    import locale
    if os.getenv('LANG') is None:
        lang, enc = locale.getdefaultlocale()
        os.environ['LANG'] = lang
gettext.install(
    'pythorce',
    os.path.join(os.path.dirname(os.path.abspath(".")), 'locale'),
    unicode=True)


@click.group(help=_('''
    Tool for generation gource's log and video from git repositories with submodules.
    '''))
@click.option('--verbose', '-v', is_flag=True, help=_('Verbose log'))
@click.option(
    '--root',
    default=os.path.dirname("."),
    type=click.Path(),
    help=_('Root repository dir'))
@click.help_option('--help', '-h', help=_('Show this message and exit.'))
@click.pass_context
def pythorce(ctx, verbose, root):
    setup_logger(logging.DEBUG if verbose else logging.INFO)
    ctx.obj = {
        'root': root
    }


# commands
@pythorce.command(name="collect-submodules", help=_('''
    ...later...
    '''))
@click.help_option('--help', '-h', help=_('Show this message and exit.'))
@click.pass_obj
def collect_subs(config):
    from scm import collect_subs
    collect_subs(config)


@pythorce.command(name="generator", help=_('''
    ...later...
    '''))
@click.argument('start', nargs=1)
@click.argument('end', default="HEAD")
@click.option('--get-config-to', '-gct', help='...later', default=None)
@click.option('--get-config-from', '-gcf', help='...later', default=None)
@click.help_option('--help', '-h', help=_('Show this message and exit.'))
@click.pass_obj
def generator(config, start, end, get_config_to, get_config_from):
    from scm import generator
    generator(config, start, end, get_config_to, get_config_from)


@pythorce.command(name="history-repos-list", help=_('''
    ...later...
    '''))
@click.argument('start', nargs=1)
@click.argument('end', default="HEAD")
@click.option('--list-dst', '-ld', help=_('file to save info'), default=None)
@click.help_option('--help', '-h', help=_('Show this message and exit.'))
@click.pass_obj
def history_repos_list(config, start, end, list_dst):
    from scm import history_repos_list
    history_repos_list(config, start, end, list_dst)


@pythorce.command(name="create-config", help=_('''
    ...later...
    '''))
@click.option('--config-dst', '-cd', help=_('file to save config'), default=None)
@click.help_option('--help', '-h', help=_('Show this message and exit.'))
@click.pass_obj
def create_config(config, config_dst):
    from scm import create_config
    create_config(config, config_dst)


@pythorce.command(help=_('''
    Print help for specified command.
    '''))
@click.argument('command-name', nargs=1)
@click.help_option('--help', '-h', help=_('Show this message and exit.'))
@click.pass_context
def help(ctx, command_name):
    if command_name in pythorce.commands:
        cmd = pythorce.commands[command_name]
        cmd_ctx = click.Context(cmd, parent=ctx.parent, info_name=command_name)
        print(cmd.get_help(cmd_ctx))
    else:
        raise click.BadParameter(_("No such command '{0}'").format(
            help.params[0].human_readable_name))


def setup_logger(log_level=logging.INFO):
    logging.getLogger().setLevel(logging.DEBUG)

    class ClickStreamHandler(logging.StreamHandler):
        def emit(self, record):
            try:
                click.echo(self.format(record), file=self.stream)
                self.flush()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                self.handleError(record)

    stream_handler = ClickStreamHandler()
    stream_handler.setLevel(log_level)
    logging.getLogger().addHandler(stream_handler)


def main():
    try:
        pythorce()
    except Exception as e:
        print(u"args: {}".format(e.args))
        print(u"message: {}".format(e.message))
        print(u'Operation failed')
        return 1


if __name__ == '__main__':
    sys.exit(main())
