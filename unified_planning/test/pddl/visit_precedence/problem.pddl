
(define (problem visit_precedence_problem)
 (:domain visit_precedence_domain)
 (:objects
   l1 l2 l3 - location
 )
 (:init (precedes l1 l2) (precedes l1 l3) (precedes l2 l3))
 (:goal (and (forall (?l_0 - location)
 (and (visited ?l_0) (forall (?l2 - location)
 (or (not (precedes ?l2 ?l_0)) (visited ?l2)))))))
)
