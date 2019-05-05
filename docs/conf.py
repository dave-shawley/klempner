import klempner

project = 'Klempner'
copyright = '2019, Dave Shawley'
author = 'Dave Shawley'
release = klempner.version

extensions = ['sphinx.ext.autodoc']

html_sidebars = {
    '**': [
        'about.html', 'navigation.html', 'relations.html', 'localtoc.html',
        'searchbox.html', 'sourcelink.html'
    ],
}
html_static_path = ['.']
html_theme = 'alabaster'
html_theme_options = {
    'github_user': 'dave-shawley',
    'github_repo': 'klempner',
}
