#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import os

import logging
import click

import gettext
import platform

import scm


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

@pythorce.command(name="show", help=_('''
    ...later...
    '''))
@click.option('--start-rev', '-sr', nargs=1)
@click.option('--end-rev', '-er', default="HEAD")
@click.option('--dumped-authors', '-da', help='...later', default=None)
@click.option('--dumped-submodules', '-ds', help='...later', default=None)
@click.option('--dumped-log', '-dl', help='...later', default=None)
@click.option('--dumped-config', '-dc', help='...later', default=None)
@click.help_option('--help', '-h', help=_('Show this message and exit.'))
@click.pass_obj
def show(config, start_rev, end_rev, dumped_authors, dumped_submodules, dumped_log, dumped_config):
    scm.show(config, start_rev, end_rev, dumped_authors, dumped_submodules, dumped_log, dumped_config)


@pythorce.command(name="dump-video", help=_('''
    ...later...
    '''))
@click.option('--dumped-config', '-dc', help='...later', default=None)
@click.option('--video-name', '-vn', help='...later', default=None)
@click.option('--dumped-ffmpeg-config', '-dfc', help='...later', default=None)
@click.help_option('--help', '-h', help=_('Show this message and exit.'))
@click.pass_obj
def dump_video(config, dumped_config, video_name, dumped_ffmpeg_config):
    scm.dump_video(dumped_config, video_name, dumped_ffmpeg_config)


@pythorce.command(name="dump-log", help=_('''
    ...later...
    '''))
@click.argument('start', nargs=1)
@click.argument('end', default="HEAD")
@click.option('--dumped-authors', '-da', help='...later', default=None)
@click.option('--dumped-submodules', '-ds', help='...later', default=None)
@click.option('--dumped-log', '-dl', help='...later', default=None)
@click.help_option('--help', '-h', help=_('Show this message and exit.'))
@click.pass_obj
def dump_log(config, start, end, dumped_authors, dumped_submodules, dumped_log):
    scm.dump_log(config, start, end, dumped_authors, dumped_submodules, dumped_log)


@pythorce.command(name="history-repos-list", help=_('''
    ...later...
    '''))
@click.option('--start-rev', '-sr')
@click.option('--end-rev', '-er', default="HEAD")
@click.option('--list-dst', '-ld', help=_('file to save info'), default=None)
@click.help_option('--help', '-h', help=_('Show this message and exit.'))
@click.pass_obj
def history_repos_list(config, start_rev, end_rev, list_dst):
    scm.history_repos_list(config, start_rev, end_rev, list_dst)


@pythorce.command(name="dump-submodules", help=_('''
    Collect all submodules in repo, and write in file(--config-dst || -cd) or print part configs: allinclusive
    '''))
@click.option('--dumped-submodules', '-ds', default=None,
              help=_('file to save allinclusive'))
@click.help_option('--help', '-h', help=_('Show this message and exit.'))
@click.pass_obj
def dump_submodules(config, dumped_submodules):
    scm.dump_submodules(config, dumped_submodules)


@pythorce.command(name="dump-authors", help=_('''
    Collect all authors commit in all repos (or from file after command collect_submodules)
    '''))
@click.argument('start', nargs=1)
@click.argument('end', default="HEAD")
@click.option('--dumped-authors', '-da', help=_('file to save authors list'), default=None)
@click.option('--dumped-submodules', '-ds', help=_('dumped submodules'), default=None)
@click.help_option('--help', '-h', help=_('Show this message and exit.'))
@click.pass_obj
def dump_authors(config, dumped_authors, dumped_submodules, start, end):
    scm.dump_authors(config, dumped_authors, dumped_submodules, start, end)


@pythorce.command(name="dump-gource-config", help=_('''
    defautl config for gource
    '''))
def dump_gource_config():
    scm.dump_gource_config()


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

    # class ClickStreamHandler(logging.StreamHandler):
    #     def emit(self, record):
    #         try:
    #             click.echo(self.format(record), file=self.stream)
    #             self.flush()
    #         except (KeyboardInterrupt, SystemExit):
    #             raise
    #         except:
    #             self.handleError(record)
    #
    # stream_handler = ClickStreamHandler()
    # stream_handler.setLevel(log_level)
    # logging.getLogger().addHandler(stream_handler)


def main():
    # try:

    pythorce()
    # except Exception as e:
    #     print(u"args: {}".format(e.args))
    #     print(u"message: {}".format(e.message))
    #     print(u'Operation failed')
    #     return 1


if __name__ == '__main__':
    sys.exit(main())
