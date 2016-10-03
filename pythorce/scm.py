#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import git
import time
import codecs
import yaml


class CommitInfo(object):
    def __init__(self, commit, pre_path, get_author_name):
        self.author = commit.author.name
        self.email = str(commit.author.email).lower()
        self.logs = []
        self.timestamp = commit.authored_date
        self.repo = commit.repo
        self.date = time.strftime(
            '%d %b %Y %H:%M',
            time.gmtime(commit.authored_date - commit.author_tz_offset))
        text = commit.repo.git.diff_tree(commit.hexsha, '--', root=True, name_status=True, r=True)
        for line in text.splitlines()[1:]:
            (change_type, file_path) = line.split("\t")
            self.logs.append(u"{timestamp}|{author}|{change_type}|{pre_path}/{file_path}\r\n"
                             .format(change_type=change_type, file_path=file_path,
                                     timestamp=commit.authored_date,
                                     author=get_author_name(self.email, commit.author.name), pre_path=pre_path))


def get_default_files_path(part_name):
    return os.path.join(".pythorce", "tmp_{}.dump".format(part_name))


def dump_log(config, start_rev, end_rev, dumped_authors, dumped_submodules, dumped_log):
    if dumped_submodules is None:
        dumped_submodules = get_default_files_path("submodules")
        dump_submodules(config, dumped_submodules)

    with codecs.open(check_files(dumped_submodules), 'r', encoding='utf-8') as ss:
        submodules_content = yaml.safe_load(ss)

    if dumped_authors is None:
        authors_content = None
    else:
        with codecs.open(check_files(dumped_authors), 'r', encoding='utf-8') as authors:
            authors_content = yaml.safe_load(authors)

    def get_author_name(email, def_name):
        if authors_content is None or authors_content["authors"].get(email, None) is None:
            return def_name
        new_name = authors_content["authors"][email][0]
        try:
            new_name = authors_content(new_name, def_name)
        except Exception:
            pass
        return new_name

    def is_includes_repo(repo):
        if submodules_content is None:
            return True
        if repo.name in submodules_content["submodules"]["excludes"]:
            return False
        if repo.name in submodules_content["submodules"]["includes"]:
            return True
        return len(submodules_content["submodules"]["includes"]) == 0

    commits = collect_commits(git.Repo(config["root"]), start_rev, end_rev, get_author_name, is_includes_repo)
    full_log = u""
    authors = {}
    for commit in commits:
        if dumped_authors is None:
            collect_authors(commit, authors)
        for log in commit.logs:
            full_log += u"{}".format(log)
    if dumped_authors is None:
        dump_authors_(dumped_authors, authors)

    if not dumped_log:
        print(full_log)
        dumped_log = get_default_files_path("log")

    with codecs.open(check_files(dumped_log), 'w', encoding='utf-8') as fl:
        fl.write(full_log)
        fl.close()


def history_repos_list(config, start_rev, end_rev, list_dst):
    root_repo = git.Repo(config["root"])
    start = root_repo.git.rev_parse(start_rev) or get_first_commit(root_repo)
    end = root_repo.git.rev_parse(end_rev or "HEAD")
    repo_logs_info = [{"start": start, "end": end, "path": "", "repo": root_repo}]
    repo_walker(root_repo, start, end, "", repo_logs_info, lambda repo: True)
    full_info_str = ""
    print(repo_logs_info)
    for info in repo_logs_info:
        full_info_str += u"{start} {end} {repo_path}\r\n".format(repo_path=info["path"], start=info["start"], end=info["end"])
    if list_dst:
        with codecs.open(check_files(list_dst), 'w', encoding='utf-8') as fl:
            fl.write(full_info_str)
            fl.close()
    else:
        print(full_info_str)


def collect_subs(config):
    root_repo = git.Repo(config["root"])
    subs = [sub.name for sub in root_repo.iter_submodules()]
    return subs


def check_files(full_path):
    if not os.path.exists(os.path.dirname(full_path)):
        os.mkdir(os.path.basename(os.path.dirname(full_path)))
    return full_path


def dump_submodules(config, dumped_submodules):
    def unicode_representer(dumper, uni):
        node = yaml.ScalarNode(tag=u'tag:yaml.org,2002:str', value=u"{}".format(uni))
        return node
    yaml.add_representer(unicode, unicode_representer)

    new_config = {"submodules": {"excludes": [], "includes": collect_subs(config)}}
    if dumped_submodules:
        with codecs.open(check_files(dumped_submodules), 'w', encoding='utf-8') as cd:
            yaml.dump(new_config, cd, default_flow_style=False, allow_unicode=True)
    else:
        print(yaml.dump(new_config, default_flow_style=False))


def dump_authors(config, dumped_authors, dumped_submodules, start_rev, end_rev):
    def unicode_representer(dumper, uni):
        node = yaml.ScalarNode(tag=u'tag:yaml.org,2002:str', value=u"{}".format(uni))
        return node
    yaml.add_representer(unicode, unicode_representer)

    if dumped_submodules is None:
        dumped_submodules = get_default_files_path("submodules")
        dump_submodules(config, dumped_submodules)

    with codecs.open(check_files(dumped_submodules), 'r', encoding='utf-8') as dumped_subs:
        subs = yaml.safe_load(dumped_subs)
        dumped_subs.close()

    def is_includes_repo(repo):
        if subs is None:
            return True
        if repo.name in subs["submodules"]["excludes"]:
            return False
        if repo.name in subs["submodules"]["includes"]:
            return True
        return len(subs["submodules"]["includes"]) == 0

    def get_author_name(email, def_name):
        return def_name

    commits = collect_commits(git.Repo(config["root"]), start_rev, end_rev, get_author_name, is_includes_repo)
    authors = {}
    for commit in commits:
        collect_authors(commit, authors)

    dump_authors_(dumped_authors, authors)


def collect_authors(commit, authors):
    if authors.get(commit.email, None) is None:
        authors[commit.email] = []

    if commit.author not in authors[commit.email]:
        authors[commit.email].append(commit.author)


def dump_authors_(dumped_authors, authors):
    new_config = {"authors": authors}
    if not dumped_authors:
        print(yaml.dump(new_config, default_flow_style=False))
        dumped_authors = get_default_files_path("authors")

    with codecs.open(check_files(dumped_authors), 'w', encoding='utf-8') as da:
        yaml.dump(new_config, da, default_flow_style=False, allow_unicode=True)


def repo_walker(repo, start, end, start_path, repo_logs_info, is_includes_repo):
    for sub in repo.submodules:
        if not is_includes_repo(sub):
            continue
        path = u"{0}/{1}".format(start_path, sub.path)
        start_sub, end_sub = get_log_range(repo, sub, start, end)
        repo_logs_info.append({"start": start_sub, "end": end_sub, "path": path, "repo": sub.module()})
        repo_walker(sub.module(), start_sub, end_sub, path, repo_logs_info, is_includes_repo)


def get_log_range(repo, sub, start, end):
    try:
        ls_tree = repo.git.ls_tree(start, sub.path).split(" ")
    except git.exc.GitCommandError:
        ls_tree = [u""]
        pass
    if ls_tree != [u""]:
        start_sub = ls_tree[2].split("\t")[0]
    else:
        start_sub = get_first_commit(sub.module())
    ls_tree = repo.git.ls_tree(end, sub.path).split(" ")
    if ls_tree != [u""]:
        end_sub = ls_tree[2].split("\t")[0]
    else:
        end_sub = sub.module().rev_parse("HEAD")
    return start_sub, end_sub


def get_first_commit(repo):
    # rev-list --max-parents=0 HEAD
    return repo.git.rev_list("HEAD", "-1", max_parents=0)


def collect_commits(root_repo, start_rev, end_rev, get_author_name, is_includes_repo):
    start = root_repo.git.rev_parse(start_rev)
    end = root_repo.git.rev_parse(end_rev)
    repo_logs_info = [{"start": start, "end": end, "path": os.path.basename(root_repo.working_dir), "repo": root_repo}]
    repo_walker(root_repo, start, end, repo_logs_info[0]["path"], repo_logs_info, is_includes_repo)
    commits = []
    for info in repo_logs_info:
        tmp_commits = list(info["repo"].iter_commits('{0}..{1}'.format(info["start"], info["end"])))
        commits.extend([CommitInfo(commit, info["path"], get_author_name) for commit in tmp_commits])
    commits.sort(key=lambda commit: commit.timestamp)
    return commits


def show(config, start_rev, end_rev, dumped_authors, dumped_submodules, dumped_log, dumped_config):
    if dumped_config is None:
        if dumped_log is None:
            dump_log(config, start_rev, end_rev, dumped_authors, dumped_submodules, dumped_log)
            dumped_log = get_default_files_path("log")
        dumped_config = get_default_files_path("gource_config")
        dump_gource_config(dumped_config, dumped_log)
    os.system('gource --load-config {config}'.format(config=dumped_config))


def dump_video(dumped_config, video_name=None, dumped_ffmpeg_config=None, with_audio=None):
    ppm_file = get_default_files_path("ppm")
    video_file = get_default_files_path("video") if video_name is None else video_name
    os.system('gource --load-config {config} --output-ppm-stream {ppm_file}'
              .format(config=dumped_config, ppm_file=ppm_file))
    if dumped_ffmpeg_config is None:
        dumped_ffmpeg_config = get_default_files_path("ffmpeg_config")
        dump_ffmpeg_config(dumped_ffmpeg_config, ppm_file, video_file)

    with open(check_files(dumped_ffmpeg_config)) as ffmeg_config:
        command = u'ffmpeg {audio}{config}'.format(config=ffmeg_config.read(), audio=(with_audio+' ') if with_audio is not None else "")
        print("full command:: ", command)
        os.system(command)


def dump_gource_config(gource_config, dumped_log):
    g_config = open(check_files(gource_config), 'w')
    g_config.write('[gource]\n')
    g_config.write('  path={log}\n'.format(log=dumped_log))
    g_config.write('  seconds-per-day=0.5\n')
    g_config.write('  file-idle-time=0.01\n')
    g_config.write('  auto-skip-seconds=1\n')
    g_config.write('  viewport=1920x1280\n')
    g_config.write('  font-size=10\n')
    g_config.write('  title="change me in .python/tmp_gource_config.dump"\n')
    g_config.write('  hide=filenames,dirnames,\n')
    g_config.close()


def dump_ffmpeg_config(ffmped_config, ppm_file, video_file):
    g_config = open(check_files(ffmped_config), 'w')
    g_config.write('-y -r 60 -f image2pipe -vcodec ppm -i {ppm_file} -vcodec libx264 -preset ultrafast '
                   '-pix_fmt yuv420p -crf 1 -threads 0 -bf 0 {video_file}.avi'
                   .format(ppm_file=ppm_file, video_file=video_file))
    g_config.close()
