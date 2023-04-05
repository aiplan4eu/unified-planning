(define (problem simple_ma-problem)
 (:domain simple_ma-domain)
 (:objects
   office1 - office
   home1 - home
   close20_ - close20
   open20_ - open20
   robot_a - robot_a_type
   scale_a - scale_a_type
 )
 (:init
  (a_pos robot_a office1))
 (:goal (and (a_pos robot_a home1) (a_open scale_a open20_)))
)