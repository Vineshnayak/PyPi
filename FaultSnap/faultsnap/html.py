import os
from faultsnap.capsule import read_capsule, read_manifest
from faultsnap.context_graph import generate_mermaid_graph
from faultsnap.templates.html_report import TEMPLATE

def generate_html_report(capsule_path, output_path=None):
    """
    Generate a standalone HTML report from a .faultsnap capsule.
    Requires jinja2 to be installed.
    """
    try:
        from jinja2 import Environment, select_autoescape
    except ImportError:
        raise ImportError("The 'jinja2' library is required to generate HTML reports. Run `pip install faultsnap[html]`.")
        
    crash_data = read_capsule(capsule_path)
    manifest = crash_data.get("metadata", {})
    frames = crash_data.get("frames", [])
    
    mermaid_graph = generate_mermaid_graph(frames)
    
    # Load Mermaid JS
    try:
        import pkgutil
        mermaid_js = pkgutil.get_data("faultsnap", "templates/mermaid.min.js").decode("utf-8")
    except Exception:
        mermaid_js = "/* Failed to load local mermaid.min.js */"
    
    env = Environment(autoescape=select_autoescape(['html', 'xml']))
    template = env.from_string(TEMPLATE)
    html_content = template.render(
        manifest=manifest,
        exception_text=crash_data.get("exception_text", ""),
        mermaid_graph=mermaid_graph,
        frames=frames,
        environment=crash_data.get("environment", {}),
        mermaid_js=mermaid_js
    )
    
    if output_path is None:
        base_name = os.path.basename(capsule_path)
        dir_name = os.path.dirname(capsule_path)
        output_path = os.path.join(dir_name, os.path.splitext(base_name)[0] + ".html")
        
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return output_path
