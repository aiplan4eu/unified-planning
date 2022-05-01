(define (problem ZTRAVEL-1-3)
(:domain zeno-travel)
(:objects
 plane1 - aircraft
 person1 person2 person3 - person
 city0 city1 city2 - city
 fl0 fl1 fl2 fl3 fl4 fl5 fl6 - flevel
)
(:init
 (myAgent plane1)
 (= (at plane1) city0)
 (= (fuel-level plane1) fl2)
 (= (in person1) city2)
 (= (in person2) city1)
 (= (in person3) city2)
 (= (next fl0) fl1)
 (= (next fl1) fl2)
 (= (next fl2) fl3)
 (= (next fl3) fl4)
 (= (next fl4) fl5)
 (= (next fl5) fl6)
)
(:global-goal (and
 (= (at plane1) city2)
 (= (in person1) city1)
 (= (in person3) city2)
)))
