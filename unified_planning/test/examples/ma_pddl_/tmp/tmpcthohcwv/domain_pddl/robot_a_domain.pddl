(define (domain simple_ma-domain)
 (:requirements :factored-privacy :typing)
 (:types location door robot_a_type scale_a_type)
 (:constants
   close20 - door
   office home - location
   ?scale_a - scale_a_type
 )
 (:predicates
   (open ?agent - scale_a_type ?door - door)
(a_open ?agent - scale_a_type ?door - door)
  (:private
   (a_pos ?agent - robot_a_type ?loc - location)))
 (:action movegripper
  :parameters ( ?robot_a - robot_a_type)
  :precondition (and 
   (open ?scale_a close20)
   (a_pos ?robot_a office)
   (a_pos ?robot_a office)
  )
  :effect (and
   (a_pos ?robot_a home)
))
)
