(define (domain simple_ma-domain)
 (:requirements :factored-privacy :typing :negative-preconditions :disjunctive-preconditions :existential-preconditions)
 (:types location door robot_a_type scale_a_type)
 (:constants
   office home - location
 )
 (:predicates
 (a_open ?agent - scale_a_type ?door - door)
  (:private
   (a_at_ ?agent - robot_a_type ?loc - location)
   (a_pos ?agent - robot_a_type ?loc - location)))
 (:action movegripper
  :parameters ( ?robot_a - robot_a_type)
  :precondition (and 
   (and (imply (or (not (pos ?robot_a office)) (not (pos ?robot_a home))) (pos ?robot_a home)) (imply (pos ?robot_a home) (or (not (pos ?robot_a office)) (not (pos ?robot_a home)))) )
  )
  :effect (and
   (a_pos ?? home)
))
)
