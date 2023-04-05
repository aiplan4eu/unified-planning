(define (domain simple_ma-domain)
 (:requirements :factored-privacy :typing :negative-preconditions :disjunctive-preconditions :existential-preconditions)
 (:types location door robot_a_type scale_a_type)
 (:constants
   close20 open20 - door
 )
 (:predicates
 (a_pos ?agent - robot_a_type ?loc - location)
  (:private
   (a_open ?agent - scale_a_type ?door - door)))
 (:action open_door
  :parameters ( ?scale_a - scale_a_type)
  :precondition (and 
   (open close20)
  )
  :effect (and
   (a_open ?? open20)
))
)
