(define (problem ZTRAVEL-3-6)
(:domain zeno-travel)
(:objects
 plane1 plane2 plane3 - aircraft
 person1 person2 person3 person4 person5 person6 - person
 city0 city1 city2 city3 city4 - city
 fl0 fl1 fl2 fl3 fl4 fl5 fl6 - flevel
)
(:shared-data
  ((at ?a - aircraft) - city)
  ((in ?p - person) - (either city aircraft)) - 
(either plane1 plane2)
)
(:init
 (myAgent plane3)
 (= (at plane1) city0)
 (= (at plane2) city3)
 (= (at plane3) city0)
 (= (fuel-level plane3) fl3)
 (= (in person1) city1)
 (= (in person2) city0)
 (= (in person3) city2)
 (= (in person4) city0)
 (= (in person5) city3)
 (= (in person6) city4)
 (= (next fl0) fl1)
 (= (next fl1) fl2)
 (= (next fl2) fl3)
 (= (next fl3) fl4)
 (= (next fl4) fl5)
 (= (next fl5) fl6)
)
(:global-goal (and
 (= (at plane1) city3)
 (= (in person1) city0)
 (= (in person2) city0)
 (= (in person3) city1)
 (= (in person4) city0)
 (= (in person5) city3)
 (= (in person6) city2)
)))
