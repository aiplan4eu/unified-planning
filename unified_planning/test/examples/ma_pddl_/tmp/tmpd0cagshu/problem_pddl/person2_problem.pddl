(define (problem ma_taxi-problem)
 (:domain ma_taxi-domain)
 (:objects
   g1 g2 c h1 h2 - location
   t1 t2 - taxi
   person1 - person1_type
   person2 - person2_type
   taxi1 - taxi1_type
   taxi2 - taxi2_type
 )
 (:init
  (directly_connected g1 c)
  (directly_connected g2 c)
  (directly_connected c g1)
  (directly_connected c g2)
  (directly_connected c h1)
  (directly_connected c h2)
  (directly_connected h1 c)
  (directly_connected h2 c)
  (a_pos person1 h1)
  (a_pos person2 h2)
  (at_ t1 g1)
  (at_ t2 g2)
  (empty t1)
  (empty t2)
  (free h1)
  (free h2)
  (free c)
  (a_goal_of person2 c))
 (:goal (and (a_pos person1 c) (a_pos person2 c)))
)