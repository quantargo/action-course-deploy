### CREATE MODULE
# 1. Create Git repository
# 2. Create Preliminary index.yml
# 3. Start build

import yaml
from yaml import SafeLoader, SafeDumper
import os
import json
import sys
import glob
import frontmatter
from frontmatter.default_handlers import BaseHandler
from io import BytesIO
import re

class YAMLHandlerNoReorder(BaseHandler):
    """
    Load and export YAML metadata. By default, this handler uses YAML's
    "safe" mode, though it's possible to override that.
    """

    FM_BOUNDARY = re.compile(r"^-{3,}\s*$", re.MULTILINE)
    START_DELIMITER = END_DELIMITER = "---"

    def load(self, fm, **kwargs):
        """
        Parse YAML front matter. This uses yaml.SafeLoader by default. 
        """
        kwargs.setdefault("Loader", SafeLoader)
        return yaml.load(fm, **kwargs)

    def export(self, metadata, **kwargs):
        """
        Export metadata as YAML. This uses yaml.SafeDumper by default.
        """
        kwargs.setdefault("Dumper", SafeDumper)
        kwargs.setdefault("default_flow_style", False)
        kwargs.setdefault("allow_unicode", True)

        metadata = yaml.dump(metadata, default_flow_style=False, sort_keys=False).strip()
        return metadata

def get_path_names(pattern, sort = True):
  res = [d.replace('./', '') for d in glob.glob(pattern)]
  res.sort()
  return res

with open('index.yml', 'r') as f:
  module = yaml.load(f)

module['moduleId'] = sys.argv[1]
module['contentId'] = sys.argv[1]

if 'image' in module:
  module['image'] = '/'.join(['/assets/courses', module['moduleId'], module['image']])

topics = []
contents = []
for d in get_path_names('./[0-9][0-9]*'):
    file_idx_topic = os.path.join(d, 'index.yml')
    with open(file_idx_topic, 'r') as f:
      topic = yaml.load(f, Loader=yaml.BaseLoader)
    topic['contentId'] = module['moduleId'] + '#' + d
    topic['type'] = 'contentId'
    if 'image' in topic:
      topic['image'] = '/'.join(['/assets/courses', module['moduleId'], d , topic['image']])
    topics.append(topic)

    content = {}
    content['contentId'] = module['moduleId'] + '#' + d
    content['moduleId'] = module['moduleId']
    content['title'] = topic['title']
    content['contentType'] = 'index'
    content['contents'] = []

    dir_chapter = './%s/*.Rmd' % (d)
    for rmd in get_path_names(dir_chapter):
      print('rmd: ' + rmd)
      chapter = {}
      chapter['type'] = 'contentId'
      chapter['content'] = '#'.join([module['moduleId'], 
                            d, 
                            os.path.basename(rmd).replace('.Rmd', '')])
      chapter['contentId'] = '#'.join([module['moduleId'], 
                            d, 
                            os.path.basename(rmd).replace('.Rmd', '')])
      content['contents'].append(chapter)
      # Adjust content id in file
      print('contentId: ' + content['contentId'])
      section = None
      with open(rmd, 'r') as f:
        section = frontmatter.loads(f.read())
        print('Setting tutorial id to "' + chapter['content'] + '"')
        section.metadata['tutorial']['id'] = chapter['content']
      with open(rmd, 'w+') as f:
        f.write(frontmatter.dumps(section, handler=YAMLHandlerNoReorder()))
        f.write("\n")
    contents.append(content)

with open('contents.yml', 'w+') as f:
  yaml.dump(contents, f, default_flow_style=False, sort_keys=False)

module['contents'] = topics
# Include stats
n_exercises = 0
n_quizzes = 0

for cfile in get_path_names('./[0-9][0-9]*/*.json'):
    with open(cfile, 'r') as f:
      chapter = json.load(f)
      for c in chapter:
        if 'contentType' in c and 'exerciseType' in c:
          if c['contentType'] == 'exercise':
            if c['exerciseType'] == 'code':
              n_exercises += 1
            if c['exerciseType'].startswith('quiz'):
              n_quizzes += 1

module['moduleStats'] = {
  'topics': len(topics),
  'exercises': n_exercises,
  'quizzes': n_quizzes
}

with open('index.yml', 'w+') as f:
  yaml.dump(module, f, default_flow_style=False, sort_keys=False)


course = {
  'moduleId': module['moduleId'],
  'contentId': module['contentId'] + '#' + 'course',
  'contentType': 'course',
  'image': module['image'],
  'title': module['title']
}
achievements = []
for bfile in get_path_names('./[0-9][0-9]*/index.yml'):
  with open(bfile, 'r') as f:
    badge = yaml.load(f, Loader=yaml.BaseLoader)
    badge['moduleId'] = module['moduleId']
    badge['contentId'] = '#'.join([module['contentId'], os.path.dirname(bfile), 'badge'])
    badge['contentType'] = 'badge'
    badge['image'] = '/'.join(['/assets/courses', module['contentId'], os.path.dirname(bfile), badge['image']])
    badge['title'] = badge['badgeTitle']
    achievements.append(badge)
    for cfile in get_path_names(os.path.dirname(bfile) + '/*.json'):
      with open(cfile, 'r') as f:
        chapter = json.load(f)
        if (chapter[0]['contentType'] == 'recipe'):
          achievements.append({
            'moduleId': module['moduleId'],
            'contentId': '_'.join([badge['contentId'], 'dependency', chapter[0]['contentId']]),
            'dependencyFrom': badge['contentId'],
            'dependencyTo': chapter[0]['contentId'],
            'contentType': 'dependency'
          })
          
          for ex in chapter[0]['dependencies']:
            achievements.append({
              'moduleId': module['moduleId'],
              'contentId': '_'.join([chapter[0]['contentId'], 'dependency', ex]),
              'dependencyFrom': chapter[0]['contentId'],
              'dependencyTo': ex,
              'contentType': 'dependency'
            })
      
    achievements.append({
            'moduleId': module['moduleId'],
            'contentId': '_'.join([course['contentId'], 'dependency', badge['contentId']]),
            'dependencyFrom': course['contentId'],
            'dependencyTo': badge['contentId'],
            'contentType': 'dependency'
          })
achievements.append(course)
certificate = {
  'moduleId': module['moduleId'],
  'contentId': module['contentId'] + '#' + 'certificate',
  'contentType': 'certificate',
  'image': '/img/certificate.png',
  'title': 'Certificate ' + module['title']
}
achievements.append(certificate)

if ('assessment' in module) and (module['assessment'] == False):
  achievements.append({
    'moduleId': module['moduleId'],
    'contentId': '_'.join([certificate['contentId'], 'dependency', course['contentId']]),
    'dependencyFrom': certificate['contentId'],
    'dependencyTo': course['contentId'],
    'contentType': 'dependency'
  })

with open('badge.yml', 'w+') as f:
  yaml.dump(achievements, f, default_flow_style=False, sort_keys=False)
