import hcl2

with open('anime-data/gintama.anime', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove lines starting with '@version'
cleaned = [line for line in lines if not line.strip().startswith('@version')]

text = ''.join(cleaned)

data = hcl2.loads(text)

print(data)
