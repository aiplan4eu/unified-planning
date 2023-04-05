(define (problem simple_ma-problem)
 (:domain simple_ma-domain)
 (:objects
   open20 - door
   robot_a - robot_a_type
 )
 (:init
  (a_pos robot_a office))
 (:goal (and (a_pos robot_a home) (not ?(open scale_a open20))))
)