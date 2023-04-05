(define (domain ma_dcrm_p_g-domain)
 (:requirements :factored-privacy :typing)
 (:types location stateg door pouchobj ag - object
    robot_a_type scale_a_type - ag
 )
 (:constants
   active startstate - stateg
 )
 (:predicates
  (pouchat ?pouch - pouchobj ?loc - location)
  (:private
   (a_at_ ?agent - ag ?loc - location)
   (a_instateg ?agent - ag ?stategrip - stateg)))
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
  :parameters ( ?robot_a - robot_a_type ?fromloc - location ?toloc - location)
  :precondition (and 
   (a_instateg ?robot_a active)
   (a_at_ ?robot_a ?fromloc)
  )
  :effect (and
   (a_at_ ?robot_a ?toloc)
   (not (a_at_ ?robot_a ?fromloc))
))
)
