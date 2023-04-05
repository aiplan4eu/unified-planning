(define (problem simple_ma-problem)
 (:domain simple_ma-domain)
 (:objects
   office - location
   scale_a - scale_a_type
 )
 (:init
  (a_open scale_a close20))
 (:goal (and (a_pos robot_a home) (not (open scale_a open20))))
)