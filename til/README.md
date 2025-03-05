README.md

# How to generate the website

## Requirements

```
pip install beautifulsoup4
```

## Generate the website

```
python make_website.py
```


pandoc -s md/something.md -o html/something.html --css https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.1.0/github-markdown.min.css