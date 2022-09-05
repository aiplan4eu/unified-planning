(define (domain multiple-vars-forall)
(:requirements :typing :negative-preconditions :conditional-effects)

(:types location)

(:predicates
    (safe ?l1 - location ?l2 - location) ;; Checks if the road between 2 locations is safe

  )

;; Check the safety of a road
(:action check
  :parameters (?l1 - location ?l2 - location)
  :precondition (and
		(not (safe ?l1 ?l2))
		)
  :effect (and
		(safe ?l1 ?l2)
		)
)

;; natural disaster, every road might not be safe
(:action natural_disaster
  :parameters ()
  :precondition ()
  :effect (and
		(forall (?l1 - location ?l2 - location)
        	(when (safe ?l1 ?l2)
				(and
				(not (safe ?l1 ?l2))
				)
		    )
		)
		)
)

)
