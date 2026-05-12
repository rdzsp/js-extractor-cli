import argparse

from js_extractor.utils import setup_logger

from js_extractor.extractor import extract

def parse_args():
    parser = argparse.ArgumentParser(
        prog="js_extractor",
        description=(
            "Extract JavaScript files from a target website and scan them "
            "using custom YAML regex pattern groups."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  Basic scan:
      python js_extractor.py https://example.com

  Use custom regex group directory:
      python js_extractor.py https://example.com ./groups

  Using named arguments:
      python js_extractor.py -u https://example.com -g ./groups

  Enable verbose logging:
      python js_extractor.py -u https://example.com -v

  Browser mode:
      python js_extractor.py -u https://example.com --browser

  Login flow:
      python js_extractor.py -u https://example.com \\
          --browser \\
          --login \\
          --login-url https://example.com/login \\
          --login-success-indicator Logout

  Force re-login even if state.json exists:
      python js_extractor.py -u https://example.com \\
          --browser \\
          --login \\
          --force-relogin

  Match extraction context:
      python js_extractor.py -u https://example.com \\
          --after 50 --before 50
"""
    )

    #
    # Positional arguments
    #
    parser.add_argument(
        "url",
        nargs="?",
        help="Target URL"
    )

    parser.add_argument(
        "group",
        nargs="?",
        default=None,
        help="Directory containing YAML regex group files"
    )

    #
    # Optional aliases
    #
    parser.add_argument(
        "-u", "--url",
        dest="url_arg",
        metavar="URL",
        help="Target URL (alternative to positional argument)"
    )

    parser.add_argument(
        "-g", "--group",
        dest="group_arg",
        metavar="DIR",
        help="Regex group directory (alternative to positional argument)"
    )

    #
    # Match context options
    #
    parser.add_argument(
        "-af", "--after",
        type=int,
        metavar="N",
        help="Show N characters after each match"
    )

    parser.add_argument(
        "-be", "--before",
        type=int,
        metavar="N",
        help="Show N characters before each match"
    )

    #
    # Output options
    #
    parser.add_argument(
        "-o", "--output",
        default="extraction_results.json",
        metavar="FILE",
        help="Output JSON file (default: extraction_results.json)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose/debug logging"
    )

    #
    # Browser options
    #
    parser.add_argument(
        "-b", "--browser",
        action="store_true",
        help="Use Playwright browser mode instead of requests"
    )

    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=10,
        metavar="SECONDS",
        help="Request timeout in seconds (default: 10)"
    )

    #
    # Authentication options
    #
    auth_group = parser.add_argument_group("authentication")

    auth_group.add_argument(
        "-l", "--login",
        action="store_true",
        help="Enable interactive login mode (requires --browser)"
    )

    auth_group.add_argument(
        "-lu", "--login-url",
        metavar="URL",
        help="Login page URL"
    )

    auth_group.add_argument(
        "-lsi", "--login-success-indicator",
        default="Logout",
        metavar="TEXT",
        help='Text indicator that confirms successful login '
             '(default: "Logout")'
    )

    auth_group.add_argument(
        "-ss", "--storage-state",
        default=".auth/state.json",
        metavar="FILE",
        help=(
            "Path to Playwright storage state JSON file "
            '(default: ".auth/state.json")'
        )
    )

    auth_group.add_argument(
        "-fr", "--force-relogin",
        action="store_true",
        help="Force re-login even if the state file already exists"
    )

    args = parser.parse_args()

    #
    # Normalize arguments
    #
    args.target_url = args.url_arg or args.url
    args.group_dir = args.group_arg or args.group

    #
    # Validate required URL
    #
    if not args.target_url:
        parser.error("URL is required")

    return args

def main():
    args = parse_args()

    logger = setup_logger(args.verbose)

    extract(
        target_url=args.target_url,
        group_dir=args.group_dir,
        browser=args.browser,
        timeout=args.timeout,
        verbose=args.verbose,
        login=args.login,
        login_url=args.login_url,
        login_success_indicator=args.login_success_indicator,
        storage_state=args.storage_state,
        force_relogin=args.force_relogin,
        before=args.before,
        after=args.after,
        output=args.output,
        logger=logger
    )