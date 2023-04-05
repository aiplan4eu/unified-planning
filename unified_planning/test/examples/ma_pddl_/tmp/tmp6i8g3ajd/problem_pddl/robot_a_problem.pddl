(define (problem ma_dcrm_p_g-problem)
 (:domain ma_dcrm_p_g-domain)
 (:objects
   vision2 - location
   pouch1 - pouchobj
   robot_a - robot_a_type
   scale_a - scale_a_type
 )
 (:init
  (a_at_ robot_a office)
  (a_instateg robot_a startstate)
  (a_statedoor scale_a close20))
 (:goal (and (a_ma_dcrm_fake_goal ?robot_a) (ma_dcrm_fake_goal_0)))
)