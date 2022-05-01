(define (problem ZTRAVEL-3-7)
(:domain zeno-travel)
(:objects
 plane1 plane2 plane3 - aircraft
 person1 person2 person3 person4 person5 person6 person7 - person
 city0 city1 city2 city3 city4 city5 - city
 fl0 fl1 fl2 fl3 fl4 fl5 fl6 - flevel
)
(:shared-data
  ((at ?a - aircraft) - city)
  ((in ?p - person) - (either city aircraft)) - 
(either plane2 plane3)
)
(:init
 (myAgent plane1)
 (= (at plane1) city4)
 (= (at plane2) city4)
 (= (at plane3) city1)
 (= (fuel-level plane1) fl4)
 (= (in person1) city4)
 (= (in person2) city2)
 (= (in person3) city2)
 (= (in person4) city0)
 (= (in person5) city2)
 (= (in person6) city2)
 (= (in person7) city5)
 (= (next fl0) fl1)
 (= (next fl1) fl2)
 (= (next fl2) fl3)
 (= (next fl3) fl4)
 (= (next fl4) fl5)
 (= (next fl5) fl6)
)
(:global-goal (and
 (= (at plane1) city1)
 (= (in person1) city4)
 (= (in person2) city1)
 (= (in person3) city2)
 (= (in person4) city2)
 (= (in person5) city2)
 (= (in person6) city4)
 (= (in person7) city0)
)))
