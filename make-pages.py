#!/usr/bin/env python3
import sys
import os
import re
import argparse
import json
import yaml
import jinja2 as jinja
from datetime import datetime
from dotenv import load_dotenv
from dataclasses import dataclass


def getArgs():
    def csl(arg):
        return arg.split(',')

    parser = argparse.ArgumentParser(description='Render templates')
    parser.add_argument('root', help='Directory with templates and data')
    parser.add_argument('dist', help='Output directory')
    parser.add_argument('-l', '--langs', type=csl, default=[], help='List of languages')
    parser.add_argument('-t', '--templates', nargs='*', default=[], help='Additional directories for template lookup')
    parser.add_argument('-s', '--strings', default='./lang', help='Translated string directory')
    return parser.parse_args()

@dataclass
class Page:
    root: str
    file: str
    lang: str

    @property
    def name(self):
        return os.path.normpath(os.path.splitext(os.path.splitext(self.file)[0])[0])

    @property
    def distfile(self):
        df = os.path.splitext(self.file)[0]
        return os.path.normpath(os.path.join(self.lang, df))

    @property
    def datapath(self):
        return os.path.normpath(os.path.join(
            self.root,
            f"{self.name}.{self.lang}.yml" if self.lang else f"{self.name}.yml"
        ));

    def template(self, env):
        return env.get_template(self.file)

    def data(self):
        with open(self.datapath) as fh:
            return yaml.safe_load(fh)

    def render(self, env, **extra):
        data = self.data()
        env.globals['page'] = {
            'name': self.name,
            'lang': self.lang,
        }
        return self.template(env).render(
            **data,
            **extra
        )

def getTemplates(root):
    for folder, _, files in os.walk(root):
        for file in files:
            if re.search(r'\..*\.jinja$', file):
                relpath = os.path.relpath(folder, root)
                yield os.path.join(relpath, file)

def getPages(root, langs = []):
    langs = langs if '' in langs else ['', *langs]
    for file in getTemplates(root):
        for lang in langs:
            page = Page(
                root = root,
                file = file,
                lang = lang
            )
            if not os.path.exists(page.datapath):
                continue
            yield page
        
def getStrings(stringdir, lang):
    langdir = os.path.join(stringdir, lang)
    ret = {}
    for folder, _, files in os.walk(langdir):
        for file in files:
            if re.search(r'\.json$', file):
                tlkey = os.path.splitext(file)[0]
                with open(os.path.join(folder, file)) as fh:
                    ret[tlkey] = json.load(fh)
    return ret

def setupJinjaEnv(
    root,
    dist,
    stringdir,
    langs,
    currentLang,
    templates=[],
    envdata={}
):
    env = jinja.Environment(
        loader = jinja.FileSystemLoader([root, *templates]),
    )

    def assetContent(path):
        try: 
            with open(os.path.join(dist, path)) as fh:
                return fh.read();
        except:
            return '';
        
    def tojson(obj):
        return json.dumps(obj)
    
    env.filters['json'] = tojson
    env.globals['assetContent'] = assetContent
    env.globals['langs'] = langs
    env.globals['env'] = envdata
    env.globals['__'] = getStrings(stringdir, currentLang)
    return env

def main():
    args = getArgs()
    load_dotenv('.env')
    envdata = {
        'buildstamp': datetime.utcnow().strftime("%Y-%m-%d"),
        **os.environ
    }
    for page in getPages(args.root, args.langs):
        distfile = os.path.normpath(os.path.join(args.dist, page.distfile))
        os.makedirs(os.path.dirname(distfile), exist_ok=True)
        with open(distfile, 'w') as fh:
            fh.write(page.render(setupJinjaEnv(
                root = args.root,
                dist = args.dist,
                templates = args.templates,
                stringdir = args.strings,
                currentLang = page.lang,
                langs = args.langs,
                envdata = envdata
            )))

if __name__ == '__main__':
    main()