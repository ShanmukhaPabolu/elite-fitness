import os
import glob

html_files = glob.glob('*.html')
for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '<script src=\"/static/sync.js\"></script>' not in content:
        # inject before </head>
        modified = content.replace('</head>', '    <script src=\"/static/sync.js\"></script>\n</head>')
        if modified != content:
            with open(file, 'w', encoding='utf-8') as f:
                f.write(modified)
            print(f'Updated {file}')
