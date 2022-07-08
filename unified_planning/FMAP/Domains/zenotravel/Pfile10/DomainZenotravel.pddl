(define (domain zeno-travel)
(:requirements :typing :equality :fluents)
(:types
    aircraft - agent
    person city flevel - object)
(:predicates
  (myAgent ?a - aircraft))
(:functions
  (at ?a - aircraft) - city
  (in ?p - person) - (either city aircraft)
  (fuel-level ?a - aircraft) - flevel
  (next ?l1 - flevel) - flevel)
(:action board
:parameters (?p - person ?a - aircraft ?c - city)
:precondition (and (myAgent ?a) (= (at ?a) ?c) (= (in ?p) ?c))
:effect (assign (in ?p) ?a))
(:action debark
:parameters (?p - person ?a - aircraft ?c - city)
:precondition (and (myAgent ?a) (= (at ?a) ?c) (= (in ?p) ?a))
:effect (assign (in ?p) ?c))
(:action fly
:parameters (?a - aircraft ?c1 ?c2 - city ?l1 ?l2 - flevel)
:precondition (and (myAgent ?a) (= (at ?a) ?c1)
                   (= (fuel-level ?a) ?l1) (= (next ?l2) ?l1))
:effect (and (assign (at ?a) ?c2) (assign (fuel-level ?a) ?l2)))
(:action zoom
:parameters (?a - aircraft ?c1 ?c2 - city ?l1 ?l2 ?l3 - flevel)
:precondition (and (myAgent ?a) (= (at ?a) ?c1)
        (= (fuel-level ?a) ?l1) (= (next ?l2) ?l1) (= (next ?l3) ?l2))
:effect (and (assign (at ?a) ?c2) (assign (fuel-level ?a) ?l3)))
(:action refuel
:parameters (?a - aircraft ?c - city ?l - flevel ?l1 - flevel)
:precondition (and (myAgent ?a) (= (fuel-level ?a) ?l)
                   (= (at ?a) ?c) (= (next ?l) ?l1))
:effect (assign (fuel-level ?a) ?l1)))
