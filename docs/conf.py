import klempner

project = 'Klempner'
copyright = '2019, Dave Shawley'
author = 'Dave Shawley'
release = klempner.version

extensions = ['sphinx.ext.autodoc']

html_sidebars = {
    '**': [
        'about.html', 'navigation.html', 'relations.html', 'searchbox.html',
        'sourcelink.html'
    ],
}
html_static_path = ['.']
html_theme = 'alabaster'
html_theme_options = {
    'github_user': 'dave-shawley',
    'github_repo': 'klempner',
}

extensions.append('sphinx.ext.extlinks')
extlinks = {
    'compare': ('https://github.com/dave-shawley/klempner/compare/%s',
                'changes: '),
}

extensions.append('sphinx.ext.intersphinx')
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}
