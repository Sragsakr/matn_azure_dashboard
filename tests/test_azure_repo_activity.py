import unittest

from azure_repo_activity import AzureRepoActivityClient, contributor_rows


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"HTTP {self.status_code}")


class PagingSession:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def get(self, url, headers, params, timeout):
        self.calls.append((url, dict(params)))
        skip = int(params.get("$skip", 0))
        top = int(params["$top"])
        return FakeResponse({"value": self.rows[skip:skip + top]})


class ScriptedSession:
    def __init__(self):
        self.calls = []

    def get(self, url, headers, params, timeout):
        self.calls.append((url, dict(params)))
        if url.endswith("/_apis/git/repositories"):
            return FakeResponse({"value": [{
                "id": "r1", "name": "web", "defaultBranch": "refs/heads/main",
                "size": 120, "remoteUrl": "https://clone", "webUrl": "https://web",
                "isDisabled": False,
            }]})
        if url.endswith("/r1/commits"):
            return FakeResponse({"value": [{
                "commitId": "abc", "comment": "Add dashboard",
                "author": {"name": "Sara", "email": "sara@example.com", "date": "2026-08-20T10:00:00Z"},
                "committer": {"name": "Sara", "email": "sara@example.com", "date": "2026-08-20T10:01:00Z"},
                "_links": {"web": {"href": "https://commit"}},
            }]})
        if url.endswith("/r1/pushes"):
            return FakeResponse({"value": [{
                "pushId": 7, "date": "2026-08-20T10:02:00Z",
                "pushedBy": {"displayName": "Sara", "uniqueName": "sara@example.com"},
                "commits": [{"commitId": "abc"}],
                "refUpdates": [{"name": "refs/heads/main"}],
                "_links": {"web": {"href": "https://push"}},
            }]})
        if url.endswith("/r1/pullrequests"):
            return FakeResponse({"value": [{
                "pullRequestId": 4, "title": "Dashboard", "description": "Details",
                "status": "completed", "createdBy": {"displayName": "Sara", "uniqueName": "sara@example.com"},
                "creationDate": "2026-08-20T09:00:00Z", "closedDate": "2026-08-20T11:00:00Z",
                "sourceRefName": "refs/heads/feature", "targetRefName": "refs/heads/main",
                "reviewers": [{"displayName": "Omar", "uniqueName": "omar@example.com", "vote": 10}],
                "_links": {"web": {"href": "https://pr"}},
            }]})
        if url.endswith("/r1/commits/abc/changes"):
            return FakeResponse({"changes": [{
                "changeType": "add", "item": {"path": "/dashboard.py", "gitObjectType": "blob", "objectId": "obj"},
            }]})
        raise AssertionError(f"Unexpected URL: {url}")


class FailingCommitsSession(ScriptedSession):
    def get(self, url, headers, params, timeout):
        if url.endswith("/r1/commits"):
            return FakeResponse({}, status=403)
        return super().get(url, headers, params, timeout)


class AzureRepoActivityTests(unittest.TestCase):
    def test_value_pages_reads_every_skip_page(self):
        rows = [{"id": index} for index in range(205)]
        session = PagingSession(rows)
        client = AzureRepoActivityClient("org", "project", "pat", session=session)

        actual = client.value_pages("git/repositories")

        self.assertEqual(rows, actual)
        self.assertEqual([0, 100, 200], [call[1]["$skip"] for call in session.calls])

    def test_fetch_all_normalizes_repository_activity_and_changes(self):
        client = AzureRepoActivityClient("org", "project", "pat", session=ScriptedSession())

        activity = client.fetch_all()

        self.assertEqual("web", activity["repositories"][0]["Repository"])
        self.assertEqual("Sara", activity["commits"][0]["Author"])
        self.assertEqual(7, activity["pushes"][0]["Push ID"])
        self.assertEqual("Omar (+10)", activity["pull_requests"][0]["Reviewers"])
        self.assertEqual("/dashboard.py", activity["changes"][0]["Path"])
        self.assertEqual([], activity["failures"])

    def test_repository_endpoint_failure_keeps_other_activity(self):
        client = AzureRepoActivityClient(
            "org", "project", "pat", session=FailingCommitsSession()
        )

        activity = client.fetch_all()

        self.assertEqual([], activity["commits"])
        self.assertEqual(1, len(activity["pushes"]))
        self.assertEqual("commits", activity["failures"][0]["Operation"])

    def test_contributor_rows_reconcile_loaded_activity(self):
        dataset = {
            "commits": [{"Author": "Sara", "Author Email": "sara@example.com", "Repository": "web"}],
            "pushes": [{"Pushed By": "Sara", "Pusher Email": "sara@example.com", "Repository": "web"}],
            "pull_requests": [{"Created By": "Sara", "Creator Email": "sara@example.com", "Repository": "api"}],
        }

        rows = contributor_rows(dataset)

        self.assertEqual([{
            "Contributor": "Sara", "Email": "sara@example.com", "Repositories": "api, web",
            "Commits": 1, "Pushes": 1, "Pull Requests": 1,
        }], rows)


if __name__ == "__main__":
    unittest.main()
