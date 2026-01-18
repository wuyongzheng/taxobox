.PHONY: all
all: html/page-en-animal.tsv.gz html/page-en-plant.tsv.gz html/page-zh-animal.tsv.gz html/page-zh-plant.tsv.gz html/tax-en-animal.tsv.gz html/tax-en-plant.tsv.gz html/tax-zh-animal.tsv.gz html/tax-zh-plant.tsv.gz

html/tax-en-plant.tsv html/page-en-plant.tsv: wikidump/enwiki-20260101-pages-articles-multistream.xml.bz2 scripts/parse-xmldump.py
	python3 scripts/parse-xmldump.py -d wikidump/enwiki-20260101-pages-articles-multistream.xml.bz2 -t html/tax-en-plant.tsv -p html/page-en-plant.tsv -l err -r Plantae

html/tax-en-animal.tsv html/page-en-animal.tsv: wikidump/enwiki-20260101-pages-articles-multistream.xml.bz2 scripts/parse-xmldump.py
	python3 scripts/parse-xmldump.py -d wikidump/enwiki-20260101-pages-articles-multistream.xml.bz2 -t html/tax-en-animal.tsv -p html/page-en-animal.tsv -l err -r Animalia

html/tax-zh-plant.tsv html/page-zh-plant.tsv: wikidump/zhwiki-20260101-pages-articles-multistream.xml.bz2 scripts/parse-xmldump.py
	python3 scripts/parse-xmldump.py -d wikidump/zhwiki-20260101-pages-articles-multistream.xml.bz2 -t html/tax-zh-plant.tsv -p html/page-zh-plant.tsv -l err -r Plantae

html/tax-zh-animal.tsv html/page-zh-animal.tsv: wikidump/zhwiki-20260101-pages-articles-multistream.xml.bz2 scripts/parse-xmldump.py
	python3 scripts/parse-xmldump.py -d wikidump/zhwiki-20260101-pages-articles-multistream.xml.bz2 -t html/tax-zh-animal.tsv -p html/page-zh-animal.tsv -l err -r Animalia

html/%.tsv.gz: html/%.tsv
	gzip -c $< > $@
