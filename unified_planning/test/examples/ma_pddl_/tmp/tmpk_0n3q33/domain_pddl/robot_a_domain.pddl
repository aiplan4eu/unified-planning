(define (domain simple_ma-domain)
 (:requirements :factored-privacy :typing :negative-preconditions)
 (:types location door robot_a_type scale_a_type)
 (:constants
   home office - location
   close20 - door
   scale_a - scale_a_type
 )
 (:predicates
   (open ?agent - scale_a_type ?door - door)
(a_open ?agent - scale_a_type ?door - door)
  (:private
   (a_at_ ?agent - robot_a_type ?loc - location)
   (a_pos ?agent - robot_a_type ?loc - location)))
 (:action movegripper
  :parameters ( ?r - robot_a_type)
  :precondition (and 
   (a_pos ?r office)
   (open scale_a close20)
  )
  :effect (and
   (a_pos ?r home)
))
)
