(define (problem ma_logistic-problem)
 (:domain ma_logistic-domain)
 (:objects
   pos1 pos2 - location
   cit1 cit2 - city
   obj21 obj22 obj23 obj11 obj13 obj12 - package
   apt2 apt1 - airport
   apn1 - airplane_
   truck1 - truck1_type
   truck2 - truck2_type
   airplane - airplane_type
 )
 (:init
  (a_pos truck1 pos1)
  (at_ obj11 pos1)
  (at_ obj12 pos1)
  (at_ obj13 pos1)
  (a_in_city truck1 pos1 cit1)
  (a_in_city truck1 apt1 cit1)
  (at_ obj21 pos2)
  (at_ obj22 pos2)
  (at_ obj23 pos2))
 (:goal (and (at_ obj11 apt1) (at_ obj23 pos1) (at_ obj13 apt1) (at_ obj21 pos1)))
)