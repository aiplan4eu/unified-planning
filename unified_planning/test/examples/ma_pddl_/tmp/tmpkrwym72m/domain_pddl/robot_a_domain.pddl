(define (domain simple_ma-domain)
 (:requirements :factored-privacy :typing)
 (:types location door robot_a_type scale_a_type)
 (:constants
   home office - location
 )
 (:predicates
 (open ?agent - scale_a_type ?door - door)
  (:private
   (at_ ?agent - robot_a_type ?loc - location)
   (pos ?agent - robot_a_type ?loc - location)))
 (:action movegripper
  :parameters ( ?r - robot_a_type)
  :precondition (and 
   (pos ?r office)
  )
  :effect (and
   (pos ?r home)
))
)
