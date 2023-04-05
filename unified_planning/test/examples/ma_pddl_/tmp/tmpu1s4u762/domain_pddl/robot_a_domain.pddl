(define (domain ma_dcrm_p_g-domain)
 (:requirements :factored-privacy :typing)
 (:types location stateg door pouchobj ag - object
    robot_a_type scale_a_type - ag
 )
 (:constants
   startstate active - stateg
   office home - location
   open20 close20 - door
   scale_a - scale_a_type
 )
 (:predicates
  (pouchat ?pouch - pouchobj ?loc - location)
  (a_at_ ?agent - ag ?loc - location)
  (a_statedoor ?agent - ag ?door - door)
  (:private
   (a_instateg ?agent - ag ?stategrip - stateg)
   (a_ma_dcrm_fake_goal ?agent - ag)))
 (:action movegripper_activate
  :parameters ( ?robot_a - robot_a_type)
  :precondition (and 
   (a_instateg ?robot_a startstate)
  )
  :effect (and
   (a_instateg ?robot_a active)
   (not (a_instateg ?robot_a startstate))
   (not (a_ma_dcrm_fake_goal ?robot_a))
   (not (ma_dcrm_fake_goal_0))
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
   (not (a_ma_dcrm_fake_goal ?robot_a))
   (not (ma_dcrm_fake_goal_0))
))
 (:action ma_dcrm_fake_action
  :parameters ( ?robot_a - robot_a_type)
  :precondition (and 
   (a_statedoor scale_a open20)
  )
  :effect (and
   (a_ma_dcrm_fake_goal ?robot_a)
))
 (:action ma_dcrm_fake_action_0
  :parameters ( ?robot_a - robot_a_type)
  :precondition (and 
   (a_statedoor scale_a close20)
  )
  :effect (and
   (a_ma_dcrm_fake_goal ?robot_a)
))
)
