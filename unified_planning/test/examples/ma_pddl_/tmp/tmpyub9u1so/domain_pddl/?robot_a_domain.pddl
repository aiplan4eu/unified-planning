(define (domain simple_ma-domain)
 (:requirements :factored-privacy :typing :negative-preconditions :disjunctive-preconditions)
 (:types location door robot_a_type scale_a_type)
 (:constants
   home office - location
 )
 (:predicates
 (a_open ?agent - scale_a_type ?door - door)
  (:private
   (a_at_ ?agent - robot_a_type ?loc - location)
   (a_pos ?agent - robot_a_type ?loc - location)))
 (:action movegripper
  :parameters ( ?robot_a - robot_a_type)
  :precondition (and 
   (or (not (pos ?robot_a office)) (pos ?robot_a home))
  )
  :effect (and
   (a_pos ?? home)
))
)
