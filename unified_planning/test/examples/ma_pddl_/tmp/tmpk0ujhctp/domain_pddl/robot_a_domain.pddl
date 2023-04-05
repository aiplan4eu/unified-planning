(define (domain simple_ma-domain)
 (:requirements :factored-privacy :typing :negative-preconditions :disjunctive-preconditions)
 (:types location door robot_a_type scale_a_type)
 (:constants
   office home - location
 )
 (:predicates
 (a_open ?agent - scale_a_type ?door - door)
  (:private
   (a_pos ?agent - robot_a_type ?loc - location)))
 (:action movegripper
  :parameters ( ?robot_a - robot_a_type)
  :precondition (and 
   (and (or (not (pos office)) (pos home)) (pos office))
   (pos office)
  )
  :effect (and
   (a_pos ?robot_a home)
))
)
