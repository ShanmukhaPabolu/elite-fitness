import os
import re

html_files = [f for f in os.listdir('.') if f.endswith('.html')]

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Inject `<link rel="stylesheet" href="static/responsive.css">`
    if 'static/responsive.css' not in content:
        content = content.replace('</head>', '    <link rel="stylesheet" href="static/responsive.css">\n</head>')

    # 2. Fix explicit 100vw to 100% to avoid scrollbars
    content = re.sub(r'width:\s*100vw\s*;', 'width: 100%;', content)

    # 3. Write back
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print(f'Successfully processed {len(html_files)} HTML files.')
