NAME:=emse20
REVISION=3c6e399ad31800da1bd2ca273d7adce6610599b5

# To update, run: latex-process-inputs -makefilelist main.tex
TEX_FILES = \
$(NAME).tex

.DEFAULT_GOAL := pdf

pdf:
	latexmk -bibtex -pdf $(NAME)

final: pdf
	@echo '******** Did you spell-check the paper? ********'
	pdffonts $(NAME).pdf; fi
	
diff:
	git show $(REVISION):./emse20.tex > old.tex
	latexdiff old.tex emse20.tex > diff.tex
	latexmk diff.tex
	latexmk -c diff.tex
	rm old.tex diff.tex

clean:
	rm *aux *bbl *blg *log $(NAME).pdf *.fdb_latexmk *.synctex.gz *.fls *.out

read:
	evince emse20.pdf

tags: TAGS
TAGS: ${TEX_FILES}
	etags ${TEX_FILES}