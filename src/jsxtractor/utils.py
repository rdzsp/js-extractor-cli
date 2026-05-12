import re
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin
import requests
from dataclasses import dataclass

@dataclass
class RegexPattern:
    """Represents a single regex pattern"""
    regex: str
    description: str


@dataclass
class RegexGroup:
    """Represents a group of regex patterns"""
    name: str
    patterns: List[RegexPattern]

def setup_logger(verbose: bool = False) -> logging.Logger:
    """
    Configure and return application logger.
    """

    logger = logging.getLogger("jsxtractor")

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)

    # Console log level
    if verbose:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger

def has_display():
    """
    Check whether the current environment supports
    non-headless browser mode.
    """

    # Linux X11
    if os.environ.get("DISPLAY"):
        return True

    # Linux Wayland
    if os.environ.get("WAYLAND_DISPLAY"):
        return True

    # Windows/macOS usually support GUI
    if sys.platform.startswith("win"):
        return True

    if sys.platform == "darwin":
        return True

    return False

def parse_regex_group(logger, group_dir: Optional[str] = None) -> Dict[str, RegexGroup]:
    """
    Parse regex group from a directory of YAML files.
    Each YAML file contains exactly one regex group.
    
    Args:
        group_dir: Path to directory containing YAML group files (optional)
    
    Returns:
        Dictionary of regex groups
    """
    regex_groups = []
    
    if group_dir:
        try:
            import yaml
            group_path = Path(group_dir)
            
            if not group_path.exists():
                logger.error(f"[!] Group directory not found: {group_dir}")
                return get_default_regex_patterns()
            
            if not group_path.is_dir():
                logger.error(f"[!] Path is not a directory: {group_dir}")
                return get_default_regex_patterns()
            
            # Find all YAML files in directory
            yaml_files = list(group_path.glob("*.yaml")) + list(group_path.glob("*.yml"))
            
            if not yaml_files:
                logger.error(f"[!] No YAML files found in {group_dir}")
                return get_default_regex_patterns()
            
            logger.info(f"[*] Found {len(yaml_files)} YAML file(s) in {group_dir}")
            
            # Load each YAML file
            for yaml_file in yaml_files:
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        group = yaml.safe_load(f)
                        
                        if not group:
                            logger.debug(f"    [!] Empty file: {yaml_file.name}")
                            continue
                        
                        # Each file should contain exactly one group
                        for header, group_data in group.items():
                            if header != 'js-extractor':
                                logger.debug(f"    [!] Invalid format in {yaml_file.name}")
                                
                            if not isinstance(group_data, dict):
                                logger.debug(f"    [!] Invalid format in {yaml_file.name}")
                                continue
                            
                            if 'name' not in group_data or 'patterns' not in group_data:
                                logger.debug(f"    [!] Missing 'name' or 'patterns' in {yaml_file.name}")
                                continue
                            
                            patterns = [
                                RegexPattern(regex=p['regex'], description=p['description'])
                                for p in group_data['patterns']
                                if isinstance(p, dict) and 'regex' in p and 'description' in p
                            ]
                            
                            if patterns:
                                regex_groups.append(RegexGroup(
                                    name=group_data['name'],
                                    patterns=patterns
                                ))
                                logger.debug(f"    [+] Loaded: {group_data['name']} ({len(patterns)} patterns)")
                            
                except Exception as e:
                    logger.warning(f"    [!] Error reading {yaml_file.name}: {e}")
            
            if regex_groups:
                return regex_groups
            else:
                logger.warning("[!] No valid regex groups loaded from directory")
                return get_default_regex_patterns()
                
        except ImportError:
            logger.error("[!] PyYAML not installed. Install with: pip install pyyaml")
            return get_default_regex_patterns()
        except Exception as e:
            logger.error(f"[!] Error reading group directory: {e}")
            return get_default_regex_patterns()
    
    return get_default_regex_patterns()


def get_default_regex_patterns() -> Dict[str, RegexGroup]:
    """
    Get default regex patterns when no group directory is provided
    
    Returns:
        Dictionary with default regex group
    """
    return [
        RegexGroup(
            name="Endpoints / URLs",
            patterns=[
                RegexPattern(
                    regex=r"(?:\"|')((?:[a-zA-Z]{1,10}:\/\/|\/\/)[^\"'\/]{1,}\.[a-zA-Z]{2,}[^\"']{0,})(?:\"|')",
                    description="Full URLs with scheme or protocol-relative"
                ),
                RegexPattern(
                    regex=r"(?:\"|')((?:\/|\.\.\/|\.\/)[^\"'><,;| *()\[\]]{2,})(?:\"|')",
                    description="Relative paths"
                ),
                RegexPattern(
                    regex=r"(?:\"|')([a-zA-Z0-9_\-/]+\/[a-zA-Z0-9_\-/.]+\.(?:[a-zA-Z]{1,4}|action)(?:[?#][^\"']*)?)(?:\"|')",
                    description="Endpoints with file extensions"
                ),
                RegexPattern(
                    regex=r"(?:\"|')([a-zA-Z0-9_\-/]+\/[a-zA-Z0-9_\-/]{3,}(?:[?#][^\"' ]*)?)(?:\"|')",
                    description="REST API endpoints"
                ),
                RegexPattern(
                    regex=r"(?:\"|')([a-zA-Z0-9_\-]+\.(?:php|asp|aspx|jsp|json|action|html|js|txt|xml)(?:[?#][^\"']*)?)(?:\"|')",
                    description="Standalone files"
                ),
                RegexPattern(
                    regex=r"`((?:[^`]*\$\{[^}]+\})+[a-zA-Z0-9_\-/]*(?:\/[a-zA-Z0-9_\-/]*)*(?:[?#][^`]*)?)`",
                    description="Template literal endpoints with ${} expressions"
                ),
            ]
        )
    ]


def get_js_files_from_page(url: str, logger, timeout: int = 3000) -> List[str]:
    """
    Extract all JavaScript file URLs from a webpage using requests
    
    Args:
        url: The URL to scrape
        timeout: Timeout in seconds (default: 3000)
    
    Returns:
        List of absolute JavaScript file URLs
    """
    js_files = []
    
    try:
        from bs4 import BeautifulSoup

        logger.debug(f"[*] Opening URL: {url}")
        user_agent = get_user_agent(logger)
        headers = {
            'User-Agent': user_agent
        }
        response = requests.get(url=url, headers=headers, timeout=timeout)
        
        # Get all script tags
        soup = BeautifulSoup(response.text)
        scripts = soup.find_all('script')
        logger.debug(f"[*] Found {len(scripts)} script tags")
        
        for script in scripts:
            src = script.get('src')
            if src:
                # Convert relative URLs to absolute
                absolute_url = urljoin(url, src)
                js_files.append(absolute_url)
                logger.debug(f"    - {absolute_url}")
    except ImportError:
        logger.error("[!] beautifulsoup4 not installed. Install with: pip install beautifulsoup4")
        raise Exception("[!] beautifulsoup4 not installed. Install with: pip install beautifulsoup4")
    
    except Exception as e:
        logger.error(f"[!] Error fetching page: {e}")
        raise Exception(f"[!] Error fetching page: {e}")
    
    return js_files

def get_js_files_from_page_browser(url: str, logger, timeout: int = 30000, storage_state = None) -> List[str]:
    """
    Extract all JavaScript file URLs from a webpage using Playwright
    
    Args:
        url: The URL to scrape
        timeout: Timeout in milliseconds (default: 30000)
    
    Returns:
        List of absolute JavaScript file URLs
    """
    js_files = []
    
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.7827.3 Safari/537.36"
            browser = p.chromium.launch(headless=True)
            if storage_state:
                context = browser.new_context(
                    storage_state=storage_state, 
                    user_agent=user_agent
                )
            else:
                context = browser.new_context(
                    user_agent=user_agent
                )

            page = context.new_page()
            
            try:
                logger.debug(f"[*] Opening URL: {url}")
                page.goto(url, wait_until='load', timeout=timeout)
                
                # Get all script tags
                scripts = page.query_selector_all('script')
                logger.debug(f"[*] Found {len(scripts)} script tags")
                
                for script in scripts:
                    src = script.get_attribute('src')
                    if src:
                        # Convert relative URLs to absolute
                        absolute_url = urljoin(url, src)
                        js_files.append(absolute_url)
                        logger.debug(f"    - {absolute_url}")
                
                browser.close()
                
            except Exception as e:
                logger.error(f"[!] Error fetching page: {e}")
                if browser:
                    browser.close()
    except ImportError:
        logger.error("[!] playwright not installed. Install with: pip install playwright")
        raise Exception("[!] playwright not installed. Install with: pip install playwright")
    
    return js_files


def fetch_js_content(js_url: str, logger) -> Optional[str]:
    """
    Fetch the content of a JavaScript file
    
    Args:
        js_url: URL of the JavaScript file
    
    Returns:
        Content of the JS file or None if failed
    """
    try:
        user_agent = get_user_agent(logger)
        headers = {
            'User-Agent': user_agent
        }
        response = requests.get(js_url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"[!] Error fetching {js_url}: {e}")
        return None


def extract_matches(js_content: str, regex_groups: list[RegexGroup], 
                   js_url: str, before: int, after: int, logger) -> List[Dict]:
    """
    Extract matches from JavaScript content using regex patterns
    
    Args:
        js_content: Content of the JavaScript file
        regex_groups: List of regex groups to apply
        js_url: Source URL of the JS file
        before: Match before N chars
        after: Match after N chars
    
    Returns:
        List of dictionaries with matched values and metadata
    """
    results = []
    
    for group in regex_groups:
        for pattern in group.patterns:
            try:
                matches = re.finditer(pattern.regex, js_content)

                for match in matches:
                    # Get the first capturing group if exists
                    if match.groups():
                        value = match.group(1)
                    else:
                        value = match.group(0)

                    start = max(0, match.start() - before)
                    end = min(len(js_content), match.end() + after)

                    detail = js_content[start:end]

                    result = {
                        "value": value,
                        "start": match.start(),
                        "end": match.end(),
                        "group_name": group.name,
                        "description": pattern.description,
                        "url": js_url,
                        "detail": detail
                    }

                    results.append(result)

            except re.error as e:
                logger.error(f"[!] Regex error in pattern '{pattern.regex}': {e}")
    
    return results

def get_user_agent(logger):
    try:
        from random_user_agent.user_agent import UserAgent
        from random_user_agent.params import SoftwareName, OperatingSystem


        # you can also import SoftwareEngine, HardwareType, SoftwareType, Popularity from random_user_agent.params
        # you can also set number of user agents required by providing `limit` as parameter

        software_names = [SoftwareName.CHROME.value]
        operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]   

        user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)

        # Get Random User Agent String.
        user_agent = user_agent_rotator.get_random_user_agent()
    except ImportError:
        logger.error("[!] random_user_agent not installed. Install with: pip install random_user_agent")
        raise Exception("[!] random_user_agent not installed. Install with: pip install random_user_agent")
    
    return user_agent

def do_login(login_url: str, login_success_indicator: str, logger, storage_state):
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()

            page = context.new_page()
            page.goto(url=login_url)
            page.wait_for_function(
                "text => document.body.innerText.includes(text)",
                arg=login_success_indicator,
                timeout=180000
            )

            context.storage_state(path=storage_state)

    except ImportError:
        logger.error("[!] playwright not installed. Install with: pip install playwright")
        raise Exception("[!] playwright not installed. Install with: pip install playwright")