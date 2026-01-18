# reference: https://en.wikipedia.org/wiki/Wikipedia:Automated_taxobox_system/intro
# It takes about 1 hour and 3GB ram to run english wiki in 2026.

import sys
import argparse
import bz2

log_file = None
def eprint(*args):
    if log_file:
        print(*args, sep='\t', file=log_file)

def remove_xml_comments(text):
    while True:
        a = text.find('&lt;!--')
        if a == -1:
            return text
        b = text.find('--&gt;', a)
        if b == -1:
            return text
        text = text[:a] + text[b+6:]

def remove_includeonly(text):
    while True:
        a = text.find('&lt;includeonly&gt;')
        if a == -1:
            return text
        b = text.find('&lt;/includeonly&gt;', a)
        if b == -1:
            return text
        text = text[:a] + text[b+20:]

def remove_noinclude(text):
    while True:
        a = text.find('&lt;noinclude&gt;')
        if a == -1:
            return text
        b = text.find('&lt;/noinclude&gt;', a)
        if b == -1:
            return text
        text = text[:a] + text[b+18:]

# Remove the following text which interfere with our "taxon=" parsing
# {{ITIS |id=180469 |taxon=''Orcinus orca'' (Linnaeus, 1758) |access-date=March 9, 2011}}
# {{Cite GBIF|id=2286079|taxon=''Crassostrea virginica'' (Gmelin, 1791)|access-date=2 February 2023}}
def remove_tax_cite(text):
    lower = text.lower()
    for template in ("{{gbif", "{{itis", "{{ipni", "{{cite gbif", "{{cite itis", "{{cite ipni"):
        a = lower.find(template)
        if a == -1: continue
        b = lower.find('}}', a)
        if b == -1: continue
        text = text[:a] + text[b+2:]
        lower = lower[:a] + lower[b+2:]
    return text

# TODO: the following is wrong. It should be Ornithischia's parent, not Ornithischia.
# from
# Ornithischia/?/?: {{Don't edit this line {{{machine code|}}} |same_as=Ornithischia |parent={{Taxonomy/Ornithischia|machine code=parent}}/? }}
# to
# Ornithischia/?/?: {{Don't edit this line {{{machine code|}}} |same_as=Ornithischia |parent=Ornithischia/? }}
def fix_parent_template(text):
    a = text.find('parent={{Taxonomy/')
    if a == -1: return text
    b = text.find('|machine code=parent}}', a)
    if b == -1: return text
    return text[:a+7] + text[a+18:b] + text[b+22:]

boxes = dict()
def process_box(title, text, page_size):
    eprint('ibox1', title, text)
    text = remove_xml_comments(text)
    text = remove_tax_cite(text)
    arr = text[2:-2].split('|')
    box = dict()
    box['psize'] = page_size
    box['box'] = arr[0].strip()
    for s in arr[1:]:
        arr2 = s.split('=')
        if len(arr2) != 2:
            continue
        k = arr2[0].strip().lower()
        v = arr2[1].strip()
        #if v and k in ['image', 'genus', 'psize', 'taxon']: # save memory mode
        if v: # debug mode
            box[k] = v
    # try to fix {{Photomontage}} {{Photo montage}}
    if 'image' in box and box['image'].startswith('{{'):
        found = None
        for v in box.values():
            if not isinstance(v, str): continue
            lv = v.lower()
            if lv.endswith('.jpg') or lv.endswith('.jpeg') or lv.endswith('.png'):
                found = v
                break
        if found:
            eprint('ibpm', title, box['image'], found)
            box['image'] = found
    eprint('ibox2', title, box)
    boxes[title] = box

rankc2e = {'总域':'superregio', '域':'domain',
        '界':'regnum','亚界':'subregnum',
        '总门':'superphylum', '门':'phylum', '亚门':'subphylum',
        '纲':'classis', '亚纲':'subclassis',
        '超目':'superordo', '总目':'superordo', '目':'ordo', '亚目':'subordo', '亞目':'subordo', '下目':'infraordo',
        '超科':'superfamilia', '总科':'superfamilia', '科':'familia', '亚科':'subfamilia',
        '超族':'supertribus', '族':'tribus', '亚族':'subtribus',
        '属':'genus', '屬':'genus', '亚属':'subgenus',
        '群':'cohort'}
taxonomy = dict()
def process_taxonomy(title, text):
    eprint('itax1', title, text)
    text = remove_xml_comments(text)
    text = remove_includeonly(text)
    text = remove_noinclude(text)
    text = fix_parent_template(text)
    parent = rank = link = same_as = None
    always_display = False
    for s in text.split('|'):
        s = s.strip()
        if s.startswith('parent=') or s.startswith('parent '):
            parent = s[s.index('=')+1:].strip(' }')
        elif s.startswith('rank=') or s.startswith('rank '):
            rank = s[s.index('=')+1:].strip(' }')
        elif s.startswith('link=') or s.startswith('link '):
            link = s[s.index('=')+1:].strip(' }')
        elif s.startswith('same as=') or s.startswith('same as '):
            same_as = s[s.index('=')+1:].strip(' }')
        elif s.startswith('same_as=') or s.startswith('same_as '):
            same_as = s[s.index('=')+1:].strip(' }')
        elif s.startswith('always_display=') or s.startswith('always_display '):
            value = s[s.index('=')+1:].strip(' }')
            if value in ['yes', '是', 'true', '1']:
                always_display = True
    if (parent and rank) or same_as:
        if not link or '#' in link or '{' in link:
            link = None
        if rank:
            if rank in rankc2e:
                rank = rankc2e[rank]
            rank = rank.lower()
        if always_display and rank:
            rank = rank + "!"
        eprint('itax2', title, parent, rank, link, same_as)
        taxonomy[title] = [title, parent, rank, link, same_as]

redir = dict()
def process_redirect(title, text):
    eprint('ired1', title, text)
    a = text.find('[[')
    if a == -1:
        return
    b = text.find(']]', a)
    if b == -1:
        return
    target = text[(a+2):b]
    eprint('ired2', title, target)
    redir[title] = target

def process_page(title, text):
    title = title.replace('\t', ' ').replace('\u202f', ' ').replace('\u200e', ' ')
    text = text.replace('\t', ' ').replace('\u202f', ' ').replace('\u200e', ' ')
    #eprint('ippg', title)
    if text.startswith('#REDIRECT') or text.startswith('#Redirect') or text.startswith('#redirect') or text.startswith('#重定向'):
        return process_redirect(title, text)
    if title.startswith('Template:Taxonomy/'):
        return process_taxonomy(title[18:], text)

    index = 0
    while True:
        index = text.find('{{', index)
        if index == -1:
            break
        for template in ['automatic taxobox', 'speciesbox', 'subspeciesbox', 'infraspeciesbox', 'hybridbox', 'virusbox']:
            if not text[index+2:index+20].lower().startswith(template):
                continue
            # match closing bracket
            depth = 2
            pos = index + 2
            while depth > 0 and pos < len(text):
                if text[pos] == '{': depth += 1
                elif text[pos] == '}': depth -= 1
                pos += 1
            if depth == 0:
                process_box(title, text[index:pos], len(text))
        index += 1

def load_dump_file(file_path):
    if not file_path.endswith(".bz2"):
        print("expect a bz2 dump file")
        sys.exit(1)
    is_in_text = False
    with bz2.open(file_path, 'rt', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line == '<page>':
                title = text = ''
            elif line == '</page>':
                if title and text:
                    process_page(title, text)
                title = text = ''
            elif line.startswith('<title>'):
                assert line.endswith('</title>')
                title = line[7:-8]
            elif line.startswith('<text '):
                text = line[line.index('>')+1:]
                if text.endswith('</text>'):
                    text = text[:-7]
                else:
                    is_in_text = True
            elif line.endswith('</text>'):
                line = line[:-7]
                if line:
                    text += ' ' + line
                is_in_text = False
            elif is_in_text and line:
                text += ' ' + line

def fix_tax_redir():
    for title, target in redir.items():
        if title.startswith('Template:Taxonomy/') and target.startswith('Template:Taxonomy/'):
            source = title[18:]
            target = target[18:]
            if target in taxonomy:
                taxonomy[source] = taxonomy[target]

def fix_same_as():
    for title, tax in taxonomy.items():
        same_as = tax[4]
        if same_as:
            if same_as in taxonomy:
                for i in range(1, 4):
                    if not tax[i]:
                        tax[i] = taxonomy[same_as][i]
                eprint('isas', *tax)
            else:
                eprint('wbsa', title, same_as)

# delete taxonomy that has no page pointing to it
def prune_taxonomy_dink():
    connected = set()
    for title, box in boxes.items():
        if 'genus' in box:
            connected.add(box['genus'])
        if 'taxon' in box:
            connected.add(box['taxon'])
            connected.add(box['taxon'].split(' ')[0]) # Sometimes only the first word is used. e.g. "Denticeps clupeoides"
    dirty = True
    while dirty:
        dirty = False
        for title, tax in taxonomy.items():
            if title in connected:
                if tax[0] not in connected: # mark redir
                    connected.add(tax[0])
                    dirty = True
                p = tax[1]
                if p not in connected:
                    connected.add(p)
                    dirty = True
                if p in taxonomy and taxonomy[p][0] not in connected: # mark parent redir as well
                    connected.add(taxonomy[p][0])
                    dirty = True
    titles = list(taxonomy.keys())
    for title in titles:
        if title not in connected:
            eprint('wdink', title)
            del taxonomy[title]

# delete taxonomy that is not a decedent of the root.
def prune_taxonomy_conn(root_tax):
    connected = set()
    dirty = True
    while dirty:
        dirty = False
        for title, tax in taxonomy.items():
            if title != tax[0]: # skip redirect
                continue
            if not tax[1]: # no parent
                continue
            if title not in connected:
                if tax[1] == root_tax or (tax[1] in taxonomy and taxonomy[tax[1]][0] in connected):
                    connected.add(title)
                    dirty = True
    titles = list(taxonomy.keys())
    for title in titles:
        if taxonomy[title][0] not in connected:
            if title == taxonomy[title][0]: # skip redirect
                eprint('wdis', *taxonomy[title])
            del taxonomy[title]

def output_to_file(pages, tax_path, page_path, root_tax):
    with open(tax_path, "w") as fp:
        #print('#taxonomy', len(taxonomy), 'name,parent,rank,page', sep='\t', file=fp)
        for title, tax in sorted(taxonomy.items()):
            if title != tax[0]: # skip redirect
                continue
            parent = root_tax if tax[1] == root_tax else taxonomy[tax[1]][0] # fix parent redirect
            rank = tax[2] if tax[2] else '-'
            link = tax[3] if tax[3] else '-'
            if link not in pages and link in redir and redir[link] in pages: # fix link redirect
                link = redir[link]
            print(tax[0], parent, rank, link, sep='\t', file=fp)

    with open(page_path, "w") as fp:
        #print('#page', len(pages), 'name,taxonomy,image,redir1,redir2...', sep='\t', file=fp)
        for page in sorted(pages.values()):
            print(*page, sep='\t', file=fp)

def main():
    parser = argparse.ArgumentParser(description="Wikipedia dump parser for taxobox")
    parser.add_argument('--dump-file', '-d', type=str, required=True, help='Wiki dump file, e.g. enwiki-20260101-pages-articles-multistream.xml.bz2')
    parser.add_argument('--out-tax', '-t', type=str, required=True, help='tax output file. e.g. tax-en.tsv')
    parser.add_argument('--out-page', '-p', type=str, required=True, help='page output file. e.g. page-en.tsv')
    parser.add_argument('--out-log', '-l', type=str, help='log output file. e.g. parser.log')
    parser.add_argument('--root', '-r', type=str, default='Life', help='Root of tax tree. e.g. Plantae, Animalia, Life. default: Life')
    args = parser.parse_args()

    if args.out_log:
        global log_file
        log_file = open(args.out_log, "w")

    load_dump_file(args.dump_file)
    eprint('ipro', 'input done')

    fix_tax_redir()
    eprint('ipro', 'fix_tax_redir done')
    fix_same_as()
    eprint('ipro', 'fix_same_as done')
    prune_taxonomy_dink()
    eprint('ipro', 'prune_taxonomy_dink done')
    prune_taxonomy_conn(args.root)
    eprint('ipro', 'prune_taxonomy done')

    pages = dict() # title => [title-str, taxonomy-str, str(page-size), image-url-str]
    for title, box in boxes.items():
        if 'image' in box and box['image']:
            image = box['image']
        else:
            image = '-'
        if 'genus' in box:
            if box['genus'] in taxonomy:
                pages[title] = [title, str(box['psize']), taxonomy[box['genus']][0], image]
            else:
                eprint('wbgns', title, box['genus'])
        elif 'taxon' in box:
            genus = box['taxon']
            if genus in taxonomy:
                pages[title] = [title, str(box['psize']), taxonomy[genus][0], image]
            elif ' ' in genus and genus.split(' ')[0] in taxonomy:
                pages[title] = [title, str(box['psize']), taxonomy[genus.split(' ')[0]][0], image]
            else:
                eprint('wbtxn', title, box['taxon'])
        else:
            eprint('wbsbx', title)
    eprint('ipro', 'pages done')

    for title, target in redir.items():
        if target in pages:
            pages[target].append(title)
    eprint('ipro', 'alias done')

    output_to_file(pages, args.out_tax, args.out_page, args.root)

    if log_file:
        log_file.close()

if __name__ == '__main__':
    main()
