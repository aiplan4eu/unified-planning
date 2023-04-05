(define (domain p_g-domain)
 (:requirements :factored-privacy :typing)
 (:types location stateg door pouchobj ag - object
    robot_a_type scale_a_type - ag
 )
 (:constants
   active startstate - stateg
   office home - location
 )
 (:predicates
  (pouchat ?pouch - pouchobj ?loc - location)
  (a_statedoor ?agent - scale_a_type ?door - door)
  (a_instateg ?agent - ag ?stategrip - stateg)
  (a_at_ ?agent - ag ?loc - location)
  (a_statedoor ?agent - ag ?door - door)
)
 (:action movegripper_activate
  :parameters ( ?robot_a - robot_a_type)
  :precondition (and 
   (a_instateg ?robot_a startstate)
  )
  :effect (and
   (a_instateg ?robot_a active)
   (not (a_instateg ?robot_a startstate))
))
 (:action movegripper_move
  :parameters ( ?robot_a - robot_a_type)
  :precondition (and 
   (a_instateg ?robot_a active)
   (a_at_ ?robot_a office)
  )
  :effect (and
   (a_at_ ?robot_a home)
   (not (a_at_ ?robot_a office))
))
)
