#!/Users/andreacacioppo/Documents/andreacacioppo.github.io/mcp-server/.venv/bin/python3
"""
MCP Server for managing andreacacioppo.com website.

This server provides tools to:
- List and view CV sections
- Add publications, talks, work experience
- Update sections and profile
- Regenerate PDF
- Git commit and push changes
"""

import subprocess
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, NavigableString
from mcp.server.fastmcp import FastMCP

# Configuration
WEBSITE_DIR = Path(__file__).parent.parent
INDEX_HTML = WEBSITE_DIR / "index.html"
HARD_TRUTHS_HTML = WEBSITE_DIR / "hard-truths.html"

# Initialize MCP server
mcp = FastMCP("andreacacioppo-website")


def load_html() -> BeautifulSoup:
    """Load and parse the index.html file."""
    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        return BeautifulSoup(f.read(), "lxml")


def save_html(soup: BeautifulSoup) -> None:
    """Save the modified HTML back to file."""
    # Use the original doctype and formatting
    html_str = str(soup)
    # Ensure proper doctype
    if not html_str.strip().startswith("<!DOCTYPE"):
        html_str = "<!DOCTYPE html>\n" + html_str
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html_str)


def update_last_modified_date(soup: BeautifulSoup) -> None:
    """Update the 'Curriculum vitae - DATE' line in the header."""
    header = soup.find("header", class_="cv-header")
    if header:
        for p in header.find_all("p"):
            text = p.get_text()
            if "Curriculum vitae" in text:
                today = datetime.now().strftime("%B %d %Y")
                p.string = f"Curriculum vitae - {today}"
                break
    
    # Also update JSON-LD dateModified
    script_tags = soup.find_all("script", type="application/ld+json")
    for script in script_tags:
        if script.string and "dateModified" in script.string:
            today_iso = datetime.now().strftime("%Y-%m-%d")
            script.string = re.sub(
                r'"dateModified":\s*"[^"]*"',
                f'"dateModified": "{today_iso}"',
                script.string
            )


# ============================================================================
# TOOLS
# ============================================================================

@mcp.tool()
def list_cv_sections() -> dict[str, Any]:
    """
    List all sections in the CV with their IDs and a brief summary.
    
    Returns a dictionary with section names and their current item counts.
    """
    soup = load_html()
    sections = {}
    
    for section in soup.find_all("section"):
        section_id = section.get("id", "unknown")
        h2 = section.find("h2")
        title = h2.get_text() if h2 else section_id
        
        # Count items
        articles = section.find_all("article")
        lis = section.find("ul")
        li_count = len(lis.find_all("li")) if lis else 0
        
        sections[section_id] = {
            "title": title,
            "articles": len(articles),
            "list_items": li_count
        }
    
    return sections


@mcp.tool()
def get_section_content(section_id: str) -> str:
    """
    Get the full content of a specific section.
    
    Args:
        section_id: The ID of the section (e.g., 'publications', 'work-experience', 'talks')
    
    Returns:
        The text content of the section.
    """
    soup = load_html()
    section = soup.find("section", id=section_id)
    
    if not section:
        available = [s.get("id") for s in soup.find_all("section") if s.get("id")]
        return f"Section '{section_id}' not found. Available sections: {', '.join(available)}"
    
    return section.get_text(separator="\n", strip=True)


@mcp.tool()
def get_profile() -> str:
    """
    Get the current profile/bio text.
    
    Returns:
        The profile paragraph text.
    """
    soup = load_html()
    profile = soup.find("section", id="profile")
    if profile:
        p = profile.find("p")
        if p:
            return p.get_text()
    return "Profile section not found."


@mcp.tool()
def update_profile(new_text: str) -> str:
    """
    Update the profile/bio paragraph.
    
    Args:
        new_text: The new profile text to set.
    
    Returns:
        Confirmation message.
    """
    soup = load_html()
    profile = soup.find("section", id="profile")
    if profile:
        p = profile.find("p")
        if p:
            p.string = new_text
            update_last_modified_date(soup)
            save_html(soup)
            return "Profile updated successfully."
    return "Failed to update profile - section not found."


@mcp.tool()
def add_publication(
    authors: str,
    title: str,
    venue: str,
    year: str,
    arxiv_id: str | None = None,
    doi: str | None = None
) -> str:
    """
    Add a new publication to the publications list.
    
    Args:
        authors: Author names (e.g., "Andrea Cacioppo, Lorenzo Colantonio, and Stefano Giagu")
        title: Paper title
        venue: Publication venue (journal, conference, or "arXiv preprint")
        year: Publication year
        arxiv_id: Optional arXiv ID (e.g., "2311.15444")
        doi: Optional DOI
    
    Returns:
        Confirmation message.
    """
    soup = load_html()
    publications = soup.find("section", id="publications")
    
    if not publications:
        return "Publications section not found."
    
    ul = publications.find("ul")
    if not ul:
        return "Publications list not found."
    
    # Build the publication entry
    li = soup.new_tag("li")
    
    # Authors
    li.append(NavigableString(f"{authors}. "))
    
    # Title (bold)
    b = soup.new_tag("b")
    b.string = title
    li.append(b)
    li.append(NavigableString(". "))
    
    # Venue
    if "arXiv" in venue.lower():
        li.append(NavigableString(f"{venue} arXiv:{arxiv_id}, {year}." if arxiv_id else f"{venue}, {year}."))
    else:
        i = soup.new_tag("i")
        i.string = venue
        li.append(i)
        li.append(NavigableString(f", {year}."))
    
    # Insert at the top of the list
    if ul.li:
        ul.li.insert_before(li)
    else:
        ul.append(li)
    
    update_last_modified_date(soup)
    save_html(soup)
    
    return f"Publication '{title}' added successfully."


@mcp.tool()
def add_talk(
    date: str,
    event_name: str,
    location: str,
    talk_type: str,
    talk_title: str
) -> str:
    """
    Add a new talk/presentation to the talks section.
    
    Args:
        date: Date of the talk (e.g., "Feb 2026")
        event_name: Name of the event/conference
        location: City and country
        talk_type: Type of presentation (e.g., "Talk", "Flash Talk", "Poster")
        talk_title: Title of the presentation
    
    Returns:
        Confirmation message.
    """
    soup = load_html()
    talks = soup.find("section", id="talks")
    
    if not talks:
        return "Talks section not found."
    
    # Create new article
    article = soup.new_tag("article")
    
    # Date heading
    h3 = soup.new_tag("h3")
    h3.string = date
    article.append(h3)
    
    # Event line
    p1 = soup.new_tag("p")
    b = soup.new_tag("b")
    b.string = event_name
    p1.append(b)
    p1.append(NavigableString(f" @ {location}, {talk_type}"))
    article.append(p1)
    
    # Talk title
    p2 = soup.new_tag("p")
    p2.string = f'"{talk_title}"'
    article.append(p2)
    
    # Insert after h2
    h2 = talks.find("h2")
    first_article = talks.find("article")
    if first_article:
        first_article.insert_before(article)
    elif h2:
        h2.insert_after(article)
    
    update_last_modified_date(soup)
    save_html(soup)
    
    return f"Talk '{talk_title}' added successfully."


@mcp.tool()
def add_work_experience(
    date_range: str,
    job_title: str,
    organization: str,
    location: str,
    description: str,
    org_url: str | None = None
) -> str:
    """
    Add a new work experience entry.
    
    Args:
        date_range: Employment period (e.g., "Jan 2025 - Present")
        job_title: Your role/title
        organization: Company or institution name
        location: City and country
        description: Brief description of work (can use "Topic:" or "Tasks:" prefix)
        org_url: Optional URL for the organization
    
    Returns:
        Confirmation message.
    """
    soup = load_html()
    work = soup.find("section", id="work-experience")
    
    if not work:
        return "Work experience section not found."
    
    # Create new article
    article = soup.new_tag("article")
    
    # Date heading
    h3 = soup.new_tag("h3")
    h3.string = date_range
    article.append(h3)
    
    # Job title and organization
    p1 = soup.new_tag("p")
    b = soup.new_tag("b")
    b.string = job_title
    p1.append(b)
    p1.append(NavigableString(", "))
    
    if org_url:
        a = soup.new_tag("a", href=org_url)
        a.string = organization
        p1.append(a)
    else:
        p1.append(NavigableString(organization))
    
    p1.append(NavigableString(f", {location}"))
    article.append(p1)
    
    # Description
    p2 = soup.new_tag("p")
    p2.string = description
    article.append(p2)
    
    # Insert after h2
    h2 = work.find("h2")
    first_article = work.find("article")
    if first_article:
        first_article.insert_before(article)
    elif h2:
        h2.insert_after(article)
    
    update_last_modified_date(soup)
    save_html(soup)
    
    return f"Work experience at '{organization}' added successfully."


@mcp.tool()
def add_education(
    date_range: str,
    degree: str,
    institution: str,
    location: str,
    topics: str | None = None,
    thesis: str | None = None,
    supervisors: str | None = None,
    grade: str | None = None,
    group_name: str | None = None,
    group_url: str | None = None
) -> str:
    """
    Add a new education entry.
    
    Args:
        date_range: Period (e.g., "Oct 2022 - April 2026")
        degree: Degree name (e.g., "PhD in Physics", "M.Sc. in Computer Science")
        institution: University name
        location: City and country
        topics: Optional topics/research areas
        thesis: Optional thesis title
        supervisors: Optional supervisor names
        grade: Optional final grade
        group_name: Optional research group name
        group_url: Optional research group URL
    
    Returns:
        Confirmation message.
    """
    soup = load_html()
    education = soup.find("section", id="education")
    
    if not education:
        return "Education section not found."
    
    # Create new article
    article = soup.new_tag("article")
    
    # Date heading
    h3 = soup.new_tag("h3")
    h3.string = date_range
    article.append(h3)
    
    # Degree and institution
    p1 = soup.new_tag("p")
    b = soup.new_tag("b")
    b.string = degree
    p1.append(b)
    p1.append(NavigableString(f", {institution}, {location}"))
    article.append(p1)
    
    # Optional fields
    if topics:
        p = soup.new_tag("p")
        p.string = f"Topics: {topics}"
        article.append(p)
    
    if group_name:
        p = soup.new_tag("p")
        p.append(NavigableString("Group: "))
        if group_url:
            a = soup.new_tag("a", href=group_url)
            a.string = group_name
            p.append(a)
        else:
            p.append(NavigableString(group_name))
        article.append(p)
    
    if supervisors:
        p = soup.new_tag("p")
        p.string = f"Supervisors: {supervisors}"
        article.append(p)
    
    if thesis:
        p = soup.new_tag("p")
        p.string = f'Thesis: "{thesis}"'
        article.append(p)
    
    if grade:
        p = soup.new_tag("p")
        p.string = f"Grade: {grade}"
        article.append(p)
    
    # Insert after h2
    h2 = education.find("h2")
    first_article = education.find("article")
    if first_article:
        first_article.insert_before(article)
    elif h2:
        h2.insert_after(article)
    
    update_last_modified_date(soup)
    save_html(soup)
    
    return f"Education entry '{degree}' added successfully."


@mcp.tool()
def update_software_skills(skills: list[str]) -> str:
    """
    Replace the software/skills list with a new one.
    
    Args:
        skills: List of skill strings (e.g., ["Python, PyTorch - advanced", "TensorFlow - good"])
    
    Returns:
        Confirmation message.
    """
    soup = load_html()
    software = soup.find("section", id="software")
    
    if not software:
        return "Software section not found."
    
    ul = software.find("ul")
    if not ul:
        return "Software list not found."
    
    # Clear existing items
    ul.clear()
    
    # Add new items
    for skill in skills:
        li = soup.new_tag("li")
        li.string = skill
        ul.append(li)
    
    update_last_modified_date(soup)
    save_html(soup)
    
    return f"Software skills updated with {len(skills)} items."


@mcp.tool()
def update_languages(languages: list[str]) -> str:
    """
    Replace the languages list with a new one.
    
    Args:
        languages: List of language strings (e.g., ["Italian - native", "English - fluent"])
    
    Returns:
        Confirmation message.
    """
    soup = load_html()
    lang_section = soup.find("section", id="languages")
    
    if not lang_section:
        return "Languages section not found."
    
    ul = lang_section.find("ul")
    if not ul:
        return "Languages list not found."
    
    # Clear existing items
    ul.clear()
    
    # Add new items
    for lang in languages:
        li = soup.new_tag("li")
        li.string = lang
        ul.append(li)
    
    update_last_modified_date(soup)
    save_html(soup)
    
    return f"Languages updated with {len(languages)} items."


@mcp.tool()
def regenerate_pdf() -> str:
    """
    Run the PDF generation script to update the CV PDF.
    
    Returns:
        Output from the script or error message.
    """
    script_path = WEBSITE_DIR / "generate_cv_pdf.py"
    
    if not script_path.exists():
        return f"PDF generation script not found at {script_path}"
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(WEBSITE_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            output = result.stdout.strip() if result.stdout else "PDF generated successfully."
            return output
        else:
            return f"Script failed: {result.stderr}"
    
    except subprocess.TimeoutExpired:
        return "PDF generation timed out after 60 seconds."
    except Exception as e:
        return f"Error running script: {e}"


@mcp.tool()
def git_status() -> str:
    """
    Check the git status of the website repository.
    
    Returns:
        Git status output.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(WEBSITE_DIR),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            return output if output else "Working directory clean - no changes."
        else:
            return f"Git error: {result.stderr}"
    
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def git_diff() -> str:
    """
    Show the git diff of current changes.
    
    Returns:
        Git diff output (limited to avoid huge outputs).
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=str(WEBSITE_DIR),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            return output if output else "No changes to show."
        else:
            return f"Git error: {result.stderr}"
    
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def git_commit_push(commit_message: str) -> str:
    """
    Stage all changes, commit with the given message, and push to GitHub.
    
    Args:
        commit_message: The commit message to use.
    
    Returns:
        Result of the git operations.
    """
    results = []
    
    try:
        # Stage all changes
        add_result = subprocess.run(
            ["git", "add", "-A"],
            cwd=str(WEBSITE_DIR),
            capture_output=True,
            text=True
        )
        if add_result.returncode != 0:
            return f"Git add failed: {add_result.stderr}"
        results.append("✓ Changes staged")
        
        # Commit
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=str(WEBSITE_DIR),
            capture_output=True,
            text=True
        )
        if commit_result.returncode != 0:
            if "nothing to commit" in commit_result.stdout:
                return "Nothing to commit - working directory clean."
            return f"Git commit failed: {commit_result.stderr}"
        results.append(f"✓ Committed: {commit_message}")
        
        # Push
        push_result = subprocess.run(
            ["git", "push"],
            cwd=str(WEBSITE_DIR),
            capture_output=True,
            text=True
        )
        if push_result.returncode != 0:
            return f"Git push failed: {push_result.stderr}\n" + "\n".join(results)
        results.append("✓ Pushed to GitHub")
        
        return "\n".join(results) + "\n\nSite will update shortly at andreacacioppo.com"
    
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def remove_publication(title_substring: str) -> str:
    """
    Remove a publication by matching part of its title.
    
    Args:
        title_substring: A unique substring of the publication title to remove.
    
    Returns:
        Confirmation or error message.
    """
    soup = load_html()
    publications = soup.find("section", id="publications")
    
    if not publications:
        return "Publications section not found."
    
    ul = publications.find("ul")
    if not ul:
        return "Publications list not found."
    
    for li in ul.find_all("li"):
        if title_substring.lower() in li.get_text().lower():
            title_preview = li.get_text()[:80] + "..."
            li.decompose()
            update_last_modified_date(soup)
            save_html(soup)
            return f"Removed publication: {title_preview}"
    
    return f"No publication found containing '{title_substring}'"


@mcp.tool()
def remove_talk(title_substring: str) -> str:
    """
    Remove a talk by matching part of its title.
    
    Args:
        title_substring: A unique substring of the talk title to remove.
    
    Returns:
        Confirmation or error message.
    """
    soup = load_html()
    talks = soup.find("section", id="talks")
    
    if not talks:
        return "Talks section not found."
    
    for article in talks.find_all("article"):
        if title_substring.lower() in article.get_text().lower():
            title_preview = article.get_text()[:80].replace("\n", " ") + "..."
            article.decompose()
            update_last_modified_date(soup)
            save_html(soup)
            return f"Removed talk: {title_preview}"
    
    return f"No talk found containing '{title_substring}'"


@mcp.tool()
def get_raw_html(section_id: str) -> str:
    """
    Get the raw HTML of a specific section for manual inspection/editing.
    
    Args:
        section_id: The ID of the section.
    
    Returns:
        The raw HTML string of the section.
    """
    soup = load_html()
    section = soup.find("section", id=section_id)
    
    if not section:
        return f"Section '{section_id}' not found."
    
    return section.prettify()


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    mcp.run()
