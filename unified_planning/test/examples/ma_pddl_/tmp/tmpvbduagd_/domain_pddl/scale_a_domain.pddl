(define (domain p_g-domain)
 (:requirements :factored-privacy :typing)
 (:types location stateg door pouchobj ag - object
    robot_a_type scale_a_type - ag
 )
 (:constants
   open20 close20 - door
   home - location
 )
 (:predicates
  (pouchat ?pouch - pouchobj ?loc - location)
  (a_at_ ?agent - robot_a_type ?loc - location)
  (a_statedoor ?agent - ag ?door - door)
  (a_at_ ?agent - ag ?loc - location)
)
 (:action open_door
  :parameters ( ?scale_a - scale_a_type)
  :precondition (and 
   (a_statedoor ?scale_a close20)
   (a_at_ robot_a home)
  )
  :effect (and
   (a_statedoor ?scale_a open20)
   (not (a_statedoor ?scale_a close20))
))
)
