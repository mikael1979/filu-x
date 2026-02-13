from pathlib import Path
from typing import Dict, Any
import json
from jinja2 import Environment, PackageLoader, select_autoescape

class TemplateEngine:
    def __init__(self):
        self.env = Environment(
            loader=PackageLoader("filu_x", "templates"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def _render(self, template_name: str, context: Dict[str, Any]) -> dict:
        template = self.env.get_template(template_name)
        rendered = template.render(context)
        return json.loads(rendered)
    
    def render_profile(self, context: Dict[str, Any]) -> dict:
        return self._render("profile.json.j2", context)
    
    def render_manifest(self, context: Dict[str, Any]) -> dict:
        return self._render("manifest.json.j2", context)
    
    def render_follow_list(self, context: Dict[str, Any]) -> dict:
        return self._render("follow_list.json.j2", context)
    
    def render_private_config(self, context: Dict[str, Any]) -> dict:
        return self._render("private_config.json.j2", context)
    
    def render_post(self, context: Dict[str, Any]) -> dict:
        """Luo post.json templatista"""
        if "tags" in context and isinstance(context["tags"], str):
            context["tags"] = [t.strip() for t in context["tags"].split(",") if t.strip()]
        return self._render("post.json.j2", context)
