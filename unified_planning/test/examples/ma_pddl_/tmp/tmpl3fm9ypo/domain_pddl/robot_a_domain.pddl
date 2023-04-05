(define (domain simple_ma-domain)
 (:requirements :factored-privacy :typing :negative-preconditions :disjunctive-preconditions :existential-preconditions)
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
   (and (imply (or (not (a_pos ?robot_a office)) (not (a_pos ?robot_a home))) (a_pos ?robot_a home)) (imply (a_pos ?robot_a home) (or (not (a_pos ?robot_a office)) (not (a_pos ?robot_a home)))) )
   (and (or (a_pos ?robot_a office) (a_pos ?robot_a home)) (a_pos ?robot_a office))
   (a_pos ?robot_a office)
  )
  :effect (and
   (a_pos ?robot_a home)
))
)
