(define (domain simple_ma-domain)
 (:requirements :factored-privacy :typing)
 (:types location door robot_a_type scale_a_type)
 (:constants
   open20 close20 - door
 )
 (:predicates
 (pos ?agent - robot_a_type ?loc - location)
  (:private
   (open ?agent - scale_a_type ?door - door)))
 (:action open_door
  :parameters ( ?s - scale_a_type)
  :precondition (and 
   (open s close20)
  )
  :effect (and
   (open s open20)
))
)
