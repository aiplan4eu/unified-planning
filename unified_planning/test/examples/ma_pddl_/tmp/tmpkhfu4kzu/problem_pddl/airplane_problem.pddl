(define (problem ma_logistic-problem)
 (:domain ma_logistic-domain)
 (:objects
   pos1 pos2 - location
   cit1 cit2 - city
   obj21 obj22 obj23 obj11 obj13 obj12 - package
   apt2 apt1 - airport
   tru1 tru2 - truck_
   apn1 - airplane_
   truck1 - truck1_type
   truck2 - truck2_type
   airplane - airplane_type
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
  (at_ apn1 apt2)
  (a_pos airplane apt2))
 (:goal (and (at_ obj11 apt1) (at_ obj23 pos1) (at_ obj13 apt1) (at_ obj21 pos1)))
)