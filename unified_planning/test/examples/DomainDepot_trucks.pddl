(define (domain pddl-domain)
(:requirements :strips :typing :negative-preconditions)
(:types surface agent place hoist - object
        depot distributor - (either place agent)
        truck - agent
        crate pallet - surface
)
(:predicates 
  (myAgent ?a - truck)
  (ciao ?x - surface)
  (clear ?x - (either surface hoist)))
(:functions
  (located ?h - hoist) - place
  (at ?t - truck) - place
  (placed ?p - pallet) - place
  (pos ?c - crate) - (either place truck)
  (on ?c - crate) - (either hoist truck surface)
)
(:action Drive
 :parameters ( ?t - truck ?x - place ?y - place)
 :precondition (and (myAgent ?t) (= (at ?t) ?x))
 :effect (and (assign (at ?t) ?y)))
(:action Load
 :parameters ( ?t - truck ?p - place ?c - crate ?h - hoist)
 :precondition (and (myAgent ?t) (= (at ?t) ?p) (= (pos ?c) ?p) (not (clear ?c)) (not (clear ?h)) (= (on ?c) ?h) (= (located ?h) ?p))
 :effect (and (clear ?h) (clear ?c) (assign (pos ?c) ?t) (assign (on ?c) ?t)))
(:action Unload
 :parameters ( ?t - truck ?p - place ?c - crate ?h - hoist)
 :precondition (and (myAgent ?t) (= (located ?h) ?p) (= (at ?t) ?p) (= (pos ?c) ?t) (= (on ?c) ?t) (clear ?h) (clear ?c))
 :effect (and (assign (pos ?c) ?p) (assign (on ?c) ?h) (not (clear ?c)) (not (clear ?h))))
)
