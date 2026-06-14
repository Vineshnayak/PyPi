TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FaultSnap Report - {{ manifest.exception_type }}</title>
    <style>
        :root {
            --bg-color: #ffffff;
            --container-bg: #ffffff;
            --text-color: #24292e;
            --text-muted: #586069;
            --border-color: #e1e4e8;
            --header-bg: #f6f8fa;
            --accent-color: #0366d6;
            --error-bg: #ffeef0;
            --error-border: #d73a49;
            --code-bg: #f6f8fa;
            --row-hover: #f1f8ff;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --bg-color: #0d1117;
                --container-bg: #0d1117;
                --text-color: #c9d1d9;
                --text-muted: #8b949e;
                --border-color: #30363d;
                --header-bg: #161b22;
                --accent-color: #58a6ff;
                --error-bg: #2d1114;
                --error-border: #f85149;
                --code-bg: #161b22;
                --row-hover: #1f2428;
            }
        }

        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; 
            line-height: 1.5; 
            color: var(--text-color); 
            background: var(--bg-color); 
            margin: 0; 
            padding: 20px; 
            font-size: 14px;
        }
        .container { max-width: 1200px; margin: auto; }
        h1, h2, h3 { color: var(--text-color); border-bottom: 1px solid var(--border-color); padding-bottom: 8px; font-weight: 600; }
        h1 { font-size: 24px; display: flex; justify-content: space-between; align-items: center; }
        h2 { font-size: 18px; margin-top: 30px; }
        
        .metadata-table, .env-table, .vars-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px; }
        .metadata-table th, .env-table th, .vars-table th, .metadata-table td, .env-table td, .vars-table td { 
            border: 1px solid var(--border-color); padding: 8px 12px; text-align: left; 
        }
        .metadata-table th, .env-table th, .vars-table th { background-color: var(--header-bg); font-weight: 600; color: var(--text-muted); }
        .vars-table tr:hover { background-color: var(--row-hover); }

        .exception-box { 
            background: var(--error-bg); 
            border-left: 4px solid var(--error-border); 
            padding: 16px; 
            margin-bottom: 20px; 
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; 
            overflow-x: auto; 
            white-space: pre-wrap; 
            border-radius: 4px;
            font-size: 13px;
        }
        
        .frame { border: 1px solid var(--border-color); margin-bottom: 8px; border-radius: 6px; overflow: hidden; }
        .frame-header { 
            background: var(--header-bg); 
            padding: 12px 16px; 
            cursor: pointer; 
            display: flex; 
            justify-content: space-between; 
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; 
            font-size: 13px;
        }
        .frame-header:hover { background-color: var(--row-hover); }
        .frame-content { display: none; padding: 16px; border-top: 1px solid var(--border-color); }
        .frame.active .frame-content { display: block; }
        .frame.active .frame-header { border-bottom: 1px solid var(--border-color); }
        
        .mermaid { margin: 20px 0; display: flex; justify-content: center; background: var(--header-bg); padding: 20px; border-radius: 6px; border: 1px solid var(--border-color); }
        pre { margin: 0; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; font-size: 12px; }
        code { font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; background: var(--code-bg); padding: 2px 4px; border-radius: 4px; }
        .value-cell { max-height: 200px; overflow-y: auto; display: block; word-break: break-all; }
        
        .search-box {
            width: 100%;
            padding: 8px 12px;
            margin-bottom: 15px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            background: var(--bg-color);
            color: var(--text-color);
            font-size: 13px;
            box-sizing: border-box;
        }
        .search-box:focus {
            outline: none;
            border-color: var(--accent-color);
            box-shadow: 0 0 0 3px rgba(3, 102, 214, 0.3);
        }
    </style>
    <script>{{ mermaid_js | safe }}</script>
    <script>
        const isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        mermaid.initialize({ 
            startOnLoad: true,
            theme: isDarkMode ? 'dark' : 'default'
        });
        
        function toggleFrame(element) {
            element.parentElement.classList.toggle('active');
        }

        function filterVariables(inputId, tableId) {
            const input = document.getElementById(inputId);
            const filter = input.value.toLowerCase();
            const table = document.getElementById(tableId);
            const trs = table.getElementsByTagName("tr");

            for (let i = 1; i < trs.length; i++) {
                const td = trs[i].getElementsByTagName("td")[0];
                if (td) {
                    const txtValue = td.textContent || td.innerText;
                    if (txtValue.toLowerCase().indexOf(filter) > -1) {
                        trs[i].style.display = "";
                    } else {
                        trs[i].style.display = "none";
                    }
                }       
            }
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>
            FaultSnap Report
            <span style="font-size: 14px; font-weight: normal; color: var(--text-muted);">{{ manifest.timestamp }}</span>
        </h1>
        
        <h2>Metadata</h2>
        <table class="metadata-table">
            <tr><th style="width: 20%;">Python Version</th><td>{{ manifest.python_version }}</td></tr>
            <tr><th>Platform</th><td>{{ manifest.platform }}</td></tr>
            <tr><th>Fingerprint</th><td><code style="color: var(--accent-color);">{{ manifest.fingerprint }}</code></td></tr>
            <tr><th>Exception</th><td><strong style="color: var(--error-border);">{{ manifest.exception_type }}</strong>: {{ manifest.exception_value }}</td></tr>
        </table>

        <h2>Exception Traceback</h2>
        <div class="exception-box">{{ exception_text }}</div>

        <h2>Execution Context Graph</h2>
        <div class="mermaid">
            {{ mermaid_graph | safe }}
        </div>

        <h2>Stack Frames & Variables</h2>
        <div class="frames">
            {% for frame in frames %}
            <div class="frame {% if loop.last %}active{% endif %}">
                <div class="frame-header" onclick="toggleFrame(this)">
                    <span><span style="color: var(--accent-color);">{{ frame.filename }}</span>:{{ frame.lineno }} in <strong>{{ frame.name }}</strong></span>
                    <span>▼</span>
                </div>
                <div class="frame-content">
                    {% if frame.line %}
                    <pre style="background: var(--code-bg); padding: 12px; margin-bottom: 16px; border-radius: 6px; border: 1px solid var(--border-color);"><code>{{ frame.line }}</code></pre>
                    {% endif %}
                    
                    {% if frame.locals %}
                    <input type="text" id="search-{{ loop.index }}" class="search-box" onkeyup="filterVariables('search-{{ loop.index }}', 'table-{{ loop.index }}')" placeholder="Search variables in {{ frame.name }}...">
                    <table class="vars-table" id="table-{{ loop.index }}">
                        <tr><th>Variable</th><th>Value</th></tr>
                        {% for k, v in frame.locals.items() %}
                        <tr>
                            <td style="font-weight: 600; width: 25%;">{{ k }}</td>
                            <td><div class="value-cell"><pre>{{ v }}</pre></div></td>
                        </tr>
                        {% endfor %}
                    </table>
                    {% else %}
                    <p style="color: var(--text-muted); font-style: italic;">No local variables in this frame.</p>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>

        <h2>Environment Variables</h2>
        {% if environment %}
        <input type="text" id="search-env" class="search-box" onkeyup="filterVariables('search-env', 'table-env')" placeholder="Search environment variables...">
        <table class="env-table" id="table-env">
            <tr><th>Variable</th><th>Value</th></tr>
            {% for k, v in environment.items() %}
            <tr>
                <td style="font-weight: 600; width: 30%;">{{ k }}</td>
                <td><div class="value-cell"><pre>{{ v }}</pre></div></td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p style="color: var(--text-muted); font-style: italic;">No environment variables captured.</p>
        {% endif %}
    </div>
</body>
</html>
"""
