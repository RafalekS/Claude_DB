"""
Unified Template Manager
Handles all templates from config/templates/ folder structure
"""

from pathlib import Path
from typing import List, Dict, Optional
import re


class TemplateManager:
    """Manages templates from config/templates folder structure"""

    def __init__(self, project_root: Path = None):
        """
        Initialize template manager

        Args:
            project_root: Root directory of the project. If None, auto-detects.
        """
        if project_root is None:
            # Auto-detect project root (3 levels up from this file)
            project_root = Path(__file__).parent.parent.parent

        self.project_root = project_root
        self.templates_dir = project_root / "config" / "templates"

        # Ensure base directories exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def get_templates_dir(self, template_type: str) -> Path:
        """
        Get the templates directory for a specific type

        Args:
            template_type: One of 'agents', 'skills', 'commands', 'hooks', 'statuslines', 'mcp'

        Returns:
            Path to the templates directory
        """
        valid_types = ['agents', 'skills', 'commands', 'hooks', 'statuslines', 'mcp']
        if template_type not in valid_types:
            raise ValueError(f"Invalid template type: {template_type}. Must be one of {valid_types}")

        template_dir = self.templates_dir / template_type
        template_dir.mkdir(parents=True, exist_ok=True)
        return template_dir

    def list_templates(self, template_type: str) -> List[str]:
        """
        List all available templates for a given type (including subfolders)

        Args:
            template_type: One of 'agents', 'skills', 'commands', 'hooks', 'statuslines', 'mcp'

        Returns:
            List of template names (without extension, with subfolder paths like 'code-quality/code-reviewer')
        """
        template_dir = self.get_templates_dir(template_type)
        templates = []

        # MCP templates are JSON files, others are MD
        if template_type == 'mcp':
            # Recursive search for JSON files
            for file_path in template_dir.rglob("*.json"):
                # Get relative path from template_dir
                rel_path = file_path.relative_to(template_dir)
                # Convert to string without extension
                template_name = str(rel_path.with_suffix('')).replace('\\', '/')
                templates.append(template_name)
        else:
            # Recursive search for MD files
            for file_path in template_dir.rglob("*.md"):
                # Get relative path from template_dir
                rel_path = file_path.relative_to(template_dir)
                # Convert to string without extension
                template_name = str(rel_path.with_suffix('')).replace('\\', '/')
                templates.append(template_name)

        return sorted(templates)

    def get_template_path(self, template_type: str, template_name: str) -> Path:
        """
        Get the full path to a template file

        Args:
            template_type: One of 'agents', 'skills', 'commands', 'hooks', 'statuslines', 'mcp'
            template_name: Name of the template (with or without extension)

        Returns:
            Path to the template file
        """
        template_dir = self.get_templates_dir(template_type)

        # Add appropriate extension if not present
        if template_type == 'mcp':
            if not template_name.endswith('.json'):
                template_name = f"{template_name}.json"
        else:
            if not template_name.endswith('.md'):
                template_name = f"{template_name}.md"

        return template_dir / template_name

    def read_template(self, template_type: str, template_name: str) -> str:
        """
        Read template content

        Args:
            template_type: One of 'agents', 'skills', 'commands', 'hooks', 'statuslines'
            template_name: Name of the template

        Returns:
            Template content as string

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        template_path = self.get_template_path(template_type, template_name)

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def save_template(self, template_type: str, template_name: str, content: str) -> Path:
        """
        Save a new template (supports subfolders like 'code-quality/code-reviewer')

        Args:
            template_type: One of 'agents', 'skills', 'commands', 'hooks', 'statuslines'
            template_name: Name for the template (can include subfolder path)
            content: Template content

        Returns:
            Path to the saved template file
        """
        template_path = self.get_template_path(template_type, template_name)

        # Create parent directories if they don't exist
        template_path.parent.mkdir(parents=True, exist_ok=True)

        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return template_path

    def delete_template(self, template_type: str, template_name: str) -> bool:
        """
        Delete a template

        Args:
            template_type: One of 'agents', 'skills', 'commands', 'hooks', 'statuslines'
            template_name: Name of the template

        Returns:
            True if deleted, False if not found
        """
        template_path = self.get_template_path(template_type, template_name)

        if template_path.exists():
            template_path.unlink()
            return True

        return False

    def get_template_info(self, template_type: str, template_name: str) -> Optional[Dict[str, str]]:
        """
        Extract frontmatter info from a template

        Args:
            template_type: One of 'agents', 'skills', 'commands', 'hooks', 'statuslines'
            template_name: Name of the template

        Returns:
            Dictionary with frontmatter fields (name, description, etc.) or None
        """
        try:
            content = self.read_template(template_type, template_name)

            # Parse YAML frontmatter
            frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
            match = re.match(frontmatter_pattern, content, re.DOTALL)

            if match:
                frontmatter = match.group(1)
                info = {}

                # Parse simple key: value pairs
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()

                return info

            # For commands without frontmatter, extract description from markdown
            if template_type == 'commands':
                info = {}
                lines = content.split('\n')

                # Try to get title from # heading
                for line in lines:
                    if line.startswith('# '):
                        info['name'] = line[2:].strip()
                        break

                # Try to get description - first non-empty line after title, or ## Description section
                found_title = False
                for i, line in enumerate(lines):
                    if line.startswith('# '):
                        found_title = True
                        continue
                    if found_title and line.strip() and not line.startswith('#'):
                        info['description'] = line.strip()
                        break
                    if line.strip().lower() == '## description':
                        # Get the next non-empty line
                        for j in range(i + 1, min(i + 5, len(lines))):
                            if lines[j].strip() and not lines[j].startswith('#'):
                                info['description'] = lines[j].strip()
                                break
                        break

                return info if info else None

            return None

        except Exception:
            return None

    def create_from_template(self, template_type: str, template_name: str,
                           target_name: str, replacements: Dict[str, str] = None) -> str:
        """
        Create new content from a template with replacements

        Args:
            template_type: One of 'agents', 'skills', 'commands', 'hooks', 'statuslines'
            template_name: Name of the template to use
            target_name: Name for the new item (will replace {name} placeholder)
            replacements: Optional dict of {placeholder: value} to replace in template

        Returns:
            New content with replacements applied
        """
        content = self.read_template(template_type, template_name)

        # Default replacements
        if replacements is None:
            replacements = {}

        # Always include name replacement
        replacements['name'] = target_name
        replacements['NAME'] = target_name.replace('-', ' ').title()

        # Apply replacements
        for placeholder, value in replacements.items():
            # Support both {placeholder} and {PLACEHOLDER} formats
            content = content.replace(f"{{{placeholder}}}", value)
            content = content.replace(f"{{{placeholder.upper()}}}", value.replace('-', ' ').title())
            content = content.replace(f"{{{placeholder.lower()}}}", value)

        # Update name field in frontmatter if present
        content = re.sub(
            r'(^---\s*\nname:\s*)[^\n]+',
            f'\\1{target_name}',
            content,
            flags=re.MULTILINE
        )

        return content


# Singleton instance
_template_manager = None


def get_template_manager() -> TemplateManager:
    """Get singleton instance of TemplateManager"""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager
