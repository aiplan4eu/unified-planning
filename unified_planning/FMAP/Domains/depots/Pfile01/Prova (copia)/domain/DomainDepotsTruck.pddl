(define (domain robots-domain)
(:requirements :typing :equality :fluents)
(:types surface place hoist - object
        depot distributor - (either place agent)
        truck - agent
        crate pallet - surface)
(:predicates 
  (myAgent ?a - truck)
  (clear ?x - (either surface hoist)))
(:functions
  (located ?h - hoist) - place
  (at ?t - truck) - place
  (placed ?p - pallet) - place
  (pos ?c - crate) - (either place truck)
  (on ?c - crate) - (either surface hoist truck))
(:action Drive
 :parameters ( ?t - truck ?x - place ?y - place)
 :precondition (and (myAgent ?t) (= (at ?t) ?x))
 :effect (and (assign (at ?t) ?y)))
(:action Load
 :parameters ( ?t - truck ?x - place ?c - crate ?h - hoist)
 :precondition (and (myAgent ?t) (= (at ?t) ?x) (= (pos ?c) ?x) (not (clear ?c)) (not (clear ?h)) (= (on ?c) ?h) (= (located ?h) ?x))
 :effect (and (assign (pos ?c) ?x) (assign (on ?c) ?h) (clear ?c) (clear ?h)))
(:action Unload
 :parameters ( ?t - truck ?x - place ?c - crate ?h - hoist)
 :precondition (and (myAgent ?t) (= (located ?h) ?x) (= (at ?t) ?x) (= (pos ?c) ?t) (= (on ?c) ?t) (clear ?h) (clear ?c))
 :effect (and (assign (pos ?c) ?x) (assign (on ?c) ?h) (not (clear ?c)) (not (clear ?h))))
)

