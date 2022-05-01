(define (problem ZTRAVEL-2-4)
(:domain zeno-travel)
(:objects
 plane1 plane2 - aircraft
 person1 person2 person3 person4 - person
 city0 city1 city2 - city
 fl0 fl1 fl2 fl3 fl4 fl5 fl6 - flevel
)
(:shared-data
  ((at ?a - aircraft) - city)
  ((in ?p - person) - (either city aircraft)) - 
plane1
)
(:init
 (myAgent plane2)
 (= (at plane1) city0)
 (= (at plane2) city2)
 (= (fuel-level plane2) fl5)
 (= (in person1) city0)
 (= (in person2) city0)
 (= (in person3) city1)
 (= (in person4) city1)
 (= (next fl0) fl1)
 (= (next fl1) fl2)
 (= (next fl2) fl3)
 (= (next fl3) fl4)
 (= (next fl4) fl5)
 (= (next fl5) fl6)
)
(:global-goal (and
 (= (at plane2) city2)
 (= (in person1) city1)
 (= (in person2) city0)
 (= (in person3) city0)
 (= (in person4) city1)
)))
