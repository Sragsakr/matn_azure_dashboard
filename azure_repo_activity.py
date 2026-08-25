"""Read-only Azure Repos activity collection and normalization."""

from __future__ import annotations

import base64
from collections import defaultdict
from urllib.parse import quote

import requests

API_VERSION = "7.1"
PAGE_SIZE = 100
REQUEST_TIMEOUT = 30


def _identity(value):
    value = value or {}
    return (
        value.get("displayName") or value.get("name") or "Unknown",
        value.get("uniqueName") or value.get("email") or "",
    )


def _web_link(value):
    return value.get("_links", {}).get("web", {}).get("href", "")


def _branch_name(ref_name):
    return str(ref_name or "").removeprefix("refs/heads/")


def _reviewers(values):
    reviewers = []
    for reviewer in values or []:
        name, _ = _identity(reviewer)
        reviewers.append(f"{name} ({reviewer.get('vote', 0):+d})")
    return ", ".join(reviewers)


class AzureRepoActivityClient:
    """Collect complete Git metadata from one Azure DevOps project."""

    def __init__(self, organization, project, pat, session=None):
        token = base64.b64encode(f":{pat}".encode()).decode()
        self.base_url = (
            f"https://dev.azure.com/{quote(organization, safe='')}/"
            f"{quote(project, safe='')}/_apis"
        )
        self.headers = {"Authorization": f"Basic {token}"}
        self.session = session or requests.Session()

    def _get(self, path, params=None):
        query = dict(params or {})
        query["api-version"] = API_VERSION
        response = self.session.get(
            f"{self.base_url}/{path.lstrip('/')}",
            headers=self.headers,
            params=query,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def value_pages(self, path, params=None):
        """Read a `$top`/`$skip` Azure collection until the final short page."""
        rows = []
        skip = 0
        while True:
            query = dict(params or {})
            query.update({"$top": PAGE_SIZE, "$skip": skip})
            page = self._get(path, query).get("value", [])
            rows.extend(page)
            if len(page) < PAGE_SIZE:
                return rows
            skip += len(page)

    def change_pages(self, repository_id, commit_id):
        rows = []
        skip = 0
        path = f"git/repositories/{quote(repository_id, safe='')}/commits/{commit_id}/changes"
        while True:
            page = self._get(path, {"top": PAGE_SIZE, "skip": skip}).get("changes", [])
            rows.extend(page)
            if len(page) < PAGE_SIZE:
                return rows
            skip += len(page)

    def fetch_all(self):
        repositories = self.value_pages("git/repositories")
        dataset = {
            "repositories": [_repository_row(repo) for repo in repositories],
            "commits": [], "pushes": [], "pull_requests": [],
            "changes": [], "failures": [],
        }
        for repository in repositories:
            activity = self._repository_activity(repository)
            for key in dataset:
                if key != "repositories":
                    dataset[key].extend(activity[key])
        return dataset

    def _repository_activity(self, repository):
        repo_id = repository["id"]
        repo_name = repository.get("name") or repo_id
        collections, failures = self._repository_collections(repository)
        changes, change_failures = self._repository_changes(
            repository, collections["commits"]
        )
        return {
            "commits": [_commit_row(repo_id, repo_name, row) for row in collections["commits"]],
            "pushes": [_push_row(repo_id, repo_name, row) for row in collections["pushes"]],
            "pull_requests": [
                _pull_request_row(repo_id, repo_name, row)
                for row in collections["pull_requests"]
            ],
            "changes": changes,
            "failures": failures + change_failures,
        }

    def _repository_collections(self, repository):
        commits, commit_failures = self._safe_repo_pages(repository, "commits")
        pushes, push_failures = self._safe_repo_pages(repository, "pushes", {
            "searchCriteria.includeRefUpdates": "true",
        })
        pull_requests, pr_failures = self._safe_repo_pages(repository, "pullrequests", {
            "searchCriteria.status": "all",
        })
        return {
            "commits": commits, "pushes": pushes, "pull_requests": pull_requests,
        }, commit_failures + push_failures + pr_failures

    def _repository_changes(self, repository, commits):
        rows = []
        failures = []
        for commit in commits:
            commit_rows, commit_failures = self._commit_changes(repository, commit)
            rows.extend(commit_rows)
            failures.extend(commit_failures)
        return rows, failures

    def _safe_repo_pages(self, repository, endpoint, params=None):
        repo_id = repository["id"]
        repo_name = repository.get("name") or repo_id
        path = f"git/repositories/{quote(repo_id, safe='')}/{endpoint}"
        try:
            return self.value_pages(path, params), []
        except requests.RequestException as exc:
            return [], [_failure_row(repo_name, endpoint, exc)]

    def _commit_changes(self, repository, commit):
        repo_id = repository["id"]
        repo_name = repository.get("name") or repo_id
        commit_id = commit.get("commitId", "")
        try:
            changes = self.change_pages(repo_id, commit_id)
        except requests.RequestException as exc:
            failure = _failure_row(repo_name, f"commit {commit_id} changes", exc)
            return [], [failure]
        rows = [
            _change_row(repo_id, repo_name, commit, change, index)
            for index, change in enumerate(changes, start=1)
        ]
        return rows, []


def _repository_row(repository):
    return {
        "Repository ID": repository.get("id"),
        "Repository": repository.get("name"),
        "Default Branch": _branch_name(repository.get("defaultBranch")),
        "Size (bytes)": repository.get("size"),
        "Disabled": bool(repository.get("isDisabled")),
        "Remote URL": repository.get("remoteUrl", ""),
        "Azure Link": repository.get("webUrl") or _web_link(repository),
    }


def _commit_row(repo_id, repo_name, commit):
    author, author_email = _identity(commit.get("author"))
    committer, committer_email = _identity(commit.get("committer"))
    return {
        "Repository ID": repo_id, "Repository": repo_name,
        "Commit ID": commit.get("commitId"), "Short ID": str(commit.get("commitId", ""))[:8],
        "Message": commit.get("comment", ""), "Author": author, "Author Email": author_email,
        "Author Date": commit.get("author", {}).get("date"), "Committer": committer,
        "Committer Email": committer_email, "Commit Date": commit.get("committer", {}).get("date"),
        "Change Counts": ", ".join(f"{key}: {value}" for key, value in (commit.get("changeCounts") or {}).items()),
        "Azure Link": _web_link(commit),
    }


def _push_row(repo_id, repo_name, push):
    pusher, pusher_email = _identity(push.get("pushedBy"))
    return {
        "Repository ID": repo_id, "Repository": repo_name, "Push ID": push.get("pushId"),
        "Pushed By": pusher, "Pusher Email": pusher_email, "Push Date": push.get("date"),
        "Commits": len(push.get("commits") or []),
        "Branches": ", ".join(_branch_name(ref.get("name")) for ref in push.get("refUpdates") or []),
        "Azure Link": _web_link(push),
    }


def _pull_request_row(repo_id, repo_name, pull_request):
    creator, creator_email = _identity(pull_request.get("createdBy"))
    merge_commit = pull_request.get("lastMergeCommit") or {}
    return {
        "Repository ID": repo_id, "Repository": repo_name,
        "PR ID": pull_request.get("pullRequestId"), "Title": pull_request.get("title", ""),
        "Description": pull_request.get("description", ""), "Status": pull_request.get("status", ""),
        "Draft": bool(pull_request.get("isDraft")), "Created By": creator, "Creator Email": creator_email,
        "Created Date": pull_request.get("creationDate"), "Closed Date": pull_request.get("closedDate"),
        "Source Branch": _branch_name(pull_request.get("sourceRefName")),
        "Target Branch": _branch_name(pull_request.get("targetRefName")),
        "Reviewers": _reviewers(pull_request.get("reviewers")),
        "Merge Status": pull_request.get("mergeStatus", ""),
        "Merge Commit": merge_commit.get("commitId", ""), "Azure Link": _web_link(pull_request),
    }


def _change_row(repo_id, repo_name, commit, change, index):
    item = change.get("item") or {}
    author, author_email = _identity(commit.get("author"))
    return {
        "Repository ID": repo_id, "Repository": repo_name,
        "Commit ID": commit.get("commitId"), "Change #": index,
        "Change Type": change.get("changeType", ""), "Path": item.get("path", ""),
        "Original Path": change.get("originalPath", ""), "Git Object Type": item.get("gitObjectType", ""),
        "Object ID": item.get("objectId", ""), "Author": author, "Author Email": author_email,
        "Author Date": commit.get("author", {}).get("date"), "Message": commit.get("comment", ""),
        "Azure Link": _web_link(commit),
    }


def _failure_row(repository, operation, exception):
    return {"Repository": repository, "Operation": operation, "Error": str(exception)}


def _contributor_row(email, summary):
    return {
        "Contributor": summary["name"], "Email": email,
        "Repositories": ", ".join(sorted(filter(None, summary["repositories"]))),
        "Commits": summary["commits"], "Pushes": summary["pushes"],
        "Pull Requests": summary["pull_requests"],
    }


def contributor_rows(dataset):
    contributors = defaultdict(lambda: {
        "name": "", "repositories": set(), "commits": 0, "pushes": 0, "pull_requests": 0,
    })
    activity_specs = (
        ("commits", "Author", "Author Email", "commits"),
        ("pushes", "Pushed By", "Pusher Email", "pushes"),
        ("pull_requests", "Created By", "Creator Email", "pull_requests"),
    )
    for dataset_key, name_key, email_key, counter_key in activity_specs:
        for activity in dataset.get(dataset_key, []):
            identity_key = activity.get(email_key) or activity.get(name_key) or "Unknown"
            contributor = contributors[identity_key]
            contributor["name"] = activity.get(name_key) or contributor["name"] or "Unknown"
            contributor["repositories"].add(activity.get("Repository", ""))
            contributor[counter_key] += 1
    ordered = sorted(contributors.items(), key=lambda pair: pair[1]["name"])
    return [_contributor_row(email, summary) for email, summary in ordered]
