(define (domain logistics)
(:requirements :typing :equality :fluents)
(:types city place package agent - object
        truck airplane - agent
        airport location - place)
(:predicates (in-city ?loc - place ?city - city)
             (myAgent ?a - agent))
(:functions  (at ?a - agent) - place
          	 (in ?pkg - package) - (either place agent))
(:action LoadTruck
 :parameters    (?pkg - package ?truck - truck ?loc - place)
 :precondition  (and (myAgent ?truck) (= (at ?truck) ?loc) (= (in ?pkg) ?loc))
 :effect        (assign (in ?pkg) ?truck))
(:action LoadAirplane
 :parameters   (?pkg - package ?airplane - airplane ?loc - place)
 :precondition (and (myAgent ?airplane) (= (in ?pkg) ?loc) (= (at ?airplane) ?loc))
 :effect       (assign (in ?pkg) ?airplane))
(:action UnloadTruck
 :parameters   (?pkg - package ?truck - truck ?loc - place)
 :precondition (and (myAgent ?truck) (= (at ?truck) ?loc) (= (in ?pkg) ?truck))
 :effect       (assign (in ?pkg) ?loc))
(:action UnloadAirplane
 :parameters   (?pkg - package ?airplane - airplane ?loc - place)
 :precondition (and (myAgent ?airplane) (= (in ?pkg) ?airplane) (= (at ?airplane) ?loc))
 :effect       (assign (in ?pkg) ?loc))
(:action DriveTruck
 :parameters (?truck - truck ?loc-from - place ?loc-to - place ?city - city)
 :precondition (and (myAgent ?truck) (= (at ?truck) ?loc-from)
               (in-city ?loc-from ?city) (in-city ?loc-to ?city))
 :effect (assign (at ?truck) ?loc-to))
(:action FlyAirplane
 :parameters (?airplane - airplane ?loc-from - airport ?loc-to - airport)
 :precondition (= (at ?airplane) ?loc-from)
 :effect       (assign (at ?airplane) ?loc-to)))
