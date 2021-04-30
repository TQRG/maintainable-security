NAME:=response

TEX_FILES = \
$(NAME).tex

.DEFAULT_GOAL := pdf

pdf:
	latexmk -bibtex -pdf $(NAME)

final: pdf
	@echo '******** Did you spell-check the paper? ********'
	pdffonts $(NAME).pdf; fi

clean:
	rm *aux *bbl *blg *log $(NAME).pdf *.fdb_latexmk *.synctex.gz *.fls *.out

read:
	evince $(NAME).pdf

tags: TAGS
TAGS: ${TEX_FILES}
	etags ${TEX_FILES}