#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

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


def generator(config, start_rev, end_rev, get_config_to=None, get_config_from=None):
    if get_config_from is None:
        config_content = None
    else:
        with codecs.open(get_config_from, 'r', encoding="utf-8") as get_config:
            config_content = yaml.safe_load(get_config)

    def get_author_name(email, def_name):
        if config_content is None:
            return def_name
        new_name = config_content["authors"][email][0]
        try:
            new_name = get_author_name(new_name, def_name)
        except Exception:
            pass
        return new_name

    def is_includes_repo(repo):
        if config_content is None:
            return True
        if repo.name in config_content["submodules"]["excludes"]:
            return False
        if repo.name in config_content["submodules"]["includes"]:
            return True
        return len(config_content["submodules"]["includes"]) == 0

    root_repo = git.Repo(config["root"])
    start = root_repo.git.rev_parse(start_rev)
    end = root_repo.git.rev_parse(end_rev)
    # print(start, end, root_repo)
    repo_logs_info = [{"start": start, "end": end, "path": "", "repo": root_repo}]
    repo_walker(root_repo, start, end, "", repo_logs_info, is_includes_repo)
    commits = []
    collect_commits(repo_logs_info, commits, get_author_name)
    commits.sort(key=lambda commit: commit.timestamp)
    full_log = u""
    authors = {}
    for commit in commits:
        if authors.get(commit.email, None) is None:
            authors[commit.email] = []

        if commit.author not in authors[commit.email]:
            authors[commit.email].append(commit.author)
        if not get_config_to:
            for log in commit.logs:
                full_log += u"{}".format(log)
    if not get_config_to:
        with codecs.open("gc.test.log", 'w', encoding='utf-8') as fl:
            fl.write(full_log)
            fl.close()
    else:
        create_config(config, get_config_to, authors)


def history_repos_list(config, start_rev, end_rev, list_dst):
    root_repo = git.Repo(config["root"])
    start = root_repo.git.rev_parse(start_rev)
    end = root_repo.git.rev_parse(end_rev)
    repo_logs_info = [{"start": start, "end": end, "path": "", "repo": root_repo}]
    repo_walker(root_repo, start, end, "", repo_logs_info, lambda repo: True)
    full_info_str = ""
    for info in repo_logs_info:
        full_info_str += u"{start} {end} {repo_path}\r\n".format(repo_path=info["path"], start=info["start"], end=info["end"])
    if list_dst:
        with codecs.open(list_dst, 'w', encoding='utf-8') as fl:
            fl.write(full_info_str)
            fl.close()
    else:
        print(full_info_str)


def collect_subs(config):
    root_repo = git.Repo(config["root"])
    subs = [sub.name for sub in root_repo.iter_submodules()]
    return subs


def create_config(config, config_dst, authors=None):
    def unicode_representer(dumper, uni):
        node = yaml.ScalarNode(tag=u'tag:yaml.org,2002:str', value=u"{}".format(uni))
        return node
    yaml.add_representer(unicode, unicode_representer)

    new_config = {"submodules": {"excludes": [], "includes": collect_subs(config)}, "authors": authors}
    if config_dst:
        with codecs.open(config_dst, 'w', encoding='utf-8') as cd:
            yaml.dump(new_config, cd, default_flow_style=False, allow_unicode=True)
    else:
        print(yaml.dump(new_config, default_flow_style=False))


def repo_walker(repo, start, end, start_path, repo_logs_info, is_includes_repo):
    for sub in repo.submodules:
        if not is_includes_repo(sub):
            return
        path = u"{0}/{1}".format(start_path, sub.path)
        start_sub, end_sub = get_log_range(repo, sub.path, start, end)
        repo_logs_info.append({"start": start_sub, "end": end_sub, "path": path, "repo": sub.module()})
        repo_walker(sub.module(), start_sub, end_sub, path, repo_logs_info, is_includes_repo)


def get_log_range(repo, path, start, end):
    start_sub = repo.git.ls_tree(start, path).split(" ")[2].split("\t")[0]
    end_sub = repo.git.ls_tree(end, path).split(" ")[2].split("\t")[0]
    return start_sub, end_sub


def collect_commits(repo_logs_info, commits, get_author_name):
    for info in repo_logs_info:
        tmp_commits = list(info["repo"].iter_commits('{0}..{1}'.format(info["start"], info["end"])))
        commits.extend([CommitInfo(commit, info["path"], get_author_name) for commit in tmp_commits])
