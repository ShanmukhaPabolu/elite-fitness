import re

with open('ai.html', 'r', encoding='utf-8') as f:
    ai_content = f.read()

with open('aivoice.html', 'r', encoding='utf-8') as f:
    aivoice_content = f.read()

secure_logout_js = re.search(r'logoutBtn\.addEventListener\(\'click\', \(e\) => \{.*?\}\);', aivoice_content, re.DOTALL)
if secure_logout_js:
    ai_content = re.sub(r'logoutBtn\.addEventListener\(\'click\', \(e\) => \{.*?userNameElement\.textContent = "Athlete";\s*\}\);', secure_logout_js.group(0), ai_content, flags=re.DOTALL)

ai_content = ai_content.replace('<a href="/" class="dropdown-item" id="logoutBtn">', '<a href="/logout" class="dropdown-item" id="logoutBtn">')

with open('ai.html', 'w', encoding='utf-8') as f:
    f.write(ai_content)

with open('aivoice.html', 'w', encoding='utf-8') as f:
    f.write(ai_content)

print('Successfully synchronized ai.html and aivoice.html')
