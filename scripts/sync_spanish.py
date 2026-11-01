"""Synchronize Spanish page text from English, preserving markup and behavior.
Requires OPENAI_API_KEY as a GitHub Actions repository secret.
"""
import os, json, re, urllib.request, html
from pathlib import Path
from html.parser import HTMLParser

PAGES=['index.html','ufc-championship/index.html','ufc-fight-night/index.html','nfl-championship/index.html','super-bowl/index.html']
API='https://api.openai.com/v1/chat/completions'
class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False);self.tags=[];self.texts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        self.tags.append(tag)
        if tag in ('script','style','svg'):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ('script','style','svg'):self.skip=max(0,self.skip-1)
        if self.tags:self.tags.pop()
    def handle_data(self,data):
        if not self.skip and data.strip() and self.tags and self.tags[-1] not in ('script','style'):
            self.texts.append(data.strip())
def translate(batch):
    req=urllib.request.Request(API,data=json.dumps({
      'model':'gpt-4.1-mini','temperature':0,
      'messages':[{'role':'system','content':'Translate each English website UI text into natural Latin American Spanish for a premium VIP poker event website. Preserve names, brands, poker terms (Texas Hold’em, PLO), numerical values, event dates, HTML entities and placeholders. Return ONLY a JSON array of translated strings in exactly the same order and count. No markdown.'},{'role':'user','content':json.dumps(batch,ensure_ascii=False)}],
      'response_format':{'type':'json_object'}
    }).encode(),headers={'Authorization':'Bearer '+os.environ['OPENAI_API_KEY'],'Content-Type':'application/json'})
    # JSON object output requested; expected shape {"translations": [...]}
    with urllib.request.urlopen(req,timeout=120) as response:
        result=json.load(response)
    data=json.loads(result['choices'][0]['message']['content'])
    translations=data['translations']
    if len(translations)!=len(batch) or not all(isinstance(x,str) for x in translations):
        raise ValueError('Translation result count mismatch')
    return translations

def main():
    for page in PAGES:
        source=Path(page).read_text(encoding='utf-8')
        parser=Extract();parser.feed(source)
        unique=list(dict.fromkeys(parser.texts))
        translated={}
        for i in range(0,len(unique),45):
            batch=unique[i:i+45]
            translated.update(zip(batch,translate(batch)))
        # Replace visible text nodes only, never JS/CSS/HTML attributes.
        class Replacer(HTMLParser):
            def __init__(self):super().__init__(convert_charrefs=False);self.output=[];self.skip=0
            def handle_starttag(self,tag,attrs):
                self.output.append(self.get_starttag_text())
                if tag in ('script','style','svg'):self.skip+=1
            def handle_startendtag(self,tag,attrs):self.output.append(self.get_starttag_text())
            def handle_endtag(self,tag):
                self.output.append('</'+tag+'>')
                if tag in ('script','style','svg'):self.skip=max(0,self.skip-1)
            def handle_data(self,data):
                t=data.strip()
                self.output.append(data.replace(t,html.escape(translated[t],quote=False),1) if t in translated and not self.skip else data)
            def handle_entityref(self,name):self.output.append('&'+name+';')
            def handle_charref(self,name):self.output.append('&#'+name+';')
            def handle_comment(self,data):self.output.append('<!--'+data+'-->')
            def handle_decl(self,decl):self.output.append('<!'+decl+'>')
        r=Replacer();r.feed(source);s=''.join(r.output)
        s=s.replace('<html lang="en">','<html lang="es">')
        s=re.sub(r'<link rel="canonical" href="https://pokerevent.net(/[^"]*)">',lambda m:'<link rel="canonical" href="https://pokerevent.net/es'+m.group(1)+'">',s)
        s=re.sub(r'<meta property="og:url" content="https://pokerevent.net(/[^"]*)">',lambda m:'<meta property="og:url" content="https://pokerevent.net/es'+m.group(1)+'">',s)
        s=s.replace('"inLanguage":"en"','"inLanguage":"es"')
        s=re.sub(r'href="/(?!/|es/)', 'href="/es/',s)
        s=s.replace('href="../index.html"','href="/es/"').replace('href="index.html"','href="/es/"')
        root='' if page=='index.html' else page.split('/')[0]+'/'
        s=re.sub(r'src="(?!https?:|/|data:)([^"]+)"',lambda m:'src="/'+root+m.group(1)+'"',s)
        if '/assets/language.css' not in s:s=s.replace('</head>','<link rel="stylesheet" href="/assets/language.css"></head>')
        if '/assets/language.js' not in s:s=s.replace('</body>','<script src="/assets/language.js" defer></script></body>')
        target=Path('es')/page;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(s,encoding='utf-8')
        print('Updated',target)
if __name__=='__main__':main()
