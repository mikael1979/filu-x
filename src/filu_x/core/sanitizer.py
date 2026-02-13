"""Basic sanitization for security (minimal dependencies)"""
import re

def sanitize_html(html: str) -> str:
    """Remove dangerous elements/attributes from HTML"""
    # Simple tag stripping for alpha version
    # Full sanitization with bleach in beta
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    return text

def sanitize_markdown(md: str) -> str:
    """Return markdown as-is for alpha (sanitize in beta)"""
    return md.strip()

def sanitize_svg(svg: str) -> str:
    """Remove scripts from SVG"""
    svg = re.sub(r'<script[^>]*>.*?</script>', '', svg, flags=re.DOTALL | re.IGNORECASE)
    svg = re.sub(r'on\w+\s*=', '', svg, flags=re.IGNORECASE)
    return svg

def sanitize_css(css: str) -> str:
    """Remove dangerous CSS"""
    css = re.sub(r'@import[^;]+;', '', css)
    css = re.sub(r'url\(\s*javascript:[^)]+\)', 'url()', css, flags=re.IGNORECASE)
    css = re.sub(r'url\(\s*data:[^)]+\)', 'url()', css, flags=re.IGNORECASE)
    return css
