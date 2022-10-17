(define (problem operator_test_problem) (:domain operator_test_domain)
(:objects
    a b c
)
(:init
  (connected a b)
  (connected b c)
  (at a)
)

(:goal
  (and
    (forall 
      (?x)
      (and
        (at ?x)
        (forall (?y) (connected ?x ?y))
      )
    )
  )
)
)
