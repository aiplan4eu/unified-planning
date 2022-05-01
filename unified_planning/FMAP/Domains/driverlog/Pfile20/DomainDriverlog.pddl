(define (domain driverlog)
(:requirements :typing :equality :fluents)
(:types location truck obj - object
        driver - agent)
(:predicates (link ?x ?y - location)
             (path ?x ?y - location)
             (empty ?v - truck)
             (myAgent ?a - agent))
(:functions  (at ?d - driver) - (either location truck)
          	 (pos ?t - truck) - location
          	 (in ?o - obj) - (either location truck))
(:action Load-Truck
 :parameters    (?obj - obj ?truck - truck ?loc - location)
 :precondition  (and (= (pos ?truck) ?loc) (= (in ?obj) ?loc))
 :effect        (assign (in ?obj) ?truck))
(:action Unload-Truck
 :parameters   (?obj - obj ?truck - truck ?loc - location)
 :precondition (and (= (pos ?truck) ?loc) (= (in ?obj) ?truck))
 :effect       (assign (in ?obj) ?loc))
(:action Board-Truck
 :parameters   (?driver - driver ?truck - truck ?loc - location)
 :precondition (and (myAgent ?driver) (= (pos ?truck) ?loc)
                    (= (at ?driver) ?loc) (empty ?truck))
 :effect       (and (assign (at ?driver) ?truck) (not (empty ?truck))))
(:action Disembark-Truck
 :parameters   (?driver - driver ?truck - truck ?loc - location)
 :precondition (and (myAgent ?driver) (= (pos ?truck) ?loc)
                    (= (at ?driver) ?truck))
 :effect       (and (assign (at ?driver) ?loc) (empty ?truck)))
(:action Drive-Truck
 :parameters (?truck - truck ?loc-from - location ?loc-to - location ?driver - driver)
 :precondition (and (myAgent ?driver) (= (pos ?truck) ?loc-from)
               (= (at ?driver) ?truck) (link ?loc-from ?loc-to))
 :effect (assign (pos ?truck) ?loc-to))
(:action Walk
 :parameters (?driver - driver ?loc-from - location ?loc-to - location)
 :precondition (and (myAgent ?driver) (= (at ?driver) ?loc-from)
                    (path ?loc-from ?loc-to))
 :effect       (assign (at ?driver) ?loc-to)))
