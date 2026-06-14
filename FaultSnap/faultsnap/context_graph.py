def generate_mermaid_graph(frames):
    """
    Generate a Mermaid.js flowchart string representing the execution context graph.
    """
    if not frames:
        return ""
        
    lines = ["graph TD"]
    
    for i, frame in enumerate(frames):
        name = frame.get("name", "unknown").replace("<", "&lt;").replace(">", "&gt;")
        filename = frame.get("filename", "unknown").split("/")[-1]
        lineno = frame.get("lineno", "?")
        
        node_id = f"frame_{i}"
        node_label = f"{name}<br/><i>{filename}:{lineno}</i>"
        
        # Highlight the last frame (where the crash happened)
        if i == len(frames) - 1:
            lines.append(f"    {node_id}[\"{node_label}\"]:::crashNode")
        else:
            lines.append(f"    {node_id}[\"{node_label}\"]")
            
        if i > 0:
            prev_node_id = f"frame_{i-1}"
            lines.append(f"    {prev_node_id} -->|calls| {node_id}")
            
    lines.append("")
    lines.append("    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;")
    lines.append("    classDef crashNode fill:#ffcccc,stroke:#cc0000,stroke-width:4px;")
    
    return "\n".join(lines)
