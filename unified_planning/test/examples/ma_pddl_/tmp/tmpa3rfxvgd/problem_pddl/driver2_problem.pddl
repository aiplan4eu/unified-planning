(define (problem ma_logistic-problem)
 (:domain ma_logistic-domain)
 (:objects
   pos1 pos2 - location
   cit1 cit2 - city
   tru1 tru2 - truck
   apn1 - airplane
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
  (at_ tru2 pos2)
  (at_ obj21 pos2)
  (at_ obj22 pos2)
  (at_ obj23 pos2)
  (a_in_city driver2 pos2 cit2)
  (a_in_city driver2 apt2 cit2)
  (a_driving driver2 tru2)
  (a_pos driver2 pos2)
  (at_ apn1 apt2))
 (:goal (and (at_ obj11 apt1) (at_ obj23 pos1) (at_ obj13 pos1) (at_ obj21 pos1)))
)