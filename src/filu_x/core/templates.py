"""Jinja2 template engine for Filu-X JSON generation"""
from pathlib import Path
from typing import Dict, Any
import json
from jinja2 import Environment, PackageLoader, select_autoescape

class TemplateEngine:
    """Render JSON templates using Jinja2"""
    
    def __init__(self):
        self.env = Environment(
            loader=PackageLoader("filu_x", "templates"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def _render(self, template_name: str, context: Dict[str, Any]) -> dict:
        """Render template and parse JSON result"""
        template = self.env.get_template(template_name)
        rendered = template.render(context)
        return json.loads(rendered)
    
    def render_profile(self, context: Dict[str, Any]) -> dict:
        """Render profile.json template"""
        return self._render("profile.json.j2", context)
    
    def render_manifest(self, context: Dict[str, Any]) -> dict:
        """Render manifest.json template"""
        return self._render("manifest.json.j2", context)
    
    def render_follow_list(self, context: Dict[str, Any]) -> dict:
        """Render follow_list.json template"""
        return self._render("follow_list.json.j2", context)
    
    def render_private_config(self, context: Dict[str, Any]) -> dict:
        """Render private_config.json template"""
        return self._render("private_config.json.j2", context)
    
    def render_post(self, context: Dict[str, Any]) -> dict:
        """Render post.json template"""
        if "tags" in context and isinstance(context["tags"], str):
            context["tags"] = [t.strip() for t in context["tags"].split(",") if t.strip()]
        return self._render("post.json.j2", context)
