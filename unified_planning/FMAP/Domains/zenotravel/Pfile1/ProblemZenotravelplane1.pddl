(define (problem ZTRAVEL-1-2)
(:domain zeno-travel)
(:objects
 plane1 - aircraft
 person1 person2 - person
 city0 city1 city2 - city
 fl0 fl1 fl2 fl3 fl4 fl5 fl6 - flevel
)
(:init
 (myAgent plane1)
 (= (at plane1) city0)
 (= (fuel-level plane1) fl1)
 (= (in person1) city0)
 (= (in person2) city2)
 (= (next fl0) fl1)
 (= (next fl1) fl2)
 (= (next fl2) fl3)
 (= (next fl3) fl4)
 (= (next fl4) fl5)
 (= (next fl5) fl6)
)
(:global-goal (and
 (= (at plane1) city1)
 (= (in person1) city0)
 (= (in person2) city2)
)))
