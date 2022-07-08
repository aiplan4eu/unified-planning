(define (problem ZTRAVEL-2-6)
(:domain zeno-travel)
(:objects
 plane1 plane2 - aircraft
 person1 person2 person3 person4 person5 person6 - person
 city0 city1 city2 city3 - city
 fl0 fl1 fl2 fl3 fl4 fl5 fl6 - flevel
)
(:shared-data
  ((at ?a - aircraft) - city)
  ((in ?p - person) - (either city aircraft)) - 
plane1
)
(:init
 (myAgent plane2)
 (= (at plane1) city2)
 (= (at plane2) city1)
 (= (fuel-level plane2) fl1)
 (= (in person1) city3)
 (= (in person2) city3)
 (= (in person3) city3)
 (= (in person4) city1)
 (= (in person5) city3)
 (= (in person6) city0)
 (= (next fl0) fl1)
 (= (next fl1) fl2)
 (= (next fl2) fl3)
 (= (next fl3) fl4)
 (= (next fl4) fl5)
 (= (next fl5) fl6)
)
(:global-goal (and
 (= (at plane2) city1)
 (= (in person1) city2)
 (= (in person3) city3)
 (= (in person4) city3)
 (= (in person5) city2)
 (= (in person6) city2)
)))
