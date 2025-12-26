import os
import re
import json
import glob

# Constants
SOURCE_DIR = "../artigos-texto"
OUTPUT_DIR = "posts"
INDEX_FILE = "index.html"
SEO_FILE = "../artigos-texto/0-Instruções para SEO.md"
ASSETS_DIR = "assets"
PLACEHOLDER_IMG = "../assets/article_placeholder.png" # Relative to posts
PLACEHOLDER_IMG_INDEX = "assets/article_placeholder.png" # Relative to index

# Theme Colors (Inferred "Pet Friendly" palette)
# We will inject these via Tailwind config
TAILWIND_SCRIPT = """
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          brand: {
            50: '#fff7ed',
            100: '#ffedd5',
            200: '#fed7aa',
            300: '#fdba74',
            400: '#fb923c',
            500: '#f97316', # Orange-500
            600: '#ea580c',
            700: '#c2410c',
            800: '#9a3412',
            900: '#7c2d12',
          },
          accent: {
             50: '#f0f9ff',
             900: '#0c4a6e',
          }
        },
        fontFamily: {
          sans: ['Outfit', 'sans-serif'],
        }
      }
    }
  }
</script>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
"""

HEADER_TEMPLATE = """
<header class="bg-white shadow-sm sticky top-0 z-50">
    <div class="container mx-auto px-4 py-4 flex justify-between items-center">
        <a href="{home_link}" class="flex items-center gap-2 group">
            <img src="{logo_path}" alt="Meu Pet Cão Logo" class="h-10 w-auto group-hover:scale-105 transition-transform duration-300">
            <span class="text-xl font-bold text-brand-900 tracking-tight">MeuPet<span class="text-brand-500">Cão</span></span>
        </a>
        <nav class="hidden md:flex gap-6">
            <a href="{home_link}" class="text-gray-600 hover:text-brand-600 font-medium transition-colors">Início</a>
            <a href="#" class="text-gray-600 hover:text-brand-600 font-medium transition-colors">Categorias</a>
            <a href="#" class="text-gray-600 hover:text-brand-600 font-medium transition-colors">Sobre</a>
            <a href="#" class="text-gray-600 hover:text-brand-600 font-medium transition-colors">Contato</a>
        </nav>
        <button class="md:hidden text-gray-600 focus:outline-none">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
        </button>
    </div>
</header>
"""

FOOTER_TEMPLATE = """
<footer class="bg-brand-900 text-brand-50 mt-12 py-12">
    <div class="container mx-auto px-4 grid grid-cols-1 md:grid-cols-3 gap-8">
        <div>
            <h3 class="text-xl font-bold mb-4 flex items-center gap-2">MeuPet<span class="text-brand-400">Cão</span></h3>
            <p class="text-brand-200 text-sm leading-relaxed">
                Seu portal confiável para cuidar melhor do seu melhor amigo. Dicas de saúde, alimentação, comportamento e muito amor.
            </p>
        </div>
        <div>
            <h4 class="font-semibold mb-4 text-white">Links Rápidos</h4>
            <ul class="space-y-2 text-sm text-brand-200">
                <li><a href="{home_link}" class="hover:text-white transition-colors">Início</a></li>
                <li><a href="#" class="hover:text-white transition-colors">Sobre Nós</a></li>
                <li><a href="#" class="hover:text-white transition-colors">Política de Privacidade</a></li>
                <li><a href="#" class="hover:text-white transition-colors">Termos de Uso</a></li>
            </ul>
        </div>
        <div>
            <h4 class="font-semibold mb-4 text-white">Newsletter</h4>
            <p class="text-brand-200 text-sm mb-4">Receba dicas exclusivas no seu e-mail.</p>
            <form class="flex gap-2">
                <input type="email" placeholder="Seu e-mail..." class="bg-brand-800 text-white placeholder-brand-400 px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 w-full" disabled>
                <button type="submit" class="bg-brand-500 hover:bg-brand-400 text-white px-4 py-2 rounded-lg font-medium transition-colors" disabled>OK</button>
            </form>
        </div>
    </div>
    <div class="container mx-auto px-4 mt-8 pt-8 border-t border-brand-800 text-center text-sm text-brand-400">
        &copy; 2024 Meu Pet Cão. Todos os direitos reservados.
    </div>
</footer>
"""

def simple_markdown_to_html(md_text):
    """Converts basic markdown to HTML with Tailwind Typography classes."""
    html_lines = []
    in_list = False
    
    for line in md_text.split('\n'):
        line = line.strip()
        if not line:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue
        
        # Headers
        if line.startswith('# '):
            html_lines.append(f'<h1 class="text-4xl md:text-5xl font-bold text-gray-900 mb-6 leading-tight">{line[2:]}</h1>')
        elif line.startswith('## '):
            html_lines.append(f'<h2 class="text-2xl md:text-3xl font-bold text-gray-800 mt-10 mb-4">{line[3:]}</h2>')
        elif line.startswith('### '):
            html_lines.append(f'<h3 class="text-xl font-bold text-gray-800 mt-8 mb-3">{line[4:]}</h3>')
        
        # Bold
        line = re.sub(r'\*\*(.*?)\*\*', r'<strong class="font-bold text-gray-900">\1</strong>', line)
        
        # Lists
        if line.startswith('- '):
            if not in_list:
                html_lines.append('<ul class="list-disc pl-5 mb-6 space-y-2 text-gray-700">')
                in_list = True
            html_lines.append(f'<li>{line[2:]}</li>')
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            
            # Paragraphs (ignore if it's already a header)
            if not line.startswith('<h'):
                if line.startswith('---'):
                     html_lines.append('<hr class="my-8 border-gray-200">')
                elif line.startswith('*') and line.endswith('*'):
                     html_lines.append(f'<p class="text-sm text-gray-500 italic mt-8">{line[1:-1]}</p>')
                else:
                    html_lines.append(f'<p class="text-lg text-gray-700 leading-relaxed mb-6">{line}</p>')
    
    if in_list:
        html_lines.append("</ul>")
        
    return '\n'.join(html_lines)

def parse_seo_instructions(seo_path):
    """Parses the SEO instructions file to get mapping of Title -> Slug/Meta."""
    mapping = {}
    current_section = None
    
    if not os.path.exists(seo_path):
        return mapping

    with open(seo_path, 'r') as f:
        content = f.read()
    
    # Very basic parsing based on the file structure viewed
    # We will try to match titles to slugs and meta descriptions
    
    # Extract Slugs
    # URL structure section
    url_section = re.search(r'## Estrutura de URL Sugerida:(.*?)(##|$)', content, re.DOTALL)
    if url_section:
        urls = re.findall(r'- `/(.*?)`', url_section.group(1))
        # This is a list of slugs. We need to map them to articles. 
        # The instructions numbered the articles 1-10.
        # Let's map Index -> Slug
        slug_map = {i+1: url for i, url in enumerate(urls)}
    
    # Extract Meta Descriptions
    meta_section = re.search(r'## Meta Descrições Sugeridas.*?:(.*?)(##|$)', content, re.DOTALL)
    meta_map = {}
    if meta_section:
        metas = re.findall(r'(\d+)\.\s*\*\*(.*?)\*\*:\s*"(.*?)"', meta_section.group(1))
        for idx, topic, desc in metas:
            meta_map[int(idx)] = desc

    # Extract Categories
    cat_section = re.search(r'## Categorias Sugeridas.*?:(.*?)(##|$)', content, re.DOTALL)
    cat_map = {} # Article Index -> Category Name
    if cat_section:
        # - **Saúde e Bem-Estar** (Artigos 3, 5, 10)
        cats = re.findall(r'- \*\*(.*?)\*\* \(Artigos (.*?)\)', cat_section.group(1))
        for cat_name, art_indices in cats:
            indices = [int(x.strip()) for x in art_indices.split(',')]
            for i in indices:
                cat_map[i] = cat_name
    
    # Extract Titles from Table to link Index -> Title
    table_section = re.search(r'\| # \| Título do Artigo \|.*?\n\|---\|.*?\|\n(.*?)\n\n', content, re.DOTALL)
    title_map = {} # Title -> Index
    if table_section:
        rows = table_section.group(1).split('\n')
        for row in rows:
            if '|' in row:
                parts = [p.strip() for p in row.split('|')]
                if len(parts) > 2 and parts[1].isdigit():
                    idx = int(parts[1])
                    title = parts[2]
                    title_map[title] = idx

    # Combine all into a master map keyed by Title (loose match)
    final_map = {}
    for title, idx in title_map.items():
        final_map[title] = {
            'id': idx,
            'slug': slug_map.get(idx, f'article-{idx}'),
            'description': meta_map.get(idx, ''),
            'category': cat_map.get(idx, 'Geral')
        }
    
    return final_map

def find_article_metadata(filename, content, seo_map):
    # Try to find title in content
    title_match = re.search(r'^# (.*?)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else filename.replace('.md', '')
    
    # Try to match with SEO map
    # We do fuzzy match because filename might differ slightly from table title
    best_match = None
    
    # direct match
    if title in seo_map:
        best_match = seo_map[title]
    else:
        # substring match
        for map_title, data in seo_map.items():
            if map_title in title or title in map_title:
                best_match = data
                break
    
    if not best_match:
        # Fallback
        slug = title.lower().replace(' ', '-').replace(':', '').replace('ç', 'c').replace('ã', 'a')
        best_match = {'slug': slug, 'description': '', 'category': 'Geral'}
        
    return title, best_match

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    seo_map = parse_seo_instructions(SEO_FILE)
    print(f"Loaded SEO Map for {len(seo_map)} articles.")

    articles_data = []

    files = glob.glob(os.path.join(SOURCE_DIR, "*.md"))
    for file_path in files:
        filename = os.path.basename(file_path)
        if "Instruções" in filename:
            continue
            
        with open(file_path, 'r') as f:
            md_content = f.read()

        title, metadata = find_article_metadata(filename, md_content, seo_map)
        slug = metadata.get('slug')
        description = metadata.get('description')
        category = metadata.get('category')
        
        # Determine Image Path
        # specific image path relative to 'posts/' folder
        specific_img_name = f"{slug}.jpg"
        if os.path.exists(os.path.join("assets", specific_img_name)):
            article_img_path = f"../assets/{specific_img_name}"
            index_img_path = f"assets/{specific_img_name}"
        else:
            article_img_path = PLACEHOLDER_IMG
            index_img_path = PLACEHOLDER_IMG_INDEX

        # HTML Content
        body_html = simple_markdown_to_html(md_content)
        
        # Full Page HTML
        page_html = f"""<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Meu Pet Cão</title>
    <meta name="description" content="{description}">
    {TAILWIND_SCRIPT}
</head>
<body class="bg-brand-50 min-h-screen font-sans flex flex-col">
    {HEADER_TEMPLATE.format(home_link="../index.html", logo_path="../logo_meu_pet_cao.png")}
    
    <main class="flex-grow container mx-auto px-4 py-8 md:py-12 max-w-4xl">
        <article class="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div class="h-64 md:h-80 w-full bg-brand-100 relative overflow-hidden group">
                 <img src="{article_img_path}" alt="{title}" class="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-700">
                 <div class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
                 <div class="absolute bottom-0 left-0 p-6 md:p-8">
                    <span class="bg-brand-500 text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide mb-3 inline-block">{category}</span>
                    <h1 class="text-3xl md:text-5xl font-bold text-white leading-tight shadow-sm">{title}</h1>
                 </div>
            </div>
            
            <div class="p-6 md:p-12 prose prose-lg prose-brand max-w-none text-gray-700">
                {body_html}
            </div>
        </article>
        
        <div class="mt-12 text-center">
            <a href="../index.html" class="inline-flex items-center gap-2 text-brand-600 font-semibold hover:text-brand-800 transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
                Voltar para o Início
            </a>
        </div>
    </main>

    {FOOTER_TEMPLATE.format(home_link="../index.html")}
</body>
</html>
"""
        output_path = os.path.join(OUTPUT_DIR, f"{slug}.html")
        with open(output_path, 'w') as f:
            f.write(page_html)
            
        articles_data.append({
            'title': title,
            'slug': slug,
            'category': category,
            'description': description,
            'image_path': index_img_path
        })
        print(f"Generated: {slug}.html")

    # Generate Index
    # Group by category
    categories = {}
    for art in articles_data:
        cat = art['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(art)

    # Index HTML
    index_html_content = ""
    
    # Hero Section
    index_html_content += f"""
    <section class="bg-brand-100 py-16 md:py-24 relative overflow-hidden">
        <div class="container mx-auto px-4 relative z-10 text-center">
            <span class="text-brand-600 font-bold tracking-wider uppercase text-sm mb-4 block">Bem-vindo ao Meu Pet Cão</span>
            <h1 class="text-4xl md:text-6xl font-extrabold text-brand-900 mb-6 leading-tight">
                Tudo o que seu <span class="text-brand-600">melhor amigo</span> precisa saber.
            </h1>
            <p class="text-xl text-brand-800/80 mb-10 max-w-2xl mx-auto">
                Dicas de saúde, comportamento e bem-estar para fazer a vida do seu cão ainda mais feliz.
            </p>
            <div class="flex flex-wrap justify-center gap-4">
                 <a href="#featured" class="bg-brand-600 text-white px-8 py-3 rounded-full font-bold hover:bg-brand-700 transition-all transform hover:-translate-y-1 shadow-lg shadow-brand-500/30">
                    Começar a Ler
                </a>
            </div>
        </div>
        <!-- Decorative background elements -->
        <div class="absolute top-0 left-0 w-64 h-64 bg-brand-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 -translate-x-1/2 -translate-y-1/2"></div>
        <div class="absolute bottom-0 right-0 w-80 h-80 bg-accent-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 translate-x-1/3 translate-y-1/3"></div>
    </section>
    """

    index_html_content += '<div id="featured" class="container mx-auto px-4 py-16 space-y-20">'

    for cat_name, items in categories.items():
        index_html_content += f"""
        <section>
            <div class="flex items-end justify-between mb-8 border-b border-gray-200 pb-4">
                <h2 class="text-3xl font-bold text-gray-800">{cat_name}</h2>
                <a href="#" class="text-brand-600 hover:text-brand-800 font-medium text-sm hidden sm:block">Ver todos &rarr;</a>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        """
        
        for item in items:
            index_html_content += f"""
            <a href="posts/{item['slug']}.html" class="group bg-white rounded-xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100 flex flex-col h-full transform hover:-translate-y-1">
                <div class="h-48 overflow-hidden bg-gray-100 relative">
                    <img src="{item['image_path']}" alt="{item['title']}" class="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-500">
                    <div class="absolute top-4 left-4">
                        <span class="bg-white/90 backdrop-blur-sm text-brand-700 text-xs font-bold px-2 py-1 rounded shadow-sm">{item['category']}</span>
                    </div>
                </div>
                <div class="p-6 flex-1 flex flex-col">
                    <h3 class="text-xl font-bold text-gray-900 mb-3 group-hover:text-brand-600 transition-colors line-clamp-2">
                        {item['title']}
                    </h3>
                    <p class="text-gray-500 text-sm line-clamp-3 mb-4 flex-1">
                        {item['description']}
                    </p>
                    <span class="text-brand-600 text-sm font-semibold flex items-center gap-1 group-hover:gap-2 transition-all">
                        Ler Artigo <span class="text-lg">&rarr;</span>
                    </span>
                </div>
            </a>
            """
        
        index_html_content += """
            </div>
        </section>
        """
    
    index_html_content += "</div>"

    index_page = f"""<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meu Pet Cão | O Portal do Seu Melhor Amigo</title>
    <meta name="description" content="Portal completo com dicas de saúde, adestramento, alimentação e cuidados para cães. Tudo para o tutor consciente.">
    {TAILWIND_SCRIPT}
</head>
<body class="bg-brand-50 min-h-screen font-sans flex flex-col">
    {HEADER_TEMPLATE.format(home_link="index.html", logo_path="logo_meu_pet_cao.png")}
    
    <main class="flex-grow">
        {index_html_content}
    </main>

    {FOOTER_TEMPLATE.format(home_link="index.html")}
</body>
</html>
"""
    
    with open(INDEX_FILE, 'w') as f:
        f.write(index_page)
    print("Generated index.html")

if __name__ == "__main__":
    main()
