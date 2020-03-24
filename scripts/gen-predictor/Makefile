codegen.byte: codegen.ml ir.ml import.ml
	corebuild -no-hygiene -use-menhir -lib dynlink -lib str \
	          codegen.byte -use-ocamlfind -cflag -unsafe-string
