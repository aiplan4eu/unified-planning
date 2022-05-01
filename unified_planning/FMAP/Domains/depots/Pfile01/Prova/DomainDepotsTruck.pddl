(define (domain robots-domain)
(:requirements :strips :typing :negative-preconditions)
(:types surface agent place hoist - object
        depot distributor - (either place agent)
        truck - agent
        crate pallet - surface
)
(:predicates 
  (myAgent ?a - truck)
  (clear_s ?p0 - surface)
  (clear ?p0 - hoist)
)
(:functions
  (located ?h - hoist) - place
  (at ?t - truck) - place
  (placed ?p - pallet) - place
  (pos ?c - crate) - place
  (pos_u ?c - crate) - truck
  (on ?c - crate) - hoist
  (on_u ?c - crate) - truck
  (on_s ?c - crate) - surface)
(:action drive
 :parameters ( ?t - truck ?x - place ?y - place)
 :precondition (and (myAgent ?t) (= (at ?t) ?x))
 :effect (and (assign (at ?t) ?y)))
(:action load
 :parameters ( ?t - truck ?x - place ?c - crate ?h - hoist)
 :precondition (and (myAgent ?t) (= (at ?t) ?x) (= (pos ?c) ?x) (not (clear_s ?c)) (not (clear ?h)) (= (on ?c) ?h) (= (located ?h) ?x))
 :effect (and (assign (pos ?c) ?x) (assign (on ?c) ?h) (clear_s ?c) (clear ?h)))
(:action unload
 :parameters ( ?t - truck ?x - place ?c - crate ?h - hoist)
 :precondition (and (myAgent ?t) (= (located ?h) ?x) (= (at ?t) ?x) (= (pos_u ?c) ?t) (= (on_u ?c) ?t) (clear ?h) (clear_s ?c))
 :effect (and (assign (pos ?c) ?x) (assign (on ?c) ?h) (not (clear_s ?c)) (not (clear ?h))))
)

