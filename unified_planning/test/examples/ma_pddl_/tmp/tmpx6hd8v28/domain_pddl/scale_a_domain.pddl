(define (domain ma_dcrm_p_g-domain)
 (:requirements :factored-privacy :typing :disjunctive-preconditions)
 (:types location stateg door pouchobj ag - object
    robot_a_type scale_a_type - ag
 )
 (:constants
   open20 close20 - door
   office home - location
   pouch1 - pouchobj
   robot_a - robot_a_type
 )
 (:predicates
  (pouchat ?pouch - pouchobj ?loc - location)
  (a_at_ ?agent - ag ?loc - location)
  (a_statedoor ?agent - ag ?door - door)
  (:private
   (a_ma_dcrm_fake_goal_0 ?agent - ag)))
 (:action open_door
  :parameters ( ?scale_a - scale_a_type)
  :precondition (and 
   (a_statedoor ?scale_a close20)
   (a_at_ robot_a office)
  )
  :effect (and
   (a_statedoor ?scale_a open20)
   (not (a_statedoor ?scale_a close20))
   (not (ma_dcrm_fake_goal))
   (not (a_ma_dcrm_fake_goal_0 ?scale_a))
))
 (:action open_door_0
  :parameters ( ?scale_a - scale_a_type)
  :precondition (and 
   (a_statedoor ?scale_a close20)
   (a_at_ robot_a home)
  )
  :effect (and
   (a_statedoor ?scale_a open20)
   (not (a_statedoor ?scale_a close20))
   (not (ma_dcrm_fake_goal))
   (not (a_ma_dcrm_fake_goal_0 ?scale_a))
))
 (:action ma_dcrm_fake_action_1
  :parameters ( ?scale_a - scale_a_type)
  :precondition (and 
   (pouchat pouch1 home)
  )
  :effect (and
   (a_ma_dcrm_fake_goal_0 ?scale_a)
))
 (:action ma_dcrm_fake_action_2
  :parameters ( ?scale_a - scale_a_type)
  :precondition (and 
   (pouchat pouch1 office)
  )
  :effect (and
   (a_ma_dcrm_fake_goal_0 ?scale_a)
))
)
