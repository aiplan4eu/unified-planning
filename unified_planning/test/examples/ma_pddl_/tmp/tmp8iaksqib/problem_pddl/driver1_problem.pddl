(define (problem ma_logistic-problem)
 (:domain ma_logistic-domain)
 (:objects
   pos1 - location
   cit1 - city
   tru1 - truck
   obj21 obj22 obj23 obj11 obj13 obj12 - package
   apt2 apt1 - airport
   driver1 - driver1_type
   driver2 - driver2_type
   driver3 - driver3_type
 )
 (:init
  (at_ tru1 pos1)
  (at_ obj11 pos1)
  (at_ obj12 pos1)
  (at_ obj13 pos1)
  (a_in_city driver1 pos1 cit1)
  (a_in_city driver1 apt1 cit1)
  (at_ tru2 pos2)
  (at_ obj21 pos2)
  (at_ obj22 pos2)
  (at_ obj23 pos2))
 (:goal (and (at_ obj11 apt1) (at_ obj23 pos1) (at_ obj13 pos1) (at_ obj21 pos1)))
)