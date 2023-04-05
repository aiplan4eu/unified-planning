(define (domain simple_ma-domain)
 (:requirements :factored-privacy :typing :negative-preconditions)
 (:types location door robot_a_type scale_a_type)
 (:constants
   open20 close20 - door
   home - location
   robot_a - robot_a_type
 )
 (:predicates
   (pos ?agent - robot_a_type ?loc - location)
(a_pos ?agent - robot_a_type ?loc - location)
  (:private
   (a_open ?agent - scale_a_type ?door - door)))
 (:action open_door
  :parameters ( ?scale_a - scale_a_type)
  :precondition (and 
   (a_open ?scale_a close20)
   (pos robot_a home)
  )
  :effect (and
   (a_open ?scale_a open20)
))
)
