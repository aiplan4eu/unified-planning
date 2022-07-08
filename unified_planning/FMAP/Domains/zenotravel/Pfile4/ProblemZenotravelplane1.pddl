(define (problem ZTRAVEL-2-5)
(:domain zeno-travel)
(:objects
 plane1 plane2 - aircraft
 person1 person2 person3 person4 person5 - person
 city0 city1 city2 - city
 fl0 fl1 fl2 fl3 fl4 fl5 fl6 - flevel
)
(:shared-data
  ((at ?a - aircraft) - city)
  ((in ?p - person) - (either city aircraft)) - 
plane2
)
(:init
 (myAgent plane1)
 (= (at plane1) city2)
 (= (at plane2) city2)
 (= (fuel-level plane1) fl5)
 (= (in person1) city0)
 (= (in person2) city1)
 (= (in person3) city0)
 (= (in person4) city0)
 (= (in person5) city2)
 (= (next fl0) fl1)
 (= (next fl1) fl2)
 (= (next fl2) fl3)
 (= (next fl3) fl4)
 (= (next fl4) fl5)
 (= (next fl5) fl6)
)
(:global-goal (and
 (= (at plane1) city0)
 (= (in person2) city2)
 (= (in person3) city0)
 (= (in person4) city1)
 (= (in person5) city2)
)))
