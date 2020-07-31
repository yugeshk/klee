codegen.byte: codegen.ml ir.ml import.ml program_rules.ml
	corebuild -lib str codegen.byte -use-ocamlfind

post_processing.byte: post_processing.ml codegen.ml ir.ml import.ml domain.ml
	corebuild -lib str post_processing.byte -use-ocamlfind