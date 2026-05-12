import os

from js_extractor.utils import has_display, parse_regex_group, get_js_files_from_page, get_js_files_from_page_browser, fetch_js_content, extract_matches, do_login

def extract(
    target_url: str,
    group_dir: str | None = None,
    browser: bool = False,
    timeout: int = 10,
    verbose: bool = False,
    login: bool = False,
    login_url: str | None = None,
    login_success_indicator: str = "Logout",
    storage_state: str = None,
    force_relogin: bool = False,
    before: int | None = None,
    after: int | None = None,
    output: str = "extraction_results.json",
    logger=None
):
    """
    Extract JavaScript files from a target website and scan them
    using YAML-defined regex pattern groups.

    Args:
        target_url:
            Target website URL.

        group_dir:
            Directory containing YAML regex groups.

        browser:
            Use Playwright browser mode.

        timeout:
            Request timeout in seconds.

        verbose:
            Enable verbose logging.

        login:
            Enable interactive login flow.

        login_url:
            Login page URL.

        login_success_indicator:
            Text that indicates successful login.

        force_relogin:
            Force login even if browser state exists.

        before:
            Number of characters before match.

        after:
            Number of characters after match.

        output:
            Output JSON file path.

        logger:
            Logger instance.

    Returns:
        list[dict]:
            Extraction results.
    """

    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

    if login and not browser:
        logger.error("[!] If you want to use authentication, --browser should be enabled!")
        raise Exception("[!] If you want to use authentication, --browser should be enabled!")

    if login:
        if not login_url:
            login_url = target_url

        if not os.path.exists(storage_state) or force_relogin:
            if not has_display():
                logger.error(
                    "[!] Interactive login requires a graphical display.\n"
                    "    No display server detected.\n"
                    "    Use a desktop environment, X11 forwarding, or "
                    "run without --login."
                )
                raise Exception("[!] Interactive login requires a graphical display.\n"
                    "    No display server detected.\n"
                    "    Use a desktop environment, X11 forwarding, or "
                    "run without --login.")
            do_login(
                login_url=login_url,
                login_success_indicator=login_success_indicator,
                logger=logger,
                storage_state=storage_state
            )

    logger.debug("\n" + "=" * 70)
    logger.debug("JavaScript File Extractor with Regex Pattern Matching")
    logger.debug("=" * 70 + "\n")

    logger.debug(f"[*] Target URL: {target_url}")

    if group_dir:
        logger.debug(f"[*] Group Directory: {group_dir}")
    else:
        logger.debug("[*] Using default regex patterns")

    logger.debug(f"[*] Output File: {output}\n")

    # Step 1: Parse regex group
    logger.debug("[*] Loading regex patterns...")
    regex_groups = parse_regex_group(logger, group_dir)

    logger.debug(f"[+] Loaded {len(regex_groups)} regex group(s)\n")

    if verbose:
        for group in regex_groups:
            logger.debug(f"    - {group.name} ({len(group.patterns)} patterns)")

    # Step 2: Extract JS files from the page
    logger.info("[*] Step 1: Extracting JavaScript files from page...")

    if browser:
        js_files = get_js_files_from_page_browser(target_url, logger, storage_state)
    else:
        js_files = get_js_files_from_page(target_url, logger, timeout)

    if not js_files:
        logger.warning("[!] No JavaScript files found on the page")
        return []

    logger.info(f"[+] Found {len(js_files)} JavaScript file(s)\n")

    for js_file in js_files:
        logger.debug(f"    - {js_file}")

    # Step 3: Fetch and analyze each JS file
    logger.info("[*] Step 2: Fetching and analyzing JavaScript files...")

    all_results = []

    for idx, js_url in enumerate(js_files, 1):
        logger.debug(f"\n[*] Processing [{idx}/{len(js_files)}]: {js_url}")

        # Fetch JS content
        js_content = fetch_js_content(js_url, logger)

        if not js_content:
            continue

        logger.debug(f"    Size: {len(js_content)} bytes")

        # Extract matches using regex patterns
        matches = extract_matches(
            js_content,
            regex_groups,
            js_url,
            before,
            after,
            logger
        )

        if matches:
            logger.debug(f"    [+] Found {len(matches)} match(es)")

            for match in matches:
                all_results.append(match)

                logger.debug(
                    f"        - {match['value']} "
                    f"({match['description']})"
                )
        else:
            logger.debug("    [-] No matches found")

    # Step 4: Display final results
    logger.debug("\n" + "=" * 70)
    logger.debug("EXTRACTION RESULTS")
    logger.debug("=" * 70 + "\n")

    if all_results:
        logger.info(f"[+] Total matches found: {len(all_results)}\n")

        for idx, result in enumerate(all_results, 1):
            logger.debug(f"[{idx}]")
            logger.debug(f"  Value:       {result['value']}")
            logger.debug(f"  Group Name:  {result['group_name']}")
            logger.debug(f"  Description: {result['description']}")
            logger.debug(f"  Source URL:  {result['url']}")

        # Save results to JSON
        try:
            import json

            with open(output, "w", encoding="utf-8") as f:
                json.dump(
                    all_results,
                    f,
                    indent=2,
                    ensure_ascii=False
                )

            logger.info(f"[+] Results saved to {output}")

        except Exception as e:
            logger.error(f"[!] Could not save results: {e}")

        return all_results

    logger.warning("[-] No matches found in any JavaScript files")
    return []