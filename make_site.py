import os
import markdown
import logging
import xml.dom
import xml.dom.minidom
import html5lib
import shutil

def _YieldNodes(node):
  for child_node in node.childNodes:
    yield child_node
    for subnode in _YieldNodes(child_node):
      yield subnode

def _FindElementById(doc, elem_id):
  for node in _YieldNodes(doc):
    if node.nodeType == xml.dom.Node.ELEMENT_NODE:
      if (node.hasAttribute('id') and
          node.getAttribute('id') == elem_id):
        return node

def FillElement(template_doc, element_id, node_list):
  elem = _FindElementById(template_doc, element_id)
  for node in node_list:
    elem.appendChild(node)
  

def ParseHtmlAsNodeList(html_content):
  container = html5lib.parseFragment(html_content, treebuilder='dom')
  node_list = []
  for child in container.childNodes:
    node_list.append(child)
  return node_list

def ParseHtmlAsDocument(html_content):
  return html5lib.parse(html_content, treebuilder='dom')

def GetContent(content_dir):

  ret = dict()
  
  for filename in os.listdir(content_dir):
    path = os.path.join(content_dir, filename)
    
    if not os.path.isfile(path):
      continue

    filename_root, ext = os.path.splitext(filename)

    if ext == '.md':
      html_filename = '%s.html' % filename_root
      raw_content = open(path).read()
      xhtml_content = markdown.markdown(raw_content)
      ret[html_filename] = ParseHtmlAsNodeList(xhtml_content)

  return ret

def _GetText(node):
  ret = ''
  for node in _YieldNodes(node):
    if node.nodeType == xml.dom.Node.TEXT_NODE:
      ret += node.data
  return ret
  
def _GetTag(tag, nodes):
  for root in nodes:
    for node in _YieldNodes(root):
      if node.nodeType == xml.dom.Node.ELEMENT_NODE:
        if node.tagName == tag:
          return node

def _GetArticles(content_map):
  ret = dict()
  for path, nodes in content_map.iteritems():
    tag = _GetTag('title', nodes)
    title = _GetText(tag)

    time = _GetTag('time', nodes)
    assert time, 'time element not found'
    time_str = time.getAttribute('datetime')

    yield (path, title, time_str)


def _CreateIndexPage(articles):

  get_date = lambda article_tuple: article_tuple[2]
  articles = sorted(articles, key=get_date)
  
  impl = xml.dom.minidom.getDOMImplementation()
  doc = impl.createDocument(None, None, None)
  html = doc.createElement('html')
  body = doc.createElement('body')
  
  doc.appendChild(html)
  html.appendChild(body)

  ul = doc.createElement('ul')
  body.appendChild(ul)
      
  for article in articles:
    path, title, time_str = article
    li = doc.createElement('li')
    ul.appendChild(li)

    a = doc.createElement('a')
    text = doc.createTextNode(title)
    a.appendChild(text)

    a.setAttribute('href', path)

    li.appendChild(a)

  return doc
  


def main():
  logging.basicConfig(level=logging.INFO)
  
  root_dir = os.path.dirname(__file__)

  content_dir = os.path.join(root_dir, 'content')
  logging.info('Reading content dir %s' % content_dir)

  template_path = os.path.join(root_dir, 'template/template.html')
  template_content = open(template_path).read()
  template_doc = ParseHtmlAsDocument(template_content)

  content_map = GetContent(content_dir)
  
  output_dir = os.path.join(root_dir, '_out')  
  if os.path.exists(output_dir):
    shutil.rmtree(output_dir)

  os.mkdir(output_dir)
  os.chdir(output_dir)

  for filename, node_list in content_map.iteritems():
    empty_template = template_doc.cloneNode(True)
    FillElement(empty_template, 'content', node_list)

    logging.info('Writing path %s' % filename)
    with open(filename, 'w') as f:
      f.write(empty_template.toxml())

  articles = list(_GetArticles(content_map))
  index_page = _CreateIndexPage(articles)

  logging.info('Writing index at index.html')
  with open('index.html', 'w') as f:
    f.write(index_page.toxml())


if __name__ == '__main__':
  main()
