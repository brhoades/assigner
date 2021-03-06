import logging

from assigner import manage_users
from baserepo import Access

help="Unlock student's repo"

logger = logging.getLogger(__name__)


def unlock(args):
    """Sets each student to Developer status on their homework repository.
    """
    return manage_users(args, Access.developer)


def setup_parser(parser):
    parser.add_argument("name",
                           help="Name of the assignment to unlock.")
    parser.add_argument("--section", nargs="?",
                           help="Section to unlock")
    parser.add_argument("--student", metavar="id",
                           help="ID of student whose assignment needs " +
                                "unlocking.")
    parser.add_argument("--dry-run", action="store_true",
                           help="Don't actually do it.")
    parser.set_defaults(run=unlock)
