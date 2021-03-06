import logging
from datetime import datetime

from requests.exceptions import HTTPError
from prettytable import PrettyTable
from progressbar import ProgressBar

from assigner import get_filtered_roster
from config import config_context
from baserepo import Access, Repo, StudentRepo

help="Retrieve status of repos"

logger = logging.getLogger(__name__)


@config_context
def status(conf, args):
    """Retrieves and prints the status of repos"""
    hw_name = args.name

    if not hw_name:
        raise ValueError("Missing assignment name.")

    host = conf.gitlab_host
    namespace = conf.namespace
    token = conf.token
    semester = conf.semester

    roster = get_filtered_roster(conf.roster, args.section, args.student)
    sort_key = args.sort

    if sort_key:
        roster.sort(key=lambda s: s[sort_key])

    output = PrettyTable([
        "#", "Sec", "SID", "Name", "Status", "Branches",
        "HEAD", "Last Commit Author", "Last Commit Time"])
    output.align["Name"] = "l"
    output.align["Last Commit Author"] = "l"

    progress = ProgressBar(max_value=len(roster))

    for i, student in enumerate(roster):
        progress.update(i)

        name = student["name"]
        username = student["username"]
        student_section = student["section"]
        full_name = StudentRepo.name(semester, student_section,
                                     hw_name, username)

        row = [i+1, student_section, username, name, "", "", "", "", ""]

        try:
            repo = StudentRepo(host, namespace, full_name, token)

            if not repo.already_exists():
                row[4] = "Not Assigned"
                output.add_row(row)
                continue

            if "id" not in student:
                student["id"] = Repo.get_user_id(username, host, token)

            members = repo.list_members()
            if student["id"] not in [s["id"] for s in members]:
                row[4] = "Not Opened"
                output.add_row(row)
                continue

            if repo.info["archived"]:
                row[4] = 'Archived'
            else:
                level = Access([s["access_level"] for s in members if s["id"] == student["id"]][0])
                row[4] = "Open" if level is Access.developer else "Locked"

            branches = repo.list_branches()

            if branches:
                row[5] = ", ".join([b["name"] for b in branches])

            commits = repo.list_commits()

            if commits:
                head = commits[0]
                row[6] = head["short_id"]
                row[7] = head["author_name"]
                created_at = head["created_at"]
                # Fix UTC offset format in GitLab's datetime
                created_at = created_at[:-6] + created_at[-6:].replace(':', '')
                row[8] = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f%z")

            output.add_row(row)

        except HTTPError:
            raise

    progress.finish()
    print(output)


def setup_parser(parser):
    parser.add_argument("--section", nargs="?",
                           help="Section to get status of")
    parser.add_argument("--student", metavar="id",
                           help="ID of student.")
    parser.add_argument("--sort", nargs="?", default="name",
                           choices=["name", "username"],
                           help="Key to sort users by.")
    parser.add_argument("name", nargs="?",
                           help="Name of the assignment to look up.")
    parser.set_defaults(run=status)
