import fitz

def analyze_pdf(filepath):
    try:
        doc = fitz.open(filepath)
        page = doc[0]
        blocks = page.get_text('dict')['blocks']
        
        with open('index_layout_utf8.txt', 'w', encoding='utf-8') as f:
            f.write("--- Text Blocks ---\n")
            for b in blocks:
                if b['type'] == 0: # text block
                    lines = []
                    for l in b.get('lines', []):
                        for s in l.get('spans', []):
                            lines.append(s['text'].strip())
                    text = " ".join(lines).strip()
                    if text:
                        f.write(f"Text: '{text}'\n")
                        f.write(f"BBox: {b['bbox']}\n")
                        if 'lines' in b and b['lines'] and 'spans' in b['lines'][0] and b['lines'][0]['spans']:
                            f.write(f"Font: {b['lines'][0]['spans'][0]['font']}\n")
                            f.write(f"Size: {b['lines'][0]['spans'][0]['size']:.2f}\n")
                            f.write(f"Color: {b['lines'][0]['spans'][0]['color']}\n")
                        f.write("-" * 20 + "\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    analyze_pdf('templates/INDICE.pdf')
