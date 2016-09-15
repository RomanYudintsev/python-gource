#!/usr/bin/env python
from __future__ import print_function

import git
import time
import codecs


class CommitInfo(object):
    def __init__(self, commit, pre_path):
        self.author = commit.author.name
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
                                     timestamp=commit.authored_date, author=commit.author, pre_path=pre_path))


def generator(config, start_rev, end_rev):
    root_repo = git.Repo(config["root"])
    start = root_repo.git.rev_parse(start_rev)
    end = root_repo.git.rev_parse(end_rev)
    # print(start, end, root_repo)
    repo_logs_info = [{"start": start, "end": end, "path": "", "repo": root_repo}]
    repo_walker(root_repo, start, end, "", repo_logs_info)
    commits = []
    collect_commits(repo_logs_info, commits)
    commits.sort(key=lambda commit: commit.timestamp)
    full_log = u""
    for commit in commits:
        for log in commit.logs:
            full_log += u"{}".format(log)
    with codecs.open("gc.test.log", 'w', encoding='utf-8') as fl:
        fl.write(full_log)
        fl.close()


def history_repos_list(config, start_rev, end_rev, list_dst):
    root_repo = git.Repo(config["root"])
    start = root_repo.git.rev_parse(start_rev)
    end = root_repo.git.rev_parse(end_rev)
    repo_logs_info = [{"start": start, "end": end, "path": "", "repo": root_repo}]
    repo_walker(root_repo, start, end, "", repo_logs_info)
    full_info_str = ""
    for info in repo_logs_info:
        full_info_str += u"{start} {end} {repo_path}\r\n".format(repo_path=info["path"], start=info["start"], end=info["end"])
    if list_dst:
        with codecs.open(list_dst, 'w', encoding='utf-8') as fl:
            fl.write(full_info_str)
            fl.close()
    else:
        print(full_info_str)


def repo_walker(repo, start, end, start_path, repo_logs_info):
    for sub in repo.submodules:
        start_sub, end_sub = get_log_range(repo, sub.path, start, end)
        path = u"{0}/{1}".format(start_path, sub.path)
        repo_logs_info.append({"start": start_sub, "end": end_sub, "path": path, "repo": sub.module()})
        repo_walker(sub.module(), start_sub, end_sub, path, repo_logs_info)


def get_log_range(repo, path, start, end):
    start_sub = repo.git.ls_tree(start, path).split(" ")[2].split("\t")[0]
    end_sub = repo.git.ls_tree(end, path).split(" ")[2].split("\t")[0]
    return start_sub, end_sub


def collect_commits(repo_logs_info, commits):
    for info in repo_logs_info:
        tmp_commits = list(info["repo"].iter_commits('{0}..{1}'.format(info["start"], info["end"])))
        commits.extend([CommitInfo(commit, info["path"]) for commit in tmp_commits])
