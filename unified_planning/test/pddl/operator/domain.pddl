;Header and description

(define (domain operator_test_domain)

(:predicates ;todo: define predicates here
  (connected ?x ?y)
  (at ?x)
)


(:action move
	:parameters (?x ?y)
	:precondition (and (connected ?x ?y) (at ?x))
	:effect (and (at ?y) (not(at ?x)) )
)

)