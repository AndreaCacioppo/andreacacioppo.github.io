# Andrea Cacioppo Website MCP Server

An MCP (Model Context Protocol) server for managing your personal website and CV at andreacacioppo.com.

## Features

This MCP server provides the following tools:

| Tool | Description |
|------|-------------|
| `list_cv_sections` | List all CV sections with item counts |
| `get_section_content` | Get the text content of any section |
| `get_profile` | Get current bio text |
| `update_profile` | Update bio text |
| `add_publication` | Add a new paper to publications |
| `add_talk` | Add a new conference talk |
| `add_work_experience` | Add a new job/consulting entry |
| `add_education` | Add a new education entry |
| `update_software_skills` | Replace the skills list |
| `update_languages` | Replace the languages list |
| `remove_publication` | Remove a publication by title |
| `remove_talk` | Remove a talk by title |
| `regenerate_pdf` | Run generate_cv_pdf.py |
| `git_status` | Check repository status |
| `git_diff` | Show current changes |
| `git_commit_push` | Commit and push to GitHub |
| `get_raw_html` | Get raw HTML for a section |

## Installation

1. **Install dependencies:**

```bash
cd /Users/andreacacioppo/Documents/andreacacioppo.github.io/mcp-server
pip install -r requirements.txt
```

2. **Configure Claude Desktop:**

Add this to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "website": {
      "command": "python3",
      "args": ["/Users/andreacacioppo/Documents/andreacacioppo.github.io/mcp-server/server.py"]
    }
  }
}
```

3. **Restart Claude Desktop** to load the new MCP server.

## Usage Examples

Once connected, you can ask Claude things like:

- "Add my new IJCNN 2025 paper to my website"
- "Add the talk I'm giving in Milano-Bicocca in February"
- "Update my bio to mention my PhD defense date"
- "Show me my current publications list"
- "Regenerate the CV PDF and push all changes to GitHub"
- "What's the git status of my website?"

## How It Works

The server parses and modifies `index.html` using BeautifulSoup. When you make changes:

1. The HTML is parsed
2. The relevant section is modified
3. The "last modified" date is automatically updated
4. The HTML is saved back to disk
5. You can then commit and push with `git_commit_push`

## File Structure

```
andreacacioppo.github.io/
├── index.html              # Main CV page (modified by this server)
├── generate_cv_pdf.py      # PDF generation script
├── curriculum/
│   └── ACacioppo_CV.pdf    # Generated PDF
└── mcp-server/
    ├── server.py           # This MCP server
    ├── requirements.txt    # Python dependencies
    └── README.md           # This file
```

## Troubleshooting

**Server not appearing in Claude:**
- Check the config file path is correct
- Ensure Python 3.10+ is installed
- Try running `python3 server.py` directly to check for errors

**Git push failing:**
- Make sure you have SSH keys configured for GitHub
- Or use HTTPS with a personal access token

**PDF generation failing:**
- Check that `generate_cv_pdf.py` works when run directly
- May need additional dependencies (check that script's requirements)
